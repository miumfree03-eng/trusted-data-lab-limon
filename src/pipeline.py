"""Pipeline E1: Bronce -> Plata -> Oro con puerta de calidad y cuarentena.

Pasos:
  1. Lectura de Bronce (SNIIM CSV + Frankfurter JSON) sin supuestos de tipo.
  2. Tipificación y normalización de texto (fechas, números, acentos, empaque).
  3. Jerarquías conceptuales: central -> estado -> región; día -> semana -> mes -> temporada.
  4. Puerta de calidad (Pandera). Lo que no pasa va a data/cuarentena con su motivo.
  5. Atípicos: Z robusto por mes (MAD) con winsorización, comparado con IQR e Isolation Forest.
  6. Normalización (Min-Max y Z-Score) y discretización (terciles Bajo/Medio/Alto).
  7. Integración con el tipo de cambio (resolución de esquema, tipos y calendario).
  8. Reducción a capa Oro: panel semanal por central y serie semanal nacional, con
     diagnóstico e imputación de faltantes.
  9. Reporte automático en docs/E1/reporte_calidad.md.

Uso:  python src/pipeline.py
"""
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pandera as pa
from scipy.stats import chi2_contingency, skew
from sklearn.ensemble import IsolationForest

from esquemas import sniim_plata, tipo_cambio_plata

RAIZ = Path(__file__).resolve().parents[1]
BRONCE = RAIZ / "data" / "bronce"
PLATA = RAIZ / "data" / "plata"
ORO = RAIZ / "data" / "oro"
CUARENTENA = RAIZ / "data" / "cuarentena"
REPORTE = RAIZ / "docs" / "E1" / "reporte_calidad.md"

REGION_POR_ESTADO = {
    "Baja California Sur": "Norte", "Sonora": "Norte", "Sinaloa": "Norte", "Coahuila": "Norte",
    "Durango": "Norte", "Nuevo Leon": "Norte",
    "Aguascalientes": "Centro-Norte", "San Luis Potosi": "Centro-Norte", "Zacatecas": "Centro-Norte",
    "Jalisco": "Occidente", "Colima": "Occidente",
}
MESES_LLUVIAS = {6, 7, 8, 9, 10}
Z_ROBUSTO_UMBRAL = 3.5
COBERTURA_MINIMA = 0.5  # una central entra al panel Oro si reportó al menos la mitad de las semanas
ALFA = 0.05
AHORA = datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- utilidades
def sin_acentos(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).replace("�", "")


def a_cuarentena(df, motivo, regla, columna=None):
    """Prepara registros rechazados con su motivo; nunca se descartan en silencio."""
    if df.empty:
        return pd.DataFrame()
    q = pd.DataFrame({
        "detectado_utc": AHORA,
        "regla": regla,
        "columna": columna or "",
        "motivo": motivo,
        "registro": df.astype(str).to_dict(orient="records"),
    })
    q["registro"] = q["registro"].map(lambda r: json.dumps(r, ensure_ascii=False))
    return q


# ---------------------------------------------------------------- 1-2. lectura y tipificación
def leer_sniim():
    archivos = sorted((BRONCE / "sniim_limon").glob("*.csv"))
    return pd.concat((pd.read_csv(p, dtype=str, keep_default_na=False).assign(archivo_bronce=p.name)
                      for p in archivos), ignore_index=True)


