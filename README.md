# Trusted Data Lab · Observatorio del Precio del Limón de Colima

Proyecto integrador de Ingeniería de Datos, Análisis Estadístico y Calidad en SI (TecNM, Instituto Tecnológico de Colima, ago-dic 2026).

**Pregunta:** ¿cuánto y cuándo va a pagar el mercado mayorista por el limón de Colima, y en qué centrales de abasto conviene venderlo?

## Capas

| Capa | Estado | Contenido |
|---|---|---|
| Bronce | ✅ E0 | Precios crudos del SNIIM (limón #5, origen Colima) y FIX de Banxico, capturados por GitHub Actions |
| Plata | E1 | Limpieza, normalización y puerta de calidad |
| Oro | E3 | Datos integrados y listos para modelado y tablero |

## Estructura

```
.github/workflows/captura.yml   Captura automática (L-V 16:00 hora de Colima)
extractores/                    sniim_limon.py, banxico_fix.py
data/bronce/                    Datos crudos y bitácora de capturas
calidad/                        Registros PSP y objetivos de calidad
docs/E0/                        propuesta.md, ENTREGA.md
```

## Correr en local

```bash
pip install -r requirements.txt
python extractores/sniim_limon.py            # incremental
python extractores/sniim_limon.py --desde 2022-01   # histórico
BANXICO_TOKEN=xxxx python extractores/banxico_fix.py
```

Fuentes: Secretaría de Economía (SNIIM) y Banco de México (SIE). Uso académico.
