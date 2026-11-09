"""Resume la capa Bronce del SNIIM: registros, periodos y centrales cubiertas."""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
df = pd.concat(pd.read_csv(p, dtype=str) for p in sorted((RAIZ / "data/bronce/sniim_limon").glob("*.csv")))
fechas = pd.to_datetime(df["fecha"], dayfirst=True)
print(f"registros={len(df)}")
print(f"desde={fechas.min():%Y-%m-%d} hasta={fechas.max():%Y-%m-%d}")
print(f"meses={fechas.dt.to_period('M').nunique()} semanas={fechas.dt.to_period('W').nunique()} dias={fechas.nunique()}")
print(f"centrales={df['destino'].nunique()}")
