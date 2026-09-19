# Diseño de B3 — PostgreSQL y modelo multiempresa (revisión 9)

Para revisión de Adrián y Codex **antes de escribir código**.
Fecha: 2026-09-19 · Autor: Claude · Base: `modernizacion-diagnostico` (servidor 6.10, app 5.2 build 62)

## Qué cambia en esta revisión 9 (respuesta al informe 26 sobre `14f0bc5`)

Codex cierra RF26-QA-02, RF26-QA-03 y DOC-R7-01 en el alcance ensayado y
reproduce tres problemas del contrato de entregas de la rev. 8. Los tres se
**CONFIRMAN**. Ensayos: de 61 a **67**.

| Hallazgo de Codex | Decisión | Dónde | Ensayo |
|---|---|---|---|
| RF26-QA-04 dos peticiones simultáneas de la misma TV calculan el mismo consecutivo (`max(seq)+1`); una falla por clave duplicada | **CONFIRMADO.** El número sale de un **contador en la fila de la pantalla** (`pantalla.entrega_ultima`), y servir una lista es una transacción que empieza con `SELECT … FOR UPDATE` de esa fila: las peticiones de una misma TV se serializan y cada una ve el resultado de la anterior. El contador nunca se reinicia. Detalle que el arnés descubrió: bloquear y leer la entrega vigente deben ser **dos sentencias**, no un `JOIN`; en `READ COMMITTED` la fila bloqueada se relee al despertar pero el `JOIN` conserva la instantánea vieja y no ve la entrega que la otra transacción acaba de confirmar | §3.2b | reproducción con el SQL de la rev. 8 (A abre la transacción, B espera sobre la clave y falla con `UniqueViolation`); con la rev. 9, B espera el bloqueo de la pantalla y obtiene 2 tras el 1 de A; con la **misma** lista en carrera, 1 y 1 y una sola fila |
| RF26-QA-05 cada consulta crea otra entrega aunque no cambie la playlist; la recepción queda siempre una atrás (2/1, 3/2, 4/3) | **CONFIRMADO.** Servir es **idempotente**: con el bloqueo tomado se lee la entrega vigente y, si ya es `(lista, version)`, se devuelve su número sin crear nada. Solo un cambio de lista o de versión —o volver a una anterior, que es otra asignación— crea la entrega siguiente. Una TV que consulta cada minuto sin novedades sigue "al día" | §3.2b | reproducción con el SQL de la rev. 8 (`[(2,1),(4,3),(6,5)]`); con la rev. 9 cinco consultas seguidas devuelven 1 y la recepción sigue al día; v2 → 2; otra lista → 3; volver → 4 |
| RF26-QA-06 borrar una lista referenciada falla: `ON DELETE SET NULL` de la llave compuesta `(id, entrega_x)` intenta anular también `id` | **CONFIRMADO.** `ON DELETE SET NULL (entrega_x)` con lista de columnas (PostgreSQL 15+; el proyecto fija 16). Borrar la lista borra su historial y sus entregas, anula los tres punteros de la pantalla y conserva `id` y el contador; la siguiente entrega continúa la numeración, así que un número borrado **nunca se reutiliza**. Regla del servidor: un `en=` que ya no existe es "entrega desconocida" (viola la FK), se ignora, y la TV recibe una entrega nueva en su próxima consulta | §3.2b; `22-…md` §5 | reproducción con la rev. 8 (`NotNullViolation`); con la rev. 9 el borrado entra, la pantalla queda `(id, NULL, NULL, NULL, ultima=1)`, confirmar la 1 falla por FK, la siguiente entrega es la 2 y se confirma |

## Qué cambió en la revisión 8 (respuesta al informe 25 sobre `050cc2d`)

Codex cierra el drenaje acotado a la base (B3-R4-01) y los cruces de sucursal
(RF26-QA-01). Las tres correcciones que quedan —RF26-QA-02, RF26-QA-03 y
DOC-R7-01— se **CONFIRMAN**. Ensayos: de 55 a **61**.

| Corrección de Codex | Decisión | Dónde | Ensayo |
|---|---|---|---|
| RF26-QA-02 [P1] El par `(lista, version)` distingue listas distintas, pero no dos asignaciones sucesivas de la **misma** lista (L1 → L2 → L1): una confirmación de la primera asignación parece "al día" en la tercera | **CONFIRMADO.** Lo que se confirma no es un contenido sino una **entrega**: cada vez que el servidor sirve `(lista, version)` a una pantalla inserta una fila en `pantalla_entrega` con número **consecutivo por pantalla**; la respuesta lleva ese número, la TV lo devuelve en el latido y en la confirmación, y `pantalla.entrega_env / entrega_rec / entrega_conf` guardan números de entrega con FK a la tabla. "Al día" es `entrega_conf = entrega_env`. Confirmar es **monótono** (`UPDATE … WHERE entrega_conf IS NULL OR entrega_conf < n`): una confirmación atrasada no retrocede nada, y una entrega que la pantalla nunca recibió viola la FK. El par sigue disponible para el panel por la fila de la entrega | §3.2b; `22-…md` §5 | `test_ensayo_destinos.py`: reproducción del L1 → L2 → L1 con el esquema de la rev. 7 ("al día" falso); con la rev. 8, el contraejemplo de Codex tal cual (confirma L1, reproduce L2, se reasigna L1, llega la confirmación atrasada de la primera L1: 0 filas, no "al día"), duplicados y desordenados (0 filas), inexistente (FK), reconexión (la TV vuelve declarando la entrega 3 con la 4 enviada: el panel ve 4/3/3; un latido viejo no retrocede), numeración independiente por pantalla |
| RF26-QA-03 [P1] `lista_version` sin `empresa_id`: el SQL admite que una pantalla confirme una versión de una lista de **otra empresa** (RLS no interviene en la comprobación de llaves foráneas) | **CONFIRMADO.** `lista_version` lleva `empresa_id` con FK `(lista_id, empresa_id) → lista` y `UNIQUE (lista_id, version, empresa_id)`; `pantalla_entrega` lleva `empresa_id` y referencia `pantalla(id, empresa_id)` **y** `lista_version(lista_id, version, empresa_id)`, así que pantalla y lista son de la misma empresa por construcción, diga lo que diga el `empresa_id` que escriba la aplicación | §3.2b, §3.5 | reproducción con la rev. 7 (la pantalla de A confirma la lista de B); con la rev. 8 y como propietario: versión con empresa equivocada y entrega cruzada fallan por FK. **Como `lumin_app`, con las políticas escritas en el DDL del ensayo:** sin contexto no ve ni inserta historial ni entregas; con empresa A no ve el historial de B, no puede insertar en él (política) ni mintiendo la empresa (FK), la entrega cruzada falla por los dos caminos, la confirmación sobre una pantalla de B toca 0 filas; positivo: su lista avanza a v2 y el historial v1 sigue legible y referenciado |
| DOC-R7-01 [P2] Precisión documental: mover una pantalla de sucursal **no** limpia relaciones en cascada; la base rechaza el movimiento hasta que se limpien explícitamente | **CONFIRMADO.** Es lo que el ensayo ya demostraba y el texto de la rev. 7 decía mal. Corregido en §3.2b y en el documento 22 (§2 y §6): el `UPDATE` de `sucursal_id` falla mientras queden miembros o destinos; "mover" es **una transacción** del servidor que borra miembros y destinos y luego mueve, y el panel lo avisa antes. El esquema impide hacerlo a medias; no lo hace por uno | §3.2b; `22-…md` §2, §6 | `test_mover_pantalla_de_sucursal_exige_limpiar_grupos_y_destinos`: rechazo con miembro, rechazo con destino, transacción correcta; `test_mover_pantalla_es_una_transaccion_que_revierte_entera`: fallo intermedio (sucursal de otra empresa) deja relaciones y sucursal intactas. No se usa `ON UPDATE CASCADE`, que no significa borrar los vínculos de la sucursal anterior |

## Qué cambió en la revisión 7 (respuesta a `24-qa-B3-rev6-RF26-a0583df.md`)

Los tres problemas se **CONFIRMAN**. Ensayos: de 50 a **55**.

| Problema de Codex | Decisión | Dónde | Ensayo |
|---|---|---|---|
| 1. El drenaje termina sesiones de `lumin_app` en **otras bases** de la misma instancia (la consulta a `pg_stat_activity` filtraba solo por `usename`) | **CONFIRMADO.** La barrera queda acotada a **esta base**: `usename = 'lumin_app' AND datname = <base>`. Es también lo que el `REVOKE CONNECT ON DATABASE` cierra, así que el "cero sesiones" que se verifica y la entrada que se cerró hablan de la misma base. Otras bases de la instancia (otro entorno, otro producto) no se tocan | §7.3 | `test_ensayo_sesiones.py` (19): se crea una segunda base con una conexión `lumin_app` con transacción abierta; el drenaje de `lumin_ensayo` la deja viva y su commit confirma; se conservan los 18 anteriores |
| 2. Las restricciones de §3.2b permitían relacionar pantallas, grupos y listas de **sucursales distintas** (miembro y destino solo comprobaban `empresa_id`) | **CONFIRMADO.** La sucursal viaja en todas las llaves: `pantalla`, `lista` y `grupo_pantallas` exponen `UNIQUE (id, sucursal_id)`; `grupo_pantalla_miembro` y `lista_destino` llevan `sucursal_id NOT NULL` y sus llaves foráneas son compuestas `(x_id, sucursal_id)`. Un cruce de sucursal viola la FK; mover una pantalla de sucursal exige antes quitarla de sus grupos y destinos (la relación pertenece a la sucursal, no viaja con la TV; *la rev. 7 decía "en cascada", corregido en la rev. 8: la base rechaza el movimiento, no limpia*) | §3.2b | `test_ensayo_destinos.py` (4): reproducción con el DDL de la rev. 6 (los tres cruces entran), el DDL de la rev. 7 rechaza los mismos tres y acepta los correctos, mover de sucursal exige limpiar membresías y destinos |
| 3. Dos listas pueden tener "versión 1": confirmar solo el número no identifica qué lista reproduce la TV | **CONFIRMADO.** La confirmación es el **par** `(lista_id, version)`. Las versiones son un historial append-only (`lista_version`), y la pantalla guarda `lista_conf_id + lista_conf_version` con `CHECK` de par completo y FK al historial: no se puede confirmar una versión que no existió, y una lista puede avanzar sin dejar colgada la confirmación de una versión anterior. Lo mismo para "enviada" y "recibida" (B5b): siempre el par | §3.2b; `22-…md` §5 y §6 | `test_ensayo_destinos.py`: dos listas en versión 1 se distinguen por el par; un par inexistente se rechaza; la lista avanza a 2 y la confirmación de 1 sigue siendo consultable |

## Qué cambió en la revisión 6 (respuesta a `23-qa-B3-rev5-B5a-R2-3a1eaf9.md`)

| Corrección de Codex | Decisión | Dónde | Ensayo |
|---|---|---|---|
| B3-R4-01 (continúa) [P1] una conexión `idle` preexistente sobrevivía al drenaje y podía iniciar y confirmar una escritura después | **CONFIRMADO.** El drenaje de la rev. 5 solo terminaba sesiones con transacción viva; una conexión de pool ya abierta no necesita `CONNECT` para empezar otra. Ahora la **barrera** es terminar **todas** las sesiones de `lumin_app` —también las `idle`— después de la gracia, y verificar que quedan **cero**; con la entrada cerrada, cero sesiones ahora significa cero escritores hasta que se reabra. La gracia es cortesía con lo que estaba a medias, no la barrera. Acotado al rol `lumin_app` de esta base: espejo y migración no se tocan | §7.3 | `test_ensayo_sesiones.py` (18): reproducción del caso de Codex sobre la barrera vieja (`idle` escribe después), la `idle` preexistente falla al escribir tras el drenaje y no puede reconectar, una petición admitida antes de la barrera que empieza su SQL después falla, otros roles siguen conectados; se conservan conexión nueva, transacción a tiempo, consulta activa, rollback forzado y bloqueo. Total **50** |
| RF-26 (panel): semántica de grupos, prioridad, confirmación de reemplazo, contrato de datos, estados de entrega | Propuesta de impacto en `22-rf26-destinos-de-lista.md`; su esquema entra en este diseño como **§3.2b (contrato, no ensayado)** | §3.2b | — (diseño) |

## Qué cambió en la revisión 5 (respuesta a `22-qa-B3-rev4-B5a-1f7782e.md`)

Las dos correcciones de B3 se **CONFIRMAN**. Ensayos: de 39 a **46**, con la
reproducción de cada defecto con el protocolo anterior.

| Corrección de Codex | Decisión | Dónde | Ensayo |
|---|---|---|---|
| B3-R4-01 [P1] el drenaje cancelaba consultas y retornaba; una transacción `idle in transaction` seguía viva y confirmaba después | **CONFIRMADO.** Contrato nuevo en cuatro pasos: (1) cerrar la entrada con `REVOKE CONNECT ON DATABASE … FROM lumin_app` (la base ya no da `CONNECT` a `PUBLIC`); (2) esperar hasta el plazo a que **ninguna** conexión de `lumin_app` tenga transacción capaz de confirmar (activa, `idle in transaction` o con `backend_xid`); (3) al vencer, **`pg_terminate_backend`** (termina con rollback; cancelar no bastaba); (4) volver a comprobar; si aún queda una, `DrenajeIncompleto` y la reversión se **bloquea**, incluida la de emergencia | §7.3, §7.6 | `test_ensayo_sesiones.py`: reproducción (cancelar no impide el commit tardío), termina `idle in transaction` y el commit falla, termina una consulta activa, cierra la entrada a nuevos escritores, deja confirmar a quien llega a tiempo, `revertir` no escribe con drenaje incompleto |
| B3-R4-02 [P1] reintentar una publicación ya confirmada con la misma posesión devolvía "0 filas" y el contrato ordenaba borrar el artefacto publicado | **CONFIRMADO.** `publicar` devuelve tres resultados: `publicado`, `ya_publicado` (fila `hecho` con **mi** posesión y **mi** ruta: éxito idempotente, el archivo se conserva) y `perdido` (otra posesión ganó o el trabajo fue cancelado/reabierto). Solo `perdido` descarta, y solo lo que lleva la posesión propia. Un artefacto referenciado por `resultado` nunca se borra | §8b | `test_ensayo_cola.py`: reproducción del defecto con el UPDATE crudo, reintento idempotente tras respuesta perdida, reintento tras perder la posesión sigue descartando lo propio, cancelación |

