"""Prueba de estrés de la puerta de calidad: se inyectan registros corruptos y se verifica
que el pipeline no truena, que los válidos pasan y que cada inválido llega a cuarentena con motivo.

Uso:  python -m pytest tests  (o  python tests/test_puerta_calidad.py)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from esquemas import sniim_plata  # noqa: E402
from pipeline import agregar_jerarquias, puerta_de_calidad, tipificar_sniim  # noqa: E402

BASE = {"presentacion": "Caja de 20 kg.", "destino": "Jalisco: Mercado de Abasto de Guadalajara",
        "obs": "", "producto": "Limón c/semilla # 5 - Primera", "origen": "Colima", "fuente_url": "", "capturado_utc": ""}


def fila(fecha, pmin, pmax, pfrec, **extra):
    return {**BASE, "fecha": fecha, "precio_min": pmin, "precio_max": pmax, "precio_frec": pfrec, **extra}


def test_cuarentena_con_motivo():
    crudo = pd.DataFrame([
        fila("02/05/2025", "20", "25", "22"),                     # válido
        fila("31/02/2025", "20", "25", "22"),                     # fecha imposible
        fila("03/05/2025", "veinte", "25", "22"),                 # precio no numérico
        fila("05/05/2025", "30", "25", "28"),                     # min > max
        fila("06/05/2025", "20", "25", "40"),                     # frecuente fuera de rango
        fila("07/05/2025", "20", "25", "-3"),                     # precio negativo
        fila("08/05/2025", "20", "900", "22"),                    # precio implausible
        fila("09/05/2025", "20", "25", "22", destino="Marte: Central X"),  # región desconocida
        fila("02/05/2025", "20", "25", "22"),                     # duplicado del primero
    ])
    df, rechazos = tipificar_sniim(crudo)
    df = agregar_jerarquias(df).reset_index(drop=True)
    validos, q = puerta_de_calidad(df, sniim_plata)
    cuarentena = pd.concat([r for r in rechazos + [q] if not r.empty], ignore_index=True)

    assert len(validos) == 1                               # solo el registro válido pasa a Plata
    assert len(validos) + len(cuarentena) == len(crudo)    # nada se pierde en silencio
    assert cuarentena["motivo"].str.len().gt(0).all()      # todo rechazo lleva motivo
    textos = " ".join(cuarentena["motivo"])
    for esperado in ["fecha", "numérico", "duplicado", "precio_min mayor", "fuera del rango", "isin"]:
        assert esperado in textos, esperado


if __name__ == "__main__":
    test_cuarentena_con_motivo()
    print("OK: la puerta de calidad envía a cuarentena todos los registros corruptos, con motivo.")
