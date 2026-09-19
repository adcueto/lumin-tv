# Plan maestro y tablero inicial

Flujo: Pendiente → En desarrollo → Entregado a QA → Correcciones o Aprobado.
Un bloqueo es un atributo adicional, no una aprobación. Actualización tras clonado: LTV-000 completada; LTV-002 tiene inspección y caracterización inicial completadas con defectos abiertos (ver 09), sin aprobación de software. LTV-001 pasa a Pendiente de correcciones acotadas según 03. Las demás tareas están Pendientes. Las fases posteriores expresan planificación; no autorizan despliegues ni cambios en LUMIA.

| ID / prioridad | Responsable | Alcance | Dependencias | Aceptación |
|---|---|---|---|---|
| LTV-000 / P0 | Codex, por indicación del propietario | Clonar fuente existente | Completada | main en ea610d6; ruta confirmada y línea base limpia |
| LTV-001 / P0 | Claude | Corregir permisos de sucursal y preparar decisiones de seguridad | LTV-000, auditoría inicial 09 | Entrega según 03; rechazo de permisos inválidos y traslado no autorizado |
| LTV-002 / P0 | Codex | Auditoría inicial y línea base de regresión | LTV-001 | SHA/estado identificados, hallazgos reproducibles y matriz de evidencia |
| LTV-003 / P0 | Claude + Codex | Acordar arquitectura y contratos | LTV-002 | Contratos sustentados en código, transición Roku, decisiones registradas |
| LTV-004 / P0 | Claude | Multiempresa, autenticación y permisos | LTV-003 | Pruebas negativas API/archivos/dispositivos/jobs; soporte auditado |
| LTV-005 / P1 | Claude | Catálogo, suscripciones, cuotas, complementos | LTV-004 | Cuotas concurrentes, dependencias y acceso separados del pago; sin cobros públicos |
| LTV-006A / P1 | Antigravity | Propuesta visual y mapa de estados | Brief; acceso necesario solo para inventario real | Entrega según 04; propuesta claramente identificada |
| LTV-006B / P1 | Antigravity | Panel conectado y operación existente | LTV-003, 004, 005, 006A | Datos reales, permisos, sucursales y errores verificados |
| LTV-007 / P1 | Claude; UI Antigravity | Turnos comunes por giro | LTV-004, 006B | Estados válidos, folios opcionales, publicidad reanudada tras llamados |
| LTV-008 / P1 | Claude | Conector LUMIA por sucursal | LTV-003, 005, 007; BLK-002 resuelto | Mapeo seguro, autenticación, idempotencia, auditoría y reintentos |
| LTV-009 / P2 | Claude; UI Antigravity | Reconocimientos manuales y menú digital | LTV-005, 006B | Permisos, horarios e historial; sin datos privados ni automatismos sin contrato |
| LTV-010 / P1 | Claude | Android TV/Google TV | LTV-003, 004; contratos de reproducción | Matriz física y regresión Roku; vinculación, offline y recuperación probados |
| LTV-011 / P2 | Antigravity; API Claude | Web comercial conectada | LTV-005; disponibilidad real de módulos | Catálogo único, formularios reales, compatibilidad exacta; publicación pendiente del propietario |
| LTV-012 / P0 lanzamiento | Codex + propietario | Piloto LUMIN y evaluación de salida | Entregas pertinentes aprobadas | Matriz completa, limitaciones conocidas, migración y recuperación verificadas; autorización del propietario |

## Secuencia y trabajo simultáneo

Fuente recuperada. Priorizar defectos de permisos antes del SaaS. Claude corrige el bloque acotado de 03; Antigravity prepara la propuesta visual de 04. La implementación simultánea requiere ramas/worktrees separados, base común, propiedad de archivos y contratos acordados. La propuesta histórica FastAPI/Vue/SQLite debe reevaluarse frente a multiempresa; no se considera arquitectura aprobada.

## Condiciones de lanzamiento

Aislamiento, permisos y seguridad son obligatorios en todos los planes. CI verde o compilación no sustituyen QA de comportamiento. No anunciar Android, integraciones ni métricas sin evidencia. LUMIN será la única empresa piloto persistente, configurada como una empresa normal. Empresas de prueba solo en entornos aislados.