## Qué cambió en la revisión 4 (respuesta a `19-qa-B1-R4-B3-rev3-ce4716f.md`)

Las cuatro correcciones se **CONFIRMAN**. Los ensayos de `servidor/ensayos_b3/`
pasan de 21 a **39**; cada corrección tiene el suyo, incluida la reproducción
del defecto con el protocolo anterior donde aplica.

| Corrección de Codex | Decisión | Dónde | Ensayo |
|---|---|---|---|
| B3-R3-01 [P1] el paso 4 filtraba `membresia` por una empresa que aún no estaba en el contexto | **CONFIRMADO.** La empresa heredada se resuelve **por columna** (`empresa.heredada`, visible para `lumin_app` sin contexto por una rama nueva de la política) y la membresía se comprueba **con ese UUID como parámetro**, por la rama `usuario_id` de la política de `membresia`; solo entonces se asigna `lumin.empresa_id`. Sin consulta circular | §3.5 | `resolver_sesion_migrada` en `test_ensayo_rls.py`: migrada con membresía válida → resuelve la heredada; sin membresía → 401; membresía solo en otra empresa → 401; revocada/vencida → 401; sesión nueva con empresa → no toca la heredada; latido sin sesión ve solo la heredada |
| B3-R3-02 [P1] forzar la reversión con el último `sesiones.json` podía resucitar una revocación posterior | **CONFIRMADO.** La excepción **desaparece**. Toda reversión, incluida la inmediata tras el humo, pasa por el mismo guardián: drenar transacciones en vuelo de `lumin_app`, verificar el estado **final** en PostgreSQL y escribir congelado ∩ vigentes. PostgreSQL inaccesible → **no hay reversión automática**. Única vía de emergencia, con autorización explícita de Adrián: escribir `{}` (todas las sesiones cerradas) declarando que los demás documentos pueden estar desactualizados. Nunca se usa "el último archivo exportado" | §7.3, §7.6 | `test_ensayo_sesiones.py`: reproducción del defecto (revocar tras la última exportación y restaurar ese archivo → cookie aceptada), `revertir` bloquea sin PostgreSQL, emergencia cierra todas, normal usa el estado final, drenaje espera y cancela |
| B3-R3-03 [P2] dos posesiones compartían el nombre del artefacto; el perdedor borraba el de la ganadora | **CONFIRMADO.** El artefacto lleva la **posesión** en el nombre (`<nombre>.<digest8>.<posesion8>.mp4`); publicar es un solo `UPDATE` condicionado a la posesión que además guarda la ruta; quien pierde borra **solo** lo que lleva su posesión; los huérfanos (sin referencia y sin posesión viva) los recoge un barrido | §8b | `test_ensayo_cola.py`: reproducción del defecto con el nombre compartido ("hecho sin archivo"), A vencido / B publicado / A descartado, caída tras escribir y antes del `UPDATE`, reintento idempotente, cancelación en curso |
| B3-R3-04 [P2] el guardián no consultaba el propietario; la matriz decía "ensayado" donde solo hay contrato | **CONFIRMADO.** `guardian_de_catalogo` exige propietario `lumin_migracion`, RLS activa, política para todo `GRANT` y roles sin atributos peligrosos, con **dos casos negativos** (tabla creada por `lumin_app`; tabla sin RLS con `GRANT`). La matriz gana una columna **Ensayado / Contrato** y el texto ya no atribuye a los ensayos lo que no ejecutan | §3.5 | `test_guardian_*` (3) |

## Qué cambió en la revisión 3 (respuesta a `15-qa-R3-y-diseno-B3-rev2-78306df.md`)

Las tres objeciones se **CONFIRMAN**. Esta vez cada corrección viene con un
**ensayo ejecutable** contra PostgreSQL 16 real y datos sintéticos, en
`servidor/ensayos_b3/` (21 ensayos en esta revisión, 39 en la 4; se omiten, no
pasan, si no hay base de ensayo). No es implementación de B3: es el diseño demostrado antes de
programarlo.

| Objeción de Codex | Decisión | Dónde | Ensayo |
|---|---|---|---|
| B3-R2-01 `max(bigserial)` no representa el orden de confirmación | **CONFIRMADO.** El espejo ya no mira `max(id)`. Procesa las marcas **pendientes que ve** (`procesada_en IS NULL`: solo confirmadas) dentro de **una instantánea `REPEATABLE READ`** que también lee todos los documentos; escribe los archivos; y **solo después** marca esas filas. Una marca de una transacción aún abierta no se ve, no se marca y se procesa en el ciclo siguiente a su confirmación. Converge solo; sin nueva escritura | §7.4 | `test_ensayo_espejo.py`: el protocolo viejo **pierde A** con el orden exacto A-reserva/B-confirma/espejo/A-confirma; el nuevo converge; más los tres cortes (tras escribir y antes de marcar, a mitad de los archivos, fallo al persistir el marcador en disco) |
| B3-R2-02 la copia congelada resucita sesiones revocadas | **CONFIRMADO.** `sesiones.json` deja de estar congelado: el espejo lo **regenera** como *copia congelada ∩ sesiones vigentes en PostgreSQL* (hash presente, `revocada_en IS NULL`, no vencida, usuario activo). Un logout durante B3 desaparece del archivo en el siguiente ciclo. Las creadas después del corte siguen sin poder volcarse (solo hash) y quedan cerradas al revertir. No hay tokens nuevos en claro en ningún lado | §7.6 | `test_ensayo_sesiones.py`, con el **servidor 6.10 real**: reproduce el defecto y comprueba el contrato corregido |
| B3-R2-03 permisos: `GRANT INSERT` sin política bloquea el outbox; `FORCE` anula la exención del propietario; el hilo espejo no tiene rol | **CONFIRMADO.** Matriz completa rol/tabla/operación/política. Políticas `FOR INSERT … WITH CHECK` explícitas para `espejo_marca` y `auditoria`. Tercer rol **`lumin_espejo`** (lee todo; solo escribe `espejo_marca.procesada_en` y `espejo_estado`). **`ENABLE`, no `FORCE`**: el propietario `lumin_migracion` queda exento y es quien migra, respalda y restaura; `lumin_app` y `lumin_espejo` no son propietarios de nada. Sin `BYPASSRLS` para nadie | §3.5 | `test_ensayo_rls.py`: cada operación con su rol real, controles negativos, `pg_dump` + `pg_restore` con las políticas dentro, demostración de por qué no `FORCE`, guardián de catálogo |
| Precisiones: §7.4 "13 documentos" vs sesiones; §3.5 arranque con `empresa_id NULL`; §8b límites de publicación y digest por destino; §7.3 número de turno y IPs | Incorporadas | §7.4, §3.5, §8b, §7.3 | — |

Hallazgo propio del ensayo, incorporado: la política de `sesion` necesitaba
`WITH CHECK (token_hash = gc('token_hash') OR usuario_id = …)`; con solo
`usuario_id` el logout (que revoca durante la resolución de la cookie, cuando el
contexto aún no tiene `usuario_id`) fallaba por RLS.

## Qué cambió en la revisión 2 (respuesta a `14-qa-R2-y-diseno-B3-5c96845.md`)

| Objeción de Codex | Decisión | Dónde |
|---|---|---|
| B3-QA-01 la escritura doble no define recuperación ante escritura parcial | **CONFIRMADO.** Se sustituye "escribir en los dos lados" por un **espejo derivado**: cada transacción deja una marca en una tabla de salida (`espejo_marca`) dentro de la misma transacción; un único hilo regenera los JSON completos **desde PostgreSQL** y marca las filas que procesó (en la rev. 3, por marcas pendientes, no por `max(id)`). La reversión se **bloquea** si hay marcas sin aplicar. Con PostgreSQL caído no hay escritura en ningún lado | §7.4 |
| B3-QA-02 la exportación no puede reconstruir sesiones desde el hash | **CONFIRMADO** (superado en rev. 3 por B3-R2-02). El espejo **no toca** `sesiones.json`: queda congelado en su estado del corte. Contrato explícito: toda reversión conserva las sesiones anteriores al corte y **cierra** las creadas después; esas personas vuelven a entrar. Sin tokens en claro | §7.6 |
| B3-QA-03 `lista_elemento` fuera de la política; contrato del rol incompleto; guardián textual insuficiente | **CONFIRMADO.** `lista_elemento` gana `empresa_id` con llaves compuestas y política propia. Contrato del rol: no propietario, `NOINHERIT`, sin `SET ROLE` (el `FORCE` de esta revisión se retira en la 3, ver B3-R2-03). Políticas concretas para las tablas de identidad. El guardián textual se reemplaza por controles negativos ejecutados como `lumin_app` sin JOIN | §3.2, §3.5, §6.3 |
| B3-QA-04 la petición pública del medio no identifica la empresa | **CONFIRMADO.** Contrato explícito de B3: las rutas heredadas `/videos/<clave>/…` resuelven **solo** dentro de la **empresa heredada** (configurada, LUMIN) y **ninguna segunda empresa puede activarse** hasta que exista un espacio de nombres verificable (B8). Se prueba por HTTP real | §8a |
| B3-QA-05 una pantalla pendiente puede apuntar a una lista de otra empresa | **CONFIRMADO.** `CHECK (lista_id IS NULL OR sucursal_id IS NOT NULL)` y FK adicional `(lista_id, empresa_id)` | §3.1 |
| Cola: hash por tamaño, posesión, cancelación de `en_curso` | Incorporado: clave por digest del contenido, `posesion` comprobada al publicar, cancelación de `en_curso` | §8b |
| Corte: solo lectura debe congelar TODOS los escritores; apertura controlada para el humo | Incorporado: modo `LUMIN_SOLO_LECTURA` a nivel de servidor (latidos, contadores, sesiones, turnos, subidas), y ventana de humo con escrituras solo desde una IP | §7.3 |
| Equivalencia §11: declarar normalizaciones; no prometer `numero/desfase` idénticos | Incorporado: equivalencia **semántica** con lista explícita de exclusiones; byte a byte solo para `playlist.json` | §11 |
| Alcance: preparar el esquema no habilita varias empresas | Incorporado como límite explícito, con guarda en la base y en el servidor | §0, §8a |
| D1/D2 con datos concretos | Herramienta de solo lectura `servidor/herramientas/inventario_decisiones.py` para que Adrián la corra en el VPS y tenga IDs y usuarios exactos | §9 |
Responde a los siete puntos de "Orientación para el diseño B3" de `13-qa-B2-0c00f35.md`
(Codex): §3–5 → punto 1; §6 → punto 2; §7 → punto 3; §3.4 y §7.6 → punto 4; §8a → punto 5;
§8b → punto 6; §10 → punto 7.

> Nada de este documento se ejecuta sobre producción. La migración descrita se
> ensaya sobre copias sintéticas y sobre una copia **anonimizada** de los JSON,
> y solo llega al VPS con autorización expresa, en una ventana acordada.

---

## 0. Resumen en una página

**Qué es B3.** Sustituir los 13 archivos JSON del servidor por PostgreSQL, con
un modelo que ya lleva `empresa_id` en todas las tablas de datos, sin que las
TVs, el POS ni el panel noten el cambio. LUMIN queda como la empresa 1.

**Cómo, en cuatro decisiones:**

1. **Un paquete de datos, no un servidor nuevo.** `servidor/lumin_datos/`
   (SQLAlchemy 2 + Alembic) con repositorios por entidad. El servidor 6.x
   actual pasa a usarlos en lugar de `leer_json/escribir_json`. Un solo proceso
   escribe la base. FastAPI (B5) consumirá el mismo paquete: el trabajo de datos
   se hace una vez.
2. **Aislamiento en cuatro capas**, porque las llaves compuestas solas no
   bastan: (a) llaves foráneas compuestas; (b) un `Contexto` obligatorio en cada
   repositorio que filtra por `empresa_id`; (c) **Row Level Security** de
   PostgreSQL como red de seguridad ante un `WHERE` olvidado; (d) una suite con
   **dos empresas** que ataca cada función de lectura y escritura con
   identificadores cruzados, más un guardián en pruebas que revisa cada SQL
   emitido.
3. **Los contratos no cambian.** `GET /playlist.json` byte a byte, `POST/PUT
   /api/turno` igual, `/videos/<sucursal>/<archivo>` igual porque **los archivos
   no se mueven**. El identificador Roku (`GetChannelClientId`) se conserva como
   llave natural. Las cookies de sesión vigentes siguen sirviendo. Los nombres
   de usuario y contraseñas actuales siguen funcionando.
4. **Migración con dos marchas atrás.** Ventana corta con congelación de
   escrituras; después, un **espejo derivado** regenera los 13 JSON desde
   PostgreSQL durante 7 días (marcas pendientes + instantánea única, §7.4),
   de modo que revertir es volver a apuntar el servidor a los JSON **sin
   perder lo escrito después del cambio** y sin resucitar sesiones cerradas
   (§7.6). Pasada la semana, la reversión es por exportación PostgreSQL → JSON,
   con la misma verificación. Los tres protocolos delicados (espejo, sesiones,
   RLS) están **ensayados** contra PostgreSQL 16 en `servidor/ensayos_b3/`.

**Qué no es B3.** No es FastAPI (B5), no es React (B6), no cambia permisos
(B4: hoy se preservan los efectivos, explícitos), no toca el reproductor, no
mueve medios, no introduce planes ni cobros. **Y no habilita una segunda
empresa:** el esquema la admite, pero el servidor y la base impiden activarla
hasta que los medios y las pantallas lleven una identidad de empresa
verificable (B8). Preparar el modelo no es comercializar.

---

## 1. Alcance

| Dentro | Fuera (bloque) |
|---|---|
| Esquema PostgreSQL con `empresa_id` | Endurecer permisos F01/F02/F03 (B4) |
| Paquete `lumin_datos/` con repositorios y `Contexto` | API v2 / FastAPI (B5) |
| Rewire de `servidor_lumin.py` a repositorios | Panel React (B6) |
| Migración JSON → PostgreSQL, respaldo, reversión, escritura doble | Mover medios a S3 / nginx (B5) |
| Suite "dos empresas" y pruebas de contrato | Credencial por pantalla (B8) |
| Instalación de PostgreSQL en el VPS, roles, `pg_dump` nocturno | Reasignar los números de pantalla ya duplicados (decisión, §9) |
| Reserva de columnas para B4/B5 (correo, `clave_evento`) | Cualquier cobro, plan o portal del propietario |

