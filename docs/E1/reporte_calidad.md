# Reporte automático de calidad · E1

Generado por `src/pipeline.py` el 2026-11-12T19:31:24+00:00 (UTC). No editar a mano: se regenera en cada corrida.

## Flujo de registros

| Etapa | Registros |
|---|---|
| Bronce SNIIM (crudo) | 17,462 |
| Rechazados al tipificar (fecha, número o duplicado) | 0 |
| Rechazados por la puerta de calidad (Pandera) | 0 |
| **Plata (válidos)** | **17,462** |
| En cuarentena (esta corrida) | 0 |
| Tipo de cambio: días hábiles publicados → días calendario | 1,246 → 1,778 (532 imputados por arrastre) |

Los datos reales del SNIIM de esta corrida no tuvieron registros inválidos. Que la puerta sí detiene datos corruptos se comprueba en cada corrida con `tests/test_puerta_calidad.py`, que inyecta 8 registros dañados (fecha imposible, texto en precio, duplicado, mín > máx, frecuente fuera de rango, precio negativo, precio implausible y región desconocida) y verifica que los 8 lleguen a cuarentena con su motivo.

## Valores faltantes

- En los campos del SNIIM no hay celdas vacías; el faltante es **estructural**: en el panel semana × central falta el **28.7%** de las celdas (la central no reportó limón #5 esa semana).
- Prueba χ² de independencia (α = 0.05) entre faltar y **central**: p = 0.00e+00 (dependiente). Entre faltar y **temporada**: p = 0.122 (sin evidencia de dependencia).
- Como la ausencia depende de una variable observada (la central), el mecanismo **no es MCAR**; se trata como **MAR** condicionado a la central; la temporada no explica los faltantes. No se descarta un componente **MNAR** (una central puede dejar de reportar cuando no le llega limón, lo que se relaciona con el precio); por eso se imputa solo en huecos cortos y se marca cada valor imputado.
- **Selección de centrales para Oro:** se excluyen las que reportaron menos del 50% de las semanas (Central de Abasto de Aguascalientes, Central de Abasto Francisco Villa, Zona de Abasto de Mazatlan, Central de Abasto de Cd. Obregon, Mercado de Abasto de Zacatecas); imputarlas sería inventar casi toda su serie. Sus registros siguen en Plata.
- **Imputación (capa Oro):** interpolación lineal dentro de la central para huecos de hasta 2 semanas; si sigue faltando, **mediana** de la misma semana en las centrales de su región. Se usa la mediana y no la media porque la distribución del precio tiene sesgo positivo (asimetría = 1.61). Resultado: 13 celdas imputadas de 2,540; 0 quedan sin dato marcadas como `sin_dato`.
- **Tipo de cambio:** los huecos son fines de semana y festivos del BCE, ajenos al precio del limón (MCAR respecto a la variable de interés); se arrastra el último valor publicado (*forward fill*), que es el tipo de cambio vigente.

Centrales con más semanas sin reporte:

| Central | % de semanas sin dato |
|---|---|
| Central de Abasto de Aguascalientes | 100% |
| Central de Abasto Francisco Villa | 99% |
| Zona de Abasto de Mazatlan | 91% |
| Central de Abasto de Cd. Obregon | 71% |
| Mercado de Abasto de Zacatecas | 64% |
| Centro de Distribucion y Abasto de Gomez Palacio | 2% |

## Atípicos y ruido

| Método | Registros marcados | Uso |
|---|---|---|
| **Z robusto por mes** (mediana y MAD, umbral ±3.5) | **133** | **Tratamiento: winsorización al límite del mes** |
| IQR global (1.5 × IQR) | 689 | Comparativo: marca la temporada alta completa como atípica |
| Isolation Forest (precio, amplitud máx−mín, mes; contaminación 1 %) | 162 | Comparativo multivariado |

El valor original se conserva en `precio_frec_original` y la marca en `atipico_z`; ningún registro se elimina.

## Normalización y discretización

- `precio_frec_minmax`: escala [0, 1]. `precio_frec_z`: media 0, desviación 1.
- `nivel_precio` por terciles: **Bajo** < 20.79 ≤ **Medio** < 28.00 ≤ **Alto** ($/kg).
- Jerarquías conceptuales: central → estado → región (Norte, Centro-Norte, Occidente); día → semana → mes → trimestre → año; mes → temporada (Lluvias jun–oct / Secas).

## Reducción

- Plata: 17,462 registros diarios → Oro por central: 2,540 filas semana × central → Oro nacional: 254 semanas.
- Selección de variables en Oro: se quitan la URL de origen, la hora de captura y el texto libre de observaciones (que siguen en Plata para trazabilidad).
