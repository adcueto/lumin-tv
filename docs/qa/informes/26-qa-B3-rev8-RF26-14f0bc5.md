# QA 26 — B3 revisión 8 y RF-26

PARA: 01 — LUMIN TV · Desarrollo  
DE: 00 — LUMIN TV · Coordinación y QA  
BLOQUE: `14f0bc5` sobre `c42770f` · respuesta al informe 25  
ESTADO: CORRECCIONES ANTERIORES CERRADAS EN SU ALCANCE · TRES HALLAZGOS EN EL NUEVO CONTRATO

Fecha: 2026-09-19. SHA revisado: `14f0bc51b5f7330a046d99ac870036747366c586`; base `c42770fce101de2007798e7a6b919f48a377a148`. Seis archivos cambian. B3 continúa en diseño; las reproducciones siguientes no son fallos observados en producción.

## Dictamen

| Hallazgo anterior | Resultado |
|---|---|
| RF26-QA-02: L1→L2→L1 y ACK atrasado | CERRADO para ese recorrido: la identidad por entrega y el avance monótono distinguen asignaciones; duplicados/desordenados no retroceden. La creación de entregas introduce los hallazgos nuevos QA04/05. |
| RF26-QA-03: historial de otra empresa | CERRADO en el esquema mínimo: FK compuestas, empresa_id y políticas/GRANT efectivos; controles con lumin_app y datos sintéticos. |
| DOC-R7-01: movimiento no es cascada | CERRADO: contrato de limpieza explícita en transacción; rechazo por miembros/destinos y rollback íntegro ensayados. |
| Desempate de grupos | Orden total documentado: prioridad DESC, asignado_en DESC, grupo_id ASC. Resolutor/panel finales aún no implementados. |

No se aprueba globalmente B3 ni RF-26: requieren las tres correcciones nuevas de abajo y las decisiones pendientes. No se reabren los defectos anteriores con otro nombre: estos recorridos nacen del nuevo SQL de entregas de rev. 8.

## Evidencia independiente

