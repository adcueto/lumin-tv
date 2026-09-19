# QA 24 — B3 revisión 6, RF-26 y panel revisión 3

PARA: 01 — LUMIN TV · Desarrollo  
DE: 00 — LUMIN TV · Coordinación y QA  
BLOQUE: a0583df · respuesta al informe 23  
ESTADO: B3-R4-01 CERRADO EN SU RECORRIDO · CORRECCIONES NUEVAS DE ALCANCE Y RF-26

Fecha: 2026-09-19. Candidato `a0583df14a5367f2ac8b33c3c3711fb84373ba65`; base `3a1eaf92e7d1e51ee1e13d41356f4788760c6fbc`. Diez archivos cambiados, 352 inserciones y 52 eliminaciones. Este es un informe nuevo del candidato nuevo; no es reenvío del informe 23.

## Resultado

El caso anterior de B3-R4-01 queda cerrado: la conexión idle preexistente se termina, la petición admitida antes del corte ya no puede iniciar SQL después y no quedan sesiones del rol en la base ensayada. Se ejecutaron los 50 ensayos, incluidos esos recorridos.

Se conservan los cierres de permisos, recarga, publicación idempotente y ancho móvil. Se abren tres hallazgos del alcance nuevo: el selector del drenaje no filtra por base de datos; el DDL RF-26 permite cruces de sucursal; y el identificador de confirmación de entrega no distingue listas distintas con igual versión. B3 y RF-26 requieren esas correcciones antes de congelar el diseño. No se declara implementada ni aprobada la aplicación completa.

## Evidencia comprobada

| Control | Resultado | Naturaleza |
|---|---|---|
| Ensayos B3 locales | 50 pasan, 0 omitidos/fallos/errores; 78.14 s | Ejecutados por Codex, PG 16.15 y psycopg 3.2.3 en base desechable |
| Ancho del prototipo rev3 | 33/33 combinaciones correctas | Playwright Node local; once secciones, 360/390/1366 px; captura propia de Listas inspeccionada |
| CI run 35432801874 | Tres jobs success, SHA exacto | Logs consultados: 28 servidor, 50 PG, 42+21 Roku y compilación |
| Servidor/Roku respecto a QA 23 | Código, pruebas y manifest sin cambios | Identidad comprobada por diff y hashes; NO se repitieron localmente esas suites sin cambios |
| Drenaje entre bases | Otra base también pierde su sesión | Caso adicional real en cluster desechable |
| Relaciones RF-26 | Cuatro relaciones inválidas aceptadas por el DDL | SQL relevante extraído literalmente del diseño, ejecutado en esquema de QA; no producto |
| Identidad de entrega | Dos listas distintas tienen versión 1 | Confirmado en DDL; fallo del contrato de ACK analizado estáticamente, aún no hay implementación |

