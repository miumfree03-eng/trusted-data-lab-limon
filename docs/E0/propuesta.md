# Trusted Data Lab: Observatorio del Precio del Limón de Colima

**Entrega E0: Arranque, propuesta y máquina de captura**
Ingeniería de Datos (ATD-2602) · Análisis Estadístico para Ciencia de Datos · Calidad en los Sistemas de Información
Instituto Tecnológico de Colima, TecNM · Semestre agosto-diciembre 2026

**Equipo:** Antonio Efraín Arellano Verduzco (23460504) · *[Nombre del compañero] ([No. de control])*

---

## 1. Ficha del observatorio

| Campo | Definición |
|---|---|
| **Nombre** | Observatorio del Precio del Limón de Colima |
| **Sector** | Agroalimentario: comercialización al mayoreo de limón mexicano (*Citrus aurantifolia*) |
| **Región** | Origen: estado de Colima. Destino: centrales de abasto del país donde se vende el limón colimense |
| **Unidad de observación** | Precio por kilogramo (mínimo, máximo y frecuente) del limón con semilla #5, calidad Primera, origen Colima, por día y por central de abasto |
| **Pregunta detonadora** | *¿Cuánto y cuándo va a pagar el mercado mayorista por el limón de Colima, y en qué centrales de abasto conviene venderlo?* |
| **Cliente potencial** | Productores y empacadoras de limón de Tecomán y Armería, y sus asociaciones, que deciden cuándo cortar, a qué central enviar y a qué precio negociar |

**Por qué este sector.** Colima es uno de los principales productores de limón mexicano del país, y el valle de Tecomán concentra buena parte de la producción. El precio al mayoreo es muy volátil: cambia con la temporada de lluvias, las heladas en otras regiones, la demanda de exportación y los costos de transporte. El productor suele enterarse del precio por el intermediario, cuando ya cortó la fruta. Un observatorio con datos públicos y verificables le da información independiente para negociar mejor.

## 2. Entrevista de campo

> ⚠️ **Sección por completar por el equipo.** La entrevista debe ser real, de al menos 15 minutos, con alguien del sector: un productor, una empacadora, un comerciante del mercado o un técnico de la Junta Local de Sanidad Vegetal. No inventen respuestas. Abajo están las 5 preguntas preparadas; anoten las respuestas y lo que aprendieron.

| Dato | Registro |
|---|---|
| Persona entrevistada (nombre o cargo, con su permiso) | |
| Rol en el sector | |
| Fecha, lugar y duración | |
| Medio (presencial, llamada, videollamada) | |

**Preguntas y respuestas**

1. **¿Cómo se entera hoy del precio del limón antes de vender o de cortar?** ¿Con qué anticipación lo conoce y qué tan confiable le parece?
   *Respuesta:*
2. **¿En qué meses el precio sube o baja más, y a qué lo atribuye** (lluvias, heladas, exportación, plagas como el HLB)?
   *Respuesta:*
3. **¿A qué centrales de abasto o mercados se envía el limón de Colima,** y por qué se elige una u otra (precio, distancia, comprador fijo)?
   *Respuesta:*
4. **¿Qué tamaño o calibre se vende mejor** y cuánto cambia el precio entre calibres?
   *Respuesta:*
5. **Si tuviera un pronóstico del precio de las próximas semanas, ¿qué decisión cambiaría** (cortar, guardar, enviar a otra central, negociar)?
   *Respuesta:*

**Aprendizajes clave**

- *Aprendizaje 1:*
- *Aprendizaje 2:*
- *Aprendizaje 3:*
- *¿Qué cambia en el observatorio por esta entrevista?*

## 3. Las tres preguntas analíticas

| Entrega | Tipo de análisis | Pregunta |
|---|---|---|
| **E1** | Variable a pronosticar | ¿Cuál será el **precio frecuente semanal por kg** del limón #5 de Colima, en promedio de todas las centrales, en las próximas 4 a 8 semanas? Se usará la serie semanal construida en la capa Plata, con modelos de serie de tiempo (tendencia y estacionalidad). |
| **E2** | Factores a experimentar | ¿Influyen la **temporada** (lluvias de junio a octubre contra secas), la **región de la central de destino** (norte, centro, sur) y el **tipo de cambio peso-dólar** en el precio por kg? Se plantea un diseño factorial con ANOVA sobre los precios de la capa Plata. |
| **E3** | Grupos multivariados a comparar | ¿Las centrales de abasto forman **grupos con comportamiento de precio parecido**? Cada central se describe con un vector (precio medio, volatilidad, diferencia máx–mín y estacionalidad), y los grupos se comparan con MANOVA o análisis de conglomerados. |

## 4. Plan de recopilación de datos

