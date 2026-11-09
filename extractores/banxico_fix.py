"""Extractor del tipo de cambio FIX peso-dólar (Banxico SIE, serie SF43718).

Capa Bronce: guarda la respuesta de la API sin transformar en
data/bronce/banxico_fix/fix.csv (fecha y dato tal como vienen).

Requiere un token gratuito de Banxico en la variable de entorno BANXICO_TOKEN
(en GitHub: Settings > Secrets and variables > Actions). Sin token, no hace nada.
"""
import csv
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "data" / "bronce" / "banxico_fix" / "fix.csv"
SERIE = "SF43718"
URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{ini}/{fin}"

sys.path.insert(0, str(Path(__file__).parent))
from sniim_limon import anotar_bitacora  # noqa: E402


def main():
    token = os.environ.get("BANXICO_TOKEN")
    if not token:
        print("Sin BANXICO_TOKEN: se omite la captura de Banxico.")
        return
    ini = date(date.today().year - 3, 1, 1).isoformat()
    r = requests.get(URL.format(serie=SERIE, ini=ini, fin=date.today().isoformat()),
                     headers={"Bmx-Token": token, "Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    datos = r.json()["bmx"]["series"][0]["datos"]
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "dato", "serie", "capturado_utc"])
        w.writerows([d["fecha"], d["dato"], SERIE, ahora] for d in datos)
    anotar_bitacora("banxico_fix", f"{ini}..{date.today()}", len(datos), "ok")
    print(f"Banxico FIX: {len(datos)} registros")


if __name__ == "__main__":
    main()
