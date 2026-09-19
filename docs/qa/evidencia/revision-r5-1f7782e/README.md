# Evidencia QA R5 — 1f7782eb384d1bf0b05688870c524b8ccdb05fe4

Ejecutada por Codex el 2026-09-19. Fuentes extraídas por git archive a `revision-r5-1f7782e`, sin cambiar el checkout. [Informe](../../informes/22-qa-B3-rev4-B5a-1f7782e.md).

## Resultados

- Servidor: 26 pasan; ver servidor-resultados.xml.
- Ensayos B3: 39 pasan; ver b3-resultados.xml.
- Roku: 42 comprobaciones; ver roku-resultados.txt.
- Compilación: cero diagnósticos; ver compilacion.json.
- Cuatro defectos/casos adicionales: comprobaciones-adicionales.json y recargar-resultado.txt. Estos ejecutores caracterizan fallos; NO son pruebas de aceptación verdes del producto.
- CI: ci.json y ci-resumen.txt, run 35429691846 del SHA exacto.

## Repetición aislada

Extraer el candidato en una carpeta desechable. Copiar allí comprobaciones_adicionales.py, recargar_qa.brs y el ejecutor de compilación. Instalar o proporcionar Python 3.12, pytest, psycopg[binary] 3.2.3, Node y las versiones registradas de brs/bsc. Los ejecutores conservan rutas del entorno de QA; revisar y adaptar explícitamente antes de repetir.

Comandos usados desde el snapshot, con PYTHONPATH/BRS/PATH de las dependencias de QA:

```text
python -m pytest servidor/tests -q --junitxml=servidor-resultados.xml
python -m pytest servidor/ensayos_b3 -q --junitxml=b3-resultados.xml
python roku-app/pruebas/correr.py
node compilar.cjs
python comprobaciones_adicionales.py
brs -n recargar_qa.brs roku-app/components/MainScene.brs
```

Los ensayos B3 y comprobaciones adicionales requieren PostgreSQL 16 AISLADO y desechable: `LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres`. Usan preparar_base y eliminan/recrean sus bases de ensayo. Nunca apuntar al VPS o una base compartida. Se usó PG 16.15 temporal, detenido al finalizar. No copiar dependencias, datos PG ni fuentes extraídas al repositorio.

Recargar se ejecutó con dobles de nodos en brs: el archivo confirma las acciones de la función; no simula un motor SceneGraph real. El problema del observador proviene del código/XML y el contrato oficial citado en el informe. No se ha probado Roku físico.

Las capturas de UI y hashes corresponden al candidato de Claude; no se generó una captura nueva ni se ejecutó su navegador. hashes-candidato.json identifica los 34 archivos cambiados. No contiene credenciales de producción.
