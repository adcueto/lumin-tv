# QA de B1 R2, B2 R2 y diseño B3 — correcciones requeridas

Fecha: 2026-09-16. Candidato: **5c96845413f3ce11474d5123ee95fae9a63827d6**, rama modernizacion-diagnostico. Comparación de esta entrega: 0c00f35 → 5c96845.

## Dictamen por bloque

| Bloque | Resultado |
|---|---|
| B1 R2, Roku build 58 | Mejora los tres recorridos originales, pero quedan problemas de integración y de reintentos. No cerrado; falta validación física. |
| B2 R2 | Los dos hallazgos previos están corregidos en código/documentación. Diez funciones de prueba pasan en el candidato; siete fallan y tres pasan contra ea610d6. Validación local mediante ejecutor directo, no pytest/CI. |
| B3, diseño | Dirección adecuada, pero no listo para implementar tal como está: faltan garantías concretas de reversión y aislamiento. Es revisión de un diseño, no de una implementación PostgreSQL existente. |

No se modificó el repositorio ni se hicieron commits, push, despliegues o migraciones. El checkout sigue en main, ea610d6fbea8dac7c330f0ba134cf41e5d92fcdc. Las referencias de Git se verificaron localmente, sin fetch. Los dos iconos borrados y docs/coordinacion sin seguimiento son estado local previo, no cambios de este candidato.

## Evidencia independiente

- Diff de 11 archivos revisado. git diff --check: sin errores.
- Extracción de 28 archivos del SHA exacto a revision-r2-5c96845/candidato; hashes SHA-256 en revision-r2-5c96845/hashes.json.
- Tres XML de Roku parseados correctamente. No se reejecutó BrighterScript; cero diagnósticos sigue siendo evidencia aportada por Claude. No se ejecutó la app en un Roku.
- Diez funciones test_* originales de B2 ejecutadas sin modificar sus aserciones. En este candidato ya no importan pytest. Resultado: **10/10 pasan**.
- Mismas funciones contra una copia de servidor_lumin.py de ea610d6: **7 fallan/3 pasan**. Concurrencia variable: esta corrida perdió sesiones, altas y giros y rechazó conexiones; no se exige repetir los mismos conteos de otra máquina.
- El script comparar_con_base.py se inspeccionó: extrae mediante git show a temporal y configura LUMIN_SERVIDOR_BAJO_PRUEBA, sin stash ni checkout. No se ejecutó ese comando completo porque el Python disponible no tiene pytest. La comparación independiente usó el mismo arnés y la misma suite mediante revisar.py.
- Petición real a servidor candidato aislado, con video sintético: **GET /videos/plaza-de-la-mujer/qa-head.mp4 → 200; HEAD a la misma URL → 501**. Evidencia en revision-r2-5c96845/head.json. No es una petición al VPS.
- Resultados completos: revision-r2-5c96845/resultados-candidato.json y resultados-base.json. Ejecutor reproducible: revision-r2-5c96845/revisar.py. Python utilizado: C:/Users/adcueto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe.
- Una primera corrida del ejecutor de QA contra la base se interrumpió por iterar un diccionario que cambió de tamaño; se corrigió únicamente ese ejecutor para fijar la lista de funciones y se repitió la corrida completa. No se alteraron las pruebas de Claude.

## B1 R2: hallazgos abiertos

### R2-B1-01 [P1] Tamaño desconocido impide desalojar y puede bloquear la renovación de la caché

**Ubicación:** roku-app/components/CacheTask.brs, líneas 158–170 y 198–204; tamanoRemoto, líneas 245–265. Servidor: Manejador hereda de BaseHTTPRequestHandler y no implementa do_HEAD.

**Evidencia:** HEAD devuelve 501 en el servidor candidato. tamanoRemoto convierte cualquier respuesta distinta de 200 en tamaño 0. El único desalojo previo a descargar exige tamano > 0. Por tanto, el servidor actual activa precisamente la ruta sin desalojo.