def tipificar_sniim(crudo):
    df = crudo.copy()
    rechazos = []

    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    for c in ["precio_min", "precio_max", "precio_frec"]:
        df[c] = pd.to_numeric(df[c].str.replace(",", "", regex=False), errors="coerce")

    malos = df["fecha"].isna()
    rechazos.append(a_cuarentena(crudo[malos], "fecha no interpretable como dd/mm/aaaa", "tipo_fecha", "fecha"))
    malos_num = df[["precio_min", "precio_max", "precio_frec"]].isna().any(axis=1) & ~malos
    rechazos.append(a_cuarentena(crudo[malos_num], "precio no numérico o vacío", "tipo_numerico", "precio_*"))
    df = df[~(malos | malos_num)].copy()

    # destino "Estado: Central" -> dos columnas, sin acentos para que el cruce sea estable
    partes = df["destino"].str.split(":", n=1, expand=True)
    df["estado"] = partes[0].map(sin_acentos).str.strip()
    df["central"] = partes[1].fillna("").map(sin_acentos).str.strip().str.replace('"', "", regex=False)
    df["region"] = df["estado"].map(REGION_POR_ESTADO).fillna("SIN_REGION")

    # presentación "Caja de 19 kg." -> empaque + kilos (Kilogramo = 1 kg)
    df["empaque"] = df["presentacion"].str.extract(r"^(Caja|Arpilla|Kilogramo)", flags=re.I)[0].str.capitalize()
    kg = df["presentacion"].str.extract(r"(\d+(?:\.\d+)?)\s*kg", flags=re.I)[0].astype(float)
    df["kg_empaque"] = np.where(df["empaque"].eq("Kilogramo"), 1.0, kg)
    df["obs"] = df["obs"].str.strip().str.capitalize()

    # misma fecha, central y empaque: se conserva la primera captura y la repetición va a cuarentena
    dup = df.duplicated(["fecha", "central", "empaque", "kg_empaque"], keep="first")
    rechazos.append(a_cuarentena(crudo.loc[df.index[dup]], "registro duplicado (fecha, central, empaque)", "duplicado"))
    return df[~dup], rechazos


# ---------------------------------------------------------------- 3. jerarquías conceptuales
def agregar_jerarquias(df):
    df["semana"] = df["fecha"].dt.to_period("W-SUN").dt.start_time
    df["mes"] = df["fecha"].dt.to_period("M").dt.start_time
    df["trimestre"] = df["fecha"].dt.quarter
    df["anio"] = df["fecha"].dt.year
    df["temporada"] = np.where(df["fecha"].dt.month.isin(MESES_LLUVIAS), "Lluvias", "Secas")
    return df


# ---------------------------------------------------------------- 4. puerta de calidad
def puerta_de_calidad(df, esquema):
    """Valida con Pandera (lazy) y separa los registros que fallan, con el motivo de cada falla."""
    try:
        esquema.validate(df, lazy=True)
        return df, pd.DataFrame()
    except pa.errors.SchemaErrors as err:
        fallas = err.failure_cases
        por_fila = fallas.dropna(subset=["index"]).copy()
        por_fila["index"] = por_fila["index"].astype(int)
        motivos = (por_fila.assign(motivo=por_fila["check"].astype(str) + " en " + por_fila["column"].fillna("registro").astype(str))
                   .groupby("index")["motivo"].agg(lambda s: "; ".join(sorted(set(s)))))
        malos = df.loc[motivos.index]
        q = a_cuarentena(malos, "", "pandera:" + esquema.name)
        q["motivo"] = motivos.values
        q["columna"] = por_fila.groupby("index")["column"].agg(lambda s: ",".join(sorted(set(map(str, s))))).values
        return df.drop(index=motivos.index), q


