# Objetivos de calidad (PSP)

| # | Objetivo | Métrica | Meta | Cómo se mide |
|---|---|---|---|---|
| 1 | Captura confiable | % de corridas de GitHub Actions terminadas con éxito por semana | ≥ 95 % | Historial de la pestaña Actions y `data/bronce/_bitacora_capturas.csv` (estado `ok` vs `error`) |
| 2 | Cobertura de la serie | Semanas del último año con al menos un precio del limón #5 | ≥ 50 de 52 | Conteo de semanas distintas en `data/bronce/sniim_limon/` |
| 3 | Disciplina PSP | Densidad de defectos registrados y porcentaje de tiempo registrado | < 5 defectos por 100 líneas de código y 100 % de las sesiones de trabajo en `tiempo-<nombre>.csv` | Revisión semanal de los archivos de `calidad/` |
