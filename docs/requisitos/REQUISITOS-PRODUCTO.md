# Requisitos de producto — LUMIN TV

Fecha: 2026-09-19 · Versión: 1.6 · Responsable: 00 — Coordinación y QA.

Último SHA revisado: `050cc2d090b58f4d1a7b1673c830111a347b3768`. No es una consulta en vivo a GitHub.

## Objetivo y alcance

Mejorar LUMIN TV existente como plataforma de anuncios, listas y turnos por sucursal. Conservar Roku y la integración POS; preparar la base comercial futura. Este catálogo documenta necesidades y criterios, **no declara implementado el producto ni aprueba todo el roadmap**.
Instrucciones actuales del propietario y documento común prevalecen sobre el brief histórico. B1/B2, revisión del diseño B3 y correcciones de la entrega B5a son el foco de QA; el nuevo panel está en propuesta y los demás alcances B4–B8 siguen planificados; suscripciones, portal del dueño, alta pública, web, nuevos giros y Android siguen diferidos. La implementación B3 requiere cerrar diseño y encargo. No se hacen cambios en LUMIA.

## Usuarios y límites

- Hoy: propietario/admin LUMIN, operadores de sucursal, TVs Roku e integración POS existente. El servidor usa sesiones; el flujo nuevo de correo aún no está implementado/verificado.
- Futuro: administrador de empresa, operador restringido, dispositivo con credencial propia y propietario de plataforma con sesión separada.
- LUMIN será el piloto persistente inicial. Empresas de prueba solo en entornos aislados. El servidor heredado no se presenta como multiempresa comercial.

## Fuentes y precedencia

- Conversación del propietario: preservar operación, navegación por secciones, correo por código, PostgreSQL, separación de SaaS futuro y exclusión de editor/plantillas.
- [Brief íntegro](../coordinacion/08-encargo-original.txt): requisitos amplios y propuestas comerciales históricas.
- [Plan por bloques](../coordinacion/10-diagnostico-y-plan-modernizacion.md): antecedentes B1–B8; las revisiones posteriores prevalecen en contradicciones (por ejemplo, medios permanecen locales en B3).
- [Coordinación vigente](../coordinacion/16-coordinacion-agentes.md) y [último QA](../qa/informes/25-qa-B3-rev7-RF26-050cc2d.md): alcance y limitaciones.
- Estado de implementación únicamente en el [semáforo](../coordinacion/18-semaforo.md); no duplicarlo en los requisitos.

## Exclusiones y propuestas aún no aprobadas

No desarrollar editor gráfico/plantillas ni generación de anuncios como parte de esta modernización. La configuración de layouts/turnos no equivale a un editor tipo Canva. No reconstruir el POS para vender TV a otro giro. IA se registra solo como exploración. No anunciar compatibilidad universal, ventas atribuidas ni un SLA sin evidencia. Los precios/complementos del brief son propuestas; no son tarifas vigentes ni autorización de cobro. El nombre comercial y su disponibilidad requieren comprobación antes de elegirlos.

## Catálogo trazable

Cada requisito tiene aceptación observable y tareas. Los criterios amplios deben concretarse en el encargo de implementación antes de programar; no inventar contratos, umbrales o decisiones de negocio.

<a id="rf-01"></a>

### RF-01 — Operación existente

**Requisito:** Preservar Roku, playlists, turnos y URLs de medios instaladas.

**Aceptación:** Contratos con fixtures de base/candidato; transición versionada cuando haya cambios; Roku físico identificado.

