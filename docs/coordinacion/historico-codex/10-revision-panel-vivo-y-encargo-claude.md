# LUMIN TV — Revisión del panel real y encargo de mejora

Fecha: 15 de septiembre de 2026.
Página: https://tv.luminbelleza.com/
Objetivo vigente: mejorar LUMIN TV; comercialización multiempresa, suscripciones y panel del propietario quedan para después.

## Alcance de la inspección

Inspección visual y del árbol de accesibilidad de la pestaña autenticada proporcionada por Adrián. Sucursal seleccionada: Plaza de la Mujer. Se recorrió la página mediante desplazamiento y se devolvió al inicio. No se editaron campos, cambiaron sucursales, enviaron comandos, reprodujeron medios, crearon usuarios ni guardaron configuraciones.

No se probaron inicio de sesión, formularios, confirmaciones de borrado, adaptación móvil, teclado completo, reproducción física Roku ni recuperación de red. No hay un dictamen de seguridad o disponibilidad de producción. Las observaciones corresponden a un momento concreto; no se estableció el SHA desplegado.

La revisión sigue la guía design:design-critique. Las recomendaciones son propuestas, no funciones implementadas.

## 1. Qué existe y debe conservarse

- Cabecera fija con marca, selector de sucursal, alta de sucursal y cierre de sesión.
- Cinco pantallas visibles en la sucursal: cuatro indicadas en línea y una sin conexión durante la observación.
- Nombre editable, lista asignada, traslado de sucursal, turnos habilitables por pantalla, pausa, sonido y eliminación.
- Mostrar al cliente: archivo y destino, con comportamiento temporal explicado.
- Anuncio manual de turno con estación y espera aproximada.
- Subida de MP4, JPG y PNG por arrastre o selección.
- Mensaje de pantalla, cintillo animado y velocidad.
- Administración de usuarios con rol y sucursal.
- Estadísticas por contenido: hoy, siete días y treinta días.
- Campañas por contenido, días de semana, fechas y horas.
- Listas con identificación de la predeterminada «al aire» y asignación particular por TV.
- Miniaturas, orden mediante flechas y duración de imágenes.
- Biblioteca con reutilización, renombrado y distinción entre quitar de lista y eliminar archivo.

No encargar estas capacidades como inexistentes. La interfaz ya expresa conceptos útiles: sucursal seleccionada, contenido reutilizable y lista predeterminada con excepciones por pantalla.

## 2. Hallazgos de usabilidad

| ID | Observación directa | Prioridad | Mejora propuesta |
|---|---|---|---|
| UI-01 | Pantallas, usuarios, campañas, listas y biblioteca se apilan en una única página extensa | Alta | Menú lateral y rutas por tarea; selector de sucursal persistente |
| UI-02 | El primer bloque ocupa gran parte de la vista con cinco pantallas; no hay resumen de salud previo | Media | Inicio con totales y alertas; listado compacto y detalle de pantalla |
| UI-03 | Dos equipos muestran el número 6 y aparecen como P6 en destinos | Alta | Investigar origen; identificador visible inequívoco por sucursal, sin modificar a ciegas el ID usado por Roku |
| UI-04 | Cada equipo presenta «Lista al aire»; el nombre concreto de la lista predeterminada aparece mucho más abajo | Media | Mostrar «Heredada: Principal» o «Asignada: nombre», y contenido efectivo en el detalle |
| UI-05 | Traslado de sucursal y eliminación se presentan junto a controles cotidianos | Alta | Separar configuración/acciones delicadas; confirmar destino e impacto antes de aplicar cambios |
| UI-06 | La TV desconectada conserva los controles de pausa y sonido; no se explica el tratamiento del comando | Alta | Definir estados pendiente/recibido/fallido y vencimiento; no dar éxito sin confirmación correspondiente |
| UI-07 | «Mostrar al cliente» deja fotos fijas; «Enviar a…» en una lista las muestra por duración. Ambos son reproducción inmediata | Alta | Un flujo «Mostrar ahora» con selección de destino y modo explícito: una vez o mantener hasta reanudar |
| UI-08 | Los cinco interruptores de turnos observados estaban desactivados, pero «Anunciar» estaba disponible | Media | Indicar número de pantallas receptoras; advertir o bloquear si ninguna recibe turnos. No se probó si ya existe validación al enviar |
| UI-09 | El texto de ayuda de turnos expone POST y /api/turno al usuario operativo | Media | Trasladar detalles técnicos a Integraciones; explicar solo quién verá el aviso y su duración |
| UI-10 | El cintillo se edita en una sola línea; el mensaje completo no cabe en el ancho mostrado | Media | Campo multilínea, vista previa local y destino explícito antes de publicar |
| UI-11 | El formulario de usuarios está mezclado con operación diaria y solicita contraseña introducida por el administrador | Alta | Sección Usuarios, invitación por correo y verificación; conservar acceso de usuarios existentes durante la transición |
| UI-12 | Estadísticas presentan cifras idénticas entre hoy/7/30 días y afirman ser reproducciones útiles para anunciantes | Alta | Verificar semántica e instrumentación antes de ofrecerlas como evidencia. La igualdad por sí sola no demuestra un error |
| UI-13 | Fechas y horas se muestran como controles nativos pequeños; aparecen fechas mm/dd/yyyy, sin rótulos visibles persistentes claros | Media | Etiquetas Desde/Hasta/Inicio/Fin, presentación local y zona horaria; resumen legible de la programación |
| UI-14 | La ayuda dice que programar saca el archivo de la lista diaria y quitar programación lo devuelve | Alta | Explicar y previsualizar impacto en listas/TV. Conservar la regla actual hasta diseñar y aprobar cualquier cambio |
| UI-15 | Biblioteca y contenido de lista repiten gran parte de los archivos; no hay búsqueda/filtros visibles | Media | Biblioteca con búsqueda/tipo/uso y selector para agregar a listas; mantener miniaturas |
| UI-16 | Se ve un nombre largo generado automáticamente para un video | Baja | Nombre amigable editable separado del identificador y del archivo original |
| UI-17 | Quitar, eliminar lista y eliminar de la nube son operaciones diferentes; existe ayuda, pero están muy expuestas | Alta | Mantener separación semántica, mostrar dependencias y confirmar borrado. No se comprobó la confirmación actual |