---

## 2. Arquitectura del bloque

```
                servidor_lumin.py (6.x, mismo proceso, mismos contratos)
                          │
                          │  antes: leer_json / escribir_json
                          ▼
              servidor/lumin_datos/          ← NUEVO, B3
              ├── modelos.py     SQLAlchemy 2, tablas de §3
              ├── contexto.py    Contexto(empresa_id, sucursales, rol)
              ├── repos/         una funcion por operacion, todas reciben Contexto
              ├── migrar_json.py JSON → PostgreSQL, idempotente, con informe
              ├── exportar_json.py PostgreSQL → JSON (marcha atras tardia)
              └── alembic/       migraciones versionadas
                          │
                          ▼
                    PostgreSQL 16 (mismo VPS)
                    rol de aplicacion sin superusuario → RLS activa
```

**Por qué el paquete y no un servidor nuevo.** Dos procesos escribiendo los
mismos datos (viejo en JSON, nuevo en PostgreSQL) obligan a sincronizar y
abren una ventana de inconsistencia permanente. Con el paquete hay un solo
escritor desde el primer día, y el código de manejo HTTP viejo —que B5
sustituye— es solo la red de seguridad que mantiene la operación.

**Costo declarado.** El servidor gana sus primeras dependencias externas
(`sqlalchemy`, `psycopg`, `alembic`) y un servicio (`postgresql`) en el VPS.
Es el precio de tener transacciones e integridad; el documento de julio ya lo
daba por bueno.

---

## 3. Esquema PostgreSQL

Convenciones: UUID como llave primaria en todas las tablas; llaves naturales
del sistema actual conservadas en columnas `UNIQUE`; `empresa_id NOT NULL` en
toda tabla de datos; fechas `timestamptz`; nombres en español como el código.

### 3.1 Jerarquía

```sql
CREATE TABLE empresa (
  id            uuid PRIMARY KEY,
  clave         text NOT NULL UNIQUE,            -- 'lumin'
  nombre        text NOT NULL,
  estado        text NOT NULL DEFAULT 'activa'
                CHECK (estado IN ('activa','suspendida','cancelada')),
  zona_horaria  text NOT NULL DEFAULT 'America/Mexico_City',
  creada_en     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sucursal (
  id            uuid PRIMARY KEY,
  empresa_id    uuid NOT NULL REFERENCES empresa(id),
  clave         text NOT NULL,                   -- 'plaza-de-la-mujer' (va en las URLs)
  nombre        text NOT NULL,
  zona_horaria  text,                            -- NULL = la de la empresa
  activa        boolean NOT NULL DEFAULT true,
  orden         int NOT NULL DEFAULT 0,
  lista_activa_id uuid,                          -- FK compuesta mas abajo
  creada_en     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (empresa_id, clave),
  UNIQUE (id, empresa_id)                        -- ancla para FKs compuestas
);

CREATE TABLE pantalla (
  id               uuid PRIMARY KEY,
  empresa_id       uuid NOT NULL,
  sucursal_id      uuid,                         -- NULL mientras esta pendiente
  id_dispositivo   text NOT NULL UNIQUE,         -- GetChannelClientId: NO CAMBIA
  numero           int  NOT NULL,                -- visible en el panel (P6)
  desfase_rotacion int  NOT NULL DEFAULT 0,      -- antes era el mismo campo que numero
  zona             text NOT NULL DEFAULT '',
  aprobada         boolean NOT NULL DEFAULT false,
  codigo_aprobacion text NOT NULL DEFAULT '',
  visto_en         timestamptz,
  turnos_habilitados boolean NOT NULL DEFAULT false,
  lista_id         uuid,                         -- asignada; NULL = hereda de sucursal
  pausada          boolean NOT NULL DEFAULT false,
  silenciada       boolean NOT NULL DEFAULT false,
  creada_en        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (empresa_id, numero),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id),
  CHECK (aprobada = false OR sucursal_id IS NOT NULL),
  -- B3-QA-05: una pantalla pendiente (sucursal NULL) no puede tener lista;
  -- y la lista, si la hay, es de la MISMA empresa aunque la FK por sucursal
  -- no aplique por el NULL (MATCH SIMPLE).
  CHECK (lista_id IS NULL OR sucursal_id IS NOT NULL)
);
-- las dos FKs de lista_id se declaran tras crear `lista` (ver 3.2):
--   FOREIGN KEY (lista_id, sucursal_id) REFERENCES lista(id, sucursal_id)
--   FOREIGN KEY (lista_id, empresa_id)  REFERENCES lista(id, empresa_id)
```

`numero` y `desfase_rotacion` se separan: hoy son el mismo campo y por eso dos
pantallas con número repetido arrancan la lista en la misma posición.

### 3.2 Contenido y listas

```sql
CREATE TABLE contenido (
  id              uuid PRIMARY KEY,
  empresa_id      uuid NOT NULL,
  sucursal_id     uuid NOT NULL,
  nombre_archivo  text NOT NULL,                 -- 'promo uñas.mp4' (va en la URL)
  tipo            text NOT NULL CHECK (tipo IN ('video','imagen')),
  duracion_imagen int  NOT NULL DEFAULT 10,      -- duraciones.json
  girado          boolean NOT NULL DEFAULT false,-- girados.json
  posicion        int  NOT NULL DEFAULT 0,       -- ordenes.json (orden en biblioteca)
  tamano_bytes    bigint,                        -- B5 los llena; hoy NULL
  duracion_s      numeric(8,2),
  ancho           int, alto int,
  estado          text NOT NULL DEFAULT 'listo'
                  CHECK (estado IN ('procesando','listo','fallido')),
  ruta_almacen    text,                          -- NULL = local en <clave>/<archivo>; B5 (S3) la llena
  creado_en       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (sucursal_id, nombre_archivo),
  UNIQUE (id, sucursal_id),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id)
);

CREATE TABLE programacion (                      -- programacion.json: una por contenido
  contenido_id  uuid PRIMARY KEY,
  empresa_id    uuid NOT NULL,
  desde         date, hasta date,
  dias          smallint[] NOT NULL DEFAULT '{}',-- 0=lunes ... 6=domingo, como hoy
  hora_inicio   time, hora_fin time,
  FOREIGN KEY (contenido_id, empresa_id) REFERENCES contenido(id, empresa_id) ON DELETE CASCADE,
  CHECK ((hora_inicio IS NULL) = (hora_fin IS NULL))
);

CREATE TABLE lista (
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  clave        text NOT NULL,                    -- 'principal', 'navidad' (lid actual)
  nombre       text NOT NULL,
  creada_en    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (sucursal_id, clave),
  UNIQUE (id, sucursal_id),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id)
);

CREATE TABLE lista_elemento (
  lista_id      uuid NOT NULL,
  contenido_id  uuid NOT NULL,
  sucursal_id   uuid NOT NULL,                   -- redundante a proposito
  empresa_id    uuid NOT NULL,                   -- B3-QA-03: toda tabla de datos lo lleva
  posicion      int  NOT NULL,
  PRIMARY KEY (lista_id, contenido_id),
  UNIQUE (lista_id, posicion) DEFERRABLE INITIALLY DEFERRED,
  -- lista y contenido deben ser de la MISMA sucursal y la MISMA empresa:
  -- lo impone la base por las cuatro llaves
  FOREIGN KEY (lista_id, sucursal_id)     REFERENCES lista(id, sucursal_id)     ON DELETE CASCADE,
  FOREIGN KEY (contenido_id, sucursal_id) REFERENCES contenido(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (lista_id, empresa_id)      REFERENCES lista(id, empresa_id)      ON DELETE CASCADE,
  FOREIGN KEY (contenido_id, empresa_id)  REFERENCES contenido(id, empresa_id)  ON DELETE CASCADE
);

ALTER TABLE sucursal ADD FOREIGN KEY (lista_activa_id, id) REFERENCES lista(id, sucursal_id);
ALTER TABLE pantalla ADD FOREIGN KEY (lista_id, sucursal_id) REFERENCES lista(id, sucursal_id);
ALTER TABLE pantalla ADD FOREIGN KEY (lista_id, empresa_id)  REFERENCES lista(id, empresa_id);
```

Regla general que sale de B3-QA-03 y B3-QA-05: **ninguna tabla de datos se
apoya en una llave foránea para heredar la empresa.** Todas llevan
`empresa_id` propio, amarrado por llave compuesta, y su propia política de
RLS. Las llaves compuestas garantizan que las relaciones no crucen empresas;
la columna y la política garantizan que un `SELECT` directo tampoco.

`ON DELETE CASCADE` en `lista_elemento` reproduce la regla de hoy: borrar un
archivo lo quita de las listas; borrar una lista **no** borra archivos.

### 3.2b Destinos de lista y grupos de pantallas (RF-26) — rev. 8, restricciones ensayadas

Detalle y decisiones en `22-rf26-destinos-de-lista.md`. Lo que entra en el
esquema para no necesitar otra migración cuando B6/B7 lo implementen. La
regla de la rev. 7: **la sucursal viaja en todas las llaves**. `pantalla`,
`lista` y `grupo_pantallas` exponen `UNIQUE (id, sucursal_id)`, y las tablas
de relación referencian ese par, de modo que una pantalla de Juriquilla no
puede entrar en un grupo de Plaza ni una lista de Plaza asignarse a un
destino de Juriquilla: el cruce viola la llave foránea, no depende de que la
aplicación lo compruebe.

```sql
-- Requisito previo en las tablas de §3.1/§3.2 (además de UNIQUE (id, empresa_id)):
ALTER TABLE pantalla ADD UNIQUE (id, sucursal_id);
ALTER TABLE lista    ADD UNIQUE (id, sucursal_id);

CREATE TABLE grupo_pantallas (                    -- grupo PERSISTENTE, por sucursal
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  nombre       text NOT NULL,
  UNIQUE (sucursal_id, nombre),
  UNIQUE (id, empresa_id),
  UNIQUE (id, sucursal_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE TABLE grupo_pantalla_miembro (
  grupo_id     uuid NOT NULL,
  pantalla_id  uuid NOT NULL,
  sucursal_id  uuid NOT NULL,                       -- la de AMBOS: lo garantizan las dos FK compuestas
  empresa_id   uuid NOT NULL,
  PRIMARY KEY (grupo_id, pantalla_id),
  FOREIGN KEY (grupo_id,    sucursal_id) REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla(id, sucursal_id)        ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
-- Asignacion de una lista a un destino. Un destino es UNA pantalla o UN grupo,
-- y lista y destino son de la MISMA sucursal.
CREATE TABLE lista_destino (
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  lista_id     uuid NOT NULL,
  pantalla_id  uuid,                                -- exactamente uno de los dos
  grupo_id     uuid,
  prioridad    int  NOT NULL DEFAULT 0,             -- desempate explicito entre grupos
  asignado_por uuid, asignado_en timestamptz NOT NULL DEFAULT now(),
  CHECK ((pantalla_id IS NULL) <> (grupo_id IS NULL)),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (lista_id,    sucursal_id) REFERENCES lista(id, sucursal_id)           ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla(id, sucursal_id)        ON DELETE CASCADE,
  FOREIGN KEY (grupo_id,    sucursal_id) REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
CREATE UNIQUE INDEX un_destino_por_pantalla ON lista_destino (pantalla_id) WHERE pantalla_id IS NOT NULL;
CREATE UNIQUE INDEX una_lista_por_grupo     ON lista_destino (grupo_id)    WHERE grupo_id IS NOT NULL;

-- Historial de versiones, POR EMPRESA (informe 25, problema 2). Append-only: cada +1
-- inserta una fila; nunca se borra ni se reescribe mientras exista la lista.
ALTER TABLE lista ADD COLUMN version int NOT NULL DEFAULT 1;      -- +1 en cada cambio de elementos/orden
CREATE TABLE lista_version (
  lista_id   uuid NOT NULL,
  version    int  NOT NULL,
  empresa_id uuid NOT NULL,
  creada_en  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (lista_id, version),
  UNIQUE (lista_id, version, empresa_id),
  FOREIGN KEY (lista_id, empresa_id) REFERENCES lista(id, empresa_id) ON DELETE CASCADE
);
-- ENTREGA (informe 25, problema 1). Lo que se confirma no es un contenido sino una
-- entrega: cada vez que el servidor sirve (lista, version) a una pantalla inserta una
-- fila con numero consecutivo POR PANTALLA. La respuesta lleva el numero; la TV lo
-- devuelve en el latido (recibida) y en la confirmacion (reproduciendo). Dos listas
-- con "version 1" y dos asignaciones sucesivas de la misma lista son entregas distintas.
CREATE TABLE pantalla_entrega (
  pantalla_id uuid   NOT NULL,
  seq         bigint NOT NULL,                                     -- 1, 2, 3… por pantalla
  empresa_id  uuid   NOT NULL,
  lista_id    uuid   NOT NULL,
  version     int    NOT NULL,
  enviada_en  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (pantalla_id, seq),
  FOREIGN KEY (pantalla_id, empresa_id)       REFERENCES pantalla(id, empresa_id)                     ON DELETE CASCADE,
  FOREIGN KEY (lista_id, version, empresa_id) REFERENCES lista_version(lista_id, version, empresa_id) ON DELETE CASCADE
);
ALTER TABLE pantalla
  ADD COLUMN entrega_ultima bigint NOT NULL DEFAULT 0,   -- contador por pantalla: nunca se reinicia ni reutiliza (rev. 9)
  ADD COLUMN entrega_env  bigint,   -- ultima entrega servida
  ADD COLUMN entrega_rec  bigint,   -- ultima que la TV declaro aplicada en su latido (B5b)
  ADD COLUMN entrega_conf bigint,   -- ultima que la TV confirmo reproduciendo (propuesta 7)
  -- SET NULL POR COLUMNA (PostgreSQL 15+): al borrar la entrega se anula el puntero, no el id (rev. 9)
  ADD FOREIGN KEY (id, entrega_env)  REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL (entrega_env),
  ADD FOREIGN KEY (id, entrega_rec)  REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL (entrega_rec),
  ADD FOREIGN KEY (id, entrega_conf) REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL (entrega_conf);
```

