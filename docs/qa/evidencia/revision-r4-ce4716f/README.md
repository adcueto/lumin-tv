# Reproducir QA ce4716f

SHA: ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2. Evidencia local de Codex, 2026-09-16.

1. Extraer ese SHA con git archive a una carpeta aislada. No ejecutar junto a producción.
2. Instalar pytest 9.1.1, psycopg[binary] 3.2.3, @rokucommunity/brs 0.47.6, brighterscript 0.73.5 en un entorno de QA. Aquí Python 3.12, Node 24.18.1, PostgreSQL 16.15 Windows.
3. Iniciar un cluster PG16 desechable en 127.0.0.1:55432. Añadir sus binarios al PATH para que pg_dump y pg_restore se ejecuten: no aceptar ese test omitido. Se usó trust exclusivamente en el cluster sintético de loopback; no es configuración de producción.
4. Establecer `LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres`. ATENCIÓN: preparar_base recrea lumin_ensayo; usar SOLO el cluster desechable.
5. Desde la raíz de la copia: `python -m pytest servidor/tests -q --junitxml=servidor-resultados.xml` y `python -m pytest servidor/ensayos_b3 -q --junitxml=b3-resultados.xml`. Resultado: 21 y 21 passed; sin skips ni errores.
6. BRS apunta al ejecutable brs instalado (`brs.cmd` en Windows). `python roku-app/pruebas/correr.py`: 35 comprobaciones, 0 fallos. Se sustituyen solo las interfaces declaradas por el arnés; no es prueba física.
7. Copiar compilar.cjs a la raíz extraída; sus dependencias están en deps/node/node_modules. Ejecutar `node compilar.cjs`: 8 BRS/XML, 0 diagnósticos; no genera paquete.
8. Copiar comprobaciones_adicionales.py a la raíz extraída; mantener DSN local. `python comprobaciones_adicionales.py`: reproduce los contratos objetados en el informe. El script modifica únicamente su base sintética y temporales, no producto. Necesita el candidato y sus dependencias; los archivos de evidencia solos no son un checkout ejecutable.
9. Detener el cluster: pg_ctl -D <directorio-exclusivo-QA> -m fast -w stop. Se hizo al terminar esta revisión.

Los XML JUnit contienen rutas/nombre de host del entorno local, no datos productivos. No se copian binarios, dependencias, bases de datos ni snapshots fuente al repositorio. hashes.json identifica los archivos del candidato revisado.