**Recorrido estático:** caché con tres videos de 70 MiB = 210 MiB; el presupuesto utilizable es 250−20 = 230 MiB. Cambiar a una lista con un archivo nuevo de 30 MiB. aplicarDeseados no borra los anteriores porque 210 < 250. HEAD falla; topeEsteArchivo queda en 20 MiB. Al superar ese tamaño la descarga se cancela, o se rechaza al completarse, y se devuelve sin_espacio. Reintentar sin liberar los anteriores produce lo mismo. La lista nueva puede quedarse sin copia local aunque exista contenido obsoleto desalojable.

**Corrección:** soportar HEAD coherente con GET para medios sin incrementar estadísticas, y resolver también el tamaño desconocido sin depender de que HEAD siempre exista. Definir reserva/desalojo conservador y evitar repetir una descarga que no cabe sin cambiar el presupuesto.

**Aceptación:** pruebas del servidor para HEAD de medio real/inexistente y ausencia de incremento del contador; Roku con tamaño conocido y desconocido, caché casi llena y cambio de lista. Aquí se reprodujo HTTP 501; el efecto en la caché se identificó por análisis de código, no en hardware.

### R2-B1-02 [P2] La reconciliación pierde el historial y puede duplicar el trabajo activo

**Ubicación:** CacheTask.brs, líneas 67–77, 86–109 y 206–209; MainScene.brs, reconciliación cada 60 segundos.

previos conserva solo lo que permanece en m.cola. Los archivos descartados por 404/403/tamaño o por agotar intentos desaparecen de ella; al siguiente aplicarDeseados, siguen faltando en disco y se insertan con intentos=0. Así no se cumple la afirmación «404 no se reintenta» ni el máximo global por archivo mientras la lista no cambie.

Además, siguienteListo retira el trabajo activo antes de descargar. Si llega una reconciliación durante la descarga, aplicarDeseados no lo encuentra en previos ni en disco definitivo y crea otro intento cero para la misma URL. Cuando falla el activo, se agrega también su reintento con espera. El duplicado listo puede saltarse la espera creciente.

**Corrección:** estado por URL/versión separado de la cola: activo, intentos, próxima fecha, éxito y fallo terminal; cola deduplicada. Reconciliar no debe reiniciar intentos ni insertar el activo. Definir qué cambio o acción permite volver a intentar un fallo terminal.

**Aceptación:** mantener una URL 404 durante varias reconciliaciones; agotar cinco intentos con lista estable; reconciliar durante una descarga fallida de más de 60 segundos. Verificar conteos y esperas. Los cinco intentos totales actuales permiten cuatro esperas (30/60/120/240); la espera de 300 anunciada tampoco se alcanza dentro de ese ciclo.

### Hallazgo previo B1-QA-03

El recorrido concreto n=5 → caída → n=5 → nuevo n=6 está corregido estáticamente: la bandera se consume antes del retorno por número idéntico. Validarlo físicamente en F17; esto no certifica todos los casos de comandos, arranque o caída.

## B3: objeciones al diseño antes de implementarlo

Todas las líneas de esta sección corresponden a docs/coordinacion/13-diseno-B3-postgresql.md del candidato.

### B3-QA-01 [P1] La escritura doble no define recuperación frente a una escritura parcial

**Líneas 541–552.** Confirmar una transacción PostgreSQL y escribir después un JSON son dos operaciones independientes. Si el proceso cae o falla el disco entre ambas, PostgreSQL y los JSON divergen. Un solo proceso también tiene múltiples hilos HTTP; por sí solo no garantiza orden idéntico entre almacenes. El documento promete que basta reiniciar 6.10 y que todo lo posterior al corte está en JSON, pero no define protocolo que lo garantice.

Especificar fuente de verdad, límites de transacción, orden por operación, registro durable de operaciones pendientes, reejecución idempotente y criterio verificable de espejo sincronizado. La reversión debe bloquearse si falta sincronizar; cubrir explícitamente qué ocurre si PostgreSQL no está accesible. Ensayar caídas antes y después del commit y durante la escritura de archivos, fallos de disco y mutaciones de varios JSON. Siete días es una duración, no una garantía de consistencia.

### B3-QA-02 [P1] La exportación tardía no puede reconstruir sesiones desde token_hash