**Fase:** B1–B8.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-004](../coordinacion/17-backlog-maestro.md#bl-004), [BL-005](../coordinacion/17-backlog-maestro.md#bl-005), [BL-015](../coordinacion/17-backlog-maestro.md#bl-015), [BL-023](../coordinacion/17-backlog-maestro.md#bl-023), [BL-027](../coordinacion/17-backlog-maestro.md#bl-027), [BL-031](../coordinacion/17-backlog-maestro.md#bl-031), [BL-046](../coordinacion/17-backlog-maestro.md#bl-046), [BL-047](../coordinacion/17-backlog-maestro.md#bl-047), [BL-049](../coordinacion/17-backlog-maestro.md#bl-049), [BL-050](../coordinacion/17-backlog-maestro.md#bl-050), [BL-081](../coordinacion/17-backlog-maestro.md#bl-081).

<a id="rf-02"></a>

### RF-02 — Reproductor

**Requisito:** Recuperar reproducción tras pérdida de internet, fallo de servidor y archivos dañados.

**Aceptación:** No queda cargando indefinidamente; respaldo visible cuando no hay medio local; reconexión sin reiniciar; matrices F1–F21 según entrega.

**Fase:** B1.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-002](../coordinacion/17-backlog-maestro.md#bl-002), [BL-004](../coordinacion/17-backlog-maestro.md#bl-004), [BL-005](../coordinacion/17-backlog-maestro.md#bl-005), [BL-051](../coordinacion/17-backlog-maestro.md#bl-051), [BL-081](../coordinacion/17-backlog-maestro.md#bl-081).

<a id="rf-03"></a>

### RF-03 — Caché

**Requisito:** Caché limitada con desalojo, temporales, descarga completa y reintentos acotados.

**Aceptación:** Probar tamaño conocido/desconocido, suma sobre presupuesto, lista estable/cambiada, descarga activa y cuarentena; no prometer persistencia tras reinicio sin evidencia.

**Fase:** B1.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-002](../coordinacion/17-backlog-maestro.md#bl-002), [BL-003](../coordinacion/17-backlog-maestro.md#bl-003), [BL-004](../coordinacion/17-backlog-maestro.md#bl-004), [BL-005](../coordinacion/17-backlog-maestro.md#bl-005), [BL-007](../coordinacion/17-backlog-maestro.md#bl-007), [BL-051](../coordinacion/17-backlog-maestro.md#bl-051).

<a id="rf-04"></a>

### RF-04 — Sucursal/pantallas

**Requisito:** Varias sucursales y pantallas con promos/precios propios, orientación y asignación de listas.

**Aceptación:** Operar dos sucursales sin mezclar contenido; ID de dispositivo preservado; número visible y desfase diferenciados.

**Fase:** B3/B5/B6.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-012](../coordinacion/17-backlog-maestro.md#bl-012), [BL-017](../coordinacion/17-backlog-maestro.md#bl-017), [BL-023](../coordinacion/17-backlog-maestro.md#bl-023), [BL-032](../coordinacion/17-backlog-maestro.md#bl-032), [BL-038](../coordinacion/17-backlog-maestro.md#bl-038), [BL-076](../coordinacion/17-backlog-maestro.md#bl-076), [BL-077](../coordinacion/17-backlog-maestro.md#bl-077), [BL-078](../coordinacion/17-backlog-maestro.md#bl-078), [BL-079](../coordinacion/17-backlog-maestro.md#bl-079), [BL-083](../coordinacion/17-backlog-maestro.md#bl-083), [BL-084](../coordinacion/17-backlog-maestro.md#bl-084).

<a id="rf-05"></a>

### RF-05 — Biblioteca

**Requisito:** Subir y administrar imágenes/videos preparados externamente, con vista previa, duración y validación.

**Aceptación:** Archivo inválido rechazado con motivo; renombrar/eliminar mantiene integridad de listas; consumo real; tratamiento explícito de contenido en uso.

**Fase:** B5/B6.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-014](../coordinacion/17-backlog-maestro.md#bl-014), [BL-035](../coordinacion/17-backlog-maestro.md#bl-035), [BL-036](../coordinacion/17-backlog-maestro.md#bl-036), [BL-039](../coordinacion/17-backlog-maestro.md#bl-039), [BL-053](../coordinacion/17-backlog-maestro.md#bl-053).

<a id="rf-06"></a>

### RF-06 — Listas

**Requisito:** Crear, ordenar, renombrar y asignar múltiples listas; distinguir herencia de sucursal y asignación de pantalla.

**Aceptación:** Orden y selección reproducibles; heredada/asignada claramente visibles; eliminar lista no borra medios.

**Fase:** B3/B5/B6.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-023](../coordinacion/17-backlog-maestro.md#bl-023), [BL-032](../coordinacion/17-backlog-maestro.md#bl-032), [BL-039](../coordinacion/17-backlog-maestro.md#bl-039), [BL-076](../coordinacion/17-backlog-maestro.md#bl-076), [BL-077](../coordinacion/17-backlog-maestro.md#bl-077), [BL-078](../coordinacion/17-backlog-maestro.md#bl-078), [BL-079](../coordinacion/17-backlog-maestro.md#bl-079).

<a id="rf-07"></a>

### RF-07 — Programación

**Requisito:** Programar contenido por fechas, días, horas, vencimiento, prioridad y destino.

**Aceptación:** Regla de conflictos escrita; pruebas en medianoche, zonas horarias, solapamientos y respaldo; recepción confirmada por dispositivo.

**Fase:** B7.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-041](../coordinacion/17-backlog-maestro.md#bl-041), [BL-043](../coordinacion/17-backlog-maestro.md#bl-043), [BL-044](../coordinacion/17-backlog-maestro.md#bl-044).

<a id="rf-08"></a>

### RF-08 — Mensajes

**Requisito:** Conservar franja inferior/cintillo y gestionar mensajes por sucursal/destino.

**Aceptación:** Configurar texto y velocidad; convivencia con anuncios/turnos. Banner/pantalla completa y prioridades del brief se refinan antes de ampliar.

**Fase:** B5/B6/B7.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-040](../coordinacion/17-backlog-maestro.md#bl-040), [BL-044](../coordinacion/17-backlog-maestro.md#bl-044).

<a id="rf-09"></a>

### RF-09 — Turnos actuales

**Requisito:** Mostrar llamado, estación y cola compatible con el POS sin interrumpir indebidamente publicidad.

**Aceptación:** Regresión POST/PUT, folio, estación, expiración y fin del llamado; volver a anuncios; espera solo con cálculo/contrato definido.

**Fase:** B1/B5/B6.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-004](../coordinacion/17-backlog-maestro.md#bl-004), [BL-005](../coordinacion/17-backlog-maestro.md#bl-005), [BL-015](../coordinacion/17-backlog-maestro.md#bl-015), [BL-027](../coordinacion/17-backlog-maestro.md#bl-027), [BL-033](../coordinacion/17-backlog-maestro.md#bl-033), [BL-040](../coordinacion/17-backlog-maestro.md#bl-040), [BL-051](../coordinacion/17-backlog-maestro.md#bl-051), [BL-064](../coordinacion/17-backlog-maestro.md#bl-064).

<a id="rf-10"></a>

### RF-10 — Integración POS

**Requisito:** Mantener TV usable sin POS y una integración opcional por sucursal.

**Aceptación:** Autenticación, pertenencia, idempotencia, reintentos y auditoría; no modificar LUMIA en este encargo.

**Fase:** B5/B8; comercial futuro.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-027](../coordinacion/17-backlog-maestro.md#bl-027), [BL-033](../coordinacion/17-backlog-maestro.md#bl-033), [BL-040](../coordinacion/17-backlog-maestro.md#bl-040), [BL-065](../coordinacion/17-backlog-maestro.md#bl-065).

<a id="rf-11"></a>

### RF-11 — Estado/estadísticas

**Requisito:** Distinguir conexión, sincronización, descarga y reproducción confirmada.

**Aceptación:** HEAD/404 no cuentan descarga; eventos repetidos no duplican; conexión no implica reproducción; ninguna equivalencia con personas o ventas.

**Fase:** B2/B5/B8.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-006](../coordinacion/17-backlog-maestro.md#bl-006), [BL-007](../coordinacion/17-backlog-maestro.md#bl-007), [BL-032](../coordinacion/17-backlog-maestro.md#bl-032), [BL-034](../coordinacion/17-backlog-maestro.md#bl-034), [BL-038](../coordinacion/17-backlog-maestro.md#bl-038), [BL-044](../coordinacion/17-backlog-maestro.md#bl-044), [BL-046](../coordinacion/17-backlog-maestro.md#bl-046), [BL-080](../coordinacion/17-backlog-maestro.md#bl-080), [BL-081](../coordinacion/17-backlog-maestro.md#bl-081).

<a id="rf-12"></a>

### RF-12 — Identidad

**Requisito:** Inicio de sesión, verificación de correo mediante código e invitaciones.

**Aceptación:** Código con propósito, expiración, único uso, límites concurrentes y recuperación; invitación/admin en B4, alta pública diferida; correo real solo en entorno autorizado.

**Fase:** B4; alta pública futura.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-010](../coordinacion/17-backlog-maestro.md#bl-010), [BL-013](../coordinacion/17-backlog-maestro.md#bl-013), [BL-028](../coordinacion/17-backlog-maestro.md#bl-028), [BL-030](../coordinacion/17-backlog-maestro.md#bl-030), [BL-041](../coordinacion/17-backlog-maestro.md#bl-041), [BL-052](../coordinacion/17-backlog-maestro.md#bl-052), [BL-057](../coordinacion/17-backlog-maestro.md#bl-057), [BL-074](../coordinacion/17-backlog-maestro.md#bl-074), [BL-080](../coordinacion/17-backlog-maestro.md#bl-080).

<a id="rf-13"></a>

### RF-13 — Permisos

**Requisito:** Admin de empresa y operador limitado a sucursales/acciones concedidas.

**Aceptación:** Lista vacía no concede todo; ID fuera de alcance rechazado; traslado valida origen y destino; sin credencial fija de bootstrap.

**Fase:** B4.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-012](../coordinacion/17-backlog-maestro.md#bl-012), [BL-018](../coordinacion/17-backlog-maestro.md#bl-018), [BL-029](../coordinacion/17-backlog-maestro.md#bl-029), [BL-030](../coordinacion/17-backlog-maestro.md#bl-030), [BL-041](../coordinacion/17-backlog-maestro.md#bl-041).

<a id="rf-14"></a>

### RF-14 — Panel

**Requisito:** Panel con navegación lateral, secciones/rutas y selector global de sucursal.

**Aceptación:** Once secciones actuales: Inicio, Pantallas, Biblioteca, Listas, Programación, Mensajes, Turnos, Sucursales, Integraciones, Usuarios y Configuración; no mostrar módulos futuros como funcionales.

**Fase:** B6.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-037](../coordinacion/17-backlog-maestro.md#bl-037), [BL-038](../coordinacion/17-backlog-maestro.md#bl-038), [BL-039](../coordinacion/17-backlog-maestro.md#bl-039), [BL-040](../coordinacion/17-backlog-maestro.md#bl-040), [BL-041](../coordinacion/17-backlog-maestro.md#bl-041), [BL-042](../coordinacion/17-backlog-maestro.md#bl-042), [BL-082](../coordinacion/17-backlog-maestro.md#bl-082).

<a id="rf-15"></a>

### RF-15 — Dispositivo

**Requisito:** Vinculación temporal y credencial propia renovable/revocable por pantalla.

**Aceptación:** Código expirado/reutilizado rechazado; token sin acceso admin; URLs/medios y ámbito de empresa protegidos; transición de flota compatible.

**Fase:** B8.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-005](../coordinacion/17-backlog-maestro.md#bl-005), [BL-036](../coordinacion/17-backlog-maestro.md#bl-036), [BL-045](../coordinacion/17-backlog-maestro.md#bl-045), [BL-046](../coordinacion/17-backlog-maestro.md#bl-046), [BL-047](../coordinacion/17-backlog-maestro.md#bl-047), [BL-051](../coordinacion/17-backlog-maestro.md#bl-051), [BL-059](../coordinacion/17-backlog-maestro.md#bl-059), [BL-068](../coordinacion/17-backlog-maestro.md#bl-068).

<a id="rf-16"></a>

### RF-16 — Empresas

**Requisito:** Preparar empresa → sucursal → pantalla, aislando datos, medios y procesos.

**Aceptación:** Dos empresas sintéticas con claves iguales; filtros, RLS y FKs probados; segunda empresa operativa bloqueada hasta cerrar contratos de medios/dispositivos.

**Fase:** B3/B8.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-011](../coordinacion/17-backlog-maestro.md#bl-011), [BL-016](../coordinacion/17-backlog-maestro.md#bl-016), [BL-022](../coordinacion/17-backlog-maestro.md#bl-022), [BL-025](../coordinacion/17-backlog-maestro.md#bl-025), [BL-036](../coordinacion/17-backlog-maestro.md#bl-036), [BL-045](../coordinacion/17-backlog-maestro.md#bl-045), [BL-047](../coordinacion/17-backlog-maestro.md#bl-047), [BL-056](../coordinacion/17-backlog-maestro.md#bl-056), [BL-057](../coordinacion/17-backlog-maestro.md#bl-057), [BL-070](../coordinacion/17-backlog-maestro.md#bl-070).

<a id="rf-17"></a>

### RF-17 — Portal del dueño

**Requisito:** Portal separado para empresas, planes, pagos, límites, incidencias y soporte.

**Aceptación:** Sesión de empresa no sirve en plataforma; soporte y suspensión auditados; excepciones explícitas, sin trato especial oculto a LUMIN.

**Fase:** Comercial diferido.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-056](../coordinacion/17-backlog-maestro.md#bl-056), [BL-070](../coordinacion/17-backlog-maestro.md#bl-070).

<a id="rf-18"></a>

### RF-18 — Suscripciones

**Requisito:** Catálogo versionado, planes, complementos, cuotas, consumo y estados de servicio.

**Aceptación:** Validación concurrente de cuotas; pago separado de acceso; no borrar contenido por reducción; regularización accesible; dependencias de módulos explicadas.

**Fase:** Comercial diferido.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-055](../coordinacion/17-backlog-maestro.md#bl-055), [BL-057](../coordinacion/17-backlog-maestro.md#bl-057), [BL-058](../coordinacion/17-backlog-maestro.md#bl-058), [BL-059](../coordinacion/17-backlog-maestro.md#bl-059), [BL-061](../coordinacion/17-backlog-maestro.md#bl-061), [BL-065](../coordinacion/17-backlog-maestro.md#bl-065), [BL-070](../coordinacion/17-backlog-maestro.md#bl-070).

<a id="rf-19"></a>

### RF-19 — Cobros

**Requisito:** Definir forma de cobro, precios, impuestos, vigencia, cancelación y reactivación.

**Aceptación:** Modelo de costos aprobado; manual/recurrente decidido; monto y fecha antes de confirmar; webhooks idempotentes si se elige pasarela; sin cargos sin aceptación.

**Fase:** Comercial diferido.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-054](../coordinacion/17-backlog-maestro.md#bl-054), [BL-055](../coordinacion/17-backlog-maestro.md#bl-055), [BL-060](../coordinacion/17-backlog-maestro.md#bl-060), [BL-061](../coordinacion/17-backlog-maestro.md#bl-061), [BL-063](../coordinacion/17-backlog-maestro.md#bl-063), [BL-069](../coordinacion/17-backlog-maestro.md#bl-069), [BL-070](../coordinacion/17-backlog-maestro.md#bl-070).

<a id="rf-20"></a>

### RF-20 — Web comercial

**Requisito:** Web con funciones, giros, compatibilidad, planes, contacto/demo y acceso.

**Aceptación:** Catálogo único con backend; formularios reales; próximos módulos rotulados; sin testimonios ficticios; textos legales revisados antes de publicación.

**Fase:** Comercial diferido.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-062](../coordinacion/17-backlog-maestro.md#bl-062), [BL-063](../coordinacion/17-backlog-maestro.md#bl-063), [BL-069](../coordinacion/17-backlog-maestro.md#bl-069), [BL-070](../coordinacion/17-backlog-maestro.md#bl-070).

<a id="rf-21"></a>

### RF-21 — Turnos ampliados

**Requisito:** Motor configurable por giro con folios, cola, estados, áreas y privacidad.

**Aceptación:** Crear/llamar/repetir/atender/cancelar; reinicio/prefijos configurados; folio sin nombre permitido; voz opcional definida; espera no inventada.

**Fase:** Expansión diferida.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-064](../coordinacion/17-backlog-maestro.md#bl-064).

<a id="rf-22"></a>

### RF-22 — Reconocimientos

**Requisito:** Módulo de empleado del mes con selección manual e historial.

**Aceptación:** Programación y destinos; sin datos privados; automatización POS solo con contrato y aprobación; una imagen normal no requiere el módulo.

**Fase:** Expansión diferida.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-066](../coordinacion/17-backlog-maestro.md#bl-066).

<a id="rf-23"></a>

### RF-23 — Menú digital

**Requisito:** Productos, categorías, precios, disponibilidad y horarios de menú.

**Aceptación:** Publicación consistente por sucursal; integración automática solo con contrato; una imagen normal de menú sigue siendo contenido común.

**Fase:** Expansión diferida.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-067](../coordinacion/17-backlog-maestro.md#bl-067).

<a id="rf-24"></a>

### RF-24 — Android

**Requisito:** Evaluar/desarrollar Android TV/Google TV sobre contratos comunes.

**Aceptación:** Equipo físico, codecs, orientación, control remoto, offline, distribución y actualización verificados; no implica Tizen/webOS.

**Fase:** Expansión diferida.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-068](../coordinacion/17-backlog-maestro.md#bl-068).

<a id="rnf-01"></a>

### RNF-01 — Persistencia

**Requisito:** Migrar JSON a PostgreSQL con IDs, relaciones y semántica conservados.

**Aceptación:** Migración idempotente; diferencias permitidas enumeradas; comparación de contratos, copia sintética y luego anonimizada autorizada; decisiones D1/D2 aplicadas explícitamente.

**Fase:** B3.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-016](../coordinacion/17-backlog-maestro.md#bl-016), [BL-017](../coordinacion/17-backlog-maestro.md#bl-017), [BL-018](../coordinacion/17-backlog-maestro.md#bl-018), [BL-020](../coordinacion/17-backlog-maestro.md#bl-020), [BL-021](../coordinacion/17-backlog-maestro.md#bl-021), [BL-022](../coordinacion/17-backlog-maestro.md#bl-022), [BL-023](../coordinacion/17-backlog-maestro.md#bl-023), [BL-026](../coordinacion/17-backlog-maestro.md#bl-026).

<a id="rnf-02"></a>

### RNF-02 — Recuperación

**Requisito:** Espejo/exportación y rollback consistentes, sin reactivar sesiones revocadas.

**Aceptación:** Ensayos de commits fuera de orden, caída entre pasos y disco lleno; snapshot coherente; revocaciones conservadas o logout total definido; recuperación cronometrada.

**Fase:** B3.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-009](../coordinacion/17-backlog-maestro.md#bl-009), [BL-010](../coordinacion/17-backlog-maestro.md#bl-010), [BL-013](../coordinacion/17-backlog-maestro.md#bl-013), [BL-016](../coordinacion/17-backlog-maestro.md#bl-016), [BL-019](../coordinacion/17-backlog-maestro.md#bl-019), [BL-021](../coordinacion/17-backlog-maestro.md#bl-021), [BL-024](../coordinacion/17-backlog-maestro.md#bl-024), [BL-026](../coordinacion/17-backlog-maestro.md#bl-026), [BL-074](../coordinacion/17-backlog-maestro.md#bl-074).

<a id="rnf-03"></a>

### RNF-03 — Arquitectura

**Requisito:** Modernización incremental: Python, PostgreSQL, API modular y panel React/TypeScript propuestos.

**Aceptación:** ADRs y dependencias revisadas; B3 conserva servidor/medios, B5 define FastAPI/entrega de medios; S3 según evidencia; sin reescritura integral ni stack aprobado por existencia de documento.

**Fase:** B3–B6.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-022](../coordinacion/17-backlog-maestro.md#bl-022), [BL-031](../coordinacion/17-backlog-maestro.md#bl-031), [BL-036](../coordinacion/17-backlog-maestro.md#bl-036), [BL-053](../coordinacion/17-backlog-maestro.md#bl-053), [BL-072](../coordinacion/17-backlog-maestro.md#bl-072).

<a id="rnf-04"></a>

### RNF-04 — Concurrencia

**Requisito:** Evitar pérdidas de sesiones, altas, marcas de giro y solicitudes simultáneas.

**Aceptación:** Suite original contra SHA exacto; 120 respuestas contabilizadas y sin excepciones; nueva persistencia conserva garantías con pruebas concurrentes.

**Fase:** B2/B3.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-006](../coordinacion/17-backlog-maestro.md#bl-006), [BL-008](../coordinacion/17-backlog-maestro.md#bl-008), [BL-009](../coordinacion/17-backlog-maestro.md#bl-009), [BL-024](../coordinacion/17-backlog-maestro.md#bl-024), [BL-025](../coordinacion/17-backlog-maestro.md#bl-025), [BL-053](../coordinacion/17-backlog-maestro.md#bl-053).

<a id="rnf-05"></a>

### RNF-05 — Seguridad

**Requisito:** Aislamiento efectivo, secretos protegidos y permisos mínimos.

**Aceptación:** Pruebas negativas por tabla/API/archivo/job; roles RLS ejecutables; sin tokens en informes; auth por dispositivo cuando se habilite multiempresa real.

**Fase:** B3/B4/B8.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-010](../coordinacion/17-backlog-maestro.md#bl-010), [BL-011](../coordinacion/17-backlog-maestro.md#bl-011), [BL-013](../coordinacion/17-backlog-maestro.md#bl-013), [BL-016](../coordinacion/17-backlog-maestro.md#bl-016), [BL-019](../coordinacion/17-backlog-maestro.md#bl-019), [BL-020](../coordinacion/17-backlog-maestro.md#bl-020), [BL-022](../coordinacion/17-backlog-maestro.md#bl-022), [BL-025](../coordinacion/17-backlog-maestro.md#bl-025), [BL-029](../coordinacion/17-backlog-maestro.md#bl-029), [BL-030](../coordinacion/17-backlog-maestro.md#bl-030), [BL-036](../coordinacion/17-backlog-maestro.md#bl-036), [BL-045](../coordinacion/17-backlog-maestro.md#bl-045), [BL-047](../coordinacion/17-backlog-maestro.md#bl-047), [BL-072](../coordinacion/17-backlog-maestro.md#bl-072), [BL-074](../coordinacion/17-backlog-maestro.md#bl-074), [BL-075](../coordinacion/17-backlog-maestro.md#bl-075).

<a id="rnf-06"></a>

### RNF-06 — Procesamiento

**Requisito:** Procesar medios sin bloquear panel mediante trabajos recuperables cuando se implemente B5.

**Aceptación:** Digest/versión/destino correctos; posesión y publicación consistentes; reintentos/cancelación incluidos en_curso; caída entre DB y archivo recuperable.

**Fase:** B5.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-014](../coordinacion/17-backlog-maestro.md#bl-014), [BL-035](../coordinacion/17-backlog-maestro.md#bl-035).

<a id="rnf-07"></a>

### RNF-07 — Observabilidad

**Requisito:** Bitácora con rotación, errores útiles y métricas veraces.

**Aceptación:** Error sintético queda registrado sin secretos; conexiones/errores rastreables; alarmas y retención definidos antes de operar nueva infraestructura.

**Fase:** B2/B5/Release.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-006](../coordinacion/17-backlog-maestro.md#bl-006), [BL-034](../coordinacion/17-backlog-maestro.md#bl-034), [BL-048](../coordinacion/17-backlog-maestro.md#bl-048), [BL-050](../coordinacion/17-backlog-maestro.md#bl-050), [BL-053](../coordinacion/17-backlog-maestro.md#bl-053).

<a id="rnf-08"></a>

### RNF-08 — UX y accesibilidad

**Requisito:** Interfaz responsive, consistente, accesible y conectada a datos reales.

**Aceptación:** Carga/vacío/error/sin permiso; teclado/foco/etiquetas/contraste; verificar 360/768/1440 px; mocks identificados solo en propuestas.

**Fase:** B6.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-037](../coordinacion/17-backlog-maestro.md#bl-037), [BL-038](../coordinacion/17-backlog-maestro.md#bl-038), [BL-039](../coordinacion/17-backlog-maestro.md#bl-039), [BL-042](../coordinacion/17-backlog-maestro.md#bl-042), [BL-082](../coordinacion/17-backlog-maestro.md#bl-082).

<a id="rnf-09"></a>

### RNF-09 — Release

**Requisito:** Respaldos restaurables, configuración reproducible y release autorizado.

**Aceptación:** Restaurar DB y medios en limpio; HTTPS/roles/secretos/servicio; candidato y plan de reversión identificados; ensayo previo y autorización de producción.

**Fase:** B3/Release.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-015](../coordinacion/17-backlog-maestro.md#bl-015), [BL-026](../coordinacion/17-backlog-maestro.md#bl-026), [BL-048](../coordinacion/17-backlog-maestro.md#bl-048), [BL-049](../coordinacion/17-backlog-maestro.md#bl-049), [BL-050](../coordinacion/17-backlog-maestro.md#bl-050), [BL-070](../coordinacion/17-backlog-maestro.md#bl-070).

<a id="rnf-10"></a>

### RNF-10 — QA y coordinación

**Requisito:** Trazabilidad requisitos → tareas → SHA → evidencia → dictamen.

**Aceptación:** Fuente de estado única; evidencia estática/ejecutada/aportada distinguida; CI por SHA o alternativa acordada; no verde global por compilación.

**Fase:** Transversal.

**Origen:** Conversación del propietario y docs/coordinacion/08-encargo-original.txt.

**Tareas:** [BL-001](../coordinacion/17-backlog-maestro.md#bl-001), [BL-008](../coordinacion/17-backlog-maestro.md#bl-008), [BL-012](../coordinacion/17-backlog-maestro.md#bl-012), [BL-016](../coordinacion/17-backlog-maestro.md#bl-016), [BL-021](../coordinacion/17-backlog-maestro.md#bl-021), [BL-027](../coordinacion/17-backlog-maestro.md#bl-027), [BL-042](../coordinacion/17-backlog-maestro.md#bl-042), [BL-050](../coordinacion/17-backlog-maestro.md#bl-050), [BL-070](../coordinacion/17-backlog-maestro.md#bl-070), [BL-072](../coordinacion/17-backlog-maestro.md#bl-072), [BL-073](../coordinacion/17-backlog-maestro.md#bl-073), [BL-075](../coordinacion/17-backlog-maestro.md#bl-075).

<a id="rf-25"></a>

### RF-25 — Exploración IA

**Requisito:** Evaluar usos de IA que ayuden a operar o diagnosticar sin construir un editor de anuncios.

**Aceptación:** Caso de uso, datos necesarios, costo, privacidad y comparación sin IA; decidir adoptar o descartar. No implica funcionalidad aprobada.

**Fase:** Exploración diferida.

**Origen:** Conversación del propietario: investigar ventajas de IA, editor/plantillas excluidos.

**Tareas:** [BL-071](../coordinacion/17-backlog-maestro.md#bl-071).

<a id="rf-26"></a>

### RF-26 — Playlists por destino y grupos

**Requisito:** Elegir desde cada playlist una TV, varias TVs o grupos nombrados donde mostrarla; administrar miembros y consultar la asignación efectiva.

**Aceptación:** Selección individual/múltiple/grupal sin duplicados; conflictos y membresía explícitos; permisos por empresa/sucursal; offline y recepción por TV; conservar turnos/cintillo. Detalle y decisiones en docs/requisitos/RF-26-playlists-por-tv-y-grupo.md.

**Fase:** Impacto en diseño B3; implementación propuesta B5/B6.

**Origen:** Petición expresa de Adrián del 2026-09-19; docs/requisitos/RF-26-playlists-por-tv-y-grupo.md.

**Tareas:** [BL-076](../coordinacion/17-backlog-maestro.md#bl-076), [BL-077](../coordinacion/17-backlog-maestro.md#bl-077), [BL-078](../coordinacion/17-backlog-maestro.md#bl-078), [BL-079](../coordinacion/17-backlog-maestro.md#bl-079), [BL-083](../coordinacion/17-backlog-maestro.md#bl-083), [BL-084](../coordinacion/17-backlog-maestro.md#bl-084).

## Reglas para cambiar requisitos

Conservar IDs. Añadir o revisar un requisito con fuente, motivo, impacto en contratos/datos y tareas afectadas; actualizar la fuente backlog.json y regenerar. Un cambio de aceptación no cierra retroactivamente un hallazgo. Las decisiones del propietario deben quedar identificadas y no deducirse de que la propuesta esté escrita.

## Pendientes de definición

Tiempos/umbrales físicos, formatos y tamaños, capacidad/costos, entorno de correo, números/permisos D1/D2, política de recuperación y ventana de corte. Futuro: precios/impuestos, cobro manual o pasarela, gracia de pago, cancelaciones y tolerancia offline. Ver las tareas de decisiones y comerciales; ninguna se considera resuelta por este catálogo.
