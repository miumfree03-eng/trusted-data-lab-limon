# Trusted Data Lab · Observatorio del Precio del Limón de Colima

Proyecto integrador de Ingeniería de Datos, Análisis Estadístico y Calidad en SI (TecNM, Instituto Tecnológico de Colima, ago-dic 2026).

**Pregunta:** ¿cuánto y cuándo va a pagar el mercado mayorista por el limón de Colima, y en qué centrales de abasto conviene venderlo?

## Capas

| Capa | Estado | Contenido |
|---|---|---|
| Bronce | ✅ E0 | Precios crudos del SNIIM (limón #5, origen Colima) y tipo de cambio (Frankfurter/BCE; Banxico con token), capturados por GitHub Actions |
| Plata | ✅ E1 | Limpieza, atípicos, normalización y puerta de calidad Pandera con cuarentena (`data/plata`, `data/cuarentena`) |
| Oro | ✅ E1 (base) · E3 | Panel semanal por central y serie semanal nacional (`data/oro`); en E3 se optimiza y publica |

## Estructura

```
.github/workflows/captura.yml   Captura automática (L-V 16:00 hora de Colima)
extractores/                    sniim_limon.py, frankfurter_usdmxn.py, banxico_fix.py
src/                            pipeline.py (Plata/Oro) y esquemas.py (puerta de calidad Pandera)
tests/                          Prueba de estrés con registros corruptos
data/bronce/                    Datos crudos y bitácora de capturas
data/plata/  data/oro/          Datos limpios e integrados / agregados semanales
data/cuarentena/                Registros rechazados con su motivo
calidad/                        Registros PSP y objetivos de calidad
docs/E0/                        propuesta.md, ENTREGA.md
```

## Correr en local

```bash
pip install -r requirements.txt
python tests/test_puerta_calidad.py          # prueba de estrés de la puerta de calidad
python src/pipeline.py                       # Bronce -> Plata -> Oro + docs/E1/reporte_calidad.md
python extractores/sniim_limon.py            # incremental
python extractores/sniim_limon.py --desde 2022-01   # histórico
BANXICO_TOKEN=xxxx python extractores/banxico_fix.py
```

Fuentes: Secretaría de Economía (SNIIM) y Banco de México (SIE). Uso académico.
