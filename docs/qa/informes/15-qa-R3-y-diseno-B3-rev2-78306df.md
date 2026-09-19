# QA B1 R3 y diseño B3 revisión 2 — correcciones requeridas

Fecha: 2026-09-16. Candidato exacto: **78306df3f81b53328cd7fbdd07b294d3b0a1c262**. Comparación: 5c968454 → 78306df3. Repositorio inspeccionado: C:/Users/adcueto/Claude/lumin-tv.

## Resultado por bloque

| Bloque | Resultado |
|---|---|
| Servidor / B2 + HEAD | **13 funciones de prueba pasan** en el candidato. Las mismas contra ea610d6: **10 fallan / 3 pasan**. Ejecutor directo, sin pytest/CI. HEAD y ausencia de incremento de contadores comprobados. |
| B1 R3, build 59 | La reserva para tamaño desconocido y el registro independiente están incorporados, pero la protección contra duplicados impide encolar el reintento del trabajo que acaba de fallar. Sigue pendiente cerrar B1 y probar hardware. |
| Diseño B3 rev2 | Mejoran el esquema, los límites del producto y el procedimiento de corte. Quedan defectos concretos en el espejo, reversión de sesiones y contrato RLS. Requiere otra revisión antes de implementar. |
| Inventario D1/D2 | Solo lectura en el código y en el ensayo sintético; sin hashes/sales en la salida normal. No listo para basar decisiones: una ruta inexistente produce inventario vacío exitoso. |

No se tocó producción, no se ejecutó la herramienta en el VPS, no se modificó el repositorio, no se hizo checkout/commit/push. La rama candidata se comprobó mediante los objetos locales; no se verificó el push remoto mediante fetch. HEAD del checkout sigue siendo main/ea610d6. No se emite aprobación global ni de despliegue.

## Evidencia independiente y límites

- git diff --check 5c96845 78306df: sin errores; diff de 11 archivos revisado.
- Snapshot de 29 archivos del commit exacto en revision-r3-78306df/candidato; hashes en revision-r3-78306df/hashes.json.
- Tres XML de Roku parseados correctamente. No se reejecutó BrighterScript ni se ejecutó el reproductor. Los cero diagnósticos de compilación son evidencia aportada por Claude.
- Suite original de trece funciones, sin cambiar sus aserciones, ejecutada mediante revision-r3-78306df/revisar.py. Resultados en resultados-candidato.json y resultados-base.json de esa carpeta. Se usó Python del runtime de Codex; pytest no está instalado. No se presenta como ejecución de pytest ni CI verde.
- Herramienta de inventario ensayada con dos pantallas y un operador sintéticos, incluyendo credenciales centinela: archivos idénticos antes/después, centinelas ausentes de salida. Ruta inexistente: exit 0 y mensajes de ausencia de problemas. Evidencia en inventario-resultados.json.
- Demostración de reversión de sesiones con el servidor existente y datos sintéticos: cookie válida → cerrar sesión → cookie inválida → restaurar el JSON congelado → cookie válida otra vez. Evidencia en sesion-reversion.json. **No es ejecución de B3**, que todavía no existe; demuestra cómo 6.10 interpreta el archivo propuesto para revertir.
- Hallazgos del SQL y del espejo son análisis del diseño, sin PostgreSQL ejecutado localmente.

## Hallazgos B1 R3

### R3-B1-01 [P1] El reintento se descarta porque la descarga todavía figura como activa

**Archivo:** roku-app/components/CacheTask.brs, líneas 74–89, 123–128 y 231–233.

Tras un fallo transitorio, ejecutar llama registrarFallo mientras m.activo todavía contiene la URL. registrarFallo fija noAntesDe e invoca encolar(url); encolar retorna inmediatamente porque url = m.activo. Después se limpia m.activo, pero no se vuelve a encolar.

