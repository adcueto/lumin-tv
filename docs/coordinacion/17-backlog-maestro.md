# Backlog maestro — LUMIN TV

Fecha: 2026-09-19 · Versión: 1.7 · Responsable: 00 — Coordinación y QA.

Último SHA revisado: `14f0bc51b5f7330a046d99ac870036747366c586`. No es una consulta en vivo a GitHub.

## Cómo usarlo

Fuente editable de tareas/requisitos: [backlog.json](backlog.json). Esta vista, los requisitos y el semáforo se generan con `python actualizar_tablero.py`; no editar sus tablas por separado. IDs BL-* son nuevos y no reutilizan los LTV-* del plan histórico. Cambiar estado requiere evidencia, SHA y responsable; no basta un reporte verbal de finalización.
Registrar lo pendiente no lo autoriza. `actual` señala correcciones/documentación dentro del encargo vigente; `planificado` requiere el encargo correspondiente; `diferido` no se activa ahora. Los responsables futuros 02/03 son propuestas hasta asignación. No se inventaron fechas ni estimaciones.
Prioridades: P0 = integridad/seguridad o condición de cierre del bloque aplicable; P1 = modernización/operación; P2 = expansión. Una prioridad P0 en B4 no autoriza saltarse el diseño o la transición de B3.

## Índice de tareas

