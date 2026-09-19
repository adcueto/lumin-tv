# RF-26 — Playlists por TV y por grupo

PARA: 01 — LUMIN TV · Desarrollo  
DE: 00 — LUMIN TV · Coordinación y QA  
BLOQUE: RF-26 · selección de destinos y grupos de TVs  
ESTADO: REQUISITO REGISTRADO · DISEÑO PENDIENTE

Fecha: 2026-09-19 · Versión: 1.0. Fuente: petición de Adrián de elegir desde cada playlist las TVs individuales o grupos donde reproducir, usando como referencia conceptual los grupos de bocinas. La analogía describe una experiencia deseada; no solicita integrar Spotify ni Alexa.

## Necesidad expresada por el propietario

La aplicación debe tener una biblioteca de playlists. Desde cada playlist, el usuario puede elegir una TV, varias TVs o un grupo de TVs donde quiere mostrarla. Los grupos tienen nombres comprensibles, por ejemplo «Recepción», «Área de manicure» o «Todas las TVs de la sucursal».

Una playlist se reutiliza en varios destinos, sin crear copias solo para asignarla a varias TVs. Debe poder verse desde la lista dónde está asignada y desde cada TV cuál es su lista efectiva y por qué.

## Flujo propuesto

1. Entrar a **Playlists**, crear/editar una lista o abrir una existente.
2. Pulsar **Reproducir en…**.
3. Seleccionar TVs individuales y/o grupos. Mostrar nombre, sucursal y estado de conexión; filtrar por sucursal y buscar por nombre.
4. Presentar un resumen de las TVs únicas afectadas y de qué asignaciones cambiarán. Si una TV aparece individualmente y dentro de un grupo, contarla una sola vez.
5. Confirmar la publicación y mostrar el resultado por TV. Diferenciar asignación guardada, recepción por el dispositivo y reproducción confirmada. No llamar «reproduciendo» a una TV solo por guardar la selección.

Ejemplo: «Promociones de uñas» → Reproducir en → grupo «Área de manicure» → TV Manicure 1 y TV Manicure 2. «Servicios premium» puede quedar en la TV de recepción.

En **Pantallas → Grupos**, crear, renombrar y editar los miembros. La configuración de turnos y cintillo de cada pantalla debe conservarse al cambiar la playlist.

## Reglas propuestas para el diseño; todavía no son decisiones aprobadas

- Una TV tiene una playlist efectiva de publicidad en un momento dado. Reemplazarla debe mostrar el cambio antes de aplicar; no mezclar listas implícitamente.
- El servidor valida empresa, permisos, sucursal y compatibilidad de todos los destinos; ocultar controles en la interfaz no basta. No debe haber grupos entre empresas distintas.
- La lista y su versión publicada deben identificarse. Ante desconexión, una TV conserva el contenido disponible y recibe la última asignación vigente al reconectar; comandos antiguos no deben sobrescribirla.
- La confirmación en el servidor debe ser coherente ante errores/reintentos o cambios simultáneos. Definir publicación repetible sin duplicados y detección de edición concurrente. Esto no exige que todos los equipos conecten al mismo tiempo.
- Reutilizar una lista no debe cambiarla al editar un destino. Definir guardar borrador/publicar cambios y avisar cuántas pantallas recibirán la nueva versión.
- Ante un destino incompatible o no autorizado, explicar el motivo antes de publicar. Nunca omitir TVs silenciosamente.

## Decisiones que Desarrollo debe concretar en su propuesta

1. **Miembros nuevos o retirados del grupo:** distinguir grupo persistente que sigue su playlist de grupo usado como selección de TVs al publicar. Recomendar un comportamiento, mostrar su efecto en la interfaz y definir qué pasa al retirar una TV. No cambiar contenidos silenciosamente al editar grupos.
2. **Cruces:** si una TV puede pertenecer a varios grupos, definir resolución de dos asignaciones distintas, prioridad de selección individual, herencia de sucursal y programación horaria. Mostrar siempre la asignación efectiva y su origen. No resolver por orden accidental de consultas.
3. **Varias sucursales:** evaluar grupos y reutilización de la misma lista entre sucursales de una empresa. No afirmar que ya está soportado: en el diseño B3 rev3 revisado, pantalla/lista/contenido están relacionados por sucursal mediante llaves compuestas. Cambiar ese alcance afecta permisos y rutas de medios, y necesita una propuesta explícita; no retirar las llaves sin sustitución segura.
4. **Cambio de lista en reproducción:** proponer terminar el elemento actual o cambiar inmediatamente; explicar la opción escogida y el comportamiento offline, sin interrumpir turnos/cintillo.
5. **Eliminar grupo o lista en uso:** definir respaldo y confirmar destinos afectados. Borrar un grupo no debe borrar pantallas ni medios.

## Criterios de aceptación

- Asignar L1 a TV1 sin afectar TV2; luego L1 a TV1+TV2 con una sola selección múltiple.
- Asignar L1 a G1={TV1,TV2}; destino repetido no genera duplicados. Mostrar las TVs incluidas antes de confirmar.
- Cambiar a L2 mostrando qué cambia y resolver grupo/individual/horario según la regla aprobada. Probar grupos superpuestos y publicaciones simultáneas.
- TV2 desconectada: queda pendiente, no falsamente «reproduciendo»; al volver recibe la última asignación vigente y no una versión anterior.
- Editar miembros o eliminar grupo/lista en uso cumple la regla aprobada, mantiene un respaldo definido y conserva las pantallas y medios.
- Aislar empresas y permisos por sucursal incluso al enviar IDs ajenos directamente a la API; probar claves iguales en sucursales distintas.
- Conservar turnos del POS, cintillo y recuperación de red. Verificar reproducción en Roku físico y registrar versión/build.

## Alcance y siguiente paso

Registrar este requisito no lo declara implementado. 01 debe evaluar el impacto sobre el diseño B3 antes de congelarlo y proponer el bloque de implementación para datos/API y panel B5/B6. 02 solo participa cuando tenga un encargo concreto. El registro no cambia los dictámenes QA anteriores ni activa producción, migración, SaaS o suscripciones.

La función solicitada es asignación/distribución a destinos. **Sincronía exacta de fotogramas, video wall, audio multiroom e integración con asistentes de voz requieren requisitos y ensayos separados**; no se prometen por agrupar TVs.

Seguimiento: RF-26 y BL-076 a BL-079 en [backlog](../coordinacion/17-backlog-maestro.md). El documento se prepara para lectura de Claude; no se envía automáticamente a otro chat.