SQL del servidor, ensayado tal cual (rev. 9). Servir una lista es **una
transacción de cuatro sentencias**; el `FOR UPDATE` inicial serializa las
peticiones de una misma TV y la lectura de la entrega vigente va en una
sentencia aparte (con un `JOIN` en la misma sentencia del `FOR UPDATE`, la
segunda petición despierta con la fila releída pero la instantánea vieja del
`JOIN`, no ve la entrega recién confirmada y crea otra: lo detectó el arnés):

```sql
BEGIN;
-- 1. bloquear la pantalla (serializa a la misma TV) y leer el contador y la entrega vigente
SELECT entrega_ultima, entrega_env FROM pantalla WHERE id = :p FOR UPDATE;
-- 2. si entrega_env no es NULL: ¿la vigente ya es (lista, version)? entonces devolver entrega_env y COMMIT
SELECT lista_id, version FROM pantalla_entrega WHERE pantalla_id = :p AND seq = :entrega_env;
-- 3. si cambio algo: siguiente numero, nueva entrega, apuntar
UPDATE pantalla SET entrega_ultima = entrega_ultima + 1 WHERE id = :p RETURNING entrega_ultima;   -- :seq
INSERT INTO pantalla_entrega (pantalla_id, seq, empresa_id, lista_id, version) VALUES (:p, :seq, :empresa, :lista, :version);
UPDATE pantalla SET entrega_env = :seq WHERE id = :p;
COMMIT;
-- Confirmar (y declarar en el latido) es monotono: atrasada, duplicada o desordenada = 0 filas;
-- una entrega que la pantalla nunca recibio, o que se borro con su lista, viola la FK:
-- "entrega desconocida", el servidor la ignora y la TV recibe una nueva en su proxima consulta.
UPDATE pantalla SET entrega_conf = :seq
 WHERE id = :p AND (entrega_conf IS NULL OR entrega_conf < :seq);
-- "Al dia"
SELECT entrega_conf IS NOT NULL AND entrega_conf = entrega_env FROM pantalla WHERE id = :p;
```

Consecuencias que el ensayo comprueba (`test_ensayo_destinos.py`, 16): con el
DDL de la rev. 6 los tres cruces de sucursal entraban; con el de la rev. 7 y
posteriores los tres fallan con violación de llave foránea y las relaciones
correctas entran. **Mover una pantalla de sucursal no limpia nada en cascada**
(precisión del informe 25): el `UPDATE` de `sucursal_id` es rechazado mientras
queden miembros o destinos de la sucursal vieja; "mover" es una transacción
del servidor que borra miembros y destinos y luego mueve, y el panel lo avisa
en el cuadro de "Mover a…". Con el esquema de la rev. 7, L1 → L2 → L1 daba
"al día" con una confirmación de la primera asignación, y una pantalla de la
empresa A podía confirmar una lista de la empresa B; con el de la rev. 8 la
entrega 3 no se da por confirmada con la 1, la confirmación atrasada devuelve
0 filas, la entrega inexistente falla, cada pantalla numera por su cuenta, y
la versión o la entrega con empresa cruzada fallan por FK sea cual sea el
`empresa_id` que escriba la aplicación. El historial y las entregas llevan
RLS **en el DDL del ensayo** (política estándar por empresa, `GRANT SELECT,
INSERT` a `lumin_app`: append-only) y se ejercen con el rol real: sin
contexto, empresa equivocada, consulta directa al historial, confirmación
cruzada y el positivo del historial antiguo legítimo. Con el SQL de la rev.
8, dos peticiones simultáneas de la misma TV chocaban por clave duplicada,
cada consulta sin cambios creaba otra entrega y borrar una lista referenciada
fallaba; con la rev. 9 se serializan (1 y 2; con la misma lista 1 y 1), cinco
consultas sin cambios devuelven la misma entrega, y borrar la lista anula
solo los punteros, conserva el contador y no reutiliza números. Se ensaya
con `pantalla_e`/`lista_e` mínimas porque el esquema completo de §3 no existe
todavía.

Resolución de la lista efectiva de una pantalla, **determinista y en este
orden**: (1) asignación directa a la pantalla (`un_destino_por_pantalla`
impide dos); (2) si no hay, la asignación de grupo con **mayor `prioridad`**
entre los grupos a los que pertenece, a igual prioridad la **más
reciente** (`asignado_en`) y, si aun así empatan, la de menor `grupo_id`
(orden total `prioridad DESC, asignado_en DESC, grupo_id ASC`; el empate de
prioridad se muestra como conflicto en el panel); (3) si no hay, la lista
programada vigente (B7);
(4) la lista al aire de la sucursal. Todas las tablas nuevas llevan
`empresa_id` con la política estándar de §3.5 (contrato; el aislamiento por
sucursal lo dan las llaves de arriba, la política RLS sigue siendo por
empresa). El resto —qué se confirma al reemplazar, qué pasa al borrar un
grupo, qué significa cada estado de entrega— está en el documento 22.

### 3.3 Operación

```sql
CREATE TABLE ajustes_sucursal (                  -- ajustes.json
  sucursal_id      uuid PRIMARY KEY,
  empresa_id       uuid NOT NULL,
  mensaje          text NOT NULL DEFAULT '',
  cintillo_animado boolean NOT NULL DEFAULT true,
  velocidad        int NOT NULL DEFAULT 130,
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);

CREATE TABLE comando_pantalla (                  -- comandos.json: el ULTIMO comando
  pantalla_id  uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  n            int  NOT NULL,                    -- contador monotono que dedupe la TV
  accion       text NOT NULL,
  url          text NOT NULL DEFAULT '',
  tipo         text NOT NULL DEFAULT '',
  duracion     int  NOT NULL DEFAULT 10,
  emitido_en   timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (pantalla_id, empresa_id) REFERENCES pantalla(id, empresa_id) ON DELETE CASCADE
);

CREATE TABLE turno_vigente (                     -- turnos.json: el ULTIMO turno
  sucursal_id  uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  n            int  NOT NULL,
  numero       text NOT NULL, estacion text NOT NULL DEFAULT '',
  espera       text NOT NULL DEFAULT '',
  duracion     int  NOT NULL DEFAULT 60,
  proximos     jsonb NOT NULL DEFAULT '[]',
  ts           bigint NOT NULL,                  -- epoch, lo que hoy lee la TV
  clave_evento text,                             -- reservado para B5 (QA-G02)
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX turno_clave_evento ON turno_vigente (empresa_id, clave_evento)
  WHERE clave_evento IS NOT NULL;

CREATE TABLE descarga_diaria (                   -- contadores.json, con su nombre real
  sucursal_id    uuid NOT NULL,
  empresa_id     uuid NOT NULL,
  nombre_archivo text NOT NULL,                  -- no FK: hay conteos de archivos ya borrados
  fecha          date NOT NULL,
  veces          int  NOT NULL DEFAULT 0,
  PRIMARY KEY (sucursal_id, nombre_archivo, fecha),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
```

Se llama `descarga_diaria` y no "reproducciones" porque eso es lo que cuenta.
Las reproducciones confirmadas llegan con los eventos del reproductor (B5/B8) a
una tabla `evento_pantalla` que B3 **no** crea todavía.

### 3.4 Identidad

```sql
CREATE TABLE usuario (
  id              uuid PRIMARY KEY,
  nombre_usuario  text NOT NULL UNIQUE,          -- 'admin', 'pos-plaza': lo que teclean hoy
  correo          text UNIQUE,                   -- NULL hasta B4
  correo_verificado_en timestamptz,
  contrasena_hash text NOT NULL,
  contrasena_sal  text,                          -- solo mientras algoritmo = 'sha256-sal'
  algoritmo       text NOT NULL DEFAULT 'sha256-sal'
                  CHECK (algoritmo IN ('sha256-sal','argon2id')),
  activo          boolean NOT NULL DEFAULT true,
  creado_en       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE membresia (
  id          uuid PRIMARY KEY,
  empresa_id  uuid NOT NULL REFERENCES empresa(id),
  usuario_id  uuid NOT NULL REFERENCES usuario(id),
  rol         text NOT NULL CHECK (rol IN ('admin_empresa','operador')),
  UNIQUE (empresa_id, usuario_id),
  UNIQUE (id, empresa_id)
);

CREATE TABLE membresia_sucursal (                -- concesion EXPLICITA; vacio = nada
  membresia_id uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  empresa_id   uuid NOT NULL,
  PRIMARY KEY (membresia_id, sucursal_id),
  FOREIGN KEY (membresia_id, empresa_id) REFERENCES membresia(id, empresa_id) ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id,  empresa_id) REFERENCES sucursal(id, empresa_id)  ON DELETE CASCADE
);

CREATE TABLE sesion (
  token_hash   text PRIMARY KEY,                 -- sha256 del valor de la cookie
  usuario_id   uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  empresa_id   uuid REFERENCES empresa(id),      -- NULL en sesiones migradas; B4 lo exige
  expira_en    timestamptz NOT NULL,
  revocada_en  timestamptz,
  creada_en    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE auditoria (
  id           uuid PRIMARY KEY,
  ocurrido_en  timestamptz NOT NULL DEFAULT now(),
  empresa_id   uuid,
  usuario_id   uuid,
  accion       text NOT NULL,
  objeto_tipo  text, objeto_id text,
  datos        jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE migracion_json (                    -- bitacora de la migracion
  id          serial PRIMARY KEY,
  ejecutada_en timestamptz NOT NULL DEFAULT now(),
  archivo     text NOT NULL, registros int NOT NULL,
  advertencias jsonb NOT NULL DEFAULT '[]'
);
```

**Contraseñas:** las actuales son `sha256(sal + contraseña)`. Se migran **tal
cual**, con `algoritmo = 'sha256-sal'`, para que nadie tenga que cambiar de
contraseña el día del corte. B4 recifra a Argon2id en el siguiente inicio de
sesión exitoso. Sin esto, la migración bloquearía la operación.

### 3.5 Row Level Security: contrato completo

**Roles (revisión 3).** Tres, con propósito único cada uno. Ninguno es
`SUPERUSER` ni tiene `BYPASSRLS`; `lumin_app` y `lumin_espejo` son `NOINHERIT`
y no son miembros de nadie (`SET ROLE` falla, ensayado).

| Rol | Propietario de las tablas | RLS | Para qué | Desde dónde |
|---|---|---|---|---|
| `lumin_migracion` | **Sí** | `ENABLE`, **no `FORCE`**: como propietario queda **exento** | Alembic, `migrar_json`, `verificar_espejo`, `pg_dump`/`pg_restore` | Solo consola del VPS |
| `lumin_app` | No | Se le aplica siempre; sin política, cero filas | Las rutas HTTP | El servidor, pool principal |
| `lumin_espejo` | No | Se le aplica siempre; sus políticas son `USING (true)` **solo de lectura** | El hilo espejo (§7.4) y `exportar_json.py` | El servidor, **una** conexión aparte |

**Por qué `ENABLE` y no `FORCE`.** Codex tenía razón: `FORCE` somete también al
propietario, y como no habría política para él, migración, verificación y
respaldo verían **cero filas** (ensayado: `test_por_que_no_force_rls`). La
protección que buscaba `FORCE` ("si `lumin_app` llegara a ser propietario") se
obtiene de otra forma: el guardián de catálogo (`guardian_de_catalogo`, con la
lista de tablas tomada del catálogo) exige que **toda** tabla del esquema tenga
como propietario a `lumin_migracion`, RLS activa y una política para cada
`GRANT` a `lumin_app`, y que ningún rol tenga atributos peligrosos. Tiene dos
casos negativos que lo hacen fallar (una tabla creada por `lumin_app` con RLS y
política propias; una tabla sin RLS con `GRANT`): rev. 4, B3-R3-04.

**Matriz rol / tabla / operación / política.** Un `GRANT` y una política son
controles distintos: los dos deben permitir la operación. La última columna
dice, tabla por tabla, si la fila está en `servidor/ensayos_b3/ddl_minimo.sql`
**y se ejecuta** en los 39 ensayos, o si es **contrato** para la
implementación (mismo patrón, todavía sin ejecutar). El guardián de catálogo
(`guardian_de_catalogo`) correrá contra el esquema completo cuando exista y
hará fallar la suite ante cualquier tabla sin política, sin RLS o con otro
propietario.