### Fuente 1: SNIIM, Secretaría de Economía (fuente principal)

| Aspecto | Detalle |
|---|---|
| **Qué es** | Sistema Nacional de Información e Integración de Mercados. Publica los precios al mayoreo de frutas y hortalizas en las centrales de abasto del país. |
| **Datos** | Fecha, presentación (p. ej., caja de 19 kg), central de destino, precio mínimo, máximo y frecuente en pesos por kg. Producto: *Limón c/semilla # 5 - Primera* (ID 421), origen Colima (ID 8). |
| **Método** | Consulta HTTP a la página pública de resultados por rango de fechas y extracción de la tabla HTML (*web scraping*). Una petición por mes, con 3 segundos de pausa entre peticiones. |
| **Frecuencia** | Diaria en días hábiles. La GitHub Action corre de lunes a viernes. |
| **Histórico** | Carga inicial del 9 nov 2026: **17,439 registros** desde el 3 de enero de 2022, es decir, **59 meses** o **254 semanas** (más de 36 periodos), en 15 centrales de abasto. |
| **Autenticación** | Ninguna: es información pública. |

### Fuente 2: Banco de México, SIE API (fuente complementaria)

| Aspecto | Detalle |
|---|---|
| **Qué es** | API REST del Sistema de Información Económica de Banxico. |
| **Datos** | Serie SF43718: tipo de cambio FIX peso-dólar diario. Se usa como factor explicativo en E2 por la relación entre el limón y la exportación. |
| **Formato** | JSON. |
| **Autenticación** | Token gratuito que se envía en el encabezado `Bmx-Token`. Se guarda como secreto de GitHub (`BANXICO_TOKEN`), nunca en el código. |

### Análisis ético y legal

| Criterio | SNIIM | Banxico SIE |
|---|---|---|
| **robots.txt** | Revisado el 9 nov 2026. Solo prohíbe `/Analisis/`, `/2010/`, `/Sicia*` y los archivos `*.xls`. La ruta de consulta que usamos (`/NUEVO/Consultas/...`) **está permitida**. Además, el extractor verifica robots.txt antes de cada corrida y se detiene si la ruta deja de estar permitida. | Es una API oficial pensada para consumo automatizado, así que robots.txt no aplica. |
| **Términos de uso** | Es información pública del Gobierno de México, generada para dar transparencia a los mercados. Se cita la fuente en cada registro (`fuente_url`). *Pendiente: confirmar en el sitio si existen términos de uso específicos y anotarlos aquí.* | Se usa con un token personal y respetando los límites de consultas que Banxico establece para su API. Los datos se citan como "Fuente: Banco de México, SIE". |
| **Carga al servidor** | Una petición por mes consultado, 3 segundos de pausa y un *User-Agent* que identifica el proyecto escolar. La captura diaria solo vuelve a pedir el mes en curso. | Una petición por corrida. |
| **Datos personales** | No hay: son precios agregados por central de abasto. | No hay. |
| **Uso** | Académico y sin fines de lucro. Los datos crudos no se modifican en la capa Bronce. | Igual. |

## 5. Arquitectura de la capa Bronce

```
GitHub Actions (L-V, 16:00 Colima)
   ├── extractores/sniim_limon.py ──► data/bronce/sniim_limon/AAAA-MM.csv
   ├── extractores/banxico_fix.py ──► data/bronce/banxico_fix/fix.csv
   └── cada corrida ────────────────► data/bronce/_bitacora_capturas.csv
                                         (fecha, fuente, periodo, registros, estado)
```

- **Bronce = datos crudos.** Las columnas y los textos se guardan tal como los publica la fuente, más la URL consultada y la hora de captura (UTC). La limpieza se hará en la capa Plata (E1).
- **Incremental e idempotente.** Cada corrida vuelve a pedir el último mes guardado y los siguientes, y reescribe ese archivo de mes completo. Así no se duplican registros.
- **Trazabilidad.** La bitácora registra cada captura, y el historial de commits del bot muestra cuándo entró cada dato.

## 6. Sistema de calidad inicial (PSP)

- Registros de tiempo y defectos por integrante en `calidad/tiempo-<nombre>.csv` y `calidad/defectos-<nombre>.csv`.
- Tres objetivos de calidad medibles en [`calidad/objetivos.md`](../../calidad/objetivos.md): confiabilidad de la captura (≥ 95 %), cobertura semanal (≥ 50 de 52 semanas) y disciplina PSP.

## 7. Referencias

- Secretaría de Economía. *Sistema Nacional de Información e Integración de Mercados (SNIIM)*. http://www.economia-sniim.gob.mx/
- Banco de México. *API del Sistema de Información Económica (SIE)*. https://www.banxico.org.mx/SieAPIRest/service/v1/
