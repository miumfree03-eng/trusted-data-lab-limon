# Declaración de ética y legalidad de los datos

**Proyecto:** Trusted Data Lab · Observatorio del Precio del Limón de Colima
**Equipo:** Antonio Efraín Arellano Verduzco · Oscar Emiliano Ramírez García
**Última revisión:** 22 de noviembre de 2026

## 1. Fuentes, licencias y términos de uso

| Fuente | Qué tomamos | Acceso | Licencia y términos | robots.txt / política de uso |
|---|---|---|---|---|
| **SNIIM** (Secretaría de Economía) | Precios al mayoreo del limón #5, origen Colima | Página pública de consulta (*scraping* de la tabla HTML) | Información pública del Gobierno de México; se cita la fuente en cada registro (`fuente_url`). No encontramos una licencia específica publicada en el sitio, así que la tratamos como información pública con atribución. | Revisado: solo prohíbe `/Analisis/`, `/2010/`, `/Sicia*` y los archivos `*.xls`. La ruta que usamos está permitida, y el extractor verifica robots.txt en cada corrida. |
| **Frankfurter** (tipos de referencia del BCE) | Tipo de cambio USD/MXN diario | API REST abierta, sin token | Datos de referencia del Banco Central Europeo, de uso libre con atribución | Es una API pensada para consumo automatizado; hacemos una petición por corrida. |
| **OpenStreetMap / Nominatim** | Ubicación de las 15 centrales de abasto | API Nominatim | **ODbL 1.0**: atribución "© OpenStreetMap contributors", y las obras derivadas que se publiquen deben mantener la misma licencia | Cumplimos su política de uso: *User-Agent* identificable, máximo 1 petición por segundo y caché local para no repetir consultas. |
| **Natural Earth** | Contornos de países para el mapa | Descarga única | Dominio público | No aplica; se descarga una sola vez y se guarda en Bronce. |
| **Banxico SIE** (opcional) | Tipo de cambio FIX | API con token personal | Términos de la API de Banxico; el token se guarda como secreto de GitHub y nunca en el código | No aplica; es una API oficial. |

## 2. Privacidad

- **No recopilamos datos personales.** Todas las fuentes son agregadas: precios por central de abasto, tipos de cambio diarios y ubicaciones de mercados públicos. No hay nombres de personas, teléfonos ni identificadores individuales.
- Para la fuente geoespacial usamos la ubicación de **establecimientos públicos** (centrales de abasto), no de domicilios particulares.
- Las credenciales (como el token de Banxico) viven en los secretos de GitHub y en un `.env` excluido por `.gitignore`.

## 3. Sesgos y limitaciones conocidas

| Sesgo o limitación | Efecto | Mitigación |
|---|---|---|
| **Cobertura desigual de centrales:** algunas reportan casi todas las semanas y otras casi nunca | Una media nacional ingenua sobrerrepresenta a Gómez Palacio, Torreón y Aguascalientes | En Oro usamos la **mediana** por semana; excluimos del panel las centrales con menos del 50 % de cobertura y lo documentamos en el reporte de calidad |
| **Solo limón #5 calidad Primera** | No representa todos los calibres ni el precio que recibe el productor | Se declara en la ficha del observatorio; los resultados se interpretan como precio **al mayoreo en destino** |
| **Precisión de la geolocalización:** 3 centrales se ubicaron por su nombre y 12 por la ciudad sede | La distancia puede variar algunos kilómetros | La columna `precision` en `centrales_geo.geojson` lo indica; a escala nacional el error es menor al 2 % de la distancia |
| **Datos voluntarios de OSM** | Pueden faltar o estar desactualizados | Se guarda la respuesta cruda en Bronce con su fecha de captura para poder auditarla y corregirla |
| **Imputación de faltantes** | Puede suavizar movimientos reales del precio | Solo se imputan huecos cortos y cada valor imputado se marca (`metodo_imputacion`, `n_registros_origen = 0`) |

## 4. Uso responsable

El observatorio es de **uso académico** y sin fines de lucro. Sus resultados apoyan la toma de decisiones, pero no sustituyen la consulta de las fuentes oficiales. Cualquier publicación de los datos derivados mantiene la atribución a SNIIM, BCE/Frankfurter y OpenStreetMap, y la licencia ODbL para las capas que contienen datos de OSM.