| Tabla | `lumin_app` GRANT | `lumin_app` política | `lumin_espejo` | `lumin_migracion` | Ensayado / Contrato |
|---|---|---|---|---|---|
| `sucursal`, `trabajo` | `SELECT, INSERT, UPDATE, DELETE` (`trabajo`: sin `DELETE`) | `FOR ALL USING (empresa_id = gc('empresa_id')) WITH CHECK (igual)` | `SELECT`, `USING (true)` | todo, exento | **Ensayado** |
| `pantalla`, `contenido`, `programacion`, `lista`, `lista_elemento`, `ajustes_sucursal`, `comando_pantalla`, `turno_vigente`, `descarga_diaria` | `SELECT, INSERT, UPDATE, DELETE` | mismo patrón que `sucursal` | `SELECT`, `USING (true)` | todo | Contrato (mismo patrón) |
| `pantalla`, además | — | `FOR SELECT/UPDATE USING (id_dispositivo = gc('id_dispositivo'))` para el latido sin sesión | ídem | ídem | Contrato |
| `empresa` | `SELECT` | `USING (id = gc('empresa_id') OR heredada OR id IN (SELECT empresa_id FROM membresia WHERE usuario_id = gc('usuario_id')))` — la rama `heredada` (rev. 4) es la que permite arrancar sin contexto: latido de la TV, rutas 6.x y sesiones migradas | `SELECT`, `USING (true)` | todo | **Ensayado** |
| `membresia` | `SELECT` (escritura en B4) | `USING (empresa_id = gc('empresa_id') OR usuario_id = gc('usuario_id'))` — la segunda rama permite comprobar la propia membresía antes de asignar la empresa | `SELECT`, `USING (true)` | todo | **Ensayado** |
| `membresia_sucursal` | `SELECT` | mismo patrón que `membresia` (vía `membresia_id`) | `SELECT`, `USING (true)` | todo | Contrato |
| `usuario` | `SELECT` (`UPDATE` de `contrasena_*` en B4) | `USING (id = gc('usuario_id') OR (gc('fase') = 'login' AND nombre_usuario = gc('nombre_usuario')))` | `SELECT`, `USING (true)` | todo | **Ensayado** |
| `sesion` | `SELECT, INSERT, UPDATE` | `USING (token_hash = gc('token_hash') OR usuario_id = gc('usuario_id'))` **y** `WITH CHECK (token_hash = gc('token_hash') OR usuario_id = gc('usuario_id'))` — la rama del token en `WITH CHECK` es la que permite el logout (hallazgo del ensayo) | `SELECT`, `USING (true)` | todo | **Ensayado** |
| `auditoria` | **solo `INSERT`** | `FOR INSERT WITH CHECK (empresa_id IS NULL OR empresa_id = gc('empresa_id'))` — `NULL` para los eventos sin empresa (login fallido) | `SELECT`, `USING (true)` | todo | **Ensayado** |
| `espejo_marca` | **solo `INSERT`** | `FOR INSERT WITH CHECK (true)` — la marca no lleva datos | `SELECT` `USING (true)` y `UPDATE (procesada_en)` `USING (true) WITH CHECK (true)` | todo | **Ensayado** |
| `espejo_estado` | ninguno | ninguna | `SELECT, UPDATE`, `FOR ALL USING (true) WITH CHECK (true)` | todo | **Ensayado** |
| `migracion_json` | ninguno | ninguna | `SELECT` | todo | Contrato |
| `grupo_pantallas`, `grupo_pantalla_miembro`, `lista_destino`, `lista_version`, `pantalla_entrega` (§3.2b) | `SELECT, INSERT, UPDATE, DELETE` (`lista_version` y `pantalla_entrega`: solo `SELECT, INSERT`) | mismo patrón que `sucursal` (todas llevan `empresa_id`) | `SELECT`, `USING (true)` | todo | Grupos y destinos: política contrato, restricciones de sucursal **ensayadas**. `lista_version` y `pantalla_entrega`: **política y restricciones ensayadas** con `lumin_app` (`test_ensayo_destinos.py`); las FK compuestas dan la empresa aunque RLS no intervenga en su comprobación (informe 25) |
| Roles y cluster | `lumin_migracion` es miembro de `pg_signal_backend` y `pg_read_all_stats` (drenaje de §7.3); nadie tiene `SUPERUSER`, `BYPASSRLS` ni `CREATEROLE` | | | | **Ensayado** |

Notas ensayadas: las columnas `GENERATED … AS IDENTITY` de `auditoria` y
`espejo_marca` **no** exigen `USAGE` sobre su secuencia para insertar como
`lumin_app` (PostgreSQL 16.13); si una versión lo exigiera, el DDL añade el
`GRANT USAGE` y el ensayo lo detecta. `pg_dump -Fc` como `lumin_migracion` y
`pg_restore` en una base nueva conservan filas de todas las empresas **y** las
políticas (`pg_policies` viaja con el volcado).

**Arranque de la autenticación con una sesión migrada (`empresa_id NULL`),
orden corregido en la rev. 4 (B3-R3-01).** Dentro de la transacción de la
petición, y sin filtrar nunca `membresia` por una empresa que aún no está en
el contexto:

1. `SET LOCAL lumin.token_hash`.
2. `SELECT usuario_id, empresa_id FROM sesion WHERE revocada_en IS NULL AND
   expira_en > now()` — la política deja pasar solo esa fila; cero filas → 401.
3. `SET LOCAL lumin.usuario_id`.
4. Si `empresa_id` es `NULL` (todas las migradas): `SELECT id FROM empresa
   WHERE heredada` — visible **sin** contexto por la rama `heredada` de la
   política; es la misma consulta con la que las rutas 6.x (latido, `/videos/`)
   construyen su `Contexto` sin usuario. Después `SELECT 1 FROM membresia
   WHERE usuario_id = $usuario AND empresa_id = $heredada` **con los dos como
   parámetros**, permitido por la rama `usuario_id = gc('usuario_id')`; cero
   filas → 401 y auditoría.
5. `SET LOCAL lumin.empresa_id`.

Desde B4, `sesion.empresa_id` es obligatoria y el paso 4 desaparece; una
sesión con empresa (creada por 6.11) no consulta la heredada. Ensayado en
`resolver_sesion_migrada` (`test_ensayo_rls.py`): membresía válida → resuelve
la heredada y ve sus datos; sin membresía → 401 y el contexto queda vacío;
membresía solo en otra empresa → 401; revocada o vencida → 401; con empresa
propia → no toca la heredada. El login por contraseña se ensaya en
`test_app_sesiones_y_login`: con `fase = 'login'` el nombre resuelve **una**
fila; sin la fase, el mismo nombre resuelve **cero**.

**Contexto por transacción.** El servidor abre cada transacción con
`SET LOCAL` (alcance de transacción: se limpia solo al confirmar o abortar, no
sobrevive a la reutilización de la conexión):

```sql
SET LOCAL lumin.empresa_id     = '<uuid>';   -- vacío si aún no se conoce
SET LOCAL lumin.usuario_id     = '<uuid>';   -- vacío para la TV
SET LOCAL lumin.token_hash     = '<sha256>'; -- solo durante la resolución de sesión
SET LOCAL lumin.id_dispositivo = '<id>';     -- solo para la TV
```

**Función de contexto.** `lumin.gc(nombre)` devuelve el GUC o `NULL` si no
está puesto (`nullif(current_setting('lumin.'||nombre, true), '')`), para que
la comparación con `NULL` sea falsa y la ausencia de contexto devuelva cero
filas. Ensayado: misma conexión, transacción como `A` → como `B` → sin
contexto: 1 fila, 1 fila distinta, 0 filas.

**Reutilización de conexiones.** Prueba obligatoria: misma conexión,
transacción como `A` → transacción como `B` → transacción sin contexto: la
tercera devuelve cero filas en todas las tablas de datos, y la segunda no ve
nada de `A`. Además, el pool ejecuta `DISCARD ALL` al devolver una conexión.

**Guardián en pruebas, versión corregida.** Buscar el texto `empresa_id` en el
SQL no demuestra nada (`SELECT empresa_id FROM sucursal` lo contiene y no
filtra). Se sustituye por **controles negativos** ejecutados como `lumin_app`,
con SQL crudo, **sin JOIN ni repositorio**: para cada tabla con `empresa_id`,
(1) `SELECT count(*)` sin contexto → 0; (2) con contexto de `A` → solo filas
de `A`; (3) `INSERT` de una fila de `B` con contexto de `A` → rechazado por
`WITH CHECK`; (4) `UPDATE`/`DELETE` de una fila de `B` con contexto de `A` → 0
filas afectadas y la fila intacta. La lista de tablas se toma del catálogo, no
de una constante, para que una tabla nueva sin política haga fallar la prueba.

---

## 4. Mapeo JSON → PostgreSQL

| JSON (6.x) | Tabla | Notas de conversión |
|---|---|---|
| `sucursales.json` `[{clave,nombre}]` | `sucursal` | `orden` = posición en la lista; todas bajo `empresa` 'lumin' |
| `tvs.json` `{id: {indice,sucursal,zona,aprobada,codigo,visto,turnos,lista,pausada,silencio}}` | `pantalla` | `id` → `id_dispositivo`; `indice+1` → `numero`; `indice` → `desfase_rotacion`; `sucursal ''` → `sucursal_id NULL`; `lista` (lid) → `lista_id` buscando en la sucursal; `visto` epoch → `visto_en` |
| `ordenes.json` `{clave: [archivos]}` | `contenido.posicion` | El orden de la biblioteca. Archivos en disco sin entrada → se crean con posición al final (hoy `lista_archivos` hace lo mismo) |
| `listas.json` `{clave: {activa, listas: {lid: {nombre, archivos}}}}` | `lista`, `lista_elemento`, `sucursal.lista_activa_id` | Archivos referenciados que ya no existen en disco → se omiten con advertencia (hoy se filtran al leer) |
| `duraciones.json` | `contenido.duracion_imagen` | Se acota a 3–120 como hoy |
| `girados.json` | `contenido.girado` | |
| `programacion.json` | `programacion` | `dias` [0..6] igual; `hini/hfin` "HH:MM" → `time` |
| `ajustes.json` | `ajustes_sucursal` | Defectos actuales: mensaje '', animado true, 130 |
| `comandos.json` | `comando_pantalla` | Solo el último por pantalla, como hoy |
| `turnos.json` | `turno_vigente` | `ts` se conserva en epoch |
| `contadores.json` | `descarga_diaria` | Se migran los últimos 60 días (lo que hoy conserva) |
| `usuarios.json` `{nombre: {sal,hash,rol,sucursales}}` | `usuario`, `membresia`, `membresia_sucursal` | Ver §6: rol `admin` → `admin_empresa`; `usuario` → `operador` con concesiones **explícitas** |
| `sesiones.json` `{token: {usuario, exp}}` | `sesion` | `token_hash = sha256(token)`; la cookie sigue valiendo. Vencidas no se migran |

Lo que **no** se migra y por qué: sesiones vencidas, contadores de más de 60
días, entradas de `ordenes`/`listas` cuyo archivo ya no está en disco. Todo lo
omitido se lista en el informe de migración y queda en los JSON congelados.

---

## 5. Conservación de identificadores y contratos

| Contrato | Cómo se conserva | Prueba |
|---|---|---|
| `GET /playlist.json?id=<GetChannelClientId>` | `pantalla.id_dispositivo` es llave natural. La respuesta se arma con las mismas llaves y el mismo orden (`videos`, `mensaje`, `cintillo`, `velocidad`, `vertical`, `giro`, `comando`, `turno`); `pendiente/codigo` igual | Fixture con JSON reales sintéticos: respuesta **byte a byte** igual antes y después, para pantalla aprobada, pendiente, con turno, con comando y con lista asignada |
| Rotación escalonada | `desfase_rotacion` migra desde `indice`; misma fórmula `desfase % len` | Misma prueba: el primer video coincide |
| `POST/PUT /api/turno` | Mismo cuerpo, mismos límites (numero ≤8, estación ≤20, espera ≤10, duración 5–300, próximos ≤3), `n` sigue incrementando por sucursal | Regresión de `docs/API-turnos.md` |
| `/videos/<clave>/<archivo>`, `/miniaturas/…`, `/rapidos/…` | **Los archivos no se mueven.** `sucursal.clave` y `contenido.nombre_archivo` son los mismos textos de hoy | Ruta a disco idéntica |
| Panel actual | Todos los `/api/*` responden igual: la forma de los JSON de respuesta se conserva aunque por dentro venga de tablas | Suite de contrato del panel sobre las 30 rutas |
| Cookies de sesión | Token en la cookie no cambia; se guarda su hash | Login antes de migrar, petición después: 200 |
| Usuario y contraseña | `nombre_usuario` y hash sha256 se conservan | Login de cada usuario migrado con su contraseña |
| Número visible de pantalla | Se conserva **salvo duplicados** (§9, decisión) | Informe de migración lista cambios |
| Vigilante (Raspberry) | Habla ECP con las TVs, no con el servidor: sin efecto | — |
| App Roku 5.1 y 5.2 | No distinguen JSON de PostgreSQL | Prueba F13 de B1 sobre servidor 6.11 |

---

## 6. Aislamiento entre empresas y permisos por sucursal

### 6.1 `Contexto`: la unidad de autorización

```python
@dataclass(frozen=True)
class Contexto:
    empresa_id: UUID
    usuario_id: UUID | None          # None para la TV y el proceso del sistema
    rol: str                         # 'admin_empresa' | 'operador' | 'pantalla' | 'sistema'
    sucursales: frozenset[UUID]      # alcance EXPLICITO. Vacio = ninguna.
```

Reglas fijas:

- **Toda** función de repositorio recibe `Contexto` y añade
  `WHERE empresa_id = ctx.empresa_id`. No existe función sin contexto.
- La TV obtiene un `Contexto` de rol `pantalla` derivado de su `id_dispositivo`,
  acotado a su empresa y su sucursal. El POS, de su sesión de usuario.
- Un identificador que llega del cliente (sucursal, pantalla, lista, archivo)
  **nunca** decide la empresa: se resuelve dentro del contexto, y si no está,
  es "no encontrado", con el mismo mensaje exista o no en otra empresa.
- Cambiar algo de sucursal exige alcance en **origen y destino** (mecanismo de
  QA-F02, listo en B3; la política se endurece en B4).

### 6.2 Qué cambia y qué no en los permisos actuales

B3 **no cambia el comportamiento efectivo** de ningún usuario actual; lo hace
explícito. Así el corte no bloquea a nadie y B4 endurece con conocimiento:

| Hoy en `usuarios.json` | Efecto hoy | Migración a B3 | B4 |
|---|---|---|---|
| `rol: admin` | Todo | `admin_empresa` de 'lumin' | igual |
| `rol: usuario`, `sucursales: [a, b]` | a y b | `operador` con concesiones a, b | igual |
| `rol: usuario`, `sucursales: []` | **todas** (QA-F01) | `operador` con concesión explícita a **todas las actuales**, marcado en el informe | Adrián decide sucursal por sucursal |
| `rol: usuario`, `sucursales: ['x-inexistente']` | la primera (QA-F01) | `operador` con concesión a la primera, marcado en el informe | ídem |

La "sustitución silenciosa" de una sucursal fuera de alcance por la primera
permitida (`_sucursal_de`) se mantiene en B3 solo para las rutas del panel
viejo y **se registra en auditoría cada vez que ocurre**, para tener la cuenta
real antes de convertirla en 403 en B4.

### 6.3 Las cuatro capas, y cómo se prueba cada una

| Capa | Qué impide | Prueba |
|---|---|---|
| 1. Llaves compuestas | Que una fila apunte a un padre de otra empresa | `INSERT` directo cruzado → `IntegrityError` |
| 2. `Contexto` en repositorios | Que una consulta lea o escriba fuera de la empresa | Suite "dos empresas" (§6.4) |
| 3. Row Level Security | Que un `WHERE` olvidado filtre datos | Consulta cruda sin `SET lumin.empresa_id` → 0 filas; con la empresa equivocada → 0 filas |
| 4. Controles negativos como `lumin_app` | Que una tabla nueva quede sin política o que una política no filtre de verdad | Por cada tabla del catálogo con `empresa_id`: sin contexto → 0; contexto ajeno → 0 y sin mutación; `INSERT` cruzado → rechazado. SQL crudo, sin repositorio (§3.5) |

