# Ficha de entrega técnica · E0

| Campo | Valor |
|---|---|
| Proyecto | Trusted Data Lab · Observatorio del Precio del Limón de Colima |
| Entrega | E0: Arranque, propuesta y máquina de captura |
| Tag | `e0` |
| Equipo | Antonio Efraín Arellano Verduzco (23460504) · *[Compañero] ([No. de control])* |
| Repositorio | *[URL de GitHub]* |
| Fecha | 9 de noviembre de 2026 |

## Lista de verificación

| # | Entregable | Ubicación | Estado |
|---|---|---|---|
| 1 | Propuesta del observatorio (ficha, entrevista, 3 preguntas, plan de datos con análisis ético y legal) | `docs/E0/propuesta.md` | ✅ (falta la entrevista) |
| 2 | Extractor ético automático con GitHub Actions | `extractores/`, `.github/workflows/captura.yml` | ✅ |
| 3 | Serie histórica cruda con ≥ 36 periodos | `data/bronce/sniim_limon/` | ✅ 17,439 registros · 59 meses / 254 semanas (ene 2022–nov 2026) · 15 centrales |
| 4 | Registros PSP por integrante | `calidad/tiempo-*.csv`, `calidad/defectos-*.csv` | ✅ |
| 5 | 3 objetivos de calidad medibles | `calidad/objetivos.md` | ✅ |
| 6 | Profesores como colaboradores | Settings del repositorio | ⬜ |
| 7 | Enlace en el formulario oficial | Formulario del proyecto | ⬜ |

## Cómo verificar

1. En la pestaña **Actions**, el flujo **Captura Bronce** debe tener corridas en verde. También se puede lanzar a mano con *Run workflow*.
2. En `data/bronce/_bitacora_capturas.csv` aparece cada captura con su fuente, periodo, número de registros y estado.
3. Para correrlo en local: `pip install -r requirements.txt && python extractores/sniim_limon.py`.

## Decisiones técnicas

- **Fuente principal: SNIIM, limón con semilla #5.** De los calibres que se venden con origen Colima, es el que tiene más cobertura: 52 de 52 semanas y 12 centrales de destino en el último año.
- **Un archivo CSV por mes.** Así el extractor puede ser incremental e idempotente: cada corrida reescribe el mes en curso sin duplicar registros.
- **robots.txt se verifica en cada corrida.** Además se espera 3 segundos entre peticiones y se usa un *User-Agent* que identifica el proyecto.
- **El token de Banxico va como secreto de GitHub.** Sin token, ese paso se omite sin fallar.