## 3. Jerarquía visual y accesibilidad

Conservar marca, tarjetas, miniaturas y coherencia de colores. Cambiar la distribución, no introducir una estética distinta sin necesidad.

- Desktop: usar el ancho disponible con barra lateral, contenido principal y panel de detalle cuando ayude. Evitar que cada pantalla necesite una tarjeta tan alta.
- Formularios: etiquetas persistentes además de ejemplos. Algunos campos se exponen con nombres técnicos como tNumero/tEstacion; deben tener nombres accesibles que describan su función.
- Controles: mostrar estado de sonido actual, no solo «Silenciar / activar sonido». Complementar iconos con texto o ayuda clara y foco visible.
- Botón de reproducción inmediata: durante la observación estaba deshabilitado en el árbol, pero visualmente seguía muy destacado en rosa. Diferenciar mejor el estado inactivo.
- Normalizar altura y estilo de campos: contraseña, fechas y horas tienen apariencia distinta de los controles redondeados.
- Los textos secundarios y contornos claros necesitan medición de contraste. No se midieron ratios ni se declara conformidad WCAG.
- Preservar texto junto al color para conexión: actualmente existe y es útil.
- Validar teclado y móvil en desarrollo; no se inspeccionaron en esta sesión. Mantener flechas accesibles si se añade arrastre para ordenar.

## 4. Navegación propuesta

| Sección | Contenido |
|---|---|
| Inicio | Resumen de sucursal, desconectadas, errores, campañas próximas y accesos frecuentes |
| Pantallas | Tabla/tarjetas, filtros, vinculación, detalle, lista efectiva y comandos |
| Biblioteca | Subida, búsqueda, miniaturas, propiedades y dependencias |
| Listas | Contenido, orden, duración, edición y pantallas asignadas |
| Programación | Campañas, vencimientos, prioridades si se aprueban y resumen por pantalla |
| Mensajes | Cintillo, vista previa, publicación y retirada |
| Turnos | Anuncio manual, receptores y estado de integración |
| Sucursales | Datos y administración autorizada |
| Usuarios | Invitaciones, verificación de correo y permisos |
| Integraciones | Conexión existente al POS y documentación técnica |
| Configuración | Preferencias necesarias y cuenta |

El selector de sucursal debe mantener el ámbito en todas las rutas y avisar de cambios sin guardar. La futura empresa debe ser un ámbito de datos separado; no implementar aún portal público multiempresa, suscripciones ni pantallas comerciales vacías.

## 5. Flujos de aceptación para Claude

### Pantallas

