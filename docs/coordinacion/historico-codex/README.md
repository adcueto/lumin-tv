# LUMIN TV — Coordinación técnica y QA

## Entrada vigente — 2026-09-16

Leer primero [16-coordinacion-agentes.md](16-coordinacion-agentes.md), documento común LTV-COORD-001 v1.0: nombres de chats, roles, alcance, estado y formato de intercambio. La entrada para agentes es [AGENTS.md](../AGENTS.md).

Última revisión registrada: [15-qa-R3-y-diseno-B3-rev2-78306df.md](15-qa-R3-y-diseno-B3-rev2-78306df.md), SHA `78306df3f81b53328cd7fbdd07b294d3b0a1c262`, correcciones requeridas. Los mensajes persistentes se guardan en [intercambio/](intercambio/README.md).

**Lo que sigue se conserva como registro histórico inicial.** Sus frases sobre estado, tareas pendientes y destino de transferencia no representan el tablero actual. La referencia local vigente y las reglas de copias están en el documento 16; no implica publicación en GitHub.

Fecha: 2026-09-15. Responsable: Codex. Propietario: Adrián Pérez Cueto.

## Estado

Repositorio clonado por indicación del propietario desde `https://github.com/adcueto/lumin-tv`, rama `main`, SHA `ea610d6fbea8dac7c330f0ba134cf41e5d92fcdc`. Línea base limpia antes de añadir este paquete. Inspección estática y 9 casos locales de caracterización completados; se reprodujeron defectos y brechas. No hay aprobación de producto ni de lanzamiento SaaS.

## Documentos

- `01-inspeccion-inicial.md`: evidencia local y brechas.
- `02-plan-y-tablero.md`: prioridades, responsables y aceptación.
- `03-entrega-claude.md`: primera tarea para desarrollo principal.
- `04-entrega-antigravity.md`: primera tarea para frontend.
- `05-contratos-api.md`: registro por completar y decisiones pendientes.
- `06-protocolo-y-qa.md`: entrega, revisión y pruebas.
- `07-decisiones-y-pendientes.md`: límites, decisiones y bloqueos.
- `08-encargo-original.txt`: especificación íntegra del propietario.
- `09-auditoria-codigo.md`: arquitectura real, brechas y defectos con referencias.
- `qa_caracterizacion.py` y `qa-resultados.json`: herramienta y evidencia de 9 casos locales. Su salida exitosa confirma la reproducción de comportamientos, incluidos defectos; no significa seguridad aprobada.

## Ubicación y canales

Destino solicitado: `C:\Users\adcueto\Claude\lumin-tv\docs\coordinacion`.
La copia preparada en el espacio de esta tarea es un borrador de transferencia; una vez instalada en el destino, este será la referencia compartida. Evitar editar ambas copias de forma independiente.

Se inspeccionó el catálogo de herramientas disponible: no se identificó un canal dedicado a Claude o Antigravity. No se les han enviado mensajes ni iniciado tareas. Las entregas son documentos para transferencia. No se configuró monitoreo automático.
