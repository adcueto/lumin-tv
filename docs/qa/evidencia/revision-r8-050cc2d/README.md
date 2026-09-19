# Evidencia QA R8 — 050cc2d090b58f4d1a7b1673c830111a347b3768

Fecha 2026-09-19. [Informe25](../../informes/25-qa-B3-rev7-RF26-050cc2d.md). Base a0583df; fuente extraída por git archive sin checkout.

- b3-resultados.xml: 55 ensayos ejecutados por Codex, cero omitidos/fallos/errores, PG16.15/psycopg3.2.3/Python3.12/pytest9.1.1.
- adicionales-resultados.json: restricciones por sucursal/pantalla pendiente rechazan; movimiento con relaciones falla; confirmación hacia historial de otra empresa entra y falta columna empresa_id. Es un ejecutor de caracterización, no aprobación verde del producto.
- ddl-rf26-extraido.sql: CREATE TABLE relevantes y §3.2b copiados literalmente del diseño. Se ejecutaron como propietario en qa_rf26, sin políticas completas; no atribuir al ensayo una prueba RLS/API.
- ci.json/ci-resumen.txt: run35434726333 del SHA exacto; 28 servidor,55 PG,42+21 Roku,compilación en CI. Los componentes sin cambios se conservan por identidad con QA24; no se reejecutaron localmente pruebas o capturas sin cambios.
- identidad-producto-panel.json y hashes-candidato.json: identidad del alcance preservado y seis archivos cambiados.

## Repetición

Extraer candidato en carpeta desechable, copiar comprobaciones_adicionales.py, proporcionar dependencias de QA y ejecutar:

```text
python -m pytest servidor/ensayos_b3 -q --junitxml=b3-resultados.xml
python comprobaciones_adicionales.py
```

Usar exclusivamente un PostgreSQL16 de QA desechable en loopback y LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres. Los ensayos recrean lumin_ensayo y lumin_ensayo_otra; nunca usar VPS ni cluster compartido. El PG temporal se detuvo al finalizar. No copiar datos PG/dependencias/fuentes extraídas al repositorio.

RF26-QA-02 se sustenta en la secuencia de mensajes del contrato: no hay receptor implementado que ejecutar. Se distingue de las reproducciones SQL y de los 55 tests aportados.
