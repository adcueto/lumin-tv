# Evidencia QA R6 — 3a1eaf92e7d1e51ee1e13d41356f4788760c6fbc

Fecha 2026-09-19. [Informe 23](../../informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md). Extraído con git archive, sin checkout. No se usó lumin-pruebas de 547b969.

## Resultados y límites

- JUnit: 28 servidor y 46 PG, cero omitidos/fallos/errores. No equivalen a implementación B3.
- roku-resultados.txt: 42 planificación + 21 escena; compilacion.json: cero diagnósticos.
- Comparación base: log original aborta por falta de roRegistrySection; log adaptado reproduce 4 fallos. MainScene-base-con-asidero.brs añade solo la guarda de registro al código de base; no modifica producto. No es SceneGraph físico.
- permisos-resultados.json: 16 casos de base/candidato, POST/PUT, dos acciones y dos roles; sin tokens ni contraseñas reales.
- idle-resultados.json: reproducción de escritura desde conexión preexistente después del drenaje; el ejecutor confirma el DEFECTO, no aprobación.
- ui-resultados.json: 33 mediciones con Playwright Node/Chromium local. Capturas qa-* generadas e inspeccionadas por Codex. El Python de Claude no se ejecutó directamente; se tradujo el mismo recorrido a Node usando dependencias locales. No es auditoría WCAG ni producto React.
- ci.json y ci-resumen.txt: ejecución remota del SHA exacto, run 35431631604.

## Repetición

Copiar ejecutores de QA a un snapshot desechable del candidato. Dependencias de QA ya instaladas: Python 3.12, pytest 9.1.1, psycopg 3.2.3, Node 24.18.1, brs 0.47.6, BrighterScript 0.73.5. Los ejecutores preservan rutas del entorno original; comprobarlas y adaptarlas antes de repetir.

```text
python -m pytest servidor/tests -q --junitxml=servidor-resultados.xml
python -m pytest servidor/ensayos_b3 -q --junitxml=b3-resultados.xml
python roku-app/pruebas/correr.py
node compilar.cjs
python comprobar_permisos.py
python comprobar_idle.py
node comprobar_ui.cjs
```

Los ensayos B3 y comprobar_idle BORRAN/recrean lumin_ensayo: usar exclusivamente PG16 temporal desechable en loopback, con LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres. Nunca un servidor compartido/VPS. PG16.15 quedó detenido al terminar.

Para comparar escena con base, extraer MainScene de 1f7782e y añadir exclusivamente la guarda de registro documentada; ejecutar `python roku-app/pruebas/correr.py --escena MainScene-base-con-asidero.brs`. Esperado: salida no cero, 21 comprobaciones y 4 fallos. La base sin guarda debe registrarse como no ejecutable en este intérprete, no como suite válida.

hashes-candidato.json identifica 20 archivos cambiados del SHA. No copiar árboles fuente, cachés de dependencias ni datos PG al repositorio. Documentación instalada localmente sin commit/push.
