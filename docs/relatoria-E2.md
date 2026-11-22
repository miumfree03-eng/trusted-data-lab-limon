# Relatoría de etapa · E2 (Fuente especializada, ética y linaje)

**Periodo:** 13 al 23 de noviembre de 2026
**Equipo:** Antonio Efraín Arellano Verduzco · Oscar Emiliano Ramírez García

## 1. Punto de partida

Al cerrar E1 teníamos Bronce, Plata y Oro con puerta de calidad. Faltaban tres cosas: una fuente especializada que agregara una dimensión nueva al observatorio, una postura explícita sobre ética y legalidad, y la posibilidad de **demostrar** de dónde sale cada número de Oro.

## 2. Qué construimos

1. **Fuente geoespacial.** Ubicamos con OpenStreetMap (Nominatim) las 15 centrales de abasto a las que llega el limón de Colima. Guardamos cada respuesta cruda en Bronce y armamos con GeoPandas una capa en Plata y otra en Oro, con precio y distancia desde Tecomán, más un mapa de México.
2. **Linaje.** Cada registro de Plata tiene un `id_registro` derivado de su origen exacto en Bronce y su `capturado_utc`. Cada fila de Oro indica cuántos registros la forman, de qué archivos vienen y entre qué fechas se capturaron. La tabla `linaje_oro.csv` permite bajar de cualquier semana y central de Oro hasta las filas de Bronce.
3. **Prueba automática de linaje** (`tests/test_linaje.py`), que corre en la Action junto con la prueba de estrés de la puerta de calidad.
4. **Declaración de ética y legalidad** (`docs/etica-datos.md`), que cubre fuentes, licencias (incluida la ODbL de OSM), robots.txt y políticas de uso, privacidad, sesgos y uso responsable.

## 3. Decisiones

| Decisión | Por qué |
|---|---|
| Elegir la fuente **geoespacial** y no la de redes sociales | Las centrales tienen una ubicación física y el precio podría depender del flete. Además, no involucra datos personales. |
| Hash SHA-1 truncado como `id_registro` | Es estable entre corridas: el mismo registro de Bronce produce siempre el mismo id, sin depender del orden de las filas. |
| Declarar las filas imputadas con `n_registros_origen = 0` | El linaje no debe aparentar un origen que no existe; el valor imputado se identifica como tal. |
| Guardar la consulta y la **precisión** de la geolocalización | Para 12 centrales OSM no tiene el mercado por nombre y se ubicaron en la ciudad sede. Hay que decirlo. |
| Caché de Nominatim en Bronce | Respeta la política de 1 petición por segundo y vuelve reproducible el resultado. |

## 4. Problemas encontrados

- **Natural Earth a 50 m no incluye los estados de México**; el filtro devolvía una capa vacía y el mapa fallaba. Usamos los contornos de países como contexto.
- **Etiquetas encimadas** en el mapa para las centrales de una misma ciudad (Guadalajara, Aguascalientes, Torreón y Gómez Palacio). Las alternamos a izquierda y derecha.
- La prueba de estrés de E1 se rompió al agregar el linaje, porque sus registros de prueba no traían `archivo_bronce`. La actualizamos.

## 5. Resultados

- 15 centrales geolocalizadas (3 por nombre y 12 por ciudad), 12 con precio en el último año.
- Sin relación significativa entre distancia y precio (Spearman ρ = 0.20, p = 0.54). Colima, el destino más cercano, tuvo el precio más alto.
- Linaje verificado: 2,536 filas observadas de Oro rastreables hasta Bronce, 14 imputadas declaradas y 17,531 vínculos de linaje.

## 6. Participación

| Integrante | Aportación en E2 |
|---|---|
| Antonio Efraín Arellano Verduzco | Fuente geoespacial, linaje, pruebas y documentación |
| Oscar Emiliano Ramírez García | *Por completar por el equipo* |

## 7. Siguiente etapa (E3)

Optimizar formalmente la capa Oro y publicar el dataset, usando la región de destino y la temporada como factores del análisis.