### 6.4 Suite "dos empresas"

Se crean `A` y `B` con estructuras gemelas: dos sucursales cada una, tres
pantallas, cuatro contenidos, dos listas, un usuario admin y un operador con una
sola sucursal. Luego, **para cada función pública del repositorio** (se
enumeran por reflexión, para que una función nueva no quede sin probar):

1. Con contexto de `A` y los identificadores de `B`: lectura → vacío / no
   encontrado; escritura → rechazada; y **la fila de `B` sigue idéntica**
   (se compara antes y después).
2. Con contexto de `A` y sus propios identificadores: funciona (control
   positivo).
3. Operador de `A` con una sucursal: lo mismo entre sus dos sucursales.

Casos que se añaden a mano porque la reflexión no los cubre:

- `playlist.json` pedida con el `id_dispositivo` de una pantalla de `A`:
  nunca contiene URLs de medios de `B`, ni el turno ni el comando de `B`,
  aunque `A` y `B` tengan sucursales con la **misma `clave`**
  (`plaza-centro` en ambas), que es el caso que más fácil se cuela.
- **Medios:** `GET /videos/<clave>/<archivo>` con una clave que existe en `A`
  y en `B` resuelve **siempre** dentro de la empresa del contexto. En B3 la
  ruta pública sigue sin credencial (QA-G01, B8), así que esta prueba fija el
  comportamiento del *servidor*: la resolución de `sucursal.clave` a
  `sucursal_id` pasa por `empresa_id`. Mientras exista una sola empresa no
  hay ambigüedad; la prueba está para que la segunda no la introduzca.
- **Credenciales de pantalla:** el código de aprobación de una pantalla de
  `B` no aprueba una de `A`; `/api/tv/aprobar` con `id_dispositivo` de `B`
  desde una sesión de `A` es "no encontrado"; una pantalla movida entre
  sucursales nunca puede aterrizar en una sucursal de otra empresa (capa 1 lo
  impide, y se verifica el `IntegrityError`).
- `/api/turno` de un usuario de `A` apuntando a una sucursal de `B` (hoy caería
  en la primera de `A`: en B3 se registra en auditoría, en B4 es 403).
- `lista_elemento` intentando meter un contenido de `B` en una lista de `A`
  (lo detiene la capa 1, y se comprueba).
- Sesión de un usuario que pertenece a `A` **y** a `B`: cada sesión nombra una
  empresa y no alcanza la otra.

---

## 7. Migración

### 7.1 Principios

- **Idempotente:** correrla dos veces deja lo mismo. Cada archivo se marca en
  `migracion_json`.
- **Con informe:** cuántos registros por archivo, qué se omitió y por qué, qué
  permisos se hicieron explícitos, qué números de pantalla cambiaron.
- **Verificable antes de abrir el tráfico:** después de migrar, el propio
  script arma `playlist.json` para cada pantalla desde PostgreSQL y desde los
  JSON, y compara byte a byte. Si una difiere, aborta.
- **Nunca sobre producción sin ensayo previo** sobre copia sintética y sobre
  copia anonimizada.

### 7.2 Ensayos (antes de cualquier fecha)

1. **Sintético:** los JSON de `servidor/tests/` ampliados con los casos raros
   (pantalla pendiente, lista con archivo borrado, usuario con `[]`, sesión
   vencida, números duplicados). Migrar, verificar, exportar de vuelta,
   comparar.
2. **Anonimizado:** una copia de los JSON reales pasada por
   `anonimizar_json.py` (hashes y sales reemplazados, tokens de sesión
   descartados, nombres de usuario mapeados a `u1..uN`). Mide tiempos y
   confirma que la estructura real no trae sorpresas. **Esta copia la genera
   Adrián en el VPS y la revisa antes de compartirla**; no salen datos
   operativos del servidor.
3. **Reversión cronometrada** en ambos: ¿cuánto tarda volver a JSON?

### 7.3 El día del corte (cuando se autorice)

```
T-1 día   pg_dump del esquema vacío; respaldo completo de /opt/lumin-tv (JSON +
          medios) verificado restaurando en limpio.
T-0       Ventana nocturna de ~20 min. Las TVs siguen reproduciendo (tienen
          lista y cache).
  1. LUMIN_SOLO_LECTURA=1 y reiniciar 6.10. Solo lectura de VERDAD, a nivel
     de servidor, no de botones: el latido de /playlist.json responde pero
     NO escribe `visto`; /videos/ sirve pero NO cuenta; /api/login responde
     503 (las sesiones existentes siguen sirviendo para leer); /api/turno
     responde 503 (el POS, por contrato, registra y sigue cobrando);
     /api/subir y todo POST responden 503. Una prueba del arnés lo exige
     para cada ruta de escritura.
  2. Copiar los JSON a json-congelados/AAAA-MM-DD/ (no se borran). Como no
     hay escritores, la copia es consistente.
  3. migrar_json.py --verificar   → informe + comparación de playlist.json
     por pantalla, byte a byte, contra 6.10 en solo lectura.
  4. Arrancar 6.11 con LUMIN_DATOS=postgresql, LUMIN_ESPEJO_JSON=1 y
     LUMIN_ESCRITURAS_SOLO_DESDE=<IP de Adrián>. Es la apertura controlada:
     solo esa IP puede escribir; las TVs y el POS siguen en solo lectura.
     La IP que se compara es la del CLIENTE tal como la ve el servidor:
     si hay proxy delante, la de X-Forwarded-For SOLO si el proxy es el
     nuestro (lista fija), nunca la cabecera a ciegas. Como el POS y las TVs
     de una sucursal pueden salir por la misma IP pública que el operador,
     la ventana de humo se hace desde una red distinta a la de cualquier
     sucursal (datos móviles o el propio VPS), y se anota cuál.
  5. Humo, desde esa IP y contra el servidor real: playlist de 3 pantallas,
     un turno de prueba con numero 'QA-CORT' (7 caracteres: respeta el límite de 8 del contrato del POS; se retira al terminar),
     login con un usuario existente, subir y borrar una imagen 'humo.jpg'.
     Cada paso confirma que el espejo quedó al día (§7.4). Lo creado en el
     humo se elimina y queda anotado en el informe.
  6. Quitar LUMIN_ESCRITURAS_SOLO_DESDE. Operación normal.
T+7 días  Si todo bien y el espejo lleva 7 días sincronizado: LUMIN_ESPEJO_JSON=0.
T+30 días Se archivan los JSON congelados (no se borran).
```

Si algo falla en los pasos 3–5, la reversión es inmediata **pero pasa por el
mismo guardián** que cualquier otra (rev. 4, B3-R3-02): `revertir.py` pone solo
lectura y **drena** `lumin_app` con el contrato de la rev. 7 (B3-R4-01, tres
vueltas). Todo el drenaje está acotado a **esta base**: cada consulta a
`pg_stat_activity` filtra `usename = 'lumin_app' AND datname = '<base>'`
(informe 24, problema 1), que es exactamente el alcance del `REVOKE CONNECT
ON DATABASE`; sesiones del mismo rol en otras bases de la instancia no se
terminan ni se cuentan.

1. **Entrada cerrada:** `REVOKE CONNECT ON DATABASE lumin FROM lumin_app`. La
   base no concede `CONNECT` a `PUBLIC`, solo a los tres roles, así que el
   `REVOKE` es efectivo. Ninguna conexión nueva de la aplicación a esta base.
2. **Gracia:** hasta 30 s para que las transacciones en vuelo (`active`,
   `idle in transaction`, `backend_xid` no nulo) terminen por sí solas. Es
   cortesía con lo que estaba a medias; **no es la barrera**.
3. **Barrera:** `pg_terminate_backend` a **todas** las sesiones de `lumin_app`
   **en esta base**, incluidas las `idle`. Una conexión de pool ya abierta no
   necesita `CONNECT` para iniciar una transacción nueva (Codex lo reprodujo
   sobre la rev. 5); por eso no basta con matar las que tienen transacción.
   Una sesión terminada hace rollback, nunca commit. `lumin_migracion` es
   miembro de `pg_signal_backend` y `pg_read_all_stats` para poder hacerlo;
   espejo, migración y otras bases no se tocan.
4. **Verificación:** cero sesiones de `lumin_app` en `pg_stat_activity` **para
   esta base**. Con la entrada cerrada, cero ahora es cero hasta que se reabra:
   ningún hilo HTTP, trabajador ni conexión de pool puede empezar SQL después.
   Si queda alguna, `DrenajeIncompleto` y la reversión se **bloquea**, también
   la de emergencia.

Del lado del servidor 6.11 esto se ve como errores de conexión en las
peticiones que estaban en curso, que responden 503; el modo solo lectura HTTP
(paso 1 del corte) reduce cuántas hay, pero la garantía la da la base, no el
servidor. Solo después de la barrera `revertir.py` espera a que el espejo deje
cero marcas pendientes, verifica §7.4-8 y regenera `sesiones.json` con el
estado final (§7.6); entonces arranca 6.10. La entrada se reabre con `GRANT
CONNECT` solo al abortar la reversión y volver a 6.11.

### 7.4 Escrituras posteriores al cambio: el espejo derivado

Codex tenía razón: "escribir en PostgreSQL y luego en el JSON" son dos
operaciones sin atomicidad entre ellas. La revisión cambia el mecanismo.

**Fuente de verdad: PostgreSQL, siempre.** Los JSON no se escriben desde las
rutas; se **regeneran** desde la base.

**Los 13 documentos del espejo, enumerados** (los mismos 13 archivos que lee
6.10): `sucursales.json`, `ordenes.json`, `listas.json`, `ajustes.json`,
`duraciones.json`, `tvs.json`, `comandos.json`, `girados.json`, `turnos.json`,
`programacion.json`, `contadores.json`, `usuarios.json` y `sesiones.json`.
Los doce primeros se regeneran desde PostgreSQL; `sesiones.json` se regenera
con la regla de §7.6 (copia congelada ∩ vigentes). `verificar_espejo.py`
compara los doce con la equivalencia semántica de §11 y el decimotercero con
esa regla.

**Protocolo (revisión 3; B3-R2-01).**

1. Cada transacción que modifica datos inserta, **en la misma transacción**,
   una fila en `espejo_marca (id identity, creada_en, procesada_en NULL)`. Si
   la transacción aborta, la fila nunca es visible. Si confirma, la marca y
   los datos que anuncia se vuelven visibles **juntos**.
2. Un **único hilo espejo**, con el rol `lumin_espejo`, hace como mucho cada
   2 s **una transacción `REPEATABLE READ READ ONLY`** (una sola instantánea)
   en la que lee (a) el conjunto `P` de marcas **pendientes que ve**
   (`procesada_en IS NULL`) y (b) los doce documentos completos. Como una
   marca solo es visible si su transacción confirmó, y la instantánea es una,
   los documentos leídos contienen exactamente lo que anuncian las marcas de
   `P`, ni más ni menos. **No se usa `max(id)` para nada.** Si `P` está vacío,
   no hay trabajo (salvo en el arranque, ver 6).
3. Escribe los 13 archivos con el `escribir_json` atómico de siempre
   (temporal + `os.replace`, cada archivo entero o nada).
4. **Solo después** de escribir, en una transacción corta: `UPDATE
   espejo_marca SET procesada_en = now() WHERE id = ANY(P)` y `UPDATE
   espejo_estado SET generacion = generacion + 1, exportada_en = now(),
   marcas_cubiertas = P`. Luego escribe `json-espejo.estado` con la
   generación.
5. **Transacción tardía (el contraejemplo de Codex):** A reserva la marca 1 y
   sigue abierta; B reserva la 2 y confirma; el espejo ve `P = {2}`, exporta
   lo de B y marca solo la 2; A confirma: ahora la marca 1 es visible y sigue
   pendiente; el siguiente ciclo ve `P = {1}`, exporta (con A y B) y la
   marca. Converge sin ninguna escritura nueva. Ensayado con dos conexiones
   reales y ese orden exacto; el protocolo de la revisión 2 falla en el mismo
   ensayo (`test_protocolo_viejo_pierde_la_transaccion_tardia`).
6. **Arranque:** el primer ciclo tras arrancar el servicio exporta **siempre**,
   haya o no pendientes. Cubre cualquier caída entre los pasos 3 y 4 y el
   fallo al escribir `json-espejo.estado`.
7. **Idempotencia por construcción:** el espejo no reproduce operaciones;
   reconstruye el estado completo. Repetir un ciclo es inocuo.
8. **Sincronizado** significa exactamente: (i) no hay marcas pendientes
   visibles, (ii) la comparación semántica (§11) entre la exportación en
   memoria y los archivos no encuentra diferencias, y (iii)
   `json-espejo.estado.generacion = espejo_estado.generacion`.
   `verificar_espejo.py` imprime las tres. Una transacción **abierta** con
   marca reservada no cuenta como pendiente (no es visible): lo confirmado
   sí está sincronizado, y en cuanto confirme aparecerá como pendiente.
9. **La reversión se bloquea si no está sincronizado.** `revertir.py` pone
   solo lectura (que además impide nuevas marcas), espera hasta 30 s a que el
   hilo espejo deje `P` vacío, verifica (punto 8) y solo entonces autoriza
   arrancar 6.10. Si no lo logra (PostgreSQL caído), **no revierte**: informa
   qué falta y espera decisión humana.
10. **PostgreSQL inaccesible:** las rutas de escritura responden 503 y las de
    lectura fallan con 503; **no se escribe en ningún lado**, así que no hay
    divergencia posible. Las TVs siguen con su lista y su cache (B1).
11. **Limpieza:** las marcas procesadas se borran a los 7 días (tarea nocturna
    como `lumin_migracion`); la tabla nunca crece sin límite.

**Casos ensayados antes del corte, cada uno con su prueba automatizada:**

