# Semáforo del proyecto — LUMIN TV

Fecha: 2026-09-19 · Versión: 1.7 · Responsable: 00 — Coordinación y QA.

Último SHA revisado: `14f0bc51b5f7330a046d99ac870036747366c586`. No es una consulta en vivo a GitHub.

**Estado global:** 🔴 QA26: RF26-QA-02/03 y DOC-R7-01 cerrados en alcance ensayado. Nuevos RF26-QA-04/05/06: concurrencia, identidad estable entre consultas y borrado de lista. PG61 local y CI verdes; B3 diseño y decisiones/físico pendientes.

## Leyenda

| Señal | Significado |
|---|---|
| 🟢 Verde | Verificado solo para el alcance/evidencia de la tarea. |
| 🟡 Amarillo | Parcial o decisión pendiente; no implica que un agente esté ejecutándolo ahora. |
| 🔴 Rojo | Corrección identificada pendiente de cierre. |
| ⚪ Blanco | No iniciado/no probado; revisar dependencias antes de asignar. |
| 🔵 Azul | Futuro diferido; sin encargo de implementación. |

## Resumen de tareas

Los conteos son inventario, **no porcentaje de avance ni estimación de esfuerzo**.

| Estado | Tareas |
|---|---|
| 🟢 VERIFICADO ACOTADO | 15 |
| 🟡 PARCIAL | 7 |
| 🟡 DECISIÓN | 10 |
| 🔴 CORRECCIONES | 1 |
| ⚪ PENDIENTE | 33 |
| 🔵 DIFERIDO | 18 |
| **Total** | **84** |

## Semáforo por bloque

La señal es la condición más restrictiva registrada en cada bloque; leer los pendientes. Un bloque compuesto no recibe verde porque tenga una prueba aprobada.

| Bloque | Señal | Verificado | Parcial/decisión | Correcciones | Pendiente | Diferido |
| Gestión | 🟡 INCOMPLETO | 1 | 0 | 0 | 1 | 0 |
| B1 | 🟡 INCOMPLETO | 2 | 1 | 0 | 1 | 0 |
| B2 | 🟢 ALCANCE VERIFICADO | 2 | 0 | 0 | 0 | 0 |
| QA | 🟡 INCOMPLETO | 1 | 0 | 0 | 1 | 0 |
| B3 diseño | 🔴 CORRECCIONES | 6 | 2 | 1 | 1 | 0 |
| Decisiones | 🟡 INCOMPLETO | 1 | 8 | 0 | 2 | 0 |
| B3 implementación | 🟡 INCOMPLETO | 0 | 1 | 0 | 6 | 0 |
| B4 | ⚪ PENDIENTE | 0 | 0 | 0 | 3 | 0 |
| B5 | 🟡 INCOMPLETO | 1 | 2 | 0 | 4 | 0 |
| B5/B8 | ⚪ PENDIENTE | 0 | 0 | 0 | 2 | 0 |
| B6 | 🟡 INCOMPLETO | 1 | 2 | 0 | 5 | 0 |
| B7 | ⚪ PENDIENTE | 0 | 0 | 0 | 2 | 0 |
| B8 | ⚪ PENDIENTE | 0 | 0 | 0 | 3 | 0 |
| Release | 🟡 INCOMPLETO | 0 | 1 | 0 | 2 | 0 |
| Comercial / expansión | 🔵 DIFERIDO | 0 | 0 | 0 | 0 | 18 |

## Siguiente trabajo concreto

