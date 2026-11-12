# Relatoría de etapa · E1 (Capa Plata, limpieza y puerta de calidad)

**Periodo:** 9 al 13 de noviembre de 2026
**Equipo:** Antonio Efraín Arellano Verduzco · Oscar Emiliano Ramírez García

## 1. Punto de partida

Al cerrar E0 teníamos la capa Bronce funcionando: 17,462 precios crudos del limón con semilla #5 de Colima (SNIIM, enero 2022 a noviembre 2026, 15 centrales de abasto), capturados de lunes a viernes por GitHub Actions. El objetivo de E1 era convertir esos datos en una capa **Plata** confiable y una capa **Oro** lista para el análisis estadístico, sin perder trazabilidad.

## 2. Qué construimos

1. **Segunda fuente heterogénea.** Agregamos el tipo de cambio USD/MXN de referencia del BCE (API Frankfurter). No requiere token y su esquema es distinto al del SNIIM: JSON anidado, fechas ISO, nombres en inglés y solo días hábiles europeos. Banxico sigue preparado para cuando tengamos su token.
2. **Pipeline `src/pipeline.py`** de Bronce a Plata y Oro, con la tipificación, las jerarquías conceptuales, la normalización, la discretización, los atípicos, la integración y la reducción descritas en la ficha.
3. **Puerta de calidad con Pandera** (`src/esquemas.py`). Valida tipos, rangos plausibles, que el mínimo no supere al máximo, que el precio frecuente esté entre ambos, la región, el empaque y la unicidad. Lo que falla va a `data/cuarentena/cuarentena.csv` con su regla, su motivo y el registro original.
4. **Prueba de estrés** (`tests/test_puerta_calidad.py`). Inyecta 8 registros corruptos y comprueba que el pipeline no truena, que solo el válido pasa y que cada corrupto llega a cuarentena con motivo. Corre en cada ejecución de la Action.
5. **Reporte automático** (`docs/E1/reporte_calidad.md`), que se regenera con cada corrida.

## 3. Decisiones y su justificación

| Decisión | Por qué |
|---|---|
| Atípicos con **Z robusto por mes** (mediana y MAD) en lugar de IQR global | El precio del limón tiene una estacionalidad fuerte. El IQR global marcaba 689 registros, casi todos de temporada alta legítima; el Z robusto compara cada precio contra su propio mes y marca 133. |
| **Winsorizar** en vez de borrar | La regla del proyecto es que no se borran datos en silencio. Se recorta al límite del mes y se conservan el valor original y la marca. |
| Faltantes tratados como **MAR** | La prueba χ² muestra que faltar depende de la central (p ≈ 0) y no de la temporada (p = 0.12). |
| **Mediana** para imputar | La distribución tiene sesgo positivo (asimetría 1.61), y la media se iría hacia los picos. |
| Excluir del panel Oro las centrales con menos del 50 % de semanas | Imputarlas sería inventar su serie. Siguen en Plata para quien las necesite. |
| Tipo de cambio con **forward fill** | En fin de semana o festivo rige el último tipo publicado. Sus huecos dependen del calendario, no del precio del limón. |
| Terciles para `nivel_precio` | Dan grupos de igual tamaño (Bajo < 20.79 ≤ Medio < 28.00 ≤ Alto $/kg), útiles para comparar en E2 y E3. |

## 4. Problemas que encontramos

- **Diagnóstico erróneo de codificación.** La consola de Windows mostraba los acentos de las centrales como `�` y creímos que el extractor leía mal el sitio. Lo cambiamos a cp1252, y eso sí dañó los meses recapturados ("TorreÃ³n"). Al revisar los bytes de la respuesta confirmamos que el SNIIM envía UTF-8 correcto, así que regresamos el extractor a UTF-8 y restauramos Bronce desde el historial de git. **Aprendizaje:** antes de "corregir" datos, revisar los bytes y no lo que muestra la consola. Quedó registrado como defecto 3 del PSP.
- **Cortes de conexión del SNIIM** (error 10054) en algunos meses. Agregamos 3 reintentos con espera creciente y la opción `--meses` para recapturar meses puntuales (defecto 5).
- **La regla de unicidad de Pandera** mandaba a cuarentena tanto el original como su duplicado. Separamos la deduplicación, que conserva la primera captura, antes de la puerta (defecto 4).

## 5. Resultados

- 17,462 registros válidos en Plata; 0 en cuarentena con los datos reales. La prueba de estrés confirma que la puerta sí detiene los registros corruptos.
- Oro: un panel de 2,540 filas (semana × 10 centrales con buena cobertura; 13 celdas imputadas) y una serie nacional de 254 semanas con precio en MXN y USD.

## 6. Participación

| Integrante | Aportación en E1 |
|---|---|
| Antonio Efraín Arellano Verduzco | Segunda fuente, pipeline, puerta de calidad, prueba de estrés y documentación |
| Oscar Emiliano Ramírez García | *Por completar por el equipo* |

## 7. Siguiente etapa (E2)

Integrar la fuente especializada y el análisis de ética y linaje. Usar `data/oro/limon_semanal_nacional.csv` para el experimento de factores: temporada × región × tipo de cambio.
