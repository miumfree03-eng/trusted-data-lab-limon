"""Extractor ético de precios al mayoreo del limón de Colima (SNIIM, Secretaría de Economía).

Capa Bronce: guarda los registros tal como los publica el SNIIM, sin limpiar,
un CSV por mes en data/bronce/sniim_limon/AAAA-MM.csv, y anota cada corrida
en data/bronce/_bitacora_capturas.csv.

Es incremental: solo vuelve a pedir los meses que faltan y el mes en curso.

Uso:
    python extractores/sniim_limon.py                 # incremental
    python extractores/sniim_limon.py --desde 2022-01 # carga histórica
"""
import argparse
import csv
import re
import sys
import time
import urllib.robotparser
from datetime import date, datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "data" / "bronce" / "sniim_limon"
BITACORA = RAIZ / "data" / "bronce" / "_bitacora_capturas.csv"

SITIO = "http://www.economia-sniim.gob.mx"
URL = SITIO + "/NUEVO/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ResultadosConsultaFechaFrutasYHortalizas.aspx"
USER_AGENT = "TrustedDataLab-ITColima/0.1 (proyecto escolar; Instituto Tecnologico de Colima)"
PRODUCTO_ID, PRODUCTO = 421, "Limón c/semilla # 5 - Primera"
ORIGEN_ID, ORIGEN = 8, "Colima"
PAUSA_SEG = 3  # cortesía con el servidor entre peticiones
COLUMNAS = ["fecha", "presentacion", "destino", "precio_min", "precio_max", "precio_frec", "obs",
            "producto", "origen", "fuente_url", "capturado_utc"]

FILA = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
CELDA = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)


def permitido(url):
    rp = urllib.robotparser.RobotFileParser(SITIO + "/robots.txt")
    rp.read()
    return rp.can_fetch(USER_AGENT, url)


def meses(desde, hasta):
    a, m = desde
    while (a, m) <= hasta:
        yield a, m
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)


def fin_de_mes(a, m):
    sig = date(a + 1, 1, 1) if m == 12 else date(a, m + 1, 1)
    return date.fromordinal(sig.toordinal() - 1)


def extraer_filas(html):
    """Regresa las filas de la tabla de resultados (las que empiezan con una fecha)."""
    filas = []
    for tr in FILA.findall(html):
        celdas = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>|&nbsp;", " ", c)).strip() for c in CELDA.findall(tr)]
        if celdas and re.fullmatch(r"\d{2}/\d{2}/\d{4}", celdas[0]) and len(celdas) >= 6:
            filas.append((celdas + [""])[:7])
    return filas


def capturar_mes(sesion, a, m):
    params = {
        "fechaInicio": f"01/{m:02d}/{a}", "fechaFinal": fin_de_mes(a, m).strftime("%d/%m/%Y"),
        "ProductoId": PRODUCTO_ID, "OrigenId": ORIGEN_ID, "Origen": ORIGEN,
        "DestinoId": -1, "Destino": "Todos", "PreciosPorId": 2, "RegistrosPorPagina": 5000,
    }
    r = sesion.get(URL, params=params, timeout=120)
    r.raise_for_status()
    r.encoding = "utf-8"
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return [f + [PRODUCTO, ORIGEN, r.url, ahora] for f in extraer_filas(r.text)]


def anotar_bitacora(fuente, periodo, registros, estado, detalle=""):
    nuevo = not BITACORA.exists()
    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    with BITACORA.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["capturado_utc", "fuente", "periodo", "registros", "estado", "detalle"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), fuente, periodo, registros, estado, detalle])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default=None, help="AAAA-MM; por defecto, el primer mes que falte")
    args = ap.parse_args()

    if not permitido(URL):
        sys.exit("robots.txt no permite consultar esta ruta; no se captura nada.")

    hoy = date.today()
    DESTINO.mkdir(parents=True, exist_ok=True)
    existentes = sorted(p.stem for p in DESTINO.glob("*.csv"))
    if args.desde:
        inicio = tuple(map(int, args.desde.split("-")))
    elif existentes:
        inicio = tuple(map(int, existentes[-1].split("-")))  # se vuelve a pedir el último mes por si estaba incompleto
    else:
        inicio = (hoy.year - 3, 1)

    sesion = requests.Session()
    sesion.headers["User-Agent"] = USER_AGENT
    total = 0
    for a, m in meses(inicio, (hoy.year, hoy.month)):
        periodo = f"{a}-{m:02d}"
        try:
            filas = capturar_mes(sesion, a, m)
        except requests.RequestException as e:
            anotar_bitacora("sniim_limon", periodo, 0, "error", str(e)[:200])
            print(f"{periodo}: error {e}")
            continue
        if filas:
            with (DESTINO / f"{periodo}.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(COLUMNAS)
                w.writerows(filas)
        anotar_bitacora("sniim_limon", periodo, len(filas), "ok")
        print(f"{periodo}: {len(filas)} registros")
        total += len(filas)
        time.sleep(PAUSA_SEG)
    print(f"Total capturado: {total}")


if __name__ == "__main__":
    main()
