"""Extractor del tipo de cambio USD/MXN de referencia del Banco Central Europeo (API Frankfurter).

Capa Bronce: guarda la respuesta JSON de la API tal como llega en
data/bronce/frankfurter_usdmxn/usdmxn.json. No requiere token.

Es la segunda fuente del observatorio y sustituye a Banxico mientras no
haya BANXICO_TOKEN; su esquema (JSON anidado, fechas ISO, días hábiles
europeos) es distinto al del SNIIM (HTML tabular, fechas dd/mm/aaaa).
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "data" / "bronce" / "frankfurter_usdmxn" / "usdmxn.json"
URL = "https://api.frankfurter.app/{ini}..{fin}"
USER_AGENT = "TrustedDataLab-ITColima/0.1 (proyecto escolar; Instituto Tecnologico de Colima)"
INICIO = date(2022, 1, 1)

sys.path.insert(0, str(Path(__file__).parent))
from sniim_limon import anotar_bitacora  # noqa: E402


def main():
    fin = date.today()
    r = requests.get(URL.format(ini=INICIO.isoformat(), fin=fin.isoformat()),
                     params={"from": "USD", "to": "MXN"},
                     headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    datos = r.json()
    datos["_capturado_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    datos["_fuente_url"] = r.url
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(datos.get("rates", {}))
    anotar_bitacora("frankfurter_usdmxn", f"{INICIO}..{fin}", n, "ok")
    print(f"Frankfurter USD/MXN: {n} días")


if __name__ == "__main__":
    main()