**Recorrido:** lista con una URL → falla por tiempo/HTTP 500 → se registra espera de 30 s pero cola queda vacía → milisegundosHastaElSiguiente ignora estados no terminales que no están en la cola → wait(0). El reintento depende de que llegue otra reconciliación, no de los 30 s. Si sigue llegando playlist, típicamente esperará a la siguiente reconciliación de 60 s; sin mensajes nuevos puede quedar detenido. La secuencia autónoma de cinco esperas anunciada no se cumple.

**Corrección:** finalizar el estado activo antes de programar el siguiente intento, o separar finalizar_descarga de encolar_reintento. Mantener la exclusión del activo durante la transferencia; no quitarla sin reemplazo porque reintroduciría duplicados.

**Aceptación:** una sola URL, primer intento falla transitoriamente, no emitir más deseados/reconectado; debe iniciarse el segundo a los 30 s. Luego verificar 60/120/240/300 s, máximo seis intentos, y reconciliación durante la descarga sin duplicar el activo. Hallazgo estático, pendiente de prueba Roku o ejecución equivalente del código BrightScript.

### R3-B1-02 [P2] sin_espacio se libera con cada reconciliación, aunque la lista no cambie

**Archivo:** CacheTask.brs, líneas 131–161; MainScene.brs mantiene reconciliación periódica cada 60 s.

aplicarDeseados reemplaza m.deseadas y libera todos los estados sin_espacio sin comparar la lista anterior ni comprobar que se liberó espacio. La misma lista recibida cada minuto vuelve a habilitar el intento que el contrato dice suspender hasta un cambio de lista. Si no pudo desalojar o la reserva sigue sin caber, se repite el mismo trabajo sin que cambie su condición de éxito.

**Corrección:** distinguir reconciliación de cambio real del conjunto/versiones deseadas; habilitar por cambio o liberación efectiva del presupuesto según una política explícita. Probar varias reconciliaciones idénticas sin incremento de intentos y después un cambio que sí permita reintentarlo.

## Objeciones pendientes al diseño B3 rev2

Las líneas siguientes son de docs/coordinacion/13-diseno-B3-postgresql.md en el candidato.

### B3-R2-01 [P1] max(bigserial) no representa el orden de confirmación de las transacciones

**Líneas 650–668.** El hilo solo exporta cuando max(espejo_marca.id) > ultima_aplicada. Un único exportador no ordena los commits de los hilos HTTP que reservan los IDs.

**Contraejemplo concurrente:**

1. Transacción A reserva marca 1 y queda abierta.
2. B reserva marca 2 y confirma.
3. El espejo ve max=2, exporta lo confirmado (B, sin A) y guarda ultima_aplicada=2.
4. A confirma su marca 1.
5. max sigue siendo 2; el espejo no vuelve a exportar aunque faltan los cambios de A.

La verificación semántica propuesta detectaría la diferencia al intentar revertir y bloquearía la reversión: eso evita aceptar a ciegas el espejo, pero el hilo no tiene mecanismo para ponerse al día sin una nueva marca mayor. Reiniciar comparando solo esos contadores tampoco lo resuelve.

**Corrección:** seguimiento explícito de marcas pendientes/procesadas sin asumir orden de commit a partir de una secuencia, o protocolo de generación serializado que sí lo garantice. Definir una instantánea consistente para exportar todos los documentos y qué conjunto de marcas cubre; no leer cada documento bajo estados distintos y declararlos una generación. Mantener bloqueo de reversión y ensayo de recuperación.

**Aceptación:** dos conexiones con barreras fuerzan exactamente el orden A-reserva/B-confirma/espejo/A-confirma, sin una tercera escritura que oculte el fallo. Debe converger por sí solo. Añadir corte a mitad de generación y fallo al persistir ambos marcadores.