| ID | Bloque | Tarea | Estado | Prioridad | Responsable |
|---|---|---|---|---|---|
| [BL-001](#bl-001) | Gestión | Documentación común y estructura del repositorio | 🟢 VERIFICADO ACOTADO | P1 | 00 |
| [BL-002](#bl-002) | B1 | Corregir encolado del reintento activo | 🟢 VERIFICADO ACOTADO | P0 | 01 |
| [BL-003](#bl-003) | B1 | Distinguir reconciliación de cambio que libera espacio | 🟢 VERIFICADO ACOTADO | P1 | 01 |
| [BL-004](#bl-004) | B1 | Regresión caché, cuarentena, comando y datos obsoletos | 🟡 PARCIAL | P0 | 01 + 00 |
| [BL-005](#bl-005) | B1 | Validación física Roku F1–F24 | ⚪ PENDIENTE | P0 | Adrián + 01; revisa 00 |
| [BL-006](#bl-006) | B2 | Higiene B2: bitácora, concurrencia, índices y contadores | 🟢 VERIFICADO ACOTADO | P0 | 01; QA 00 |
| [BL-007](#bl-007) | B2 | HEAD de medios sin aumentar contadores | 🟢 VERIFICADO ACOTADO | P0 | 01; QA 00 |
| [BL-008](#bl-008) | QA | Completar ejecución pytest/CI del candidato | 🟢 VERIFICADO ACOTADO | P1 | 01 + 00 |
| [BL-009](#bl-009) | B3 diseño | Corregir espejo que asume orden por max(id) | 🟢 VERIFICADO ACOTADO | P0 | 01 |
| [BL-010](#bl-010) | B3 diseño | Reversión sin reactivar sesiones revocadas | 🟢 VERIFICADO ACOTADO | P0 | 01 |
| [BL-011](#bl-011) | B3 diseño | Completar matriz RLS, marcas y rol del espejo | 🟡 PARCIAL | P0 | 01 |
| [BL-012](#bl-012) | Decisiones | Inventario fiable: faltantes, esquema e IDs inequívocos | 🟢 VERIFICADO ACOTADO | P1 | 01 |
| [BL-013](#bl-013) | B3 diseño | Precisar documentos del espejo y contexto inicial de sesión | 🟢 VERIFICADO ACOTADO | P1 | 01 |
| [BL-014](#bl-014) | B3 diseño | Precisar publicación de trabajos y deduplicación por destino | 🟢 VERIFICADO ACOTADO | P1 | 01 |
| [BL-015](#bl-015) | B3 diseño | Precisar corte, turno de humo e IP detrás de proxy/NAT | 🟢 VERIFICADO ACOTADO | P1 | 01 |
| [BL-016](#bl-016) | B3 diseño | Revisar diseño B3 corregido y fijar aceptación | 🟡 PARCIAL | P0 | 00 |
| [BL-017](#bl-017) | Decisiones | D1: decidir números de pantallas duplicados | 🟡 DECISIÓN | P1 | Adrián |
| [BL-018](#bl-018) | Decisiones | D2: decidir permisos efectivos e inválidos por usuario | 🟡 DECISIÓN | P0 | Adrián |
| [BL-019](#bl-019) | Decisiones | D3/D4: aprobar política RLS y ventana del espejo | 🟡 DECISIÓN | P1 | Adrián + 00 |
| [BL-020](#bl-020) | Decisiones | D6: anonimización y autorización de copia | ⚪ PENDIENTE | P1 | 01; autoriza Adrián |
| [BL-021](#bl-021) | B3 implementación | Autorizar implementación acotada B3 | 🟡 DECISIÓN | P0 | Adrián |
| [BL-022](#bl-022) | B3 implementación | Paquete de datos, modelos, Alembic y roles PostgreSQL | ⚪ PENDIENTE | P0 | 01 |
| [BL-023](#bl-023) | B3 implementación | Migrador JSON y contratos del servidor sobre PostgreSQL | ⚪ PENDIENTE | P0 | 01 |
| [BL-024](#bl-024) | B3 implementación | Implementar espejo, exportación y rollback | ⚪ PENDIENTE | P0 | 01 |
| [BL-025](#bl-025) | B3 implementación | Aislamiento y concurrencia con PostgreSQL real | ⚪ PENDIENTE | P0 | 01 + 00 |
| [BL-026](#bl-026) | B3 implementación | Ensayo migración/rollback y restauración de respaldo | ⚪ PENDIENTE | P0 | 01 + 00; 03 por asignar |
| [BL-027](#bl-027) | B3 implementación | QA de B3 y compatibilidad Roku/POS | ⚪ PENDIENTE | P0 | 00 + Adrián |
| [BL-028](#bl-028) | B4 | Correo verificado, acceso e invitaciones | ⚪ PENDIENTE | P1 | 01 |
| [BL-029](#bl-029) | B4 | Permisos cerrados y traslado de sucursal | ⚪ PENDIENTE | P0 | 01 |
| [BL-030](#bl-030) | B4 | Eliminar bootstrap fijo y migrar hashes/sesiones | ⚪ PENDIENTE | P0 | 01 |
| [BL-031](#bl-031) | B5 | API modular v2 y convivencia de contratos | ⚪ PENDIENTE | P1 | 01 |
| [BL-032](#bl-032) | B5 | Estado real, sincronización y asignación heredada | 🟡 PARCIAL | P1 | 01 |
| [BL-033](#bl-033) | B5 | Idempotencia y contrato de turnos con POS | ⚪ PENDIENTE | P0 | 01 |
| [BL-034](#bl-034) | B5/B8 | Telemetría y métricas de reproducción reales | ⚪ PENDIENTE | P1 | 01 |
| [BL-035](#bl-035) | B5 | Cola de conversión y publicación de archivos | ⚪ PENDIENTE | P1 | 01 |
| [BL-036](#bl-036) | B5/B8 | Entrega de medios autorizada y capacidad | ⚪ PENDIENTE | P1 | 01; 03 por asignar |
| [BL-037](#bl-037) | B6 | Propuesta de navegación y componentes | 🟡 PARCIAL | P1 | 01 propuesta entregada; revisa 00; decide Adrián |
| [BL-038](#bl-038) | B6 | Panel: Inicio, Sucursales y Pantallas | ⚪ PENDIENTE | P1 | 02 + 01 |
| [BL-039](#bl-039) | B6 | Panel: Biblioteca y Listas | ⚪ PENDIENTE | P1 | 02 + 01 |
| [BL-040](#bl-040) | B6 | Panel: Mensajes, Turnos e Integraciones | ⚪ PENDIENTE | P1 | 02 + 01 |
| [BL-041](#bl-041) | B6 | Panel: Usuarios, Configuración y Programación | ⚪ PENDIENTE | P1 | 02 + 01 |
| [BL-042](#bl-042) | B6 | QA responsive, accesibilidad y flujo completo | ⚪ PENDIENTE | P1 | 00 + 02 |
| [BL-043](#bl-043) | B7 | Horarios, vencimientos y conflictos deterministas | ⚪ PENDIENTE | P1 | 01 |
| [BL-044](#bl-044) | B7 | Publicación por destinos y confirmación recibida | ⚪ PENDIENTE | P1 | 01 + 02 |
| [BL-045](#bl-045) | B8 | Protocolo de vinculación y tokens por pantalla | ⚪ PENDIENTE | P0 | 01 |
| [BL-046](#bl-046) | B8 | Adaptar Roku a protocolo v2 y telemetría | ⚪ PENDIENTE | P1 | 01 |
| [BL-047](#bl-047) | B8 | QA dispositivo/medios y transición de flota | ⚪ PENDIENTE | P0 | 00 + 01 + Adrián |
| [BL-048](#bl-048) | Release | Preparar release, respaldo y entorno operativo | ⚪ PENDIENTE | P0 | 03 por asignar; revisa 00 |
| [BL-049](#bl-049) | Release | D5: ventana y autorización de despliegue | 🟡 DECISIÓN | P0 | Adrián |
| [BL-050](#bl-050) | Release | Ejecutar piloto y cierre del bloque desplegado | ⚪ PENDIENTE | P0 | 03 por asignar + 00 + Adrián |
| [BL-051](#bl-051) | Decisiones | Acordar límites de espera, formatos y equipo piloto | 🟡 DECISIÓN | P1 | Adrián + 01 |
| [BL-052](#bl-052) | Decisiones | Autorizar entorno de correo y política de acceso | 🟡 DECISIÓN | P1 | Adrián |
| [BL-053](#bl-053) | Decisiones | Definir límites de carga y objetivos de rendimiento | ⚪ PENDIENTE | P1 | 01 + 00 + Adrián |
| [BL-054](#bl-054) | Comercial / expansión | Modelo de costos, precio MXN e impuestos | 🔵 DIFERIDO | P2 | Adrián + 00 |
| [BL-055](#bl-055) | Comercial / expansión | Catálogo único de planes y complementos | 🔵 DIFERIDO | P2 | 01 |
| [BL-056](#bl-056) | Comercial / expansión | Portal del propietario y soporte auditado | 🔵 DIFERIDO | P2 | 01 + 02 |
| [BL-057](#bl-057) | Comercial / expansión | Alta pública de empresa y onboarding | 🔵 DIFERIDO | P2 | 01 + 02 |
| [BL-058](#bl-058) | Comercial / expansión | Cuotas y consumo concurrente | 🔵 DIFERIDO | P2 | 01 |
| [BL-059](#bl-059) | Comercial / expansión | Estados de suscripción y política offline | 🔵 DIFERIDO | P2 | Adrián + 01 |
| [BL-060](#bl-060) | Comercial / expansión | Cobro manual o recurrente y conciliación | 🔵 DIFERIDO | P2 | Adrián + 01 |
| [BL-061](#bl-061) | Comercial / expansión | Cambios de plan, cancelación y reactivación | 🔵 DIFERIDO | P2 | 01 + 02 |
| [BL-062](#bl-062) | Comercial / expansión | Web comercial, demo/contacto y calculadora | 🔵 DIFERIDO | P2 | 02 + 01 |
| [BL-063](#bl-063) | Comercial / expansión | Términos, privacidad y autorización comercial | 🔵 DIFERIDO | P2 | Adrián; 00 coordina |
| [BL-064](#bl-064) | Comercial / expansión | Turnos configurables por giro | 🔵 DIFERIDO | P2 | 01 + 02 |
| [BL-065](#bl-065) | Comercial / expansión | Conector LUMIA comercial y dependencias | 🔵 DIFERIDO | P2 | 01 + 02 |
| [BL-066](#bl-066) | Comercial / expansión | Empleado del mes | 🔵 DIFERIDO | P2 | 01 + 02 |
| [BL-067](#bl-067) | Comercial / expansión | Menú digital dinámico | 🔵 DIFERIDO | P2 | 01 + 02 |
| [BL-068](#bl-068) | Comercial / expansión | Android TV/Google TV y matriz física | 🔵 DIFERIDO | P2 | 01 + 00 + Adrián |
| [BL-069](#bl-069) | Comercial / expansión | Identidad comercial y propuesta de valor | 🔵 DIFERIDO | P2 | Adrián + 00 |
| [BL-070](#bl-070) | Comercial / expansión | QA integral y lanzamiento SaaS | 🔵 DIFERIDO | P2 | 00 + Adrián |
| [BL-071](#bl-071) | Comercial / expansión | Evaluación acotada de IA para operación/diagnóstico | 🔵 DIFERIDO | P2 | 00 + 01 |
| [BL-072](#bl-072) | B3 diseño | Revisar piezas reutilizables del SaaS pausado | ⚪ PENDIENTE | P1 | 01 + 00 |
| [BL-073](#bl-073) | Gestión | Integrar documentación local a Git en rama acordada | ⚪ PENDIENTE | P1 | 01; coordina 00 |
| [BL-074](#bl-074) | Decisiones | D7: decidir sesiones al revertir | 🟡 DECISIÓN | P0 | Adrián |
| [BL-075](#bl-075) | B3 diseño | Corregir afirmaciones de cobertura y guardián RLS | 🟢 VERIFICADO ACOTADO | P1 | 01 |
| [BL-076](#bl-076) | B3 diseño | Diseñar destinos y grupos de TVs; impacto en B3 | 🔴 CORRECCIONES | P1 | 01; revisa 00 |
| [BL-077](#bl-077) | B5 | Datos/API para asignar playlists a TVs y grupos | ⚪ PENDIENTE | P1 | 01 |
| [BL-078](#bl-078) | B6 | Panel Reproducir en y administración de grupos | 🟡 PARCIAL | P1 | 01; 02 si se asigna |
| [BL-079](#bl-079) | QA | QA de distribución de playlists por TV y grupo | ⚪ PENDIENTE | P1 | 00; físico Adrián + 01 |
| [BL-080](#bl-080) | B5 | Permisos de comandos administrativos B5a | 🟢 VERIFICADO ACOTADO | P1 | 01; revisa 00 |
| [BL-081](#bl-081) | B5 | Recarga Roku con playlist idéntica | 🟡 PARCIAL | P1 | 01; revisa 00 |
| [BL-082](#bl-082) | B6 | Corregir desbordamiento de propuesta móvil | 🟢 VERIFICADO ACOTADO | P1 | 01; revisa 00 |
| [BL-083](#bl-083) | Decisiones | D8: concretar semántica persistente y alcance por sucursal de grupos | 🟡 DECISIÓN | P1 | Adrián; propuesta 01, registra 00 |
| [BL-084](#bl-084) | Decisiones | D9: permiso para reemplazar destino directo de otra lista | 🟡 DECISIÓN | P1 | Adrián; propuesta 01, registra 00 |

## Fichas y criterios de cierre

<a id="bl-001"></a>

### BL-001 — Documentación común y estructura del repositorio

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** Gestión · **Alcance:** actual.

**Responsable:** 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Entradas AGENTS/CLAUDE, roles e índice disponibles; enlaces comprobados.

**Evidencia/referencia:** [docs/coordinacion/consolidacion-2026-09-16.json](../coordinacion/consolidacion-2026-09-16.json)

<a id="bl-002"></a>

### BL-002 — Corregir encolado del reintento activo

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P0 · **Bloque:** B1 · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-02](../requisitos/REQUISITOS-PRODUCTO.md#rf-02), [RF-03](../requisitos/REQUISITOS-PRODUCTO.md#rf-03).

**Aceptación:** Una URL falla y reintenta a 30 s sin nuevos mensajes; cinco esperas y seis intentos sin duplicados.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**Hallazgo:** R3-B1-01 cerrado en arnés brs; no hardware.

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-003"></a>

### BL-003 — Distinguir reconciliación de cambio que libera espacio

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** B1 · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-03](../requisitos/REQUISITOS-PRODUCTO.md#rf-03).

**Aceptación:** Reconciliaciones idénticas no reactivan sin_espacio; cambio efectivo sí.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**Hallazgo:** R3-B1-02 cerrado en arnés brs; no hardware.

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-004"></a>

### BL-004 — Regresión caché, cuarentena, comando y datos obsoletos

**Estado:** 🟡 PARCIAL · **Prioridad:** P0 · **Bloque:** B1 · **Alcance:** actual.

**Responsable:** 01 + 00. **Dependencias:** [BL-002](17-backlog-maestro.md#bl-002), [BL-003](17-backlog-maestro.md#bl-003)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-02](../requisitos/REQUISITOS-PRODUCTO.md#rf-02), [RF-03](../requisitos/REQUISITOS-PRODUCTO.md#rf-03), [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09).

**Aceptación:** Repetir todos los recorridos señalados en informes B1 y sus correcciones sobre un SHA; identificar compilación y límites.

**Evidencia/referencia:** [docs/qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md](../qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md)

**Hallazgo:** Arneses 42+21 pasan; recarga corregida en alcance aislado, F1–F24 físico pendiente en build 62..

**SHA al que se refiere esa evidencia:** `3a1eaf92e7d1e51ee1e13d41356f4788760c6fbc`.

<a id="bl-005"></a>

### BL-005 — Validación física Roku F1–F24

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B1 · **Alcance:** actual.

**Responsable:** Adrián + 01; revisa 00. **Dependencias:** [BL-004](17-backlog-maestro.md#bl-004), [BL-051](17-backlog-maestro.md#bl-051)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-02](../requisitos/REQUISITOS-PRODUCTO.md#rf-02), [RF-03](../requisitos/REQUISITOS-PRODUCTO.md#rf-03), [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09), [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15).

**Aceptación:** Modelo/OS/build, clips/resultados por escenario, pérdida de red/servidor, retorno, caché, turnos y comandos; tiempos acordados.

**Evidencia/referencia:** [docs/qa/informes/24-qa-B3-rev6-RF26-a0583df.md](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md)

**Hallazgo:** Físico build62 pendiente. F23a/b/c precisan los casos; corregir esperado 5.2.61 en F22 y señal de log recargar inexistente antes de ejecutar..

**SHA al que se refiere esa evidencia:** `a0583df14a5367f2ac8b33c3c3711fb84373ba65`.

<a id="bl-006"></a>

### BL-006 — Higiene B2: bitácora, concurrencia, índices y contadores

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P0 · **Bloque:** B2 · **Alcance:** actual.

**Responsable:** 01; QA 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11), [RNF-04](../requisitos/REQUISITOS-PRODUCTO.md#rnf-04), [RNF-07](../requisitos/REQUISITOS-PRODUCTO.md#rnf-07).

**Aceptación:** Diez pruebas originales pasan ahora con pytest dentro de las 21 de servidor en ce4716f; sin cambios del producto B2 desde revisión previa.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-007"></a>

### BL-007 — HEAD de medios sin aumentar contadores

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P0 · **Bloque:** B2 · **Alcance:** actual.

**Responsable:** 01; QA 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-03](../requisitos/REQUISITOS-PRODUCTO.md#rf-03), [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11).

**Aceptación:** Tres funciones HEAD pasan con las diez previas; tamaños/cabeceras/404 y ausencia de incremento comprobados.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-008"></a>

### BL-008 — Completar ejecución pytest/CI del candidato

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** QA · **Alcance:** actual.

**Responsable:** 01 + 00. **Dependencias:** [BL-002](17-backlog-maestro.md#bl-002), [BL-003](17-backlog-maestro.md#bl-003)

**Requisitos:** [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10), [RNF-04](../requisitos/REQUISITOS-PRODUCTO.md#rnf-04).

**Aceptación:** PG61 ejecutado por Codex, sin omitidos. CI35435820477: 28 servidor/61 PG/42+21 Roku/compilación. Producto idéntico a c42770f por hashes. Pruebas verdes no cierran los tres contraejemplos adicionales de QA26.

**Evidencia/referencia:** [docs/qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md](../qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md)

**SHA al que se refiere esa evidencia:** `14f0bc51b5f7330a046d99ac870036747366c586`.

<a id="bl-009"></a>

### BL-009 — Corregir espejo que asume orden por max(id)

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P0 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-04](../requisitos/REQUISITOS-PRODUCTO.md#rnf-04).

**Aceptación:** Protocolo cubre A reserva/B confirma/espejo/A confirma, sin tercer cambio; marcas pendientes y snapshot coherente.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**Hallazgo:** B3-R2-01 cerrado para protocolo del DDL mínimo con PG16; no implementación B3.

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-010"></a>

### BL-010 — Reversión sin reactivar sesiones revocadas

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P0 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12), [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Contrato de sesiones/rollback y barrera completa ensayados en PG55: revocadas no se reactivan, idle/peticiones tardías no escriben tras drenaje y otra base sobrevive. No implementa rollback productivo ni resuelve decisión D7.

**Evidencia/referencia:** [docs/qa/informes/25-qa-B3-rev7-RF26-050cc2d.md](../qa/informes/25-qa-B3-rev7-RF26-050cc2d.md)

**SHA al que se refiere esa evidencia:** `050cc2d090b58f4d1a7b1673c830111a347b3768`.

<a id="bl-011"></a>

### BL-011 — Completar matriz RLS, marcas y rol del espejo

**Estado:** 🟡 PARCIAL · **Prioridad:** P0 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** DDL/roles/políticas permiten mutación+marca, auditoría, espejo y backup; controles negativos impiden cruce.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**Hallazgo:** B3-R2-03 cerrado en DDL mínimo; B3-R3-04 cobertura/guardián pendientes.

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-012"></a>

### BL-012 — Inventario fiable: faltantes, esquema e IDs inequívocos

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04), [RF-13](../requisitos/REQUISITOS-PRODUCTO.md#rf-13), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Ocho pruebas del inventario pasan: casos originales de ruta/archivos/JSON/forma raíz, vacío y alias. No equivale a validación exhaustiva de todos los campos anidados.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**Hallazgo:** INV-01 cerrado en los ocho casos sintéticos de su suite; inventario real y decisiones pendientes.

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-013"></a>

### BL-013 — Precisar documentos del espejo y contexto inicial de sesión

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** [BL-010](17-backlog-maestro.md#bl-010), [BL-011](17-backlog-maestro.md#bl-011)

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12), [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Contexto inicial de membresía y documentos del espejo precisados en diseño rev4 y ensayos del DDL mínimo. No aprueba implementación completa ni reversión de BL-010.

**Evidencia/referencia:** [docs/qa/informes/22-qa-B3-rev4-B5a-1f7782e.md](../qa/informes/22-qa-B3-rev4-B5a-1f7782e.md)

**SHA al que se refiere esa evidencia:** `1f7782eb384d1bf0b05688870c524b8ccdb05fe4`.

<a id="bl-014"></a>

### BL-014 — Precisar publicación de trabajos y deduplicación por destino

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-05](../requisitos/REQUISITOS-PRODUCTO.md#rf-05), [RNF-06](../requisitos/REQUISITOS-PRODUCTO.md#rnf-06).

**Aceptación:** Contrato mínimo PG/archivos rev5 distingue publicado/ya_publicado/perdido; conserva artefacto al reintentar misma posesión y descarta solo al perder. Ensayos ejecutados, no trabajadores de producto.

**Evidencia/referencia:** [docs/qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md](../qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md)

**SHA al que se refiere esa evidencia:** `3a1eaf92e7d1e51ee1e13d41356f4788760c6fbc`.

<a id="bl-015"></a>

### BL-015 — Precisar corte, turno de humo e IP detrás de proxy/NAT

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09), [RNF-09](../requisitos/REQUISITOS-PRODUCTO.md#rnf-09).

**Aceptación:** B3-R4-01 y B3-R6-01 cerrados en ensayos: termina todas las sesiones de aplicación de la base objetivo, bloquea nuevas y preserva otros roles y otras bases. No es ejecución real de corte/smoke en VPS.

**Evidencia/referencia:** [docs/qa/informes/25-qa-B3-rev7-RF26-050cc2d.md](../qa/informes/25-qa-B3-rev7-RF26-050cc2d.md)

**SHA al que se refiere esa evidencia:** `050cc2d090b58f4d1a7b1673c830111a347b3768`.

<a id="bl-016"></a>

### BL-016 — Revisar diseño B3 corregido y fijar aceptación

**Estado:** 🟡 PARCIAL · **Prioridad:** P0 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 00. **Dependencias:** [BL-009](17-backlog-maestro.md#bl-009), [BL-010](17-backlog-maestro.md#bl-010), [BL-011](17-backlog-maestro.md#bl-011), [BL-013](17-backlog-maestro.md#bl-013), [BL-014](17-backlog-maestro.md#bl-014), [BL-015](17-backlog-maestro.md#bl-015), [BL-075](17-backlog-maestro.md#bl-075), [BL-076](17-backlog-maestro.md#bl-076)

**Requisitos:** [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01), [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Dictamen documental por versión/SHA; cero hallazgos críticos de diseño abiertos; implementación requiere encargo posterior.

**Evidencia/referencia:** [docs/qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md](../qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md)

**Hallazgo:** Rev8 revisada; hallazgos de QA25 cerrados en alcance. RF26-QA-04/05/06 pendientes; no aprobación global de B3..

**SHA al que se refiere esa evidencia:** `14f0bc51b5f7330a046d99ac870036747366c586`.

<a id="bl-017"></a>

### BL-017 — D1: decidir números de pantallas duplicados

**Estado:** 🟡 DECISIÓN · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** Adrián. **Dependencias:** [BL-012](17-backlog-maestro.md#bl-012)

**Requisitos:** [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04), [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01).

**Aceptación:** Tabla por ID inequívoco con número actual/propuesto y efecto en desfase; decisión explícita antes de migrar.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-018"></a>

### BL-018 — D2: decidir permisos efectivos e inválidos por usuario

**Estado:** 🟡 DECISIÓN · **Prioridad:** P0 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** Adrián. **Dependencias:** [BL-012](17-backlog-maestro.md#bl-012)

**Requisitos:** [RF-13](../requisitos/REQUISITOS-PRODUCTO.md#rf-13), [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01).

**Aceptación:** Lista por usuario, alcance actual y destino; decidir si cambio en B3 o B4 sin concesión implícita.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-019"></a>

### BL-019 — D3/D4: aprobar política RLS y ventana del espejo

**Estado:** 🟡 DECISIÓN · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** Adrián + 00. **Dependencias:** [BL-016](17-backlog-maestro.md#bl-016)

**Requisitos:** [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Decisión documentada; siete días no sustituye protocolo recuperable ni pruebas.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-020"></a>

### BL-020 — D6: anonimización y autorización de copia

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** 01; autoriza Adrián. **Dependencias:** [BL-016](17-backlog-maestro.md#bl-016)

**Requisitos:** [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Script revisado con credenciales, tokens, mensajes, turnos, zonas/nombres; compartir solo copia revisada autorizada.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-021"></a>

### BL-021 — Autorizar implementación acotada B3

**Estado:** 🟡 DECISIÓN · **Prioridad:** P0 · **Bloque:** B3 implementación · **Alcance:** planificado.

**Responsable:** Adrián. **Dependencias:** [BL-016](17-backlog-maestro.md#bl-016), [BL-019](17-backlog-maestro.md#bl-019), [BL-074](17-backlog-maestro.md#bl-074)

**Requisitos:** [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01), [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Alcance y criterios aprobados; separar autorización de implementar de fecha/corte real.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-022"></a>

### BL-022 — Paquete de datos, modelos, Alembic y roles PostgreSQL

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B3 implementación · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-021](17-backlog-maestro.md#bl-021), [BL-072](17-backlog-maestro.md#bl-072)

**Requisitos:** [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01), [RNF-03](../requisitos/REQUISITOS-PRODUCTO.md#rnf-03), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Esquema revisado implementado; FKs y RLS por tabla; segunda empresa operativa bloqueada en etapa heredada.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-023"></a>

### BL-023 — Migrador JSON y contratos del servidor sobre PostgreSQL

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B3 implementación · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-022](17-backlog-maestro.md#bl-022)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04), [RF-06](../requisitos/REQUISITOS-PRODUCTO.md#rf-06), [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01).

**Aceptación:** Idempotencia, mapeos y anomalías informadas; pruebas con decisiones sintéticas; IDs y formas de respuesta conservados.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-024"></a>

### BL-024 — Implementar espejo, exportación y rollback

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B3 implementación · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-022](17-backlog-maestro.md#bl-022)

**Requisitos:** [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-04](../requisitos/REQUISITOS-PRODUCTO.md#rnf-04).

**Aceptación:** Pruebas de caída, secuencias fuera de orden, snapshots, disco lleno, revocación y recuperación conforme al diseño aprobado.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-025"></a>

### BL-025 — Aislamiento y concurrencia con PostgreSQL real

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B3 implementación · **Alcance:** planificado.

**Responsable:** 01 + 00. **Dependencias:** [BL-023](17-backlog-maestro.md#bl-023), [BL-024](17-backlog-maestro.md#bl-024)

**Requisitos:** [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RNF-04](../requisitos/REQUISITOS-PRODUCTO.md#rnf-04), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Dos empresas sintéticas, claves iguales, SQL crudo, conexiones reutilizadas, escrituras concurrentes; registros por rol y SHA.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-026"></a>

### BL-026 — Ensayo migración/rollback y restauración de respaldo

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B3 implementación · **Alcance:** planificado.

**Responsable:** 01 + 00; 03 por asignar. **Dependencias:** [BL-023](17-backlog-maestro.md#bl-023), [BL-024](17-backlog-maestro.md#bl-024), [BL-020](17-backlog-maestro.md#bl-020)

**Requisitos:** [RNF-01](../requisitos/REQUISITOS-PRODUCTO.md#rnf-01), [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-09](../requisitos/REQUISITOS-PRODUCTO.md#rnf-09).

**Aceptación:** Sintético y luego anonimizado autorizado; restauración DB/medios, tiempos medidos y fallos de cada paso.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-027"></a>

### BL-027 — QA de B3 y compatibilidad Roku/POS

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B3 implementación · **Alcance:** planificado.

**Responsable:** 00 + Adrián. **Dependencias:** [BL-025](17-backlog-maestro.md#bl-025), [BL-026](17-backlog-maestro.md#bl-026)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09), [RF-10](../requisitos/REQUISITOS-PRODUCTO.md#rf-10), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Revisión independiente por SHA y matriz de contratos; Roku 5.1/5.2 físicos según alcance; no confundir lectura con reproducción.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-028"></a>

### BL-028 — Correo verificado, acceso e invitaciones

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B4 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-027](17-backlog-maestro.md#bl-027)

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12).

**Aceptación:** Códigos de un uso/expiración/propósito, límites/reenvíos; SMTP autorizado aparte; altas admin/invitación, sin alta pública.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-029"></a>

### BL-029 — Permisos cerrados y traslado de sucursal

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B4 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-027](17-backlog-maestro.md#bl-027), [BL-018](17-backlog-maestro.md#bl-018)

**Requisitos:** [RF-13](../requisitos/REQUISITOS-PRODUCTO.md#rf-13), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Vacío deniega, ID inválido no cambia sucursal silenciosamente, origen/destino validado; pruebas positivas y negativas.

**Evidencia/referencia:** [docs/coordinacion/09-auditoria-codigo.md](../coordinacion/09-auditoria-codigo.md)

**Hallazgo:** QA-F01 / QA-F02.

<a id="bl-030"></a>

### BL-030 — Eliminar bootstrap fijo y migrar hashes/sesiones

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B4 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-028](17-backlog-maestro.md#bl-028)

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12), [RF-13](../requisitos/REQUISITOS-PRODUCTO.md#rf-13), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Sin contraseña fija; transición Argon2id, revocación y recuperación B4 ensayadas; secretos externos.

**Evidencia/referencia:** [docs/coordinacion/09-auditoria-codigo.md](../coordinacion/09-auditoria-codigo.md)

**Hallazgo:** QA-F03.

<a id="bl-031"></a>

### BL-031 — API modular v2 y convivencia de contratos

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B5 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-027](17-backlog-maestro.md#bl-027)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RNF-03](../requisitos/REQUISITOS-PRODUCTO.md#rnf-03).

**Aceptación:** Inventario de rutas actualizado, errores/auth consistentes y endpoints antiguos preservados durante transición.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-032"></a>

### BL-032 — Estado real, sincronización y asignación heredada

**Estado:** 🟡 PARCIAL · **Prioridad:** P1 · **Bloque:** B5 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-031](17-backlog-maestro.md#bl-031)

**Requisitos:** [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04), [RF-06](../requisitos/REQUISITOS-PRODUCTO.md#rf-06), [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11).

**Aceptación:** Conectado/asignado/recibido/reproduciendo separados; números y desfase distintos; lista heredada visible.

**Evidencia/referencia:** [docs/qa/informes/22-qa-B3-rev4-B5a-1f7782e.md](../qa/informes/22-qa-B3-rev4-B5a-1f7782e.md)

**Hallazgo:** Telemetría B5a entregada; no acredita todavía ACK por versión ni reproducción efectiva/física.

**SHA al que se refiere esa evidencia:** `1f7782eb384d1bf0b05688870c524b8ccdb05fe4`.

<a id="bl-033"></a>

### BL-033 — Idempotencia y contrato de turnos con POS

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B5 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-031](17-backlog-maestro.md#bl-031)

**Requisitos:** [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09), [RF-10](../requisitos/REQUISITOS-PRODUCTO.md#rf-10).

**Aceptación:** Reintentos, eventos duplicados/tardíos y cruces de sucursal sin doble llamado; LUMIA solo lectura.

**Evidencia/referencia:** [docs/coordinacion/09-auditoria-codigo.md](../coordinacion/09-auditoria-codigo.md)

**Hallazgo:** QA-G02.

<a id="bl-034"></a>

### BL-034 — Telemetría y métricas de reproducción reales

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B5/B8 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-032](17-backlog-maestro.md#bl-032), [BL-047](17-backlog-maestro.md#bl-047)

**Requisitos:** [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11), [RNF-07](../requisitos/REQUISITOS-PRODUCTO.md#rnf-07).

**Aceptación:** Eventos confirmados por dispositivo deduplicados; descarga no se etiqueta reproducción/persona/venta.

**Evidencia/referencia:** [docs/coordinacion/09-auditoria-codigo.md](../coordinacion/09-auditoria-codigo.md)

**Hallazgo:** QA-F04: pendiente más allá de 404/HEAD.

<a id="bl-035"></a>

### BL-035 — Cola de conversión y publicación de archivos

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B5 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-031](17-backlog-maestro.md#bl-031), [BL-014](17-backlog-maestro.md#bl-014)

**Requisitos:** [RF-05](../requisitos/REQUISITOS-PRODUCTO.md#rf-05), [RNF-06](../requisitos/REQUISITOS-PRODUCTO.md#rnf-06).

**Aceptación:** Trabajador recuperable con digest, destino y posesión; cancelación en curso y publicación atómica según protocolo.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-036"></a>

### BL-036 — Entrega de medios autorizada y capacidad

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B5/B8 · **Alcance:** planificado.

**Responsable:** 01; 03 por asignar. **Dependencias:** [BL-031](17-backlog-maestro.md#bl-031), [BL-047](17-backlog-maestro.md#bl-047)

**Requisitos:** [RF-05](../requisitos/REQUISITOS-PRODUCTO.md#rf-05), [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15), [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RNF-03](../requisitos/REQUISITOS-PRODUCTO.md#rnf-03), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Acceso por empresa/sucursal verificado; nginx interno o S3 firmado justificado; no abrir alias público que salte auth; costos medidos.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-037"></a>

### BL-037 — Propuesta de navegación y componentes

**Estado:** 🟡 PARCIAL · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** planificado.

**Responsable:** 01 propuesta entregada; revisa 00; decide Adrián. **Dependencias:** [BL-031](17-backlog-maestro.md#bl-031)

**Requisitos:** [RF-14](../requisitos/REQUISITOS-PRODUCTO.md#rf-14), [RNF-08](../requisitos/REQUISITOS-PRODUCTO.md#rnf-08).

**Aceptación:** Mapa de once secciones, selector de sucursal, estados y datos/contratos; alcance asignado antes de implementar.

**Evidencia/referencia:** [docs/qa/informes/24-qa-B3-rev6-RF26-a0583df.md](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md)

**Hallazgo:** Panel rev3 mejora confirmación/reemplazo y etiqueta estados futuros; UI33 pasa. Cuatro supuestos y decisiones de grupos pendientes..

**SHA al que se refiere esa evidencia:** `a0583df14a5367f2ac8b33c3c3711fb84373ba65`.

<a id="bl-038"></a>

### BL-038 — Panel: Inicio, Sucursales y Pantallas

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** planificado.

**Responsable:** 02 + 01. **Dependencias:** [BL-037](17-backlog-maestro.md#bl-037), [BL-032](17-backlog-maestro.md#bl-032)

**Requisitos:** [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04), [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11), [RF-14](../requisitos/REQUISITOS-PRODUCTO.md#rf-14), [RNF-08](../requisitos/REQUISITOS-PRODUCTO.md#rnf-08).

**Aceptación:** Datos reales y controles soportados; estados correctos; acciones respetan permisos del servidor.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-039"></a>

### BL-039 — Panel: Biblioteca y Listas

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** planificado.

**Responsable:** 02 + 01. **Dependencias:** [BL-037](17-backlog-maestro.md#bl-037)

**Requisitos:** [RF-05](../requisitos/REQUISITOS-PRODUCTO.md#rf-05), [RF-06](../requisitos/REQUISITOS-PRODUCTO.md#rf-06), [RF-14](../requisitos/REQUISITOS-PRODUCTO.md#rf-14), [RNF-08](../requisitos/REQUISITOS-PRODUCTO.md#rnf-08).

**Aceptación:** Subir, ordenar, asignar, renombrar, borrar y errores sin mocks; herencia explícita; sin editor gráfico.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-040"></a>

### BL-040 — Panel: Mensajes, Turnos e Integraciones

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** planificado.

**Responsable:** 02 + 01. **Dependencias:** [BL-037](17-backlog-maestro.md#bl-037), [BL-033](17-backlog-maestro.md#bl-033)

**Requisitos:** [RF-08](../requisitos/REQUISITOS-PRODUCTO.md#rf-08), [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09), [RF-10](../requisitos/REQUISITOS-PRODUCTO.md#rf-10), [RF-14](../requisitos/REQUISITOS-PRODUCTO.md#rf-14).

**Aceptación:** Cintillo configurable, estado de integración y errores; configuración por pantalla/sucursal y privacidad.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-041"></a>

### BL-041 — Panel: Usuarios, Configuración y Programación

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** planificado.

**Responsable:** 02 + 01. **Dependencias:** [BL-037](17-backlog-maestro.md#bl-037), [BL-029](17-backlog-maestro.md#bl-029), [BL-043](17-backlog-maestro.md#bl-043)

**Requisitos:** [RF-07](../requisitos/REQUISITOS-PRODUCTO.md#rf-07), [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12), [RF-13](../requisitos/REQUISITOS-PRODUCTO.md#rf-13), [RF-14](../requisitos/REQUISITOS-PRODUCTO.md#rf-14).

**Aceptación:** Permisos reales, perfiles, zona horaria y reglas de horarios; no exponer módulos comerciales sin implementar.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-042"></a>

### BL-042 — QA responsive, accesibilidad y flujo completo

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** planificado.

**Responsable:** 00 + 02. **Dependencias:** [BL-038](17-backlog-maestro.md#bl-038), [BL-039](17-backlog-maestro.md#bl-039), [BL-040](17-backlog-maestro.md#bl-040), [BL-041](17-backlog-maestro.md#bl-041)

**Requisitos:** [RF-14](../requisitos/REQUISITOS-PRODUCTO.md#rf-14), [RNF-08](../requisitos/REQUISITOS-PRODUCTO.md#rnf-08), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Teclado/foco, contraste, viewport, estados error/sin permiso y cambio de sucursal sin datos previos indebidos.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-043"></a>

### BL-043 — Horarios, vencimientos y conflictos deterministas

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B7 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-031](17-backlog-maestro.md#bl-031)

**Requisitos:** [RF-07](../requisitos/REQUISITOS-PRODUCTO.md#rf-07).

**Aceptación:** Zona horaria, medianoche, solapamientos, prioridad y contenido de respaldo con pruebas reproducibles.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-044"></a>

### BL-044 — Publicación por destinos y confirmación recibida

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B7 · **Alcance:** planificado.

**Responsable:** 01 + 02. **Dependencias:** [BL-043](17-backlog-maestro.md#bl-043), [BL-032](17-backlog-maestro.md#bl-032)

**Requisitos:** [RF-07](../requisitos/REQUISITOS-PRODUCTO.md#rf-07), [RF-08](../requisitos/REQUISITOS-PRODUCTO.md#rf-08), [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11).

**Aceptación:** Cambios multi-sucursal/pantalla, estado guardado/enviado/recibido; excepciones y retirada de mensaje según capacidad.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-045"></a>

### BL-045 — Protocolo de vinculación y tokens por pantalla

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B8 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-028](17-backlog-maestro.md#bl-028), [BL-031](17-backlog-maestro.md#bl-031)

**Requisitos:** [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15), [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Código temporal único, permisos mínimos, renovación/revocación y modelo de URLs con identidad.

**Evidencia/referencia:** [docs/coordinacion/09-auditoria-codigo.md](../coordinacion/09-auditoria-codigo.md)

**Hallazgo:** QA-G01.

<a id="bl-046"></a>

### BL-046 — Adaptar Roku a protocolo v2 y telemetría

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B8 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-045](17-backlog-maestro.md#bl-045), [BL-005](17-backlog-maestro.md#bl-005)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11), [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15).

**Aceptación:** Credenciales protegidas, llamadas de reproducción y convivencia; renovar/revocar y reconectar en TV real.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-047"></a>

### BL-047 — QA dispositivo/medios y transición de flota

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** B8 · **Alcance:** planificado.

**Responsable:** 00 + 01 + Adrián. **Dependencias:** [BL-046](17-backlog-maestro.md#bl-046)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15), [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Cruce de IDs/URLs negado; regresión de clientes antiguos; migración por pantalla ensayada, activación real aparte.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-048"></a>

### BL-048 — Preparar release, respaldo y entorno operativo

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** Release · **Alcance:** planificado.

**Responsable:** 03 por asignar; revisa 00. **Dependencias:** [BL-027](17-backlog-maestro.md#bl-027)

**Requisitos:** [RNF-07](../requisitos/REQUISITOS-PRODUCTO.md#rnf-07), [RNF-09](../requisitos/REQUISITOS-PRODUCTO.md#rnf-09).

**Aceptación:** Servicios/HTTPS/secretos, restauración, capacidad, alertas y rollback documentados; alcance puede ser por bloque aprobado.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-049"></a>

### BL-049 — D5: ventana y autorización de despliegue

**Estado:** 🟡 DECISIÓN · **Prioridad:** P0 · **Bloque:** Release · **Alcance:** planificado.

**Responsable:** Adrián. **Dependencias:** [BL-048](17-backlog-maestro.md#bl-048), [BL-005](17-backlog-maestro.md#bl-005), [BL-017](17-backlog-maestro.md#bl-017), [BL-018](17-backlog-maestro.md#bl-018), [BL-019](17-backlog-maestro.md#bl-019)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RNF-09](../requisitos/REQUISITOS-PRODUCTO.md#rnf-09).

**Aceptación:** Versión, destino, operador, ventana y rollback aprobados; pendientes que apliquen al bloque resueltos.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-050"></a>

### BL-050 — Ejecutar piloto y cierre del bloque desplegado

**Estado:** ⚪ PENDIENTE · **Prioridad:** P0 · **Bloque:** Release · **Alcance:** planificado.

**Responsable:** 03 por asignar + 00 + Adrián. **Dependencias:** [BL-049](17-backlog-maestro.md#bl-049)

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RNF-07](../requisitos/REQUISITOS-PRODUCTO.md#rnf-07), [RNF-09](../requisitos/REQUISITOS-PRODUCTO.md#rnf-09), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Humo real autorizado, seguimiento del bloque, evidencia operativa y reversión lista; no implica SaaS lanzado.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-051"></a>

### BL-051 — Acordar límites de espera, formatos y equipo piloto

**Estado:** 🟡 DECISIÓN · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** Adrián + 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-02](../requisitos/REQUISITOS-PRODUCTO.md#rf-02), [RF-03](../requisitos/REQUISITOS-PRODUCTO.md#rf-03), [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09), [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15).

**Aceptación:** Registrar modelo/OS, formatos, orientación, umbral de turno vencido y aceptación de caché no garantizada tras reinicio.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-052"></a>

### BL-052 — Autorizar entorno de correo y política de acceso

**Estado:** 🟡 DECISIÓN · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** Adrián. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12).

**Aceptación:** Proveedor/remitente/entorno y destinatarios de prueba definidos; no envíos reales por una propuesta documental.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-053"></a>

### BL-053 — Definir límites de carga y objetivos de rendimiento

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** 01 + 00 + Adrián. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-05](../requisitos/REQUISITOS-PRODUCTO.md#rf-05), [RNF-03](../requisitos/REQUISITOS-PRODUCTO.md#rnf-03), [RNF-04](../requisitos/REQUISITOS-PRODUCTO.md#rnf-04), [RNF-07](../requisitos/REQUISITOS-PRODUCTO.md#rnf-07).

**Aceptación:** Carga representativa, tamaños/formatos, almacenamiento, concurrencia y umbrales medibles acordados antes de declarar escalabilidad.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-054"></a>

### BL-054 — Modelo de costos, precio MXN e impuestos

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** Adrián + 00. **Dependencias:** [BL-053](17-backlog-maestro.md#bl-053)

**Requisitos:** [RF-19](../requisitos/REQUISITOS-PRODUCTO.md#rf-19).

**Aceptación:** Validar almacenamiento/transferencia/soporte; definir impuestos. Precios del brief siguen siendo propuestas.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-055"></a>

### BL-055 — Catálogo único de planes y complementos

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01. **Dependencias:** [BL-054](17-backlog-maestro.md#bl-054)

**Requisitos:** [RF-18](../requisitos/REQUISITOS-PRODUCTO.md#rf-18), [RF-19](../requisitos/REQUISITOS-PRODUCTO.md#rf-19).

**Aceptación:** Versiones, vigencia y dependencias; misma fuente para web/panel; no precios duplicados.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-056"></a>

### BL-056 — Portal del propietario y soporte auditado

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 02. **Dependencias:** [BL-047](17-backlog-maestro.md#bl-047)

**Requisitos:** [RF-17](../requisitos/REQUISITOS-PRODUCTO.md#rf-17), [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16).

**Aceptación:** Sesión/ámbito separado, empresas, consumo, incidencias, soporte y bloqueos auditados.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-057"></a>

### BL-057 — Alta pública de empresa y onboarding

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 02. **Dependencias:** [BL-047](17-backlog-maestro.md#bl-047), [BL-055](17-backlog-maestro.md#bl-055)

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12), [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RF-18](../requisitos/REQUISITOS-PRODUCTO.md#rf-18).

**Aceptación:** Correo verificado, creación aislada, primer acceso/pantalla, prueba y aceptación de términos.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-058"></a>

### BL-058 — Cuotas y consumo concurrente

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01. **Dependencias:** [BL-055](17-backlog-maestro.md#bl-055)

**Requisitos:** [RF-18](../requisitos/REQUISITOS-PRODUCTO.md#rf-18).

**Aceptación:** Pantallas/sucursales/usuarios/listas/archivos/GB/campañas e historial por contrato; carreras no exceden cuota.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-059"></a>

### BL-059 — Estados de suscripción y política offline

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** Adrián + 01. **Dependencias:** [BL-055](17-backlog-maestro.md#bl-055)

**Requisitos:** [RF-18](../requisitos/REQUISITOS-PRODUCTO.md#rf-18), [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15).

**Aceptación:** Prueba/activa/pago pendiente/vencida/suspendida/cancelada; regularización y acceso separados; pantalla pública neutral.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-060"></a>

### BL-060 — Cobro manual o recurrente y conciliación

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** Adrián + 01. **Dependencias:** [BL-054](17-backlog-maestro.md#bl-054), [BL-059](17-backlog-maestro.md#bl-059)

**Requisitos:** [RF-19](../requisitos/REQUISITOS-PRODUCTO.md#rf-19).

**Aceptación:** Decidir manual inicial o pasarela; recibos/eventos idempotentes, reintentos, ajustes y aceptación de cargos.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-061"></a>

### BL-061 — Cambios de plan, cancelación y reactivación

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 02. **Dependencias:** [BL-058](17-backlog-maestro.md#bl-058), [BL-060](17-backlog-maestro.md#bl-060)

**Requisitos:** [RF-18](../requisitos/REQUISITOS-PRODUCTO.md#rf-18), [RF-19](../requisitos/REQUISITOS-PRODUCTO.md#rf-19).

**Aceptación:** Monto/fecha transparentes; reducción sin eliminar medios; reglas de tolerancia aprobadas.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-062"></a>

### BL-062 — Web comercial, demo/contacto y calculadora

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 02 + 01. **Dependencias:** [BL-055](17-backlog-maestro.md#bl-055)

**Requisitos:** [RF-20](../requisitos/REQUISITOS-PRODUCTO.md#rf-20).

**Aceptación:** Formularios reales, catálogo backend, compatibilidad exacta, funciones no disponibles rotuladas.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-063"></a>

### BL-063 — Términos, privacidad y autorización comercial

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** Adrián; 00 coordina. **Dependencias:** [BL-062](17-backlog-maestro.md#bl-062), [BL-060](17-backlog-maestro.md#bl-060)

**Requisitos:** [RF-20](../requisitos/REQUISITOS-PRODUCTO.md#rf-20), [RF-19](../requisitos/REQUISITOS-PRODUCTO.md#rf-19).

**Aceptación:** Revisión por responsable competente, información real y autorización de publicación/cobros.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-064"></a>

### BL-064 — Turnos configurables por giro

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 02. **Dependencias:** [BL-033](17-backlog-maestro.md#bl-033)

**Requisitos:** [RF-21](../requisitos/REQUISITOS-PRODUCTO.md#rf-21), [RF-09](../requisitos/REQUISITOS-PRODUCTO.md#rf-09).

**Aceptación:** Estados/cola/áreas/folios/privacidad; N de espera con base definida, voz opcional y llamado sin bloquear anuncios.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-065"></a>

### BL-065 — Conector LUMIA comercial y dependencias

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 02. **Dependencias:** [BL-033](17-backlog-maestro.md#bl-033), [BL-055](17-backlog-maestro.md#bl-055)

**Requisitos:** [RF-10](../requisitos/REQUISITOS-PRODUCTO.md#rf-10), [RF-18](../requisitos/REQUISITOS-PRODUCTO.md#rf-18).

**Aceptación:** Contrato por sucursal, límites/errores, Turnos + Conector transparentes; POS independiente, tarea aparte si requiere cambio.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-066"></a>

### BL-066 — Empleado del mes

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 02. **Dependencias:** [BL-055](17-backlog-maestro.md#bl-055)

**Requisitos:** [RF-22](../requisitos/REQUISITOS-PRODUCTO.md#rf-22).

**Aceptación:** Selección manual, historial/destinos, sin datos privados; integración automática posterior con contrato.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-067"></a>

### BL-067 — Menú digital dinámico

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 02. **Dependencias:** [BL-055](17-backlog-maestro.md#bl-055)

**Requisitos:** [RF-23](../requisitos/REQUISITOS-PRODUCTO.md#rf-23).

**Aceptación:** Catálogo/precios/disponibilidad/horarios por sucursal; imagen común no requiere complemento.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-068"></a>

### BL-068 — Android TV/Google TV y matriz física

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 01 + 00 + Adrián. **Dependencias:** [BL-045](17-backlog-maestro.md#bl-045)

**Requisitos:** [RF-24](../requisitos/REQUISITOS-PRODUCTO.md#rf-24), [RF-15](../requisitos/REQUISITOS-PRODUCTO.md#rf-15).

**Aceptación:** Player, control remoto, codecs/offline, distribución y actualización; pruebas físicas, sin compatibilidad universal.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-069"></a>

### BL-069 — Identidad comercial y propuesta de valor

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** Adrián + 00. **Dependencias:** [BL-054](17-backlog-maestro.md#bl-054)

**Requisitos:** [RF-20](../requisitos/REQUISITOS-PRODUCTO.md#rf-20), [RF-19](../requisitos/REQUISITOS-PRODUCTO.md#rf-19).

**Aceptación:** Nombre/dominio/marca verificados antes de elegir; evidencia de demanda/costos; no prometer ventas atribuibles sin medición.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-070"></a>

### BL-070 — QA integral y lanzamiento SaaS

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 00 + Adrián. **Dependencias:** [BL-056](17-backlog-maestro.md#bl-056), [BL-057](17-backlog-maestro.md#bl-057), [BL-058](17-backlog-maestro.md#bl-058), [BL-059](17-backlog-maestro.md#bl-059), [BL-060](17-backlog-maestro.md#bl-060), [BL-061](17-backlog-maestro.md#bl-061), [BL-063](17-backlog-maestro.md#bl-063)

**Requisitos:** [RF-16](../requisitos/REQUISITOS-PRODUCTO.md#rf-16), [RF-17](../requisitos/REQUISITOS-PRODUCTO.md#rf-17), [RF-18](../requisitos/REQUISITOS-PRODUCTO.md#rf-18), [RF-19](../requisitos/REQUISITOS-PRODUCTO.md#rf-19), [RF-20](../requisitos/REQUISITOS-PRODUCTO.md#rf-20), [RNF-09](../requisitos/REQUISITOS-PRODUCTO.md#rnf-09), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Aislamiento end-to-end, cobros/pruebas y recuperación validados; sólo anunciar módulos efectivamente aprobados.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-071"></a>

### BL-071 — Evaluación acotada de IA para operación/diagnóstico

**Estado:** 🔵 DIFERIDO · **Prioridad:** P2 · **Bloque:** Comercial / expansión · **Alcance:** diferido.

**Responsable:** 00 + 01. **Dependencias:** [BL-034](17-backlog-maestro.md#bl-034)

**Requisitos:** [RF-25](../requisitos/REQUISITOS-PRODUCTO.md#rf-25).

**Aceptación:** Propuesta con datos/costos/beneficio y aceptación del propietario; ninguna generación automática ni promesa sin implementación.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-072"></a>

### BL-072 — Revisar piezas reutilizables del SaaS pausado

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B3 diseño · **Alcance:** planificado.

**Responsable:** 01 + 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RNF-03](../requisitos/REQUISITOS-PRODUCTO.md#rnf-03), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Inventario por SHA b9c1f83 y archivos realmente reutilizados; revisar/adaptar pruebas; 36 verdes aportadas no equivalen a QA de esta integración.

**Evidencia/referencia:** [docs/qa/informes/14-qa-R2-y-diseno-B3-5c96845.md](../qa/informes/14-qa-R2-y-diseno-B3-5c96845.md)

<a id="bl-073"></a>

### BL-073 — Integrar documentación local a Git en rama acordada

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** Gestión · **Alcance:** planificado.

**Responsable:** 01; coordina 00. **Dependencias:** [BL-001](17-backlog-maestro.md#bl-001)

**Requisitos:** [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Revisar archivos preparados, rama/base y diff documental; preservar borrados ajenos; commit/push conforme autorización aplicable; registrar SHA, sin mezclar producto.

**Evidencia/referencia:** Sin evidencia de cierre; criterio pendiente.

<a id="bl-074"></a>

### BL-074 — D7: decidir sesiones al revertir

**Estado:** 🟡 DECISIÓN · **Prioridad:** P0 · **Bloque:** Decisiones · **Alcance:** planificado.

**Responsable:** Adrián. **Dependencias:** [BL-010](17-backlog-maestro.md#bl-010)

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12), [RNF-02](../requisitos/REQUISITOS-PRODUCTO.md#rnf-02), [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05).

**Aceptación:** Elegir conservación de sesiones verificadas o cierre total; emergencia sin PG no puede asegurar vigencia de la última copia.

**Evidencia/referencia:** [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md)

**SHA al que se refiere esa evidencia:** `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.

<a id="bl-075"></a>

### BL-075 — Corregir afirmaciones de cobertura y guardián RLS

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RNF-05](../requisitos/REQUISITOS-PRODUCTO.md#rnf-05), [RNF-10](../requisitos/REQUISITOS-PRODUCTO.md#rnf-10).

**Aceptación:** Cobertura delimitada al DDL mínimo y guardián con control negativo de propietario ejecutados dentro de 39 ensayos PG. No acredita repositorios/esquema completo aún no implementados.

**Evidencia/referencia:** [docs/qa/informes/22-qa-B3-rev4-B5a-1f7782e.md](../qa/informes/22-qa-B3-rev4-B5a-1f7782e.md)

**SHA al que se refiere esa evidencia:** `1f7782eb384d1bf0b05688870c524b8ccdb05fe4`.

<a id="bl-076"></a>

### BL-076 — Diseñar destinos y grupos de TVs; impacto en B3

**Estado:** 🔴 CORRECCIONES · **Prioridad:** P1 · **Bloque:** B3 diseño · **Alcance:** actual.

**Responsable:** 01; revisa 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-26](../requisitos/REQUISITOS-PRODUCTO.md#rf-26), [RF-06](../requisitos/REQUISITOS-PRODUCTO.md#rf-06), [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04).

**Aceptación:** Numeración concurrente segura por pantalla; generación estable entre latidos sin cambios y distinta en L1→L2→L1; borrado coherente conservando ID de pantalla. Preservar aislamiento por empresa/sucursal, ACK monótono y movimiento transaccional.

**Evidencia/referencia:** [docs/qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md](../qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md)

**Hallazgo:** QA26 cierra RF26-QA-02/03 y DOC-R7-01. Nuevos: RF26-QA-04 max(seq)+1 colisiona entre conexiones; RF26-QA-05 nueva entrega por consulta mantiene recibida atrasada; RF26-QA-06 SET NULL compuesto intenta anular pantalla.id al borrar lista..

**SHA al que se refiere esa evidencia:** `14f0bc51b5f7330a046d99ac870036747366c586`.

<a id="bl-077"></a>

### BL-077 — Datos/API para asignar playlists a TVs y grupos

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** B5 · **Alcance:** planificado.

**Responsable:** 01. **Dependencias:** [BL-076](17-backlog-maestro.md#bl-076), [BL-021](17-backlog-maestro.md#bl-021)

**Requisitos:** [RF-26](../requisitos/REQUISITOS-PRODUCTO.md#rf-26), [RF-06](../requisitos/REQUISITOS-PRODUCTO.md#rf-06), [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04).

**Aceptación:** Encargo definido, validación de permisos servidor, publicación coherente e idempotente, resolución por TV y recuperación de última asignación offline.

**Evidencia/referencia:** [docs/requisitos/RF-26-playlists-por-tv-y-grupo.md](../requisitos/RF-26-playlists-por-tv-y-grupo.md)

<a id="bl-078"></a>

### BL-078 — Panel Reproducir en y administración de grupos

**Estado:** 🟡 PARCIAL · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** planificado.

**Responsable:** 01; 02 si se asigna. **Dependencias:** [BL-076](17-backlog-maestro.md#bl-076), [BL-077](17-backlog-maestro.md#bl-077), [BL-037](17-backlog-maestro.md#bl-037)

**Requisitos:** [RF-26](../requisitos/REQUISITOS-PRODUCTO.md#rf-26), [RF-06](../requisitos/REQUISITOS-PRODUCTO.md#rf-06), [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04).

**Aceptación:** Selector TV/grupo, destinos únicos, resumen de cambios, estado por TV y gestión de miembros con reglas aprobadas; no falsos estados de reproducción.

**Evidencia/referencia:** [docs/qa/informes/24-qa-B3-rev6-RF26-a0583df.md](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md)

**Hallazgo:** Rev3 muestra resumen único y reemplazo explícito; faltan datos/API reales y cierre del contrato RF-26..

**SHA al que se refiere esa evidencia:** `a0583df14a5367f2ac8b33c3c3711fb84373ba65`.

<a id="bl-079"></a>

### BL-079 — QA de distribución de playlists por TV y grupo

**Estado:** ⚪ PENDIENTE · **Prioridad:** P1 · **Bloque:** QA · **Alcance:** planificado.

**Responsable:** 00; físico Adrián + 01. **Dependencias:** [BL-077](17-backlog-maestro.md#bl-077), [BL-078](17-backlog-maestro.md#bl-078)

**Requisitos:** [RF-26](../requisitos/REQUISITOS-PRODUCTO.md#rf-26), [RF-06](../requisitos/REQUISITOS-PRODUCTO.md#rf-06), [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04).

**Aceptación:** Ejecutar criterios RF-26: conflictos, permisos cruzados, offline, concurrencia, edición de grupo/lista y Roku físico con turnos/cintillo preservados.

**Evidencia/referencia:** [docs/requisitos/RF-26-playlists-por-tv-y-grupo.md](../requisitos/RF-26-playlists-por-tv-y-grupo.md)

<a id="bl-080"></a>

### BL-080 — Permisos de comandos administrativos B5a

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** B5 · **Alcance:** actual.

**Responsable:** 01; revisa 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-12](../requisitos/REQUISITOS-PRODUCTO.md#rf-12), [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11).

**Aceptación:** POST/PUT recargar/vaciar_cache deniegan operador con 403 sin encolar ni avanzar n; permiten admin. Suite verifica sucursal ajena.

**Evidencia/referencia:** [docs/qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md](../qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md)

**SHA al que se refiere esa evidencia:** `3a1eaf92e7d1e51ee1e13d41356f4788760c6fbc`.

<a id="bl-081"></a>

### BL-081 — Recarga Roku con playlist idéntica

**Estado:** 🟡 PARCIAL · **Prioridad:** P1 · **Bloque:** B5 · **Alcance:** actual.

**Responsable:** 01; revisa 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-01](../requisitos/REQUISITOS-PRODUCTO.md#rf-01), [RF-02](../requisitos/REQUISITOS-PRODUCTO.md#rf-02), [RF-11](../requisitos/REQUISITOS-PRODUCTO.md#rf-11).

**Aceptación:** Recargar reinicia sin depender de JSON distinto; 21 comprobaciones aisladas pasan. Completar F23 físico con protocolo de corte realizable y build 62.

**Evidencia/referencia:** [docs/qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md](../qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md)

**Hallazgo:** B5A-QA-02 cerrado en código/arnés: 21/21; F23 físico pendiente..

**SHA al que se refiere esa evidencia:** `3a1eaf92e7d1e51ee1e13d41356f4788760c6fbc`.

<a id="bl-082"></a>

### BL-082 — Corregir desbordamiento de propuesta móvil

**Estado:** 🟢 VERIFICADO ACOTADO · **Prioridad:** P1 · **Bloque:** B6 · **Alcance:** actual.

**Responsable:** 01; revisa 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-14](../requisitos/REQUISITOS-PRODUCTO.md#rf-14), [RNF-08](../requisitos/REQUISITOS-PRODUCTO.md#rnf-08).

**Aceptación:** Rev3: 33 combinaciones de ancho sin desbordamiento y captura propia inspeccionada. Cierre acotado del ancho, no frontend/API ni accesibilidad completa.

**Evidencia/referencia:** [docs/qa/informes/24-qa-B3-rev6-RF26-a0583df.md](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md)

**SHA al que se refiere esa evidencia:** `a0583df14a5367f2ac8b33c3c3711fb84373ba65`.

<a id="bl-083"></a>

### BL-083 — D8: concretar semántica persistente y alcance por sucursal de grupos

**Estado:** 🟡 DECISIÓN · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** actual.

**Responsable:** Adrián; propuesta 01, registra 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-26](../requisitos/REQUISITOS-PRODUCTO.md#rf-26), [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04).

**Aceptación:** Resolver semántica de grupos ya solicitados, membresía y alcance por sucursal sobre propuesta 22; no interpretar selección puntual como cancelación del requisito de grupos.

**Evidencia/referencia:** [docs/qa/informes/24-qa-B3-rev6-RF26-a0583df.md](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md)

**Hallazgo:** Propuesta de Claude, no decisión aprobada.

**SHA al que se refiere esa evidencia:** `a0583df14a5367f2ac8b33c3c3711fb84373ba65`.

<a id="bl-084"></a>

### BL-084 — D9: permiso para reemplazar destino directo de otra lista

**Estado:** 🟡 DECISIÓN · **Prioridad:** P1 · **Bloque:** Decisiones · **Alcance:** actual.

**Responsable:** Adrián; propuesta 01, registra 00. **Dependencias:** Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.

**Requisitos:** [RF-26](../requisitos/REQUISITOS-PRODUCTO.md#rf-26), [RF-04](../requisitos/REQUISITOS-PRODUCTO.md#rf-04).

**Aceptación:** Decidir operador con alcance de sucursal o solo administrador; implementar validación servidor y auditoría según decisión documentada.

**Evidencia/referencia:** [docs/qa/informes/24-qa-B3-rev6-RF26-a0583df.md](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md)

**Hallazgo:** Propuesta de Claude, no decisión aprobada.

**SHA al que se refiere esa evidencia:** `a0583df14a5367f2ac8b33c3c3711fb84373ba65`.

## Regla de cierre

00 registra el dictamen por alcance después de revisar la entrega. Si hay un nuevo SHA, evaluar qué tareas afecta y reabrir lo necesario. Pruebas de equipo físico, CI y producción llevan evidencia propia. No cerrar padres automáticamente porque una subtarea esté verde. El manifiesto de consolidación acredita copias, no funcionalidad del producto.