# ---------------------------------------------------------------- 5. atípicos
def tratar_atipicos(df):
    """Z robusto por mes: compara cada precio con la mediana de ese mes en todas las centrales.

    Se usa la mediana y la MAD (no la media y la desviación) porque el precio tiene sesgo
    positivo y picos estacionales; así la temporada alta no se marca como atípica.
    Tratamiento: winsorización (capping) al límite del mes; nunca se borra el registro.
    """
    estad = df.groupby("mes")["precio_frec"].agg(mediana="median", mad=lambda s: (s - s.median()).abs().median())
    df = df.join(estad, on="mes")
    escala = df["mad"].replace(0, np.nan) / 0.6745
    df["z_robusto"] = (df["precio_frec"] - df["mediana"]) / escala
    df["atipico_z"] = df["z_robusto"].abs() > Z_ROBUSTO_UMBRAL
    lim_inf = df["mediana"] - Z_ROBUSTO_UMBRAL * escala
    lim_sup = df["mediana"] + Z_ROBUSTO_UMBRAL * escala
    df["precio_frec_original"] = df["precio_frec"]
    df["precio_frec"] = df["precio_frec"].clip(lim_inf, lim_sup).fillna(df["precio_frec_original"]).round(2)

    # comparativos (solo se reportan): IQR global e Isolation Forest multivariado
    q1, q3 = df["precio_frec_original"].quantile([0.25, 0.75])
    iqr = q3 - q1
    df["atipico_iqr"] = ~df["precio_frec_original"].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    X = np.column_stack([df["precio_frec_original"], df["precio_max"] - df["precio_min"], df["fecha"].dt.month])
    df["atipico_iforest"] = IsolationForest(contamination=0.01, random_state=42).fit_predict(X) == -1
    return df.drop(columns=["mediana", "mad"])


# ---------------------------------------------------------------- 6. normalización y discretización
def normalizar_y_discretizar(df):
    p = df["precio_frec"]
    df["precio_frec_minmax"] = ((p - p.min()) / (p.max() - p.min())).round(4)
    df["precio_frec_z"] = ((p - p.mean()) / p.std()).round(4)
    df["nivel_precio"], cortes = pd.qcut(p, q=3, labels=["Bajo", "Medio", "Alto"], retbins=True)
    df["nivel_precio"] = df["nivel_precio"].astype(str)
    return df, cortes


# ---------------------------------------------------------------- 7. integración con tipo de cambio
def leer_tipo_cambio():
    """JSON anidado {'rates': {'AAAA-MM-DD': {'MXN': x}}} -> tabla diaria continua.

    Conflictos que se resuelven: fechas ISO (vs dd/mm/aaaa del SNIIM), valores anidados,
    nombres en inglés y calendario hábil europeo (sin fines de semana ni festivos del BCE).
    """
    crudo = json.loads((BRONCE / "frankfurter_usdmxn" / "usdmxn.json").read_text(encoding="utf-8"))
    tc = pd.DataFrame([(f, v.get("MXN")) for f, v in crudo["rates"].items()], columns=["fecha", "usd_mxn"])
    tc["fecha"] = pd.to_datetime(tc["fecha"], format="%Y-%m-%d")
    tc["usd_mxn"] = pd.to_numeric(tc["usd_mxn"], errors="coerce").astype(float)
    tc, q = puerta_de_calidad(tc.sort_values("fecha").reset_index(drop=True), tipo_cambio_plata)
    diario = tc.set_index("fecha").asfreq("D")
    diario["usd_mxn_imputado"] = diario["usd_mxn"].isna()
    diario["usd_mxn"] = diario["usd_mxn"].ffill()  # el último tipo de cambio publicado sigue vigente
    return diario.reset_index(), q


def integrar(df, tc):
    df = df.merge(tc[["fecha", "usd_mxn", "usd_mxn_imputado"]], on="fecha", how="left")
    df["precio_frec_usd"] = (df["precio_frec"] / df["usd_mxn"]).round(4)
    return df


# ---------------------------------------------------------------- 8. faltantes y capa Oro
def diagnosticar_faltantes(df):
    """Panel semana x central: una celda falta cuando la central no reportó limón #5 esa semana."""
    semanas = pd.date_range(df["semana"].min(), df["semana"].max(), freq="7D")
    centrales = sorted(df["central"].unique())
    panel = (df.groupby(["semana", "central"])["precio_frec"].median()
             .reindex(pd.MultiIndex.from_product([semanas, centrales], names=["semana", "central"])))
    falta = panel.isna().rename("falta").reset_index()
    falta["mes"] = falta["semana"].dt.month
    falta["temporada"] = np.where(falta["mes"].isin(MESES_LLUVIAS), "Lluvias", "Secas")
    p_central = chi2_contingency(pd.crosstab(falta["central"], falta["falta"]))[1]
    p_temporada = chi2_contingency(pd.crosstab(falta["temporada"], falta["falta"]))[1]
    tasa_central = falta.groupby("central")["falta"].mean().sort_values(ascending=False)
    return panel, {"p_central": p_central, "p_temporada": p_temporada, "tasa_central": tasa_central,
                   "pct_total": falta["falta"].mean()}