| Tarea | Responsable | Cierre esperado |
|---|---|---|
| [BL-004](17-backlog-maestro.md#bl-004) — Regresión caché, cuarentena, comando y datos obsoletos | 01 + 00 | Repetir todos los recorridos señalados en informes B1 y sus correcciones sobre un SHA; identificar compilación y límites. |
| [BL-011](17-backlog-maestro.md#bl-011) — Completar matriz RLS, marcas y rol del espejo | 01 | DDL/roles/políticas permiten mutación+marca, auditoría, espejo y backup; controles negativos impiden cruce. |
| [BL-016](17-backlog-maestro.md#bl-016) — Revisar diseño B3 corregido y fijar aceptación | 00 | Dictamen documental por versión/SHA; cero hallazgos críticos de diseño abiertos; implementación requiere encargo posterior. |
| [BL-076](17-backlog-maestro.md#bl-076) — Diseñar destinos y grupos de TVs; impacto en B3 | 01; revisa 00 | Numeración concurrente segura por pantalla; generación estable entre latidos sin cambios y distinta en L1→L2→L1; borrado coherente conservando ID de pantalla. Preservar aislamiento por empresa/sucursal, ACK monótono y movimiento transaccional. |
| [BL-081](17-backlog-maestro.md#bl-081) — Recarga Roku con playlist idéntica | 01; revisa 00 | Recargar reinicia sin depender de JSON distinto; 21 comprobaciones aisladas pasan. Completar F23 físico con protocolo de corte realizable y build 62. |

## Decisiones del propietario

| Tarea | Decisión | Dependencias |
|---|---|---|
| [BL-017](17-backlog-maestro.md#bl-017) | D1: decidir números de pantallas duplicados | [BL-012](17-backlog-maestro.md#bl-012) |
| [BL-018](17-backlog-maestro.md#bl-018) | D2: decidir permisos efectivos e inválidos por usuario | [BL-012](17-backlog-maestro.md#bl-012) |
| [BL-019](17-backlog-maestro.md#bl-019) | D3/D4: aprobar política RLS y ventana del espejo | [BL-016](17-backlog-maestro.md#bl-016) |
| [BL-021](17-backlog-maestro.md#bl-021) | Autorizar implementación acotada B3 | [BL-016](17-backlog-maestro.md#bl-016), [BL-019](17-backlog-maestro.md#bl-019), [BL-074](17-backlog-maestro.md#bl-074) |
| [BL-049](17-backlog-maestro.md#bl-049) | D5: ventana y autorización de despliegue | [BL-048](17-backlog-maestro.md#bl-048), [BL-005](17-backlog-maestro.md#bl-005), [BL-017](17-backlog-maestro.md#bl-017), [BL-018](17-backlog-maestro.md#bl-018), [BL-019](17-backlog-maestro.md#bl-019) |
| [BL-051](17-backlog-maestro.md#bl-051) | Acordar límites de espera, formatos y equipo piloto | Definir con el equipo |
| [BL-052](17-backlog-maestro.md#bl-052) | Autorizar entorno de correo y política de acceso | Definir con el equipo |
| [BL-074](17-backlog-maestro.md#bl-074) | D7: decidir sesiones al revertir | [BL-010](17-backlog-maestro.md#bl-010) |
| [BL-083](17-backlog-maestro.md#bl-083) | D8: concretar semántica persistente y alcance por sucursal de grupos | Definir con el equipo |
| [BL-084](17-backlog-maestro.md#bl-084) | D9: permiso para reemplazar destino directo de otra lista | Definir con el equipo |

## Qué sí está comprobado

| Tarea | Alcance exacto | Evidencia |
|---|---|---|
| [BL-001](17-backlog-maestro.md#bl-001) | Entradas AGENTS/CLAUDE, roles e índice disponibles; enlaces comprobados. | [docs/coordinacion/consolidacion-2026-09-16.json](../coordinacion/consolidacion-2026-09-16.json) |
| [BL-002](17-backlog-maestro.md#bl-002) | Una URL falla y reintenta a 30 s sin nuevos mensajes; cinco esperas y seis intentos sin duplicados. | [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md) |
| [BL-003](17-backlog-maestro.md#bl-003) | Reconciliaciones idénticas no reactivan sin_espacio; cambio efectivo sí. | [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md) |
| [BL-006](17-backlog-maestro.md#bl-006) | Diez pruebas originales pasan ahora con pytest dentro de las 21 de servidor en ce4716f; sin cambios del producto B2 desde revisión previa. | [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md) |
| [BL-007](17-backlog-maestro.md#bl-007) | Tres funciones HEAD pasan con las diez previas; tamaños/cabeceras/404 y ausencia de incremento comprobados. | [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md) |
| [BL-008](17-backlog-maestro.md#bl-008) | PG61 ejecutado por Codex, sin omitidos. CI35435820477: 28 servidor/61 PG/42+21 Roku/compilación. Producto idéntico a c42770f por hashes. Pruebas verdes no cierran los tres contraejemplos adicionales de QA26. | [docs/qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md](../qa/informes/26-qa-B3-rev8-RF26-14f0bc5.md) |
| [BL-009](17-backlog-maestro.md#bl-009) | Protocolo cubre A reserva/B confirma/espejo/A confirma, sin tercer cambio; marcas pendientes y snapshot coherente. | [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md) |
| [BL-010](17-backlog-maestro.md#bl-010) | Contrato de sesiones/rollback y barrera completa ensayados en PG55: revocadas no se reactivan, idle/peticiones tardías no escriben tras drenaje y otra base sobrevive. No implementa rollback productivo ni resuelve decisión D7. | [docs/qa/informes/25-qa-B3-rev7-RF26-050cc2d.md](../qa/informes/25-qa-B3-rev7-RF26-050cc2d.md) |
| [BL-012](17-backlog-maestro.md#bl-012) | Ocho pruebas del inventario pasan: casos originales de ruta/archivos/JSON/forma raíz, vacío y alias. No equivale a validación exhaustiva de todos los campos anidados. | [docs/qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md) |
| [BL-013](17-backlog-maestro.md#bl-013) | Contexto inicial de membresía y documentos del espejo precisados en diseño rev4 y ensayos del DDL mínimo. No aprueba implementación completa ni reversión de BL-010. | [docs/qa/informes/22-qa-B3-rev4-B5a-1f7782e.md](../qa/informes/22-qa-B3-rev4-B5a-1f7782e.md) |
| [BL-014](17-backlog-maestro.md#bl-014) | Contrato mínimo PG/archivos rev5 distingue publicado/ya_publicado/perdido; conserva artefacto al reintentar misma posesión y descarta solo al perder. Ensayos ejecutados, no trabajadores de producto. | [docs/qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md](../qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md) |
| [BL-015](17-backlog-maestro.md#bl-015) | B3-R4-01 y B3-R6-01 cerrados en ensayos: termina todas las sesiones de aplicación de la base objetivo, bloquea nuevas y preserva otros roles y otras bases. No es ejecución real de corte/smoke en VPS. | [docs/qa/informes/25-qa-B3-rev7-RF26-050cc2d.md](../qa/informes/25-qa-B3-rev7-RF26-050cc2d.md) |
| [BL-075](17-backlog-maestro.md#bl-075) | Cobertura delimitada al DDL mínimo y guardián con control negativo de propietario ejecutados dentro de 39 ensayos PG. No acredita repositorios/esquema completo aún no implementados. | [docs/qa/informes/22-qa-B3-rev4-B5a-1f7782e.md](../qa/informes/22-qa-B3-rev4-B5a-1f7782e.md) |
| [BL-080](17-backlog-maestro.md#bl-080) | POST/PUT recargar/vaciar_cache deniegan operador con 403 sin encolar ni avanzar n; permiten admin. Suite verifica sucursal ajena. | [docs/qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md](../qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md) |
| [BL-082](17-backlog-maestro.md#bl-082) | Rev3: 33 combinaciones de ancho sin desbordamiento y captura propia inspeccionada. Cierre acotado del ancho, no frontend/API ni accesibilidad completa. | [docs/qa/informes/24-qa-B3-rev6-RF26-a0583df.md](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md) |

## Qué sigue sin verificarse

Roku físico, nueva persistencia PostgreSQL, migración/rollback implementados, frontend nuevo, autenticación por correo nueva, multiempresa operativa y módulos comerciales. La operación previa informada por Adrián no sustituye validar estos cambios.

## Actualización

01 entrega SHA y evidencia por BL/QA; 00 evalúa y actualiza backlog.json, incrementa versión/fecha y regenera las vistas. 02/03 solo actualizan por el canal de entrega asignado. No hay sincronización automática con GitHub ni monitoreo de chats. El [documento común](16-coordinacion-agentes.md) define roles y autorizaciones; este tablero registra avance.

[Backlog detallado](17-backlog-maestro.md) · [Requisitos](../requisitos/REQUISITOS-PRODUCTO.md) · [Fuente de datos](backlog.json).