**Líneas 313–319, 377 y 548–556.** Conservar solo SHA-256 del token permite validar la cookie recibida; no permite recuperar el token original. El servidor 6.10 consulta sesiones.json mediante ses.get(token), con el token sin hash como clave. Una sesión creada después de apagar el espejo JSON no puede exportarse al formato anterior desde la tabla propuesta.

Elegir un contrato de reversión realizable: por ejemplo, aceptar cierre de sesiones al revertir y exigir nuevo login, o preparar un lector anterior compatible con hashes. No guardar tokens en claro como solución improvisada. Ensayar login después del día siete y rollback. Aclarar también que la reversión a 6.10 no cubre sin adaptación los hashes Argon2id que introduzca B4. La compatibilidad de sesiones el día del corte sí es posible; el problema señalado es la marcha atrás posterior.

### B3-QA-03 [P1] lista_elemento queda fuera de la política de aislamiento descrita

**Líneas 206–215, 345–357 y 417–418.** lista_elemento no tiene empresa_id, aunque el diseño exige esa columna y filtro en todas las tablas del dominio y activa RLS en las que la tienen. Las llaves foráneas limitan qué padres puede referenciar una fila; no filtran un SELECT directo sobre sus elementos. La política propuesta para sucursal no se hereda automáticamente por una FK.

Añadir empresa_id y restricciones que lo amarren a lista/contenido/sucursal, con su política, o definir expresamente una política equivalente basada en el padre. Probar lectura y escritura directa como lumin_app, con y sin contexto, sin depender de un JOIN del repositorio. Definir además tratamiento especial para tablas globales de identidad y sesiones migradas con empresa_id NULL: aplicarles mecánicamente la igualdad propuesta no resuelve el arranque de autenticación.

Completar el contrato del rol: no propietario de las tablas (o FORCE ROW LEVEL SECURITY), sin posibilidad de asumir el rol privilegiado, además de no ser superusuario/BYPASSRLS. Probar reutilización de conexiones A → B → sin contexto. El guardián que solo busca el texto empresa_id acepta SELECT empresa_id FROM sucursal sin filtro; no demuestra aislamiento y debe acompañarse de controles negativos que omitan deliberadamente el filtro.