Base técnica: PostgreSQL documenta asignación concurrente de secuencias y que sus valores no se revierten con la transacción. El recorrido de commits anterior es una inferencia del protocolo propuesto, no un resultado de PostgreSQL ejecutado en esta revisión. [Sequence Manipulation Functions, PostgreSQL 16](https://www.postgresql.org/docs/16/functions-sequence.html).

### B3-R2-02 [P1] El JSON congelado vuelve a habilitar sesiones revocadas después del corte

**Líneas 710–712.** La política promete conservar todas las sesiones anteriores al corte y no actualizar sesiones.json. Si una de esas sesiones se cierra o revoca en PostgreSQL durante B3, la copia congelada conserva el token sin revocar. Al regresar a 6.10, ese token vuelve a ser válido mientras no haya expirado y exista el usuario.

**Evidencia:** demostración sintética con las funciones reales de 6.10; validez antes de logout=true, después=false, después de restaurar JSON congelado=true. No se registraron tokens en la evidencia.

**Corrección posible:** invalidar todas las sesiones al revertir y pedir login, o generar el archivo anterior filtrando los tokens ya existentes mediante su hash contra las sesiones todavía vigentes/no revocadas en PostgreSQL. El segundo enfoque no requiere recuperar tokens nuevos ni almacenar otros en claro, pero exige base disponible y conserva solo sesiones elegibles. Mantener expiraciones, bajas de usuarios y revocaciones; no prometer conservar la cookie del día −1 sin esas condiciones.

**Aceptación:** sesión anterior al corte cerrada durante B3 sigue inválida tras revertir; sesión nueva también queda inválida según el contrato; una anterior solo permanece válida si la política elegida lo permite. Un cierre de sesiones en la reversión es una decisión de producto que debe quedar explícita.

### B3-R2-03 [P1] Los permisos descritos bloquean outbox y contradicen el acceso del rol de migración

**Líneas 385–416 y 650–658.** Con RLS activada, GRANT INSERT sin una política INSERT no basta. La fila de auditoria/migracion_json/espejo_marca dice «sin política para lumin_app; solo INSERT por GRANT». Aplicada literalmente, cada marca insertada por una transacción de la aplicación es rechazada por RLS y la mutación que debía acompañarla aborta.

Además, la tabla de roles dice que lumin_migracion elude RLS por ser propietario, pero inmediatamente impone FORCE ROW LEVEL SECURITY en todas las tablas: ser propietario ya no da esa exención. Tampoco se asigna un rol válido al hilo espejo: debe leer marcas/estado/datos y actualizar espejo_estado, mientras esas lecturas se reservan al rol que solo puede usarse desde consola.

**Corrección:** matriz completa rol/tabla/operación/política. Políticas INSERT WITH CHECK explícitas para marcas y auditoría, permisos de secuencia cuando correspondan, y rol/función de exportación con alcance definido. Elegir expresamente cómo operan migraciones y backups con FORCE RLS, sin conceder BYPASSRLS a la aplicación. Definir esquema y permisos de espejo_estado. Un GRANT y una política RLS son controles distintos que deben permitir conjuntamente la operación.

**Aceptación:** con los roles reales del DDL, mutación de negocio + marca en una transacción, escritura de auditoría, ciclo del espejo, migración y backup/restauración completos. Repetir los controles negativos entre empresas. Fuente primaria: [Row Security Policies, PostgreSQL 16](https://www.postgresql.org/docs/16/ddl-rowsecurity.html), comportamiento por defecto sin políticas y efecto de FORCE RLS sobre propietarios.

## Herramienta D1/D2

### INV-01 [P2] Archivos ausentes o ilegibles se convierten en un diagnóstico vacío exitoso

**Archivo:** servidor/herramientas/inventario_decisiones.py, líneas 32–40 y 136–194.

leer devuelve valores vacíos si el archivo falta, y también tras ciertos errores; main interpreta esas colecciones como inventario real y devuelve 0. Con una ruta inexistente obtuve «pantallas: 0 ... usuarios: 0», «ninguno» y «todos los operadores declaran solo sucursales existentes». Esto puede hacer pasar por revisadas D1/D2 cuando no se leyó ningún dato.

**Corrección:** validar directorio, existencia/lectura y esquema de los tres archivos obligatorios antes de imprimir conclusiones. Distinguir explícitamente datos válidos vacíos de datos faltantes. Salir con código distinto de cero ante faltantes, JSON inválido o esquema incorrecto; no generar propuestas parciales.

El ensayo normal confirmó archivos sin cambios y omisión de las credenciales centinela. La salida sí contiene usuarios, sucursales y zonas como se requiere para decidir; no es un informe anonimizado. No se probó ni ejecutó sobre datos reales.

**Precisión adicional:** los sufijos de seis caracteres pueden coincidir. En el fixture, dos IDs distintos con sufijo 123456 y la misma sucursal/zona resultaron indistinguibles en la propuesta. Generar alias únicos o extender solo el sufijo necesario, con un mapeo local inequívoco para la tabla de decisión. La selección por «menor índice» no desempata pantallas cuyo número duplicado proviene del mismo índice; el código realmente desempata por ID. Corregir la explicación visible.

## Correcciones anteriores que sí están incorporadas

- HEAD de medios ya responde y no incrementa el contador según las pruebas ejecutadas.
- Tamaño desconocido reserva TOPE_ARCHIVO y activa desalojo previo: el defecto concreto de no desalojar porque HEAD falla está corregido estáticamente.
- Registro separado conserva fallos terminales, cuarentena y contador; evita reconstruir como nuevo el trabajo activo en cada reconciliación. El nuevo fallo está en cómo se programa su siguiente intento, descrito arriba.
- lista_elemento incorpora empresa_id y FKs; pantalla pendiente tiene CHECK y FK extra de empresa; estos cambios atienden los huecos de esquema señalados, pendientes de ejecutar en PostgreSQL.
- Rutas heredadas restringidas a LUMIN y bloqueo de segunda empresa activa: el límite de producto está explicitado. No equivale a multiempresa operativa ni autorización para comercializarla todavía.
- D1/D2 siguen siendo decisiones del propietario, con herramienta concreta. Fecha de corte después de QA; ensayos y copia anonimizada pendientes.

## Precisiones para completar la revisión documental

- §7.4 todavía dice exportar «13 documentos» mientras §7.6 excluye sesiones.json. Enumerar exactamente los documentos del espejo y qué compara verificar_espejo.py; las sesiones deben cumplir el contrato corregido de revocación.
- §3.5: resolver una sesión migrada con empresa_id NULL consultando membresia requiere definir el contexto inicial. Su política normal filtra por empresa ya conocida. Alinear ese arranque con la empresa heredada de §8a o una política de resolución limitada al usuario autenticado; probar el login antes de desplegar.
- §8b: definir límites de transacción/publicación al marcar hecho y renombrar el resultado. Si se confirma hecho antes del renombrado y cae el proceso, falta el archivo final y el recuperador de en_curso no lo encuentra. Usar publicación idempotente por versión y recuperación explícita; no declarar que UPDATE exitoso por sí solo resuelve la consistencia con disco. Es precisión de B5, no solicitud de implementar la cola en B3.
- §8b: digest + tipo deduplica archivos iguales de diferentes destinos de la misma empresa. Definir si se comparte un artefacto por digest con varios vínculos o si el trabajo incluye sucursal/contenido/versión; no perder la publicación del segundo destino.
- §7.3: usar un número de turno de prueba compatible con el límite de ocho caracteres; PRUEBA-CORTE supera ese contrato. La lista de IPs debe distinguir IP del cliente de la del proxy y considerar que POS/TV pueden compartir salida de red con el operador.
- No aprobar por documentación la duración de recuperación ni que todas las TVs mantienen reproducción: eso sigue sujeto a ensayos y B1 físico.

## Siguiente entrega solicitada

Corregir R3-B1-01/02 e INV-01 y presentar nuevo SHA. Revisar el diseño para B3-R2-01/02/03, con DDL mínimo ejecutable y pruebas aisladas de los protocolos cuando se autorice la implementación. Mantener B3 sin implementación de producto ni migración de producción hasta cerrar diseño y decisiones. La revisión puede avanzar con datos sintéticos; no hace falta pedir al propietario datos de producción para resolver estos hallazgos técnicos.

Informe local para Claude: C:/Users/adcueto/OneDrive/Documents/ChatGPT/LUMIN-TV/coordinacion/15-qa-R3-y-diseno-B3-rev2-78306df.md. No publicado en GitHub.
