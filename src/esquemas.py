"""Puerta de calidad: contratos (Pandera) que debe cumplir cada registro antes de entrar a la capa Plata."""
import pandas as pd
import pandera as pa
from pandera import Check, Column

PRESENTACIONES = ["Caja", "Arpilla", "Kilogramo"]
REGIONES = ["Norte", "Centro-Norte", "Occidente"]
PRECIO_MAX_PLAUSIBLE = 200.0  # $/kg; el máximo histórico observado ronda 95 $/kg

sniim_plata = pa.DataFrameSchema(
    {
        "fecha": Column("datetime64[ns]", Check.in_range(pd.Timestamp("2020-01-01"), pd.Timestamp.today().normalize()),
                        nullable=False),
        "estado": Column(str, Check.str_length(min_value=3), nullable=False),
        "central": Column(str, Check.str_length(min_value=3), nullable=False),
        "region": Column(str, Check.isin(REGIONES), nullable=False),
        "empaque": Column(str, Check.isin(PRESENTACIONES), nullable=False),
        "kg_empaque": Column(float, Check.in_range(1, 30), nullable=False),
        "precio_min": Column(float, Check.in_range(0, PRECIO_MAX_PLAUSIBLE, include_min=False), nullable=False),
        "precio_max": Column(float, Check.in_range(0, PRECIO_MAX_PLAUSIBLE, include_min=False), nullable=False),
        "precio_frec": Column(float, Check.in_range(0, PRECIO_MAX_PLAUSIBLE, include_min=False), nullable=False),
    },
    checks=[
        Check(lambda d: d["precio_min"] <= d["precio_max"], element_wise=False, name="min_menor_igual_max",
              error="precio_min mayor que precio_max"),
        Check(lambda d: d["precio_frec"].between(d["precio_min"], d["precio_max"]), element_wise=False,
              name="frec_entre_min_y_max", error="precio_frec fuera del rango [min, max]"),
    ],
    unique=["fecha", "central", "empaque", "kg_empaque"],
    strict=False,
    coerce=False,
    name="sniim_limon_plata",
)

tipo_cambio_plata = pa.DataFrameSchema(
    {
        "fecha": Column("datetime64[ns]", unique=True, nullable=False),
        "usd_mxn": Column(float, Check.in_range(10, 40), nullable=False),
    },
    strict=False,
    name="usdmxn_plata",
)
