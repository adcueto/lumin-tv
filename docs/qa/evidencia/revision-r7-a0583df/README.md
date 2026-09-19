# Evidencia QA R7 — a0583df14a5367f2ac8b33c3c3711fb84373ba65

[Informe 24](../../informes/24-qa-B3-rev6-RF26-a0583df.md). Fecha 2026-09-19. Fuente git archive del candidato; base 3a1eaf9.

- b3-resultados.xml: 50 pasan, 0 omitidos/fallos/errores, PG16.15 aislado, psycopg3.2.3, Python3.12/pytest9.1.1.
- adicionales-resultados.json y comprobaciones_adicionales.py: confirman dos defectos, no una suite de aceptación verde. Otra base del mismo cluster desechable pierde conexión; SQL de contrato RF-26 acepta relaciones inválidas.
- ddl-rf26-extraido.sql: copia literal de CREATE TABLE relevantes y §3.2b. Se ejecutó en esquema qa_rf26 como propietario, sin montar RLS completo ni API. La objeción es a las restricciones del contrato por sucursal.
- ui-resultados.json: 33 mediciones Playwright Node, Chromium local; captura qa-1366-listas.png propia inspeccionada. No React/API, no auditoría WCAG.
- identidad-servidor-roku.json: hashes iguales para los archivos del servidor actual/tests y Roku entre base/candidato. Sus 28 tests y 42+21 comprobaciones locales están en QA23; no se reejecutaron sin cambios. El CI del SHA actual sí los ejecutó nuevamente.
- ci.json y ci-resumen.txt: run 35432801874, SHA exacto y tres jobs success, 28 servidor/50 PG/42+21 Roku/compilación.

## Repetir

Extraer el SHA en un directorio desechable y copiar los ejecutores. Comandos utilizados con PYTHONPATH de las dependencias aisladas:

```text
python -m pytest servidor/ensayos_b3 -q --junitxml=b3-resultados.xml
python comprobaciones_adicionales.py
node comprobar_ui.cjs
```

Los ensayos recrean lumin_ensayo. El caso adicional termina sesiones de lumin_app tanto en lumin_ensayo como en postgres dentro del cluster desechable. Usar únicamente LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres de un cluster de QA sin otros usuarios/datos. Nunca VPS ni servicio compartido. Se detuvo PG al finalizar. El ejecutor UI conserva rutas locales de dependencias; revisar/adaptar antes de repetir.

No copiar cluster, fuentes extraídas ni dependencias al repositorio. Los archivos QA instalados son documentación y evidencia, no producto ni CI adicional integrado.
