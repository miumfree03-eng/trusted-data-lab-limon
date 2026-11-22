"""Prueba de linaje: cada fila de Oro debe poder rastrearse hasta Bronce y su fecha de ingesta.

Verifica, con los archivos generados por src/pipeline.py:
  1. Toda fila observada de Oro (por central) tiene registros de origen y fechas de ingesta.
  2. Todo id_registro de la tabla de linaje existe en Plata.
  3. Todo archivo de Bronce citado en Plata existe en data/bronce/sniim_limon/.
  4. Las filas imputadas de Oro se declaran como tales (sin fingir un origen propio).

Uso:  python tests/test_linaje.py   (después de correr python src/pipeline.py)
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]


def test_linaje_completo():
    oro = pd.read_csv(RAIZ / "data/oro/limon_semanal_central.csv")
    plata = pd.read_csv(RAIZ / "data/plata/sniim_limon_plata.csv", usecols=["id_registro", "archivo_bronce", "capturado_utc"])
    linaje = pd.read_csv(RAIZ / "data/oro/linaje_oro.csv")
    bronce = {p.name for p in (RAIZ / "data/bronce/sniim_limon").glob("*.csv")}

    observadas = oro[oro["metodo_imputacion"] == "observado"]
    assert (observadas["n_registros_origen"] > 0).all(), "fila observada de Oro sin registros de origen"
    assert observadas["ingesta_min_utc"].notna().all(), "fila observada de Oro sin fecha de ingesta"

    assert linaje["id_registro"].isin(plata["id_registro"]).all(), "id_registro de linaje que no existe en Plata"
    assert plata["id_registro"].is_unique, "id_registro repetido en Plata"
    assert set(plata["archivo_bronce"]).issubset(bronce), "Plata cita un archivo de Bronce que no existe"
    assert plata["capturado_utc"].notna().all(), "registro de Plata sin fecha de ingesta"

    imputadas = oro[oro["metodo_imputacion"] != "observado"]
    assert (imputadas["n_registros_origen"] == 0).all(), "fila imputada que aparenta tener origen propio"
    return len(observadas), len(imputadas), len(linaje)


if __name__ == "__main__":
    obs, imp, n = test_linaje_completo()
    print(f"OK: {obs} filas observadas de Oro rastreables a Bronce, {imp} imputadas declaradas, {n} vínculos de linaje.")
