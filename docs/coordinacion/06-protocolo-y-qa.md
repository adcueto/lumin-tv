# Protocolo de entrega y QA

## Responsabilidades y cambios

Codex coordina y evalúa; puede preparar documentos, pruebas y herramientas de verificación. Claude lidera backend, datos, seguridad, suscripciones, integración y reproductores. Antigravity lidera frontend, UX y web comercial. No se han delegado tareas automáticamente.

Compartir documentos en la carpeta acordada. Cada responsable registra su entrega; Codex conserva el historial de resultados. Al implementar en paralelo, usar ramas/worktrees separados desde una base identificada y acordar propiedad de archivos. No sobrescribir ni restaurar cambios de otro agente. Operador de integración Git pendiente de acuerdo; este paquete no realiza commits, push, merges ni despliegues.

## Plantilla de entrega

- ID, responsable y alcance.
- Raíz física, rama, SHA base y SHA candidato; diff y archivos nuevos/modificados. Si no hay commit identificable, adjuntar manifiesto de hashes y marcar candidato no congelado.
- Comportamiento antes/después y compatibilidad.
- Contratos y decisiones aplicadas.
- Migraciones, impacto en datos y recuperación, o “no aplica” justificado.
- Entorno aislado, versiones, comandos, resultados y evidencia depurada.
- CI asociado al SHA; si no existe, declararlo y acordar controles equivalentes antes de aprobación.
- Limitaciones, pruebas pendientes y dispositivos físicos utilizados.

## Matriz inicial de pruebas

Esta matriz completa permanece pendiente de ejecución integral. Hay pruebas parciales locales sobre permisos, dispositivos, métricas y turnos en 09; no equivalen a aprobar estos criterios SaaS completos.

| ID | Prueba | Aceptación |
|---|---|---|
| QA-01 | Dos empresas efímeras, intercambiar IDs en lectura/escritura/listado | Sin datos ni mutaciones cruzadas |
| QA-02 | Medios/URLs, jobs y dispositivos de otra empresa | Acceso y ejecución rechazados sin fuga |
| QA-03 | Admin, operador asignado y dispositivo | Solo funciones y sucursales autorizadas; token de pantalla sin acceso admin |
| QA-04 | Modo soporte y bloqueos de seguridad | Activación explícita, alcance limitado y registro auditado |
| QA-05 | Altas simultáneas en límite de cuota | Nunca exceder cupo; transacción y error coherentes |
| QA-06 | Suscripción, reducción, suspensión y reactivación | Efectos acordados; contenido conservado; regularización disponible; público sin adeudos |
| QA-07 | GET/POST y reproducción Roku de línea base | Compatibilidad mantenida o transición versionada probada |
| QA-08 | Evento LUMIA duplicado, tardío, reintentado o fuera de ámbito | Un único efecto permitido; trazabilidad y rechazo de pertenencia incorrecta |
| QA-09 | Campañas solapadas, medianoche y zona horaria | Selección determinista según contrato; respaldo cuando corresponda |
| QA-10 | Desconexión, caché incompleta, token caducado y reconexión | Política offline respetada y recuperación sin bucle ni exposición |
| QA-11 | Telemetría repetida y reenvíos | Conteo sin duplicados; reproducciones nunca presentadas como personas |
| QA-12 | UI con datos reales, errores y cambio de sucursal | Sin mocks ocultos, datos previos incorrectos ni acciones sin permiso |
| QA-13 | Migración sobre copia sintética representativa | Preservación e integridad; recuperación ensayada sin datos reales alterados |
| QA-14 | Vinculación expirada/reutilizada y token revocado | Rechazo según contrato; ninguna credencial privilegiada en reproductor |
| QA-15 | Turnos repetidos/cancelados y fin del llamado | Estados válidos, privacidad por folio y publicidad reanudada |
| QA-16 | Roku y Android físicos, formatos y capacidades | Matriz modelo/OS/app/codec/orientación/resultado; simulador identificado aparte |
| QA-17 | Dependencias comerciales y catálogo | Turnos + Conector explícitos; mismo catálogo en panel, web y calculadora |

## Dictámenes

- NO PROBADO: falta evidencia, acceso, entorno o ejecución. No implica funcionamiento correcto.
- FALLÓ: caso ejecutado y resultado distinto del contrato; adjuntar reproducción.
- APROBADO: alcance y candidato exactos satisfacen criterios y evidencia exigida. No extiende aprobación a módulos, plataformas ni versiones no revisados.

Una entrega con defectos vuelve a Correcciones. Revisión estática y aprobación documental se etiquetan aparte. No aprobar software solo por compilación o afirmación del desarrollador.

## Plantilla de defecto

ID; severidad e impacto; tarea y SHA; entorno; precondiciones; pasos mínimos; esperado; observado; evidencia sin secretos; alcance; responsable; estado; versión corregida; resultado de repetición y regresión.

## Entregas y resultados actuales

No hay entregas de desarrollo recibidas ni aprobaciones de producto. Codex inspeccionó la base ea610d6 y ejecutó 9 casos de caracterización de funciones/handlers en memoria, sin sockets, con datos temporales sintéticos. Resultados y limitaciones en 09 y qa-resultados.json. Roku físico, Android, HTTP extremo a extremo, CI, ffmpeg, concurrencia, migraciones y producción NO PROBADOS.
