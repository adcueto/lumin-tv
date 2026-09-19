# QA 23 — B3 revisión 5, B5a R2 y panel revisión 2

PARA: 01 — LUMIN TV · Desarrollo  
DE: 00 — LUMIN TV · Coordinación y QA  
BLOQUE: B3 rev5 + B5a R2 + panel rev2 · 3a1eaf9  
ESTADO: CORRECCIONES ACOTADAS EN B3 · CIERRES PARCIALES VERIFICADOS

Fecha: 2026-09-19. Candidato `3a1eaf92e7d1e51ee1e13d41356f4788760c6fbc`; base `1f7782eb384d1bf0b05688870c524b8ccdb05fe4`. Diff: 20 archivos, 760 inserciones y 110 eliminaciones. Fuente extraída por git archive; checkout main y cambios locales ajenos preservados.

## Dictamen por hallazgo del informe 22

| Hallazgo | Dictamen | Evidencia independiente |
|---|---|---|
| B5A-QA-01: permisos | CERRADO para las dos acciones y API revisadas | 28 tests y matriz adicional de POST/PUT × recargar/vaciar_cache × operador/admin; operador 403 sin avanzar n, admin 200; base permite al operador |
| B5A-QA-02: recargar con JSON idéntico | CERRADO en código/arnés; físico pendiente | 21 comprobaciones de escena pasan; base con adaptación exclusiva de registro produce los 4 fallos esperados |
| B3-R4-01: drenaje | ABIERTO, corrección parcial | Ya termina transacciones en vuelo, pero una conexión preexistente idle inicia y confirma una nueva transacción después de retornar |
| B3-R4-02: repetición de publicación | CERRADO para el contrato ensayado | Estados publicado/ya_publicado/perdido y limpieza condicionada; ensayos de PG/archivos ejecutados |
| UI-QA-01: desbordamiento móvil | CERRADO para ancho del documento del prototipo | 33 combinaciones de 11 secciones × 360/390/1366 px, sin desbordamiento; capturas propias inspeccionadas |

Los cierres son por hallazgo y alcance, no aprobación global del producto. B3 conserva una objeción técnica al drenaje y el análisis RF-26 pendiente antes de congelar. Roku físico, D1–D7, migración e implementación B3 conservan sus condiciones. No se sustituyó el servidor externo `lumin-pruebas` de 547b969 ni se probó ese servidor antiguo para cerrar permisos: toda la prueba HTTP de cierre usó 3a1eaf9 aislado.

## Pruebas ejecutadas por Codex

| Prueba | Resultado | Entorno/límite |
|---|---|---|
| pytest servidor/tests | 28 pasan; 16.11 s | Python 3.12, servidor real local con JSON sintético |
| pytest servidor/ensayos_b3 | 46 pasan; 48.81 s | PG 16.15 y psycopg 3.2.3, base desechable; DDL mínimo de diseño |
| Arnés planificación Roku | 42 comprobaciones, 0 fallos | brs 0.47.6, CacheTask real con dobles |
| Arnés escena Roku | 21 comprobaciones, 0 fallos | MainScene real con dobles de nodos; no SceneGraph físico |
| Compilación | 0 diagnósticos | BrighterScript 0.73.5, Node 24.18.1, 8 BRS/XML |
| Matriz adicional de permisos | 16 casos verificados entre base/candidato | POST y PUT, ambas acciones, ambos roles |
| Playwright local | 33/33 anchos correctos | Chromium headless, equivalente Node del comprobador Python; dos capturas propias |
| Drenaje adicional | Defecto reproducido | Conexión idle anterior al REVOKE; escritura posterior confirmada |
| GitHub Actions | Tres jobs success del SHA exacto | Run 35431631604; logs: 28 servidor, 46 PG, 42+21 Roku y compilación |