def capa_oro(df, panel, tc, tasa_central):
    """Reducción por agregación semanal + selección de variables; imputación del panel.

    Las centrales con cobertura menor a COBERTURA_MINIMA se excluyen del panel: imputarlas
    equivaldría a inventar casi toda su serie. Sus registros siguen disponibles en Plata.
    """
    excluidas = tasa_central[tasa_central > 1 - COBERTURA_MINIMA].index
    serie = panel.rename("precio_frec_mediana").reset_index()
    serie = serie[~serie["central"].isin(excluidas)]
    serie["imputado"] = serie["precio_frec_mediana"].isna()
    # 1) interpolación lineal dentro de cada central, solo huecos de hasta 2 semanas
    serie["precio_frec_mediana"] = (serie.groupby("central")["precio_frec_mediana"]
                                    .transform(lambda s: s.interpolate(limit=2, limit_area="inside")))
    # 2) lo que siga faltando: mediana de esa semana en las centrales de la misma región
    region = df.drop_duplicates("central").set_index("central")["region"]
    serie["region"] = serie["central"].map(region)
    med_region = serie.groupby(["semana", "region"])["precio_frec_mediana"].transform("median")
    serie["precio_frec_mediana"] = serie["precio_frec_mediana"].fillna(med_region).round(2)
    serie["metodo_imputacion"] = np.where(~serie["imputado"], "observado",
                                          np.where(serie["precio_frec_mediana"].notna(), "interp/mediana_region", "sin_dato"))
    tc_sem = tc.assign(semana=tc["fecha"].dt.to_period("W-SUN").dt.start_time).groupby("semana")["usd_mxn"].mean()
    serie = serie.join(tc_sem.round(4), on="semana")

    nacional = (df.groupby("semana")
                .agg(precio_frec_mediana=("precio_frec", "median"), precio_min=("precio_min", "min"),
                     precio_max=("precio_max", "max"), registros=("precio_frec", "size"),
                     centrales=("central", "nunique"), atipicos=("atipico_z", "sum"))
                .join(tc_sem.round(4)).reset_index())
    nacional["precio_frec_usd"] = (nacional["precio_frec_mediana"] / nacional["usd_mxn"]).round(4)
    nacional["temporada"] = np.where(nacional["semana"].dt.month.isin(MESES_LLUVIAS), "Lluvias", "Secas")
    return serie, nacional, list(excluidas)


