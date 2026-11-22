"""E2 · Fuente geoespacial: centrales de abasto destino del limón de Colima.

Bronce -> Plata: lee las respuestas de Nominatim (data/bronce/osm_centrales/*.json) y crea
  data/plata/centrales_geo.geojson (EPSG:4326) con la precisión de la ubicación y su linaje.
Plata -> Oro: une las centrales con el precio del limón del último año y calcula la distancia
  geodésica desde Tecomán, Colima (zona productora). Produce
  data/oro/centrales_precio_distancia.geojson y docs/E2/mapa_centrales.png.

Uso:  python src/geo_centrales.py   (después de src/pipeline.py)
"""
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests
from pyproj import Geod
from scipy.stats import spearmanr
from shapely.geometry import Point

RAIZ = Path(__file__).resolve().parents[1]
BRONCE = RAIZ / "data" / "bronce"
ORIGEN = ("Tecomán, Colima", -103.8750, 18.9083)     # principal zona productora de limón del estado
PAISES_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
              "ne_50m_admin_0_countries.geojson")
UA = {"User-Agent": "TrustedDataLab-ITColima/0.1 (proyecto escolar)"}


def centrales_plata():
    filas = []
    for archivo in sorted((BRONCE / "osm_centrales").glob("*.json")):
        d = json.loads(archivo.read_text(encoding="utf-8"))
        if not d["respuesta"]:
            continue
        r = d["respuesta"][0]
        filas.append({"central": d["central"], "estado": d["estado"], "precision": d["precision"],
                      "lugar_osm": r["display_name"], "osm_tipo": f'{r.get("osm_type")}/{r.get("osm_id")}',
                      "archivo_bronce": f"osm_centrales/{archivo.name}", "capturado_utc": d["capturado_utc"],
                      "licencia": d["licencia"], "geometry": Point(float(r["lon"]), float(r["lat"]))})
    gdf = gpd.GeoDataFrame(filas, crs="EPSG:4326")
    gdf.to_file(RAIZ / "data" / "plata" / "centrales_geo.geojson", driver="GeoJSON")
    return gdf


def contexto_mexico():
    """Capa de contexto: contornos de países (Natural Earth, dominio público), guardada en Bronce la primera vez."""
    archivo = BRONCE / "naturalearth" / "ne_50m_admin_0_countries.geojson"
    if not archivo.exists():
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(requests.get(PAISES_URL, headers=UA, timeout=180).content)
    return gpd.read_file(archivo).cx[-120:-85, 14:34]


def main():
    centrales = centrales_plata()
    plata = pd.read_csv(RAIZ / "data" / "plata" / "sniim_limon_plata.csv", parse_dates=["fecha"])
    ultimo_anio = plata[plata["fecha"] > plata["fecha"].max() - pd.Timedelta(days=365)]
    precios = (ultimo_anio.groupby("central")
               .agg(precio_mediano=("precio_frec", "median"), registros=("precio_frec", "size"),
                    ultimo_dato=("fecha", "max")).reset_index())

    oro = centrales.merge(precios, on="central", how="left")
    geod = Geod(ellps="WGS84")
    oro["distancia_km"] = [round(geod.inv(ORIGEN[1], ORIGEN[2], p.x, p.y)[2] / 1000, 1) for p in oro.geometry]
    oro["ultimo_dato"] = oro["ultimo_dato"].dt.strftime("%Y-%m-%d")
    oro.to_file(RAIZ / "data" / "oro" / "centrales_precio_distancia.geojson", driver="GeoJSON")

    con_precio = oro.dropna(subset=["precio_mediano"])
    rho, p = spearmanr(con_precio["distancia_km"], con_precio["precio_mediano"])
    print(f"Centrales: {len(oro)} (con precio el último año: {len(con_precio)}) · "
          f"Spearman distancia-precio rho={rho:.2f}, p={p:.3f}")

    # Mapa
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_facecolor("#e3eef8")
    contexto_mexico().plot(ax=ax, color="#f1efe6", edgecolor="#a8a89a", linewidth=0.6)
    for _, f in con_precio.iterrows():
        ax.plot([ORIGEN[1], f.geometry.x], [ORIGEN[2], f.geometry.y], color="#9db4d6", lw=0.8, zorder=1)
    sc = ax.scatter(con_precio.geometry.x, con_precio.geometry.y, c=con_precio["precio_mediano"], cmap="YlOrRd",
                    s=40 + con_precio["registros"] / 4, edgecolor="#333", linewidth=0.6, zorder=3)
    ax.plot(ORIGEN[1], ORIGEN[2], marker="*", color="#2e7d32", markersize=18, zorder=4)
    ax.annotate("Tecomán (origen)", (ORIGEN[1], ORIGEN[2]), xytext=(6, -12), textcoords="offset points",
                fontweight="bold", color="#2e7d32")
    # etiquetas alternadas a derecha e izquierda para que no se encimen las centrales de una misma ciudad
    for k, (_, f) in enumerate(con_precio.sort_values(["estado", "central"]).iterrows()):
        derecha = k % 2 == 0
        ax.annotate(f"{f['central'][:30]}\n${f['precio_mediano']:.0f}/kg · {f['distancia_km']:.0f} km",
                    (f.geometry.x, f.geometry.y), xytext=(7, 2) if derecha else (-7, -18), textcoords="offset points",
                    fontsize=6.5, ha="left" if derecha else "right",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75))
    fig.colorbar(sc, ax=ax, label="Precio frecuente mediano del último año ($/kg)", shrink=0.7)
    ax.set_xlim(-117.5, -96.5); ax.set_ylim(17.5, 32.8)
    ax.set_title("Destinos del limón #5 de Colima: precio al mayoreo y distancia desde Tecomán\n"
                 f"(SNIIM + OpenStreetMap · tamaño = registros · Spearman ρ = {rho:.2f}, p = {p:.3f})")
    ax.set_xlabel("Longitud"); ax.set_ylabel("Latitud")
    fig.tight_layout()
    salida = RAIZ / "docs" / "E2" / "mapa_centrales.png"
    salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida, dpi=170); plt.close(fig)
    (RAIZ / "docs" / "E2" / "geo_resumen.json").write_text(json.dumps({
        "centrales": len(oro), "con_precio": len(con_precio), "spearman_rho": round(rho, 3), "p_valor": round(p, 4),
        "precision": oro["precision"].value_counts().to_dict()}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
