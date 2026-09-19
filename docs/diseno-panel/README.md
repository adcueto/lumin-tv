# Panel v2 — propuesta visual (B6, láminas antes de código)

`prototipo.html` es una maqueta estática con datos de ejemplo: no habla con
ningún servidor, no guarda nada y no es código del producto. Sirve para que
Adrián apruebe o corrija la interfaz **antes** de programar el panel React
(decisión `21-decision-tecnologias-v2.md`). Las capturas en `capturas/` se
generan con `capturar.py` (Playwright, Chromium) a 1366×860 (escritorio) y
390×844 (celular).

## Qué propone

| Pantalla | Para quién | Qué resuelve |
|---|---|---|
| Inicio | Adrián en escritorio; recepción en celular | Estado real de cada pantalla (B5a): qué reproduce, cache, versión, sin red desde cuándo; avisos accionables (archivo que falta, app vieja, pantalla sin conexión) |
| Pantallas | Administración | Aprobar pantallas nuevas con su código; número único por sucursal (fin de los dos P6); "Lista al aire" como lista base; turnos por pantalla; recargar y vaciar cache (B5a); mover, renombrar, eliminar bajo ⋯ |
| Mostrar ahora | Recepción en celular | **Un solo flujo** para foto, video o mensaje: dónde, qué, cuánto tiempo; recientes a un toque; "Ahora mismo" lista lo que está fuera de la lista y permite quitarlo (unifica "Mostrar al cliente" y "Enviar a…") |
| Turnos | Recepción en celular | Estado del punto de venta, turno en pantalla con tiempo restante, próximos, anuncio manual con duración; deduplicación declarada |
| Biblioteca | Adrián | Subida con límites explícitos (80 MB por la cache de la TV), filtros, "sin usar", archivos que faltan marcados, conversión en curso, reproducciones **confirmadas** (no descargas) |
| Listas | Adrián | Lista base + listas propias, orden arrastrable, segundos por foto; **RF-26: "Reproducir en…"** con pantallas individuales y grupos de la sucursal, destino efectivo con la regla de prioridad (lista propia > programada > lista al aire) y estados de entrega por pantalla: *enviada* (guardada), *recibida* (la TV la pidió en su latido), *reproduciendo* (la TV confirmó); el tiempo se mide, no se promete |
| Usuarios y permisos | Adrián | Permisos explícitos por sucursal; usuario sin sucursales marcado (QA-F01); rol "integración" para el POS |

Navegación: las once secciones del plan (`10-…md §4.2`) en menú lateral en
escritorio; en celular, barra inferior con Inicio, Mostrar, Turnos, Pantallas
y Más. Programación, Mensajes, Sucursales e Integraciones se diseñan en su
bloque; aquí solo están como marcador.

Marca: los tokens del panel actual (rosa `#EFAFC7`, rosa fuerte `#EC3A80`,
dorado `#C8A96A`, tinta `#1F1F1F`, gris `#6B7280`, Poppins). Nada del tema
oscuro de la TV, que es otra pieza.

## Revisión 2 (respuesta a UI-QA-01 y ajustes de producto del informe 22)

- **UI-QA-01** confirmado: a 360 y 390 px el documento medía 580–655 px en
  Pantallas, Mostrar ahora, Listas y Usuarios. Corregido con
  `minmax(0,1fr)` en la rejilla, `min-width:0` en `main` y columnas, tablas
  anchas en un contenedor con desplazamiento propio (aviso "desliza"), tira de
  recientes contenida. `comprobar_anchura.py` verifica que
  `document.scrollWidth == viewport` en 360, 390 y 1366 para las once
  secciones; sale 1 si alguna desborda. Capturas regeneradas.
- **RF-26** incorporado en Listas (ver tabla). Es requisito pendiente de
  implementación (BL-076–079), no funcionalidad entregada.
- Retirada la promesa "menos de 10 s"; sustituida por los tres estados de
  entrega medibles. "Reproducciones confirmadas" en Biblioteca depende de la
  propuesta 7 (confirmación desde la TV), aún no implementada: es diseño.

## Revisión 3 (respuesta a "Panel y RF-26" del informe 23)

La semántica completa de destinos, grupos, prioridad, confirmación de
reemplazo, contrato de datos y estados de entrega está en
`docs/coordinacion/22-rf26-destinos-de-lista.md` (con las decisiones D8 y
D9). El prototipo muestra ahora la regla de prioridad, la prioridad editable
por grupo, el cuadro de confirmación de reemplazo con pantallas únicas y los
estados "recibida" y "reproduciendo" etiquetados como diseño hasta B5b y la
propuesta 7. Sigue siendo una propuesta; nada de esto está implementado.

## Supuestos que Adrián debe confirmar o corregir

1. La recepcionista usa el panel desde el **celular** para Mostrar ahora y
   Turnos; Adrián usa el **escritorio** para Biblioteca, Listas, Pantallas y
   Usuarios. Si es al revés en algún caso, cambia qué se diseña primero.
2. "Lista al aire" es el nombre de la lista base de cada sucursal (hoy es la
   opción vacía del selector). Se puede llamar de otra forma.
3. Los botones de operación remota (↻, ⌫) y eliminar son solo de administrador.
4. El flujo unificado de "Mostrar ahora" sustituye a "Mostrar al cliente" y
   "Enviar a…" del panel actual.

## Qué NO es

No hay componentes React todavía, ni llamadas a la API, ni estados de carga,
vacío, error o falta de permiso (esos se implementan en B6 con la regla del
plan: sin datos simulados y con permisos aplicados en el servidor).
