# LTV-001 — Primera entrega solicitada a Claude

> Encargo histórico. Antes de retomarlo, leer [16-coordinacion-agentes.md](16-coordinacion-agentes.md) y la última revisión allí identificada. No sustituye el bloque vigente ni autoriza adelantar permisos/migraciones fuera de su alcance actual.

Estado: Pendiente; BLK-001 resuelto. Documento preparado; no enviado.
Responsable: Claude, desarrollo principal. Revisión: Codex.

## Objetivo

Corregir un bloque acotado de permisos sobre la base `ea610d6fbea8dac7c330f0ba134cf41e5d92fcdc` en `C:\Users\adcueto\Claude\lumin-tv`. Revisar 09 y reproducir QA-F01/F02 antes de cambiar código. No reconstruir la aplicación.

## Bloque de corrección prioritario

- QA-F01: roles usuario sin sucursales o con asignaciones inexistentes deben fallar de forma cerrada. Conservar acceso global explícito del admin. Un ID fuera del alcance debe devolver error de autorización, no redirigirse silenciosamente a otra sucursal. Resolver también el caso de lista de permisos vacía sin provocar IndexError.
- QA-F02: restringir traslado de pantalla a admin y validar destino en servidor; permitir al operador únicamente acciones autorizadas dentro de su sucursal. No basta el selector oculto del frontend.
- Añadir pruebas negativas y positivas sobre GET, mutaciones, pantalla propia/ajena, sucursal inválida y admin; comprobar regresión de POST/PUT turno y playlist Roku.
- Entregar diff atómico, SHA candidato y pruebas. No mezclar una migración de datos, cambio de framework, nuevo diseño ni contratos incompatibles.
- QA-F03/F04 y brechas de dispositivo/idempotencia: presentar estrategia y tareas separadas. No rotar credenciales de producción ni romper URLs públicas Roku sin transición acordada.

## Documentación de apoyo, reutilizando el inventario de Codex

1. Con fuente disponible, leer instrucciones y registrar raíz Git, rama, SHA y cambios locales. Preservar trabajo ajeno.
2. Documentar stack, arranque, dependencias, frontend, persistencia, modelos, migraciones, archivos, jobs y pruebas. No copiar valores de secretos.
3. Inventariar todos los GET/POST existentes y otros métodos descubiertos: ruta exacta, handler y línea, auth, permisos, alcance de empresa/sucursal, payload, respuesta, errores, consumidores y pruebas.
4. Trazar el flujo Roku: vinculación, credenciales, polling/sincronización, listas, medios, mensajes/turnos si existen, heartbeat y telemetría. Señalar versión y capacidad real.
5. Proponer arquitectura incremental para empresa → sucursal → pantalla, auth administrativa y de dispositivos, roles y aislamiento, con migraciones y recuperación. Diferenciar propuesta de código existente.
6. Preparar el contrato común a partir de evidencia y la estrategia de compatibilidad Roku; los cambios incompatibles requieren transición versionada.
7. Proponer el siguiente bloque de multiempresa/auth con archivos previstos y pruebas, separado de las correcciones anteriores. Los contratos nuevos y las migraciones requieren revisión antes de implementación.

## Exclusiones

No modificar LUMIA ni producción. No introducir planes reales, cobros, una nueva app o cambios incompatibles en este bloque. Si LUMIA requiere cambios, crear una tarea separada sin ejecutarla.

## Entregables

Inventario con referencias a archivos; registro API 05 completado en lo verificable; flujo Roku; decisiones de arquitectura propuestas; matriz de riesgos; plan de migración; primer bloque acotado. Adjuntar rama/SHA, diff, pruebas ejecutadas con entorno y salida resumida, pruebas no ejecutadas y limitaciones.

## Criterios y evaluación de Codex

- Contrastar inventario con registro real de rutas y cada consumidor Roku.
- Confirmar que no se presentan como implementados requisitos del brief.
- Revisar separación de credenciales, comprobación de pertenencia y aislamiento de API/medios/jobs/dispositivos.
- Exigir ejemplos depurados y pruebas de regresión en entorno aislado para cualquier comportamiento afirmado.
- Revisar migración y compatibilidad antes de aprobar contratos nuevos.

Aprobación de documento y aprobación de software son dictámenes distintos. Sin fuente y versión identificable: NO PROBADO.