Referencia primaria: PostgreSQL 16, [Row Security Policies](https://www.postgresql.org/docs/16/ddl-rowsecurity.html). Las políticas se aplican por tabla y el propietario normalmente las elude salvo FORCE RLS.

### B3-QA-04 [P1] No se define de dónde sale la empresa en la petición pública del medio

**Líneas 419–423, 469–478 y sección 8a.** La playlist lleva id_dispositivo; GET /videos/<clave>/<archivo> no lleva ese identificador, una sesión de panel ni otra credencial. El reproductor hace una petición nueva para el video. Dos empresas con la misma clave de sucursal y el mismo archivo generan la misma URL; el servidor no puede deducir cuál se quiso pedir solo porque antes atendió una playlist. Además, ruta_almacen NULL deriva la misma ubicación física para ambas.

Definir en B3 un contrato explícito: mantener esas rutas antiguas ligadas solo a LUMIN y prohibir la activación operativa de una segunda empresa hasta incorporar un espacio de nombres/contexto verificable, o introducir una URL/host/credencial que sí identifique a la empresa. No hace falta desarrollar cobros para resolver este límite. Las pruebas deben usar peticiones HTTP reales para ambos medios; inyectar Contexto en una llamada interna no prueba el contrato público.

### B3-QA-05 [P2] Una pantalla pendiente puede referenciar una lista de otra empresa

**Líneas 133–153 y 219.** sucursal_id acepta NULL mientras una pantalla está pendiente. La FK (lista_id, sucursal_id) usa MATCH SIMPLE implícito: con sucursal_id NULL omite la comprobación, aunque lista_id apunte a una lista de otra empresa. El CHECK existente solo exige sucursal al aprobar; no prohíbe lista en una pantalla pendiente.

Añadir CHECK (lista_id IS NULL OR sucursal_id IS NOT NULL) y/o FK (lista_id, empresa_id) que preserve el aislamiento incluso en ese estado. Probar INSERT/UPDATE de pantalla pendiente de A con lista de B y sucursal NULL. Hallazgo del esquema propuesto, sin ejecución PostgreSQL local.

Referencia primaria: PostgreSQL 16, [Foreign Keys](https://www.postgresql.org/docs/16/ddl-constraints.html#DDL-CONSTRAINTS-FK): semántica de NULL y MATCH FULL/SIMPLE.

## Precisiones adicionales para incorporar al diseño

- **Cola futura, §8b:** hash de (sucursal, nombre, tamaño) confunde dos versiones distintas con el mismo tamaño. Usar versión/digest del contenido. El retorno a pendiente debe invalidar al trabajador anterior mediante una versión de posesión comprobada al publicar; renombrar un temporal no impide que un trabajador atrasado sobrescriba un resultado nuevo. El protocolo de cancelación debe contemplar en_curso, no solo pendiente. No se pide ejecutar la cola en B3.
- **Corte, §7.3:** el modo de solo lectura debe congelar también latidos, contadores GET, sesiones y todos los escritores, no solo botones del panel. El turno y la subida del paso 5 requieren una apertura controlada de escrituras antes del paso 6; especificar un ensayo aislado o una ventana de smoke tests que lo permita.
- **Equivalencia, §11:** ida y vuelta idéntica debe declarar las normalizaciones ya previstas: sesiones vencidas, archivos ausentes, contadores antiguos y renumeración aprobada. Separar estabilidad semántica de valores dinámicos y bytes de JSON. No prometer retorno idéntico de numero/desfase si el formato antiguo solo tiene indice.
- **Alcance B3:** preparar el esquema multiempresa no equivale a comercializar ni habilitar varias empresas reales con endpoints heredados sin credencial. Mantener explícito ese límite hasta completar identidad, permisos y dispositivos.

## Las seis decisiones: recomendación, no autorización del propietario

| Decisión | Recomendación |
|---|---|
| D1, P6 duplicados | Presentar tabla concreta con IDs, sucursal, número actual/propuesto y efecto en desfase. No se acreditó cuál es la más antigua; visto es último contacto, no alta. La decisión de cambiar números sigue siendo de Adrián. |
| D2, permisos vacíos | Presentar los usuarios afectados y sus concesiones efectivas; no convertir la propuesta en concesión general autorizada sin esa revisión. Incluir claves inexistentes y el efecto sobre sucursales futuras. |
| D3, RLS | Recomendable desde B3, una vez cerrado el alcance por tabla, rol y contexto descrito arriba. |
| D4, siete días | Puede ser una ventana de observación; aprobarla no sustituye el protocolo de recuperación ni sus pruebas. |
| D5, fecha del corte | Acordarla después de implementación, ensayos y QA; no bloquea corregir ahora el diseño. |
| D6, copia anonimizada | Preparar primero el script y revisar qué campos elimina, incluyendo mensajes/turnos, identificadores y rutas reveladoras, además de credenciales. La ejecución y transferencia de datos reales requieren la autorización correspondiente; no se hicieron aquí. |

## Mensaje propuesto para Claude

> Revisé el SHA 5c96845413f3ce11474d5123ee95fae9a63827d6. Los dos hallazgos B2 R2 están atendidos; ejecuté la suite directamente y obtuve 10 pasan en el candidato y 7 fallan/3 pasan en ea610d6, sin pytest/CI. Antes de cerrar B1 corrige el caso HEAD=501/tamaño desconocido sin desalojo y conserva estado de reintentos fuera de la cola para evitar reinicios y duplicados del activo. El recorrido concreto de comandos n=5/n=6 ya está corregido estáticamente; falta Roku físico.
>
> Prepara una revisión del diseño B3 que resuelva la atomicidad/recuperación del espejo JSON, la reversión de sesiones hash, RLS de lista_elemento y roles, la empresa de las peticiones públicas de medios y la FK de listas en pantallas pendientes. Incorpora las precisiones de cola y corte. No avances todavía a implementación B3 ni producción. Las seis decisiones están pendientes de Adrián y deben presentarse con datos concretos; no tomes las recomendaciones de QA como autorización para cambiar números o permisos.

Informe local para Claude: C:/Users/adcueto/OneDrive/Documents/ChatGPT/LUMIN-TV/coordinacion/14-qa-R2-y-diseno-B3-5c96845.md. No está publicado en GitHub.