- Cada equipo es distinguible en listado, detalle y selector de destinos.
- Se distingue «hereda la lista de sucursal» de «tiene lista propia».
- La última conexión incluye fecha/hora; estar en línea no se presenta como prueba de reproducción.
- Mover un dispositivo muestra origen, destino y repercusión en contenido/turnos, con autorización en backend.
- Comandos muestran estado real; los pendientes tienen vencimiento. Validar que reconectar no ejecute comandos viejos inesperados.

### Publicar contenido

- Subir ofrece progreso, validación y errores útiles; la inspección no probó el comportamiento actual.
- Agregar a lista no reproduce de inmediato en una TV por sorpresa.
- «Mostrar ahora» identifica archivo, pantallas, modalidad y forma de volver a la lista.
- Vista previa se distingue de publicación: probar en entorno aislado que no envía comandos ni infla estadísticas.
- Eliminar de biblioteca informa dónde se usa. Retirar de lista conserva el archivo y otras listas.

### Programación y turnos

- Programar explica si el contenido deja de estar en la rotación habitual y qué pasa al terminar.
- Se muestran fecha, hora, zona y sucursal sin ambigüedad; definir cruces de medianoche y rangos inválidos.
- Anunciar turno indica receptores; no promete entrega si no hay pantallas habilitadas/conectadas.
- Reintentos no duplican anuncios; mensajes vencidos no se muestran tras reconectar.

### Usuarios y acceso

- Conservar acceso de cuentas actuales mediante transición planificada.
- Login, recuperación y verificación por código se prueban aparte: no se inspeccionaron en vivo porque había una sesión abierta.
- Códigos expiran, reenvíos/intententos se limitan y no se filtran secretos.
- Probar permiso por sucursal en servidor, no solo ocultando controles.

## 6. Separar UI de hallazgos técnicos previos

La auditoría local anterior encontró que ciertas solicitudes de medios aumentaban contadores incluso con error, permisos demasiado amplios y falta de idempotencia en turnos. Es evidencia del SHA auditado, no prueba automática de la implementación hoy desplegada. Revisar [09-auditoria-codigo.md](09-auditoria-codigo.md) y establecer versión antes de corregir.

La pérdida de internet que deja videos cargando fue reportada por Adrián; esta visita no la reprodujo. Debe mantenerse como bloque técnico prioritario, con pruebas físicas diferenciadas de pérdida de red y reinicio de Roku.

No imponer una reescritura completa para añadir navegación. Migrar por módulos y comprobar compatibilidad con Roku y el POS. Python no impide escalar; revisar servidor, persistencia, tratamiento de medios y límites de concurrencia con evidencia.

## 7. Mensaje para Claude

**Complemento al cambio de alcance: mejoras basadas en el panel real de LUMIN TV**

Codex revisó visualmente la sesión abierta de https://tv.luminbelleza.com/, sin modificar datos ni enviar comandos. La aplicación ya tiene pantallas, sucursales, listas, biblioteca con miniaturas, campañas, mensajes, turnos, usuarios y estadísticas. Conserva estas funciones; el problema principal de interfaz es que todas comparten una página extensa.

Implementa por bloques:

1. Navegación lateral y rutas, con sucursal persistente, preservando los flujos actuales.
2. Pantallas: identificadores visibles inequívocos, lista efectiva, última conexión y detalle de estado. Investiga los dos P6 observados; no cambies los identificadores técnicos sin analizar compatibilidad.
3. Unifica reproducción inmediata en un flujo explícito con archivo, destino, duración/modo y retorno a lista. Actualmente Mostrar al cliente y Enviar a… se comportan distinto para las fotos.
4. Separa acciones delicadas de pausa/sonido. Revisa confirmaciones y dependencias para traslados y borrados, sin asumir que hoy no existen.
5. Mejora campañas y cintillo con etiquetas, resumen de efectos y vista previa local. No agregues editor gráfico ni plantillas.
6. Lleva usuarios e integraciones a sus secciones. Implementa login, recuperación y verificación por correo con alta controlada; no abras registro público multiempresa.
7. Revisa la semántica de estadísticas antes de llamarlas reproducciones certificadas o usarlas para reportes comerciales.

En paralelo al diseño, prioriza el bloqueo de videos al perder internet y verifica los hallazgos de seguridad sobre el SHA actual. Multiempresa comercial, suscripciones y panel del propietario siguen pendientes; prepara el aislamiento en el diseño de datos sin construir aún esos módulos.

Entrega primero diagnóstico del checkout, mapa de navegación y alcance del primer bloque; después implementación y pruebas en un entorno aislado. Conserva la operación actual y no despliegues ni migres datos reales sin autorización. No declares probadas las rutas, formularios o condiciones Roku que solo fueron observadas o reportadas.
