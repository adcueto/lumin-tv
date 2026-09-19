# LTV-006A — Primera entrega solicitada a Antigravity

> Propuesta de encargo histórica, no activada por su existencia. Ver roles y alcance actuales en [16-coordinacion-agentes.md](16-coordinacion-agentes.md) antes de iniciar frontend, portal o web comercial.

Estado: Pendiente. Documento preparado; no enviado.
Responsable: Antigravity, frontend y experiencia visual. Revisión: Codex.

## Objetivo y alcance

Preparar una propuesta revisable de navegación y componentes del panel empresarial desde el brief y el panel existente en `servidor/servidor_lumin.py:1559` de `ea610d6fbea8dac7c330f0ba134cf41e5d92fcdc`. Es HTML/CSS/JavaScript embebido, con fetch a API real, selector de sucursal, pantallas, listas, biblioteca, turnos y estadísticas. No hay frontend Vue implementado. No seleccionar un stack nuevo ni reemplazar la aplicación.

## Entrega concreta

1. Mapa de navegación para los 14 módulos del encargo: resumen, sucursales, pantallas, listas, biblioteca, campañas, operación de turnos, configuración de turnos, mensajes, empleado del mes, menú, usuarios, suscripción y configuración.
2. Propuesta de estructura con menú lateral, selector global de sucursal y pestañas internas. Separar panel de superadministrador y portal de empresa.
3. Bocetos de Resumen, Pantallas y detalle de pantalla, con estados cargando, vacío, error, sin permiso, desconectado y suspensión neutral para la pantalla pública.
4. Inventario propuesto de componentes: navegación, selectores, tarjetas, tablas, filtros, formularios, diálogos, avisos y estados. Identidad neutral con personalización LUMIN opcional según paleta del brief.
5. Matriz de datos necesarios y acciones por vista para acordar con Claude; no inventar URLs, propiedades de respuestas ni acciones de dispositivo.
6. Inventariar componentes/funciones reutilizables y presentar diff previsto para un primer bloque visual acotado. Por ahora entregar propuesta en archivos propios: no editar el monolito en paralelo con Claude.

## Condiciones

No simular integración terminada. Datos de bocetos identificados como demostración; no inferir audiencia o ventas desde reproducciones. Diferenciar resincronizar, reiniciar app y reiniciar equipo, según capacidades comprobadas. No publicar web ni habilitar cobros. Implementación conectada depende de LTV-003.

## Pruebas y criterios de aceptación

- Trazabilidad de cada vista al brief y de cada dato pendiente a la matriz contractual.
- Propuesta responsive a 360, 768 y 1440 px, sin pérdida de acciones críticas ni desbordamiento global.
- En implementación: teclado, foco visible y restaurado en diálogos, etiquetas, errores asociados a campos, contraste verificable, estados que no dependan solo del color.
- Selector de sucursal consistente; aislamiento real validado por backend, nunca solo por ocultación visual.
- Sin testimonios, métricas ni disponibilidad ficticios.
- Bocetos/capturas con versión; si hay código, rama/SHA, diff, pruebas y limitaciones según 06.

Codex evaluará esta primera entrega como propuesta de diseño. Integración API y accesibilidad funcional permanecen NO PROBADAS hasta contar con implementación verificable.