| Caída | Qué queda | Cómo se recupera | Ensayo |
|---|---|---|---|
| Antes del `COMMIT` | Nada en PostgreSQL, ninguna marca visible | Nada que recuperar | `test_marca_de_transaccion_abortada_no_queda_pendiente` |
| Después del `COMMIT`, antes de que el espejo corra | Marca pendiente, JSON viejo | El siguiente ciclo la ve y regenera | `test_protocolo_nuevo_converge_con_el_mismo_orden` |
| Transacción confirmada **después** de un ciclo que ya procesó una marca mayor | Marca menor pendiente y visible | El siguiente ciclo la procesa; no depende de `max(id)` | ídem (contraejemplo de Codex) |
| A mitad de la escritura de los 13 archivos | Algunos archivos nuevos, otros viejos; marcas sin procesar | Siguiente ciclo regenera los 13 | `test_caida_a_mitad_de_los_archivos` |
| Tras escribir los 13 y antes de marcar | Archivos al día, marcas pendientes | Siguiente ciclo rehace y marca (idempotente) | `test_caida_tras_escribir_y_antes_de_marcar` |
| Base marcada y `json-espejo.estado` sin escribir | Generación en disco atrasada | `sincronizado` = no (reversión bloqueada); al reiniciar, el arranque exporta y coincide | `test_fallo_al_persistir_el_marcador_en_disco` |
| Disco lleno al escribir un JSON | `os.replace` no ocurre; archivo viejo intacto; marcas pendientes | Bitácora; el espejo reintenta; reversión bloqueada hasta resolver | (prueba de la implementación) |
| Kill −9 del servidor en cualquier punto | Lo de arriba, combinado | Arranque: exporta siempre una vez | regla 6 |

**Después de apagar el espejo (día 7+).** `exportar_json.py` es el mismo
exportador del hilo espejo, ejecutado a mano en solo lectura. Misma
verificación, misma regla de bloqueo.

**Lo que ninguna marcha atrás cubre, declarado:** columnas que no existen en
el formato 6.x (`tamano_bytes`, `clave_evento`, `ruta_almacen`, y lo que
añada B4); las sesiones creadas después del corte (§7.6); y la diferencia
`numero`/`desfase_rotacion` (§11). Nada más.

### 7.6 Contraseñas y sesiones: compatibilidad y revocación (punto 4 de Codex)

| Qué | Decisión en B3 | Por qué |
|---|---|---|
| Contraseñas `sha256(sal+pwd)` | Se migran tal cual con `algoritmo='sha256-sal'`. **Nadie cambia de contraseña el día del corte** | Bloquear a las recepcionistas la noche del corte es el peor resultado posible |
| Recifrado | B4: en el siguiente login correcto se verifica con sha256, se recifra con Argon2id y se cambia `algoritmo`. Se registra en auditoría | La transición dura lo que tarde cada persona en volver a entrar |
| Contraseña fija del código (QA-F03) | **Sigue existiendo en B3** para el bootstrap del `admin`. Se declara. B4 la elimina y obliga a rotar la del `admin` | B3 no toca autenticación por alcance |
| Sesiones vigentes en el corte | Se migran (`token_hash = sha256(token)`, misma `exp`, `empresa_id NULL`); **no se revocan**. La cookie de cada quien sigue sirviendo | Cero fricción el día del corte |
| Sesiones vencidas | No se migran | Basura |
| **`sesiones.json` durante B3 y al revertir** (B3-QA-02, corregido por **B3-R2-02**) | El espejo **regenera** `sesiones.json` en cada ciclo como **copia congelada ∩ vigentes en PostgreSQL**: de la copia del corte (`json-congelados/…/sesiones.json`, que sí tiene los tokens en claro, como hoy) conserva solo los tokens cuyo `sha256` sigue en `sesion` con `revocada_en IS NULL`, `expira_en > now()` y usuario activo; `exp` = el menor de los dos. Un logout o una baja de usuario durante B3 desaparece del archivo en el siguiente ciclo del espejo (normalmente segundos; **la reversión no confía en esa frescura**: vuelve a calcular la intersección con el estado final, §7.3). Las sesiones creadas **después** del corte existen solo como hash y **no** se vuelcan: al revertir quedan cerradas y esas personas entran una vez. Cuando la última sesión anterior al corte vence, el archivo regenerado queda vacío y la copia congelada deja de tener valor. **Contrato:** revertir conserva revocaciones, vencimientos y bajas; conserva las sesiones anteriores al corte **solo** si siguen vigentes; cierra las posteriores | Ensayado con el servidor 6.10 real (`test_ensayo_sesiones.py`): reproducción del defecto de la copia congelada y contrato corregido. Sin tokens nuevos en claro en ningún lado |
| Si PostgreSQL no está disponible al revertir (rev. 4, B3-R3-02) | **No hay reversión automática.** `revertir.py` se detiene: no puede comprobar el estado final y **nunca** usa el último `sesiones.json` exportado, porque una revocación posterior a esa exportación lo dejaría válido (Codex lo reprodujo; el ensayo también). La única vía de emergencia, y solo con autorización explícita de Adrián en ese momento, escribe `{}` de forma atómica: **todas** las sesiones cerradas, cada quien entra una vez; y el informe declara que los demás documentos pueden estar desactualizados desde `espejo_estado.exportada_en`. Antes de cualquier verificación final se **drenan** las transacciones de `lumin_app` en vuelo (§7.3) | Ensayado: `revertir` bloquea sin PostgreSQL, en emergencia cierra todas, en la ruta normal usa el estado final y no el último espejo; el drenaje espera y cancela. Recomendación de Codex para D7 incorporada |
| Revocación masiva | **En B4**, cuando entren Argon2id y la sesión por ámbito: ahí se cierra todo y cada quien vuelve a entrar una vez, avisado | Una sola interrupción, cuando trae algo a cambio |
| Reversión a 6.10 **después de B4** | **No está cubierta por este diseño.** Cuando B4 recifre a Argon2id, 6.10 no podrá verificar esas contraseñas. B4 definirá su propia marcha atrás (conservar el hash sha256 hasta validar B4, o restablecimiento por correo) | Se declara para que nadie lo asuma |

### 7.5 Respaldo desde el día uno

El diseño de respaldo de la rama SQLite se adapta: `pg_dump --format=custom`
nocturno + `rclone` de medios, rotación local 14 días, remoto 90. Se instala
**antes** del corte y se prueba restaurando en limpio. Sin respaldo probado, no
hay corte.

---

## 8a. Medios: entrega y autorización (punto 5 de Codex)

**Decisión para B3: los archivos siguen en disco local, en las mismas rutas,
servidos por el mismo proceso.** Cambiar el almacenamiento y la entrega en el
mismo bloque que la base de datos duplica el riesgo de un corte que ya es el
más delicado de todo el plan.

**El límite que B3-QA-04 dejó claro, y su contrato.** `GET
/videos/<clave>/<archivo>` no lleva identidad de empresa: ni `id_dispositivo`,
ni sesión, ni credencial. Dos empresas con la misma clave de sucursal y el
mismo nombre de archivo producirían la misma URL, y el servidor no puede
adivinar cuál se pidió. Por eso B3 fija este contrato:

| Regla | Cómo se garantiza |
|---|---|
| Las rutas heredadas (`/playlist.json`, `/videos/`, `/miniaturas/`, `/rapidos/`, `/api/turno` y todo `/api/*` de 6.x) resuelven **exclusivamente** dentro de la **empresa heredada**, configurada en `LUMIN_EMPRESA_HEREDADA=lumin` | El `Contexto` de esas rutas se construye con esa empresa fija; `sucursal.clave` se busca solo ahí |
| **No puede existir más de una empresa activa** mientras rijan las rutas heredadas | Índice único parcial en la base: `CREATE UNIQUE INDEX una_sola_activa ON empresa ((true)) WHERE estado = 'activa'`; y el servidor rechaza `estado='activa'` para cualquier empresa distinta de la heredada. Las demás solo pueden existir como `suspendida` (para preparar datos) |
| Un medio de otra empresa **no es alcanzable** por ninguna URL heredada | Prueba por HTTP real: `A` (heredada) y `B` con `plaza-centro/promo.mp4` en ambas; la URL sirve el de `A`; el de `B` no se sirve por ninguna ruta, ni aparece en ninguna playlist |
| `ruta_almacen` obligatoria para toda empresa no heredada, con prefijo `<empresa.clave>/<sucursal.clave>/` | `CHECK` en `contenido`: `ruta_almacen IS NOT NULL OR empresa_id = (SELECT id FROM empresa WHERE clave = 'lumin')` se expresa como columna `heredada boolean` en `empresa` y un trigger; así dos archivos iguales de dos empresas nunca comparten ubicación física |
| Levantar el límite es trabajo de **B8**: URLs con espacio de nombres (`/m/<empresa>/<sucursal>/<archivo>`) o credencial por pantalla que identifique la empresa, y `playlist.json` v2 que las emita | Hasta entonces, el índice único y la guarda del servidor siguen puestos, con prueba que lo exige |

Lo que B3 sí deja listo para B5:

- `contenido.ruta_almacen text` (NULL solo para la empresa heredada = ruta
  local derivada de `sucursal.clave/nombre_archivo`). B5 la llena al mover a
  S3.
- La URL pública heredada no cambia: `/videos/<clave>/<archivo>` es un
  contrato de LUMIN. Quien la sirva por detrás (proceso Python hoy, nginx con
  `X-Accel-Redirect` mañana) es invisible para las TVs.

**Cómo se servirán los medios en B5 sin saltarse el aislamiento:**

| Opción | Aislamiento | Costo | Veredicto |
|---|---|---|---|
| Proceso Python (hoy) | Puede comprobar credencial de pantalla (B8) en cada petición | Compite con el panel por CPU y hilos | Se mantiene en B3 |
| nginx directo a disco | **Ninguno**: cualquiera con la URL descarga. Es lo que hay hoy (QA-G01) | Cero | **Rechazado como destino** |
| nginx con `X-Accel-Redirect` | La aplicación autoriza (credencial de pantalla, empresa, sucursal) y nginx entrega el archivo desde una ruta interna no expuesta | Una petición ligera a la app por archivo | **Propuesto para B5** |
| S3 compatible con URL firmada | La app firma por pantalla y por tiempo; el almacenamiento no sabe de empresas | Costo por transferencia; CDN opcional | Destino cuando el volumen lo justifique (P-008/D-007) |

Justificación de local frente a S3 ahora: cinco sucursales, decenas de
archivos, un VPS con disco de sobra y sin CDN. S3 resuelve un problema de
tráfico que hoy no existe y añade una dependencia externa y un costo mensual.
Se activa cuando haya evidencia (bitácora de B2 + estadísticas de B5) de que
el proceso compite por recursos, o cuando entre la segunda empresa.

**Prefijo por empresa desde ya:** las rutas nuevas que B5 cree en disco o en
S3 llevarán `<empresa.clave>/<sucursal.clave>/…`. Las actuales de LUMIN se
quedan donde están (contrato) y se registran con su ruta real en
`ruta_almacen`; una migración de archivos, si se decide, es un bloque aparte
con su propia reversión.

## 8b. Cola de trabajos en PostgreSQL (punto 6 de Codex)

B3 **no** ejecuta trabajos en segundo plano: la conversión con ffmpeg sigue
siendo síncrona dentro de `/api/subir`, como hoy. Pero crea la tabla para que
B5 mueva ahí la conversión sin otra migración:

```sql
CREATE TABLE trabajo (
  id             uuid PRIMARY KEY,
  empresa_id     uuid NOT NULL,
  tipo           text NOT NULL,                  -- 'convertir_video', 'miniatura'
  carga          jsonb NOT NULL,                 -- entrada del trabajo
  clave_idem     text,                           -- idempotencia: (empresa_id, tipo, clave_idem)
  posesion       uuid,                           -- token del trabajador que lo reclamó
  estado         text NOT NULL DEFAULT 'pendiente'
                 CHECK (estado IN ('pendiente','en_curso','hecho','fallido','cancelado')),
  intentos       int  NOT NULL DEFAULT 0,
  max_intentos   int  NOT NULL DEFAULT 3,
  no_antes_de    timestamptz NOT NULL DEFAULT now(),
  tomado_por     text,                           -- identificador del trabajador
  tomado_en      timestamptz,
  latido_en      timestamptz,                    -- el trabajador lo renueva cada 30 s
  terminado_en   timestamptz,
  error          text,
  creado_en      timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX trabajo_idem ON trabajo (empresa_id, tipo, clave_idem) WHERE clave_idem IS NOT NULL;
CREATE INDEX trabajo_pendientes ON trabajo (no_antes_de) WHERE estado = 'pendiente';
```

Protocolo, escrito ahora para que B5 no lo improvise:

- **Reclamar:** `UPDATE trabajo SET estado='en_curso', tomado_por=$w, tomado_en=now(),
  latido_en=now() WHERE id = (SELECT id FROM trabajo WHERE estado='pendiente' AND
  no_antes_de <= now() ORDER BY creado_en FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *`.
  Una transacción, un trabajador gana, los demás no bloquean.
- **Idempotencia:** `clave_idem` = `sha256` del **contenido** del archivo
  subido (no del tamaño: dos versiones distintas pueden pesar igual) más el
  `tipo`. Reencolar lo mismo no crea dos trabajos; una versión nueva del mismo
  nombre sí.
- **Posesión:** al reclamar se genera `posesion = gen_random_uuid()` y se
  devuelve al trabajador. **Publicar el resultado exige la posesión vigente.**
- **Publicación con artefacto por posesión (rev. 4, B3-R3-03):** el
  resultado se escribe primero en disco con un nombre que lleva la **posesión**
  (`<destino>/<nombre>.<digest8>.<posesion8>.mp4`), así dos posesiones del
  mismo trabajo **nunca** comparten archivo; escribirlo dos veces con la misma
  posesión es idempotente. **Después**, una sola transacción hace `UPDATE
  trabajo SET estado='hecho', terminado_en=now(), resultado=<ruta> WHERE id=$1
  AND posesion=$2 AND estado='en_curso'` (y, en la misma transacción, apunta
  `contenido.ruta_almacen` a esa ruta). Si afecta 0 filas, **en la misma
  transacción** se lee la fila y se distingue (rev. 5, B3-R4-02): si está
  `hecho` con **mi** posesión y **mi** ruta, es `ya_publicado` —éxito
  idempotente, el caso del reintento tras una confirmación cuya respuesta se
  perdió— y **no se borra nada**; en cualquier otro caso es `perdido` y el
  trabajador borra **solo el archivo que lleva su posesión en el nombre**: no
  puede tocar el de la posesión ganadora ni un artefacto referenciado por
  `resultado`. El "nombre visible" (`<nombre>.mp4` de la URL heredada)
  no se renombra: la URL lo resuelve por `ruta_almacen`. **Huérfanos** (crash
  entre disco y `UPDATE`): un barrido borra los artefactos que ninguna fila
  referencia **y** cuya posesión ya no está `en_curso`; mientras la posesión
  viva, no se toca. Así no existe "hecho sin archivo" ni "archivo publicado
  borrado por un rezagado". Ensayado en `test_ensayo_cola.py`, incluida la
  reproducción del defecto de la rev. 3 (nombre compartido → `hecho` sin
  archivo).