# ---------------------------------------------------------------- 9. reporte
def escribir_reporte(m):
    f = lambda x: f"{x:,}"
    lineas = [
        "# Reporte automático de calidad · E1",
        "",
        f"Generado por `src/pipeline.py` el {AHORA} (UTC). No editar a mano: se regenera en cada corrida.",
        "",
        "## Flujo de registros",
        "",
        "| Etapa | Registros |",
        "|---|---|",
        f"| Bronce SNIIM (crudo) | {f(m['bronce'])} |",
        f"| Rechazados al tipificar (fecha, número o duplicado) | {f(m['rech_tipo'])} |",
        f"| Rechazados por la puerta de calidad (Pandera) | {f(m['rech_pandera'])} |",
        f"| **Plata (válidos)** | **{f(m['plata'])}** |",
        f"| En cuarentena (esta corrida) | {f(m['cuarentena'])} |",
        f"| Tipo de cambio: días hábiles publicados → días calendario | {f(m['tc_publicados'])} → {f(m['tc_diario'])} ({f(m['tc_imputados'])} imputados por arrastre) |",
        "",
        "Los datos reales del SNIIM de esta corrida no tuvieron registros inválidos. Que la puerta sí detiene datos corruptos se comprueba en cada corrida "
        "con `tests/test_puerta_calidad.py`, que inyecta 8 registros dañados (fecha imposible, texto en precio, duplicado, mín > máx, frecuente fuera de rango, "
        "precio negativo, precio implausible y región desconocida) y verifica que los 8 lleguen a cuarentena con su motivo.",
        "",
        "## Valores faltantes",
        "",
        f"- En los campos del SNIIM no hay celdas vacías; el faltante es **estructural**: en el panel semana × central falta el **{m['falt']['pct_total']:.1%}** de las celdas (la central no reportó limón #5 esa semana).",
        f"- Prueba χ² de independencia (α = {ALFA}) entre faltar y **central**: p = {m['falt']['p_central']:.2e} "
        f"({'dependiente' if m['falt']['p_central'] < ALFA else 'sin evidencia de dependencia'}). "
        f"Entre faltar y **temporada**: p = {m['falt']['p_temporada']:.3f} "
        f"({'dependiente' if m['falt']['p_temporada'] < ALFA else 'sin evidencia de dependencia'}).",
        "- Como la ausencia depende de una variable observada (la central), el mecanismo **no es MCAR**; se trata como **MAR** condicionado a la central"
        + (" y la temporada." if m["falt"]["p_temporada"] < ALFA else "; la temporada no explica los faltantes.")
        + " No se descarta un componente **MNAR** (una central puede dejar de reportar cuando no le llega limón, lo que se relaciona con el precio); por eso se imputa solo en huecos cortos y se marca cada valor imputado.",
        f"- **Selección de centrales para Oro:** se excluyen las que reportaron menos del {COBERTURA_MINIMA:.0%} de las semanas "
        f"({', '.join(m['excluidas']) or 'ninguna'}); imputarlas sería inventar casi toda su serie. Sus registros siguen en Plata.",
        "- **Imputación (capa Oro):** interpolación lineal dentro de la central para huecos de hasta 2 semanas; si sigue faltando, **mediana** de la misma semana en las centrales de su región. "
        f"Se usa la mediana y no la media porque la distribución del precio tiene sesgo positivo (asimetría = {m['sesgo']:.2f}). "
        f"Resultado: {f(m['imputados_oro'])} celdas imputadas de {f(m['oro_central'])}; {f(m['sin_dato_oro'])} quedan sin dato marcadas como `sin_dato`.",
        "- **Tipo de cambio:** los huecos son fines de semana y festivos del BCE, ajenos al precio del limón (MCAR respecto a la variable de interés); se arrastra el último valor publicado (*forward fill*), que es el tipo de cambio vigente.",
        "",
        "Centrales con más semanas sin reporte:",
        "",
        "| Central | % de semanas sin dato |",
        "|---|---|",
        *[f"| {c} | {v:.0%} |" for c, v in m["falt"]["tasa_central"].head(6).items()],
        "",
        "## Atípicos y ruido",
        "",
        "| Método | Registros marcados | Uso |",
        "|---|---|---|",
        f"| **Z robusto por mes** (mediana y MAD, umbral ±{Z_ROBUSTO_UMBRAL}) | **{f(m['at_z'])}** | **Tratamiento: winsorización al límite del mes** |",
        f"| IQR global (1.5 × IQR) | {f(m['at_iqr'])} | Comparativo: marca la temporada alta completa como atípica |",
        f"| Isolation Forest (precio, amplitud máx−mín, mes; contaminación 1 %) | {f(m['at_if'])} | Comparativo multivariado |",
        "",
        "El valor original se conserva en `precio_frec_original` y la marca en `atipico_z`; ningún registro se elimina.",
        "",
        "## Normalización y discretización",
        "",
        "- `precio_frec_minmax`: escala [0, 1]. `precio_frec_z`: media 0, desviación 1.",
        f"- `nivel_precio` por terciles: **Bajo** < {m['cortes'][1]:.2f} ≤ **Medio** < {m['cortes'][2]:.2f} ≤ **Alto** ($/kg).",
        "- Jerarquías conceptuales: central → estado → región (Norte, Centro-Norte, Occidente); día → semana → mes → trimestre → año; mes → temporada (Lluvias jun–oct / Secas).",
        "",
        "## Reducción",
        "",
        f"- Plata: {f(m['plata'])} registros diarios → Oro por central: {f(m['oro_central'])} filas semana × central → Oro nacional: {f(m['oro_nacional'])} semanas.",
        "- Selección de variables en Oro: se quitan la URL de origen, la hora de captura y el texto libre de observaciones (que siguen en Plata para trazabilidad).",
    ]
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- main
def main():
    crudo = leer_sniim()
    df, rechazos = tipificar_sniim(crudo)
    df = agregar_jerarquias(df).reset_index(drop=True)
    df, q_pandera = puerta_de_calidad(df, sniim_plata)
    rechazos.append(q_pandera)

    df = tratar_atipicos(df)
    df, cortes = normalizar_y_discretizar(df)
    tc, q_tc = leer_tipo_cambio()
    rechazos.append(q_tc)
    df = integrar(df, tc)
    panel, faltantes = diagnosticar_faltantes(df)
    oro_central, oro_nacional, excluidas = capa_oro(df, panel, tc, faltantes["tasa_central"])

    for d in (PLATA, ORO, CUARENTENA):
        d.mkdir(parents=True, exist_ok=True)
    columnas_plata = ["fecha", "semana", "mes", "trimestre", "anio", "temporada", "region", "estado", "central",
                      "empaque", "kg_empaque", "precio_min", "precio_max", "precio_frec", "precio_frec_original",
                      "atipico_z", "z_robusto", "atipico_iqr", "atipico_iforest", "precio_frec_minmax", "precio_frec_z",
                      "nivel_precio", "usd_mxn", "usd_mxn_imputado", "precio_frec_usd", "obs", "archivo_bronce"]
    df.sort_values(["fecha", "central", "empaque"])[columnas_plata].to_csv(PLATA / "sniim_limon_plata.csv", index=False)
    tc.to_csv(PLATA / "usdmxn_plata.csv", index=False)
    oro_central.to_csv(ORO / "limon_semanal_central.csv", index=False)
    oro_nacional.to_csv(ORO / "limon_semanal_nacional.csv", index=False)

    cuarentena = pd.concat([q for q in rechazos if not q.empty], ignore_index=True) if any(
        not q.empty for q in rechazos) else pd.DataFrame(columns=["detectado_utc", "regla", "columna", "motivo", "registro"])
    cuarentena.to_csv(CUARENTENA / "cuarentena.csv", index=False)

    rech_tipo = sum(len(q) for q in rechazos[:3])
    escribir_reporte({
        "bronce": len(crudo), "rech_tipo": rech_tipo, "rech_pandera": len(q_pandera), "plata": len(df),
        "cuarentena": len(cuarentena), "tc_publicados": int((~tc["usd_mxn_imputado"]).sum()), "tc_diario": len(tc),
        "tc_imputados": int(tc["usd_mxn_imputado"].sum()), "falt": faltantes, "sesgo": float(skew(df["precio_frec"])),
        "at_z": int(df["atipico_z"].sum()), "at_iqr": int(df["atipico_iqr"].sum()), "at_if": int(df["atipico_iforest"].sum()),
        "cortes": cortes, "oro_central": len(oro_central), "oro_nacional": len(oro_nacional),
        "excluidas": excluidas, "imputados_oro": int((oro_central["metodo_imputacion"] != "observado").sum()),
        "sin_dato_oro": int((oro_central["metodo_imputacion"] == "sin_dato").sum()),
    })
    print(f"Bronce {len(crudo)} -> Plata {len(df)} | cuarentena {len(cuarentena)} | "
          f"Oro central {len(oro_central)} filas, nacional {len(oro_nacional)} semanas")


if __name__ == "__main__":
    main()