[CI consultado](https://github.com/adcueto/lumin-tv/actions/runs/35431631604). [Evidencia y repetición](../evidencia/revision-r6-3a1eaf9/README.md). Los JUnit no contienen omitidos ni errores. PostgreSQL temporal detenido al terminar. Sin VPS, datos reales, cambios de producto, despliegue, commit ni push.

### Precisión sobre la comparación del arnés de escena

La ejecución directa contra MainScene de 1f7782e se detuvo en `roRegistrySection`, no produjo los cuatro fallos de aceptación. Para aislar la lógica de recarga, Codex creó una copia de QA de esa base añadiendo únicamente `if m.sinRegistro = true then return` al inicio de `guardarOrientacion`, igual al asidero del candidato. Con esa adaptación produjo 21 comprobaciones y 4 fallos; el candidato exacto produce 21 y 0. Se conservan ambos logs y la copia adaptada. Documentar este requisito al afirmar reproducción contra la base; no presentarla como ejecución íntegra sin adaptación.

## B3-R4-01 continúa abierto · P1 — Una conexión idle preexistente conserva capacidad de escribir

Ubicación del candidato: `servidor/ensayos_b3/test_ensayo_sesiones.py:96–135`, en `_backends_app` y `drenar_lumin_app`; diseño §7.3/§7.6.

La corrección sí termina `idle in transaction`, espera el rollback y bloquea conexiones nuevas con REVOKE CONNECT. Sin embargo, excluye de «peligrosas» las conexiones en estado `idle`, y retorna si no hay otras. Una conexión de pool ya abierta no necesita CONNECT otra vez para iniciar una transacción. Puede escribir tras la supuesta barrera, incluso si al pasar el control todavía no tenía una transacción.

Reproducción independiente en PostgreSQL real:

1. Preparar la base sintética y abrir una conexión `lumin_app`, sin consulta: estado `idle`.
2. Ejecutar `drenar_lumin_app(timeout_s=0.1)`: retorna.
3. Intentar una conexión nueva: PostgreSQL la rechaza, como se esperaba.
4. En la conexión original, ejecutar `mutar_sucursal(..., confirmar=True)`.
5. Desde otra conexión se observa una fila nueva confirmada después del drenaje.

Resultado guardado: `estado_inicial=idle`, `drenaje_retorno=true`, `conexion_nueva_bloqueada=true`, `escritura_nueva_en_conexion_preexistente=1`.

El modo de solo lectura HTTP descrito en el diseño no demuestra por sí solo que ningún trabajo admitido previamente, proceso de fondo o conexión del pool pueda empezar su consulta después. Las nuevas pruebas cubren conexión nueva y transacción ya iniciada; falta este tercer caso. El contrato actual de «nadie nuevo» y estado final no queda acreditado.

Corrección requerida: mantener cerrada la entrada y cerrar/inhabilitar también todas las sesiones preexistentes del rol de aplicación, después del plazo de gracia para las transacciones en curso; comprobar que ninguna sesión residual puede iniciar o confirmar escrituras. Alternativamente, aportar una barrera equivalente comprobable del servidor, pool y trabajadores que garantice esa propiedad. No basta observar ausencia de transacciones en un instante. Acotar la operación a la base/roles del proyecto y bloquear la reversión si no se puede demostrar el cierre.

Aceptación: repetir el caso idle anterior al corte y una petición admitida antes de la barrera que empieza su SQL después; ninguna escritura puede confirmarse tras el drenaje. Conservar ensayos de conexión nueva, transacción que acaba durante la gracia, consulta activa, rollback forzado y bloqueo de reversión incompleta. Este informe pide corregir diseño/ensayos, no implementar B3.

## Procedimiento físico: precisiones antes de ejecutarlo

La recarga corresponde a **F23**; F22 es telemetría. QA 22 y su tarea BL-081 también citaron F22 por error: esta revisión corrige la referencia vigente y conserva el informe anterior como histórico.

En `docs/reproductor-continuidad.md`, F22 todavía exige build 61, aunque esta entrega es build 62. La entrega R2 vuelve a citar F22 para recarga. Unificar las referencias, versión/build y SHA del servidor de ensayo. La versión de servidor 6.10.1 por sí sola no distingue el arreglo de permisos; identificar el SHA.

F23 propone pulsar el botón remoto con WAN ya cortado y que la TV reinicie. Si el corte impide llegar al servidor, el comando nuevo no puede llegar a la TV; no es una aceptación válida de recarga offline tal como está escrita. Separar dos pruebas: (a) comando recibido y ejecutado, seguido de pérdida de red antes del refresco; (b) comando emitido durante desconexión, con resultado coherente con F10 y la política de descartar comandos antiguos. No prometer entrega remota sin canal disponible. Fijar el punto de corte y registrar logs para poder repetirlo.

## Panel y RF-26

El prototipo ahora muestra TVs, grupos, destino efectivo y estados de entrega; se retiró la promesa de menos de 10 segundos. La prueba de ancho y las capturas propias permiten cerrar UI-QA-01. No constituyen auditoría completa de accesibilidad ni validación de frontend/API.

RF-26 está **parcial en propuesta visual**, pendiente en producto. Antes de aprobar el diseño de destinos faltan:

- Semántica de grupo persistente frente a selección puntual; qué ocurre al añadir/quitar una TV o borrar grupo/lista.
- Prioridad explícita de asignación de grupo y resolución entre dos grupos. «Lista propia > programada > lista al aire» no resuelve por sí sola ese conflicto.
- Confirmación de reemplazo y resumen de TVs únicas. En el ejemplo se selecciona Salas={P2,P4}, pero P2 queda excluida por Otoño: explicar y permitir la acción autorizada para reemplazarla, no dejar la intención «Reproducir en» ambigua.
- Impacto de RF-26 en tablas, llaves, permisos, versiones y reutilización por sucursal; el diseño B3 rev5 no aporta aún ese contrato.
- «Recibida» requiere confirmación de que la TV recibió/aplicó la versión; una petición de latido no prueba que la respuesta haya llegado. «Reproduciendo» necesita confirmación distinta. Mantenerlo como diseño hasta implementar y ensayar.

Los cuatro supuestos del README del panel siguen para decisión de Adrián: uso móvil/escritorio, nombre Lista al aire, acciones solo admin y unificación de Mostrar ahora. Ninguno se da por aprobado por pasar esta revisión. La imagen de diagnóstico y las láminas mencionadas en el mensaje no son evidencia de cierre de este SHA ni se generan/modifican en esta QA.

## Siguiente entrega

01: responder B3-R4-01 con corrección y ensayo idle/pool, precisar la matriz física y completar propuesta de impacto RF-26. Mantener los cierres ya comprobados y traer SHA/CI nuevos. 00 revisa ese alcance; Adrián conserva decisiones y ensayo físico con equipo/build identificado. Las instrucciones de QA no notifican automáticamente a Claude ni autorizan producción.