- **Digest por destino (precisión de Codex):** `clave_idem = sha256(contenido)
  + tipo + sucursal_id`. Dos destinos de la misma empresa con el mismo archivo
  son **dos trabajos** (y dos publicaciones); compartir un artefacto por
  digest entre destinos queda para B5 como optimización explícita, no como
  efecto colateral de la deduplicación.
- **Reintentos:** al fallar, `intentos+1`, `no_antes_de = now() + 2^intentos
  minutos`, `estado='pendiente'`, `posesion=NULL` mientras `intentos <
  max_intentos`; después `fallido` con `error`, visible en el panel (B6).
- **Recuperación tras caída del trabajador:** un barrido cada minuto devuelve
  a `pendiente` (y limpia `posesion`) los `en_curso` con `latido_en` de hace
  más de 3 minutos. Quien lo reclame después recibe una posesión nueva; la
  vieja ya no sirve para publicar.
- **Cancelar, incluido `en_curso`:** borrar el contenido pone sus trabajos
  `pendiente` **y** `en_curso` en `cancelado` (y `posesion=NULL`). El
  trabajador en curso lo descubre al renovar el latido o al intentar publicar,
  y descarta el resultado.
- **Un trabajador**, como proceso `systemd` aparte, en el mismo VPS. Redis o
  Celery no se introducen sin una necesidad concreta.

## 8. Cambios en el VPS

| Qué | Detalle |
|---|---|
| PostgreSQL 16 | Paquete de la distribución, escucha solo en `localhost` |
| Base y roles | `lumin_tv`; rol `lumin_app` (sin superusuario, sin `BYPASSRLS`); rol `lumin_migracion` para Alembic y respaldos |
| Dependencias Python | `sqlalchemy`, `psycopg[binary]`, `alembic` en un venv en `/opt/lumin-tv/.venv`; el `systemd` apunta al Python del venv |
| Secretos | `/etc/default/lumin-tv` con `LUMIN_BASE_DATOS_URL`; nada en el código (QA-F03 sigue en pie para la contraseña del panel hasta B4, y se declara) |
| Despliegue | `lumin-deploy` gana un paso: `alembic upgrade head` antes de reiniciar. Se revisa ese script antes de tocarlo |

---

## 9. Decisiones que necesito de Adrián

Codex tiene razón en que D1 y D2 no se pueden decidir con propuestas
abstractas. Como no debo leer los datos de producción, dejo una herramienta de
**solo lectura** para que la corras tú en el VPS y me pegues la salida:

```bash
python3 /opt/lumin-tv/servidor/herramientas/inventario_decisiones.py /opt/lumin-tv
```

(está en `servidor/herramientas/` de la rama; hay que copiarla al VPS). Lee
`tvs.json`, `sucursales.json` y `usuarios.json`, **no escribe nada**, no
muestra hashes, sales ni tokens, y usa como alias el sufijo más corto (mínimo
6 caracteres) que distingue todos los identificadores, con el mapeo alias →
id completo al final (INV-01). Si falta un archivo, no se puede leer o no
tiene el esquema esperado, **no imprime conclusiones** y termina con código 2;
un archivo válido pero vacío se dice como tal. Ocho pruebas con datos
sintéticos en `servidor/tests/test_inventario_decisiones.py`. Imprime:

- **D1:** cada número repetido con las pantallas que lo comparten (id parcial,
  sucursal, zona, último contacto, desfase actual, turnos, lista) y el número
  que tomaría cada una con la regla propuesta. Dice explícitamente que
  `tvs.json` **no guarda fecha de alta**, así que "más antigua" no se puede
  acreditar: la regla propuesta conserva el número la primera por `indice`
  y, a igualdad de índice (lo normal entre duplicadas), la de identificador
  menor —un orden estable, no antigüedad—, y la decisión es tuya.
- **D2:** cada usuario cuyo alcance efectivo de hoy no coincide con lo que
  declara (lista vacía → todas; claves inexistentes → la primera), con sus
  sucursales declaradas, las efectivas y el motivo.

| # | Decisión | Mi propuesta (no es autorización) |
|---|---|---|
| D1 | Números de pantalla duplicados: `UNIQUE (empresa_id, numero)` no admite dos P6 | Con la salida de la herramienta en mano, decides pantalla por pantalla cuál conserva el número. Hasta entonces la migración **se niega a correr** si detecta duplicados sin una tabla de decisión firmada (`decisiones_d1.json`) |
| D2 | Usuarios con `[]` o claves inexistentes | B3 migra el alcance **efectivo de hoy**, explícito, para no cambiar el comportamiento el día del corte, y lo marca en `migracion_json`. Lo que decidas usuario por usuario lo aplica B4. Si prefieres que B3 ya aplique tu decisión, se hace con la misma tabla firmada (`decisiones_d2.json`) |
| D3 | Row Level Security | Activarla desde el día uno; el costo es mínimo y elimina una clase entera de fugas |
| D4 | Duración del espejo | 7 días de observación. Aprobarlos no sustituye el protocolo de §7.4 ni sus pruebas |
| D5 | Ventana del corte | Se acuerda **después** de la implementación, los ensayos y la revisión de Codex. No bloquea nada de este diseño |
| D7 | Sesiones al revertir (§7.6) | **Propuesta (coincide con la recomendación de Codex):** con PostgreSQL accesible, conservar solo las sesiones anteriores al corte **verificadas** vigentes en el estado final (copia congelada ∩ vigentes, tras drenar); sin PostgreSQL, **no revertir**; si tú autorizas una emergencia, cerrar **todas**. Alternativa: cerrar todas siempre (una molestia única, menos piezas). Ninguna opción usa el último archivo exportado |
| D6 | Copia anonimizada de los JSON reales para el ensayo | Primero entrego `anonimizar_json.py` y la lista exacta de campos que elimina o reemplaza (hashes, sales, tokens, **mensajes del cintillo, turnos, nombres de usuario, zonas y nombres de archivo**, que también pueden revelar cosas); tú revisas la lista, la corres en el VPS y decides si compartes la salida. Ejecutar y transferir datos reales requiere tu autorización expresa; no se ha hecho |

---

## 10. Reutilización del SaaS pausado

Repositorio `lumin-tv-saas`, commit **`b9c1f83`** (único), en
`C:\Users\adcueto\Claude\lumin-tv-saas`. Lo listado trae 36 pruebas que
pasaron contra PostgreSQL 16 en mi entorno; **Codex no las ha revisado ni
repetido**, así que cuentan como evidencia aportada, no como aprobación. Cada
pieza entra a `lumin-tv` como código nuevo del bloque que la use, con sus
pruebas adaptadas al arnés de aquí y sujeta a la misma revisión. No se copia a
ciegas: allí el dominio empezaba de cero y aquí hay llaves naturales que
respetar.

| Archivo en `lumin-tv-saas` | Destino en LUMIN TV | Bloque | Qué se adapta |
|---|---|---|---|
| `api/lumin_saas/modelos/tenancy.py` (164 líneas) | `lumin_datos/modelos.py` | **B3** | Añadir `id_dispositivo`, `numero`, `desfase_rotacion`, `clave` de sucursal, `contenido`, `lista`, `lista_elemento`, `programacion`, operación. Las llaves compuestas ya están |
| `api/lumin_saas/modelos/identidad.py` (306) | `lumin_datos/modelos.py` | **B3** (tablas) / B4 (uso) | `nombre_usuario` como llave natural; `algoritmo` de contraseña; `Sesion.empresa_id` opcional en la migración |
| `api/lumin_saas/servicios/permisos.py` (184) | `lumin_datos/contexto.py` | **B3** | `ActorEmpresa` → `Contexto`; añadir rol `pantalla` y `sistema`; la regla "vacío = nada" queda escrita pero B3 migra concesiones explícitas |
| `api/lumin_saas/db.py` (80) — `conexion_autonoma` | `lumin_datos/db.py` | **B3** | Igual; se suma el `SET LOCAL lumin.empresa_id` por transacción |
| `api/tests/test_permisos_y_aislamiento.py` (212) | `servidor/tests/test_dos_empresas.py` | **B3** | Base de la suite "dos empresas"; se cambia el arranque por el arnés del servidor real |
| `api/lumin_saas/seguridad/limites.py` (85) | `lumin_datos/limites.py` | B4 | Tal cual, ya resuelve el problema de la reversión del contador |
| `api/lumin_saas/seguridad/secretos.py` (100) | `servidor/seguridad.py` | B4 | Añadir verificación `sha256-sal` para la transición y recifrado a Argon2id |
| `api/lumin_saas/servicios/codigos.py` (220) | B4 | B4 | Tal cual: emisión, un solo uso arbitrado por `rowcount`, intentos en conexión autónoma |
| `api/lumin_saas/servicios/sesiones.py` (144) | B4 | B4 | Ámbitos `empresa`/`alta`; el de `plataforma` se deja fuera hasta el portal del propietario |
| `api/lumin_saas/servicios/autenticacion.py` (474) | B4 | B4 | **Parcial:** registro público NO (fuera de alcance); invitaciones, recuperación, acceso por código SÍ |
| `api/lumin_saas/correo/__init__.py` (108) | B4 | B4 | Adaptadores memoria/consola/SMTP tal cual |
| `api/tests/test_limites_y_concurrencia.py`, `test_registro_y_codigos.py` | B4 | B4 | Adaptar al arnés |
| `api/lumin_saas/rutas/*`, `plataforma.py`, `consola.py` | — | fuera | Portal del propietario y alta de superadministrador: pendientes por decisión |
| `.github/workflows/ci.yml` | `.github/workflows/ci.yml` | **B3** | PostgreSQL 16 como servicio, `alembic upgrade`/`downgrade`, pytest |

Lo que no se reutiliza de la rama `fase1-sqlite-respaldos`: su `registrar_tv`
(conserva el defecto de los números) y todo lo que asume SQLite. Su diseño de
respaldo sí, adaptado a `pg_dump` (§7.5).

---

## 11. Criterios de aceptación de B3

1. Las 30 rutas del panel y los 3 contratos responden **igual** que 6.10 sobre
   el mismo juego de datos: pruebas byte a byte, no "parecido".
2. Suite "dos empresas" en verde, con el guardián de SQL activo y RLS
   verificada sin `SET`.
3. Migración sobre copia sintética y sobre copia anonimizada: informe sin
   errores; **byte a byte** solo donde tiene sentido: la respuesta de
   `playlist.json` por pantalla, con el reloj fijado. Para la ida y vuelta
   JSON → PG → JSON la equivalencia es **semántica** (JSON parseado y
   normalizado) con esta lista de exclusiones declaradas: sesiones vencidas
   (no se migran), entradas de `ordenes`/`listas` cuyo archivo no está en
   disco (hoy también se filtran al leer), contadores de más de 60 días,
   `tvs.visto` (dinámico), `turnos.ts` (dinámico), los números de pantalla
   que Adrián apruebe renumerar (D1), y `indice`: el formato viejo tiene un
   solo campo para número y desfase; la exportación escribe `indice =
   numero − 1`, de modo que el panel de 6.10 muestre los números aprobados,
   y el desfase de rotación de una pantalla renumerada cambia en una
   reversión. Todo lo demás debe ser idéntico, y cualquier diferencia no
   listada aquí hace fallar la prueba.
4. Reversión ensayada por las dos vías y cronometrada.
5. `alembic downgrade base` y vuelta a `head` en CI, contra PostgreSQL 16.
6. Concurrencia sobre PostgreSQL: 40 latidos + 20 turnos + 200 descargas
   simultáneos sin pérdida ni duplicado (mismos números que B2, ahora contra la
   base).
7. Respaldo `pg_dump` nocturno instalado y restaurado en limpio una vez.
8. La app Roku 5.1 y 5.2 pasan F13 contra 6.11 en la TV de pruebas.
9. Codex no tiene hallazgos abiertos.

---

## 12. Riesgos

| Riesgo | Mitigación |
|---|---|
| El rewire de ~40 puntos de acceso del monolito introduce regresiones sutiles | Pruebas de contrato byte a byte sobre fixtures que cubren cada rama de cada ruta; el diff de `servidor_lumin.py` se revisa ruta por ruta |
| PostgreSQL caído = sistema caído (hoy los JSON nunca "se caen") | `systemd` con dependencia y reinicio; las TVs siguen con caché (B1); alerta en la bitácora; el respaldo nocturno |
| Rendimiento del latido (20 pantallas × cada 4 s) | Es un `UPDATE` de una columna; medido en B2-SaaS a 836/s. Índice por `id_dispositivo` |
| RLS mal configurada bloquea todo | Prueba de arranque que falla si el rol tiene `BYPASSRLS` o si `SET` no surte efecto |
| Migrar contraseñas sha256 "perpetúa" QA-F03 | Es temporal y declarado: B4 recifra en el siguiente login y obliga a rotar la del admin inicial |
| El script de anonimización deja algo sensible | Lo revisa Adrián antes de compartir la copia; la copia vive solo en el entorno de pruebas y se borra al terminar |

---

## 13. Lo que pido para cerrar la revisión

- Las siete decisiones de §9 (D7 es nueva en esta revisión).
- Que Codex repita los 67 ensayos de `servidor/ensayos_b3/` en su entorno
  (necesitan un PostgreSQL 16 de ensayo y `psycopg` 3; el README dice cómo).
  Son la evidencia de B3-R2-01/02/03; sin repetirlos, cuentan como evidencia
  aportada por Claude.
- Objeciones de Codex al esquema (§3), en especial a `descarga_diaria` sin
  FK, a `sesion.empresa_id` nulo en migración, y a la política de §6.2.
- Confirmación de que el ensayo con copia anonimizada es aceptable dentro de
  D-006 ("sin alteración de datos reales").

Hasta entonces, **no escribo código de B3**.
