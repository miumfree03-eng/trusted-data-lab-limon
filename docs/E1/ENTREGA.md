# Ficha de entrega técnica · E1

| Campo | Valor |
|---|---|
| Proyecto | Trusted Data Lab · Observatorio del Precio del Limón de Colima |
| Entrega | E1: Capa Plata, limpieza y puerta de calidad |
| Tag | `e1` |
| Equipo | Antonio Efraín Arellano Verduzco (23460504) · Oscar Emiliano Ramírez García |
| Repositorio | https://github.com/miumfree03-eng/trusted-data-lab-limon |
| Fecha | 13 de noviembre de 2026 |

## Lista de verificación

| # | Requisito | Dónde está | Estado |
|---|---|---|---|
| 1a | Faltantes: diagnóstico MCAR/MAR/MNAR e imputación justificada | `src/pipeline.py` (`diagnosticar_faltantes`, `capa_oro`, `leer_tipo_cambio`) · [reporte](reporte_calidad.md#valores-faltantes) | ✅ |
| 1b | Atípicos y ruido (IQR, Z robusto, Isolation Forest) | `tratar_atipicos` · [reporte](reporte_calidad.md#atípicos-y-ruido) | ✅ |
| 1c | Normalización Min-Max y Z-Score | `normalizar_y_discretizar` → `precio_frec_minmax`, `precio_frec_z` | ✅ |
| 1d | Discretización y jerarquías conceptuales | `nivel_precio` (terciles) · central→estado→región · día→semana→mes→trimestre→año · temporada | ✅ |
| 1e | Reducción (agregación y selección de variables) | `capa_oro` → `data/oro/` | ✅ |
| 2 | Integración de fuentes heterogéneas | SNIIM (HTML→CSV, dd/mm/aaaa, cp1252) + Frankfurter (JSON anidado, ISO, días hábiles BCE) → `integrar` | ✅ |
| 3 | Puerta de calidad automática con Pandera y cuarentena con motivo | `src/esquemas.py`, `puerta_de_calidad` → `data/cuarentena/cuarentena.csv` · prueba de estrés `tests/test_puerta_calidad.py` | ✅ |
| 4 | Ficha técnica y relatoría | este archivo · [`docs/relatoria-E1.md`](../relatoria-E1.md) | ✅ |

## Salidas

| Capa | Archivo | Contenido |
|---|---|---|
| Plata | `data/plata/sniim_limon_plata.csv` | Registros diarios válidos, tipificados, con jerarquías, marcas de atípicos, normalización, nivel de precio y precio en USD |
| Plata | `data/plata/usdmxn_plata.csv` | Tipo de cambio diario continuo, con marca de imputación |
| Cuarentena | `data/cuarentena/cuarentena.csv` | Cada registro rechazado, con regla, columna, motivo y el registro original en JSON |
| Oro | `data/oro/limon_semanal_central.csv` | Panel semana × central con imputación marcada |
| Oro | `data/oro/limon_semanal_nacional.csv` | Serie semanal nacional (insumo del pronóstico E1/E2 de Estadística) |

## Cómo verificar

```bash
pip install -r requirements.txt
python tests/test_puerta_calidad.py   # inyecta 9 registros (8 corruptos) y verifica la cuarentena
python src/pipeline.py                # Bronce -> Plata -> Oro y regenera docs/E1/reporte_calidad.md
```

La GitHub Action **Captura Bronce y pipeline Plata-Oro** corre ambos pasos de lunes a viernes después de capturar.