[CI](https://github.com/adcueto/lumin-tv/actions/runs/35432801874). [Evidencia y ejecutores](../evidencia/revision-r7-a0583df/README.md). [QA anterior](23-qa-B3-rev5-B5a-R2-3a1eaf9.md).

Fuentes extraídas con git archive sin cambiar checkout main. Se conservaron los borrados de iconos y documentos locales ajenos. PostgreSQL temporal detenido; no se accedió al VPS, no hubo datos reales, producto modificado, commit, push, despliegue ni migración.

## B3-R6-01 · P1 — El drenaje termina sesiones de otras bases del mismo cluster

Referencia: `servidor/ensayos_b3/test_ensayo_sesiones.py:97–101` y llamadas de `drenar_lumin_app`. El contrato afirma «Solo se toca el rol lumin_app de ESTA base», pero `_backends_app` filtra únicamente `usename` y PID. REVOKE CONNECT sí se ejecuta sobre la base objetivo, mientras pg_terminate_backend recibe también PIDs de cualquier otra base donde opere ese rol.

Reproducción: abrir como lumin_app una conexión a lumin_ensayo y otra a postgres, ambas dentro del cluster aislado. Drenar lumin_ensayo. Ambas conexiones fallan después con OperationalError: se terminaron las dos. El ensayo nuevo «otros roles» no cubre «mismo rol, otra base». Además, la otra base conserva permiso para reconectar, de modo que su actividad puede interferir con la comprobación de cero sesiones.

Corregir el selector y todas las verificaciones de drenaje para incluir la identidad de la base objetivo (por ejemplo datid/current_database en la conexión de control). Ensayo de aceptación: cerrar todas las sesiones objetivo y bloquear reconexión allí; mantener utilizable la sesión del mismo rol en otra base, además de espejo/migración. No basta corregir el comentario. Esto no reabre la lógica idle ya arreglada: es un defecto distinto en el alcance del cierre.

## RF26-QA-01 · P1 — Las relaciones nuevas no garantizan una misma sucursal

Referencias: diseño B3 §3.2b, líneas 329–350; documento 22 §2/§6. Se prometen grupos y listas por sucursal, sin reutilización entre sucursales. Sin embargo, las llaves nuevas solo relacionan id y empresa_id. Compartir empresa no garantiza compartir sucursal.

Al ejecutar el SQL exacto de las tablas relevantes se aceptaron y confirmaron:

- Grupo de sucursal A con una TV de B.
- Destino de lista de B hacia grupo de A.
- Destino de lista de A hacia TV de B.
- Destino directo hacia una TV pendiente con sucursal NULL.

Se usó el propietario del esquema para aislar y comprobar las restricciones; no se afirma haber explotado una API futura ni probado RLS completo. Una política estándar basada solo en empresa_id tampoco distingue A de B. El SQL original de pantalla/lista ya cuidaba estas invariantes; el camino nuevo lista_destino las permite evitar.

Corrección: transportar la sucursal y amarrar mediante llaves compuestas grupo, miembro, pantalla y lista, o aportar una restricción equivalente completa; prohibir destinos a pantallas pendientes/sin sucursal. Mantener validación de permisos de sucursal en API/repositorio además de integridad en base. Añadir ensayos de misma sucursal admitida, distinta sucursal rechazada, empresa distinta rechazada y pantalla pendiente rechazada. Incorporar este contrato al DDL de ensayos; los 50 actuales no cubren RF-26.

## RF26-QA-02 · P1 — El ACK de versión puede confirmar una lista equivocada

Referencias: documento 22 §5; B3 líneas 355–358. Cada lista inicia su propio contador version=1, pero la pantalla guarda solo tres enteros de versión y la TV enviaría únicamente lv=N. Esos valores no identifican qué lista ni qué asignación confirmó la TV.

Contraejemplo del contrato: una TV reproduce L1/v1; se asigna L2/v1. Antes de recibir L2, llega un latido de L1 con lv=1. La observación es indistinguible de una confirmación válida de L2/v1. Limpiar el estado al reasignar no evita que un latido retrasado lo vuelva a llenar. Volver de L1 a L2 y otra vez a L1 puede producir una ambigüedad similar aun añadiendo solo lista_id.

Esto es una objeción de diseño, no una prueba de comportamiento de software inexistente. El fixture confirma dos listas distintas con versión 1. Definir una identidad de entrega por pantalla: lista_id/version más una generación de asignación o publicación inequívoca, repetida en respuesta y ACK; aceptar solo la identidad vigente. Diferenciar guardada/enviada, recibida/aplicada y reproduciendo sin avanzar por mensajes tardíos. Ensayar L1/v1→L2/v1, L1→L2→L1, duplicados, reordenación y reconexión offline antes de fijar columnas/protocolo.

## Precisiones para la siguiente revisión

### Prioridad de grupos

Mayor prioridad y fecha más reciente mejora el contrato, pero no constituye un orden total: asignado_en usa DEFAULT now(), y dos destinos creados en la misma transacción pueden tener exactamente la misma fecha y prioridad. Añadir desempate estable o rechazar empates explícitamente y mostrar el criterio. No depender del orden accidental de filas.

La propuesta de grupos persistentes, resumen de TVs únicas y reemplazo explícito sí responde a lo pedido y se refleja en la maqueta. Falta cerrar la confirmación de cambios de miembros, publicación/edición concurrente y cómo se mantiene o sustituye pantalla.lista_id frente a lista_destino. No trasladar dos fuentes editables de asignación al producto sin contrato de transición.

### F22/F23 físicos

La división F23a/b/c y la exigencia del SHA mejoran el procedimiento. F23c coincide con la rama actual: al reconectar solo se descarta el comando viejo reproducir; recargar puede aplicarse. Se verificó por lectura, no por TV física.

Quedan dos detalles concretos: F22 pide build 62 pero conserva «app 5.2.61» en la salida esperada. F23b y F23a esperan una línea de log recargar que MainScene.brs no imprime. Definir una señal disponible o instrumentación de ensayo para acreditar comando recibido ANTES del corte/refresco. No considerar ejecutable ese punto de corte solo por describirlo. Un archivo git archive tampoco contiene .git: registrar SHA del paquete por manifiesto/hash o desde el checkout que lo produjo.

## Decisiones y alcance

El documento 22 introduce D8 (semántica persistente y alcance de grupos) y D9 (permiso para reemplazar una asignación directa). Se registran como propuestas pendientes, sin inventar aprobación. La solicitud de Adrián ya pide grupos: D8 debe concretar cómo funcionan, no reabrir si quiere grupos o eliminar ese requisito por simplificación. D1–D7 y los cuatro supuestos del panel mantienen su estado.

El anonimizador de D6 sigue pendiente y no forma parte de este candidato. Esta revisión no encarga ejecutarlo en el VPS ni obtener datos reales. Su preparación independiente puede coordinarse en su tarea existente sin confundirla con el cierre B3/RF-26.

## Siguiente entrega de 01

Responder por B3-R6-01, RF26-QA-01 y RF26-QA-02; añadir ensayos y resolver las precisiones de prioridad/procedimiento. Mantener los cierres anteriores y traer SHA/CI nuevos. B3-R4-01 queda cerrado para el caso idle/petición tardía; el diseño global sigue con correcciones. Informe 24 y tablero instalados localmente, sin envío automático a Claude ni cambio de producto.