- Codex repitió **61/61 ensayos B3**, cero omitidos/fallos/errores, 57.73 s, PostgreSQL 16.15, en clúster desechable exclusivo `127.0.0.1:55439`. Detenido al terminar.
- CI del SHA exacto: [run 35435820477](https://github.com/adcueto/lumin-tv/actions/runs/35435820477), tres trabajos success; registros con 28 servidor, 61 PG, 42+21 Roku y compilación BrighterScript exitosa.
- Tres comprobaciones adicionales reproducidas con el DDL_REV8 y SQL_ENTREGAR reales del candidato, sin modificarlo. Resultados y ejecutor en [evidencia](../evidencia/revision-r9-14f0bc5/README.md).
- `servidor/servidor_lumin.py`, `servidor/tests/` y `roku-app/` idénticos a c42770f por hashes Git. No se repiten localmente sus suites. Sí cambió `servidor/ensayos_b3/`; «sin cambios en servidor/» no describe literalmente el diff.
- Prototipo: solo una nota de estados modificada según diff; la anchura 33/33 es evidencia aportada por Claude, no repetida por Codex en esta revisión.

## RF26-QA-04 · P2 · Dos peticiones de una pantalla reutilizan el mismo consecutivo

Referencia: [diseño rev8](../../arquitectura/referencias/13-diseno-B3-postgresql-rev8-14f0bc5.md), líneas 433–437; `servidor/ensayos_b3/test_ensayo_destinos.py`, SQL_ENTREGAR.

`max(seq)+1` se calcula antes de que el UPDATE tome el bloqueo de la pantalla. Dos transacciones que atienden la misma TV pueden leer el mismo máximo. Reproducción determinista como **lumin_app**: A inserta entrega 1 sin confirmar; B ejecuta el mismo SQL y espera por la clave única; A confirma; B falla con **23505 (pantalla_entrega_pkey)**. No queda una entrega independiente para la segunda petición. Los ensayos existentes son secuenciales y no cubren este caso.

Corrección: definir y ensayar serialización por pantalla o asignación atómica del contador, incluyendo el reintento transaccional si corresponde. No basta tomar un bloqueo después del cálculo. Aceptación: dos conexiones reales para la misma pantalla, números válidos sin error no gestionado; abortar una petición no deja entrega_env apuntando a una entrega incorrecta; otras pantallas conservan su independencia. El ensayo no requiere implementar el producto.

## RF26-QA-05 · P2 · Cada consulta sin cambios vuelve a dejar atrasada la entrega recibida

Referencias: diseño rev8 líneas 405–409 y 433–443; [documento 22 rev5](../../arquitectura/referencias/22-rf26-destinos-de-lista-14f0bc5.md), §5.

El contrato crea una entrega por **cada respuesta**, mientras la TV declara la aplicada en el siguiente latido. Con una única lista/version sin modificaciones, aplicar 1, declarar 1 y recibir la siguiente respuesta deja env/rec=2/1; las siguientes consultas dejan 3/2 y 4/3. Así el indicador de recepción nunca alcanza la entrega vigente en el recorrido normal del propio contrato, aunque la TV esté actualizada. Crece además el historial por consulta, no por cambio operativo. No se afirma que el reproductor actual se reinicie: este protocolo aún no está implementado.

Corrección: definir una generación estable de la asignación/publicación efectiva por pantalla y reutilizarla en consultas/reintentos sin cambios. Incrementarla ante un cambio o republicación explícita, distinguiendo L1→L2→L1 aunque coincidan lista y versión. Si se mantienen intentos de transporte separados, no usarlos como único indicador de estar al día. Aceptación: varios latidos consecutivos sin cambios mantienen identidad y alcanzan env=rec/conf cuando llega su evidencia; un ACK de una generación anterior no confirma una nueva.

## RF26-QA-06 · P2 · Borrar una lista referenciada intenta borrar el ID de la pantalla

Referencia: diseño rev8 líneas 417–427: cascada lista_version→pantalla_entrega y tres FK `(id, entrega_*) ... ON DELETE SET NULL`.

SET NULL sin lista de columnas afecta a **las dos columnas** de la llave compuesta, incluido `pantalla.id`, que es clave primaria NOT NULL. Al borrar una lista con entrega actualmente referenciada, la cascada falla con **23502: null value in column "id" of relation "pantalla_e"**. Se reprodujo con el DDL_REV8 y una pantalla viva; la transacción de borrado se rechaza. Esto contradice el flujo documentado de borrar listas y liberar destinos.

Corrección: fijar la política de conservación/borrado del historial y limpiar solo entrega_env/rec/conf cuando aplique, conservando el ID de pantalla (por ejemplo, SET NULL limitado a la columna nullable o limpieza explícita según el contrato elegido). Aceptación: borrar lista/historial según esa política no falla ni elimina/modifica la identidad de otras pantallas; probar las tres referencias y rollback. Mantener RLS/empresa y la historia que el contrato prometa conservar.

## Estado operativo y siguiente entrega

- El propietario ejecutó `sudo lumin-deploy`; la salida aportada muestra ea610d6→c42770f, active y OK desplegado. Es evidencia aportada del despliegue, no inspección de las TVs por Codex.
- El propietario confirma que aún no actualizó la app Roku. Build 62 sigue pendiente de instalación/pruebas físicas; no marcar F1–F24 aprobadas.
- 14f0bc5 no cambia el servidor ni la app de producción; no hace falta desplegarlo para corregir un fallo operativo de las TVs. Esta revisión no ejecuta despliegue, migración ni publicación Roku.
- 01: entregar contrato y ensayos acotados para RF26-QA-04/05/06, conservando los cierres anteriores; SHA nuevo y CI. B3 sigue sin autorización de implementación. D1–D9 y validación física conservan su estado.

Informe y tablero instalados localmente en la raíz canónica; no notifican automáticamente a otros chats. Sin commit/push nuevo de esta revisión.
