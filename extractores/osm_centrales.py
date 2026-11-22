"""Extractor geoespacial: ubicación de las centrales de abasto destino (OpenStreetMap / Nominatim).

Capa Bronce: guarda la respuesta JSON cruda de Nominatim para cada central en
data/bronce/osm_centrales/<clave>.json, junto con la consulta y la hora de captura.
Respeta la política de uso de Nominatim: User-Agent identificable y 1 petición por segundo.
Solo vuelve a consultar las centrales que aún no tienen archivo.

Uso:  python extractores/osm_centrales.py
"""
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "data" / "bronce" / "osm_centrales"
PLATA = RAIZ / "data" / "plata" / "sniim_limon_plata.csv"
UA = {"User-Agent": "TrustedDataLab-ITColima/0.1 (proyecto escolar; Instituto Tecnologico de Colima)"}
URL = "https://nominatim.openstreetmap.org/search"

# Ciudad sede de cada central (para la consulta de respaldo si OSM no tiene la central por nombre)
CIUDAD = {
    "Aguascalientes": "Aguascalientes", "Baja California Sur": "La Paz", "Coahuila": "Torreón",
    "Colima": "Colima", "Durango": "Gómez Palacio", "Jalisco": "Guadalajara", "Nuevo Leon": "San Nicolás de los Garza",
    "San Luis Potosi": "San Luis Potosí", "Sinaloa": "Mazatlán", "Sonora": "Hermosillo", "Zacatecas": "Zacatecas",
}
CIUDAD_CENTRAL = {"Central de Abasto de Cd. Obregon": "Ciudad Obregón", "Central de Abasto Francisco Villa": "Durango"}

sys.path.insert(0, str(Path(__file__).parent))
from sniim_limon import anotar_bitacora  # noqa: E402


def clave(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")


def buscar(q):
    r = requests.get(URL, headers=UA, timeout=60, params={"q": q, "format": "json", "limit": 1, "countrycodes": "mx"})
    r.raise_for_status()
    time.sleep(1.1)
    return r.json()


def main():
    centrales = pd.read_csv(PLATA, usecols=["estado", "central"]).drop_duplicates()
    DESTINO.mkdir(parents=True, exist_ok=True)
    nuevos = 0
    for _, fila in centrales.iterrows():
        archivo = DESTINO / f"{clave(fila['central'])}.json"
        if archivo.exists():
            continue
        ciudad = CIUDAD_CENTRAL.get(fila["central"], CIUDAD.get(fila["estado"], fila["estado"]))
        consultas = [f"{fila['central']}, {ciudad}, {fila['estado']}, México", f"{ciudad}, {fila['estado']}, México"]
        for nivel, q in zip(("central", "ciudad"), consultas):
            resp = buscar(q)
            if resp:
                break
        archivo.write_text(json.dumps({
            "central": fila["central"], "estado": fila["estado"], "consulta": q, "precision": nivel,
            "respuesta": resp, "fuente_url": URL, "licencia": "ODbL (OpenStreetMap contributors)",
            "capturado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        nuevos += 1
        print(f"{fila['central']}: {nivel} -> {resp[0]['display_name'][:60] if resp else 'sin resultado'}")
    anotar_bitacora("osm_centrales", "catalogo", nuevos, "ok")
    print(f"Centrales nuevas geocodificadas: {nuevos}")


if __name__ == "__main__":
    main()
