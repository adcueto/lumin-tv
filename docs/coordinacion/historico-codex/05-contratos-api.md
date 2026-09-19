# Registro de contratos API existentes y propuestas pendientes

Fecha: 2026-09-15. Base `ea610d6fbea8dac7c330f0ba134cf41e5d92fcdc`. Inventario estático del servidor; los casos locales ejecutados se delimitan en 09. Estos contratos heredados no constituyen un contrato SaaS aprobado. No se realizaron peticiones al dominio de producción.

## Inventario real

Referencias a `servidor/servidor_lumin.py`. Todas las rutas POST también se despachan mediante PUT, porque `do_PUT = do_POST` en 1463; la documentación anterior solo destaca PUT para turnos. Revisar esta amplitud antes de diseñar una versión nueva.

| Método | Rutas | Autorización / referencia |
|---|---|---|
| GET | /playlist.json?id=... | Sin sesión; aprobación por ID, 727 |
| GET | /videos/<sucursal>/<archivo>, /rapidos/<sucursal>/<archivo>, /miniaturas/<sucursal>/<archivo> | Sin sesión, 775/789/798 |
| GET | /manifest.json, /sw.js, /icono-192.png, /icono-512.png | Públicos, 811–821 |
| GET | /, /index.html | Login sin sesión; panel con sesión, 824–834 |
| GET | /api/yo | Sesión, 836 |
| GET | /api/usuarios | Admin, 839 |
| GET | /api/sucursales | Sesión y sucursales_permitidas, 849 |
| GET | /api/listas, /api/biblioteca, /api/lista | Sesión, _sucursal_de; lista opcional para /api/lista, 852/856/875 |
| GET | /api/tvs, /api/ajustes, /api/estadisticas | Sesión, _sucursal_de, 893/903/907 |
| GET | /api/tv/pendientes | Admin, 897 |
| POST/PUT | /api/login | Credenciales; sin sesión previa, 977 |
| POST/PUT | /api/logout | Sesión, 995 |
| POST/PUT | /api/usuarios, /api/usuarios/eliminar | Admin, 1001/1014 |
| POST/PUT | /api/subir, /api/rapido | Sesión; subida/control de contenido, 1026/1062 |
| POST/PUT | /api/sucursales | Admin, 1109 |
| POST/PUT | /api/ajustes, /api/programar, /api/duracion, /api/eliminar | Sesión y sucursal, 1122/1140/1161/1174 |
| POST/PUT | /api/listas/crear, /api/listas/renombrar, /api/listas/eliminar, /api/listas/activar, /api/listas/contenido | Sesión y sucursal, 1197/1209/1222/1245/1257 |
| POST/PUT | /api/renombrar, /api/mover | Sesión y sucursal, 1279/1328 |
| POST/PUT | /api/turno | Sesión y sucursal, 1345 |
| POST/PUT | /api/tv/aprobar, /api/tv/eliminar | Admin, 1376/1395 |
| POST/PUT | /api/tv | Pantalla permitida; fallo en autorización del destino, 1409 |
| POST/PUT | /api/tv/comando | Pantallas permitidas; pausa/continuar/reproducir/silencio/sonido, 1429 |

La presencia de comprobaciones de sucursal no implica seguridad aprobada: ver F01/F02. Los esquemas detallados de las operaciones auxiliares deben completarse antes de modificarlas; no sustituir esta tabla por un OpenAPI inventado.

## Contratos críticos heredados

### Login

POST /api/login: JSON `usuario`, `contrasena`; éxito 200 `{"ok":true}` con cookie sesion HttpOnly/SameSite=Lax, 30 días. Fallo 401. Cookie sin Secure en código. Sesión requerida por API administrativa; roles admin/usuario. No existe identidad Empresa en este contrato.

### Playlist Roku

GET /playlist.json?id=<GetChannelClientId>, ID truncado a 64 caracteres. Para dispositivo no aprobado: 200 con pendiente, codigo, vertical, giro. Para aprobado: 200 con videos[], mensaje, cintillo, velocidad, vertical, giro, comando y turno. Cada item tiene title, url, tipo, duracion, mini. Comando y turno llevan n; {n:0} cuando no hay evento. GET registra/actualiza presencia del dispositivo. Host/X-Forwarded-Proto influyen en URLs; configuración del proxy no auditada.

Consumidor: roku-app/components/PlaylistTask.brs y MainScene.brs. No token enviado por el reproductor. Mantener forma de respuesta y transición explícita al introducir autenticación. Pendiente prueba física de todos los campos.

### Turno

POST/PUT /api/turno con cookie: sucursal en cuerpo o query; numero hasta 8 caracteres, estacion hasta 20, espera hasta 10, duracion convertida a entero y limitada a 5–300 (defecto 60), proximos hasta 3 objetos con numero/estacion. Éxito 200 {ok:true}. No requiere numero no vacío en implementación, aunque docs/API-turnos.md lo marca obligatorio. Tipos malformados no cubiertos integralmente; no prometer validación exhaustiva.

Guarda un único turno por sucursal con n incremental y ts; no cola ni clave de deduplicación. Pantallas con turnos habilitados lo reciben en playlist. Un usuario puede tener varias sucursales; la documentación de “su propia sucursal” simplifica el comportamiento real. Documentar rechazos explícitos como corrección del control de acceso, conservando casos autorizados.

### Medios y métricas

GET de medios sirve bytes y soporta Range en _servir_archivo. No hay token ni empresa. La lectura /videos incrementa contadores por solicitud sin Range o con bytes=0-, incluso antes de 404. /api/estadisticas responde nombre/hoy/d7/d30, no confirmaciones de reproducción ni personas. Diseñar telemetría nueva sin reinterpretar estos datos históricos como visualizaciones comprobadas.

### ECP LAN

docs/API-control-roku.md y vigilante/vigilante_lumin.py describen GET query/apps, query/active-app y POST keypress/PowerOn, keypress/PowerOff, launch/<canal> en puerto 8060. Es comunicación local separada de la API Python; no se ha probado ninguna TV física en esta sesión. La guía contiene recomendaciones de configuración inconsistentes entre preparación y prueba mínima: verificarlas en equipos antes de publicar una matriz.

## Compatibilidad y propuestas

El diseño histórico pide preservar playlist, turno y URLs /videos. El nuevo requisito de medios/dispositivos autenticados exige diseñar una transición: no prometer conservar acceso público indefinidamente ni cortar Roku sin migración. FastAPI/Vue/SQLite/PostgreSQL/CDN están propuestos en el documento histórico; ninguno se da por implementado o aprobado por este inventario.

## Ficha por operación existente

| Campo obligatorio | Evidencia requerida |
|---|---|
| ID, versión, método y ruta exacta | Registro de rutas y archivo:línea |
| Estado | Existente verificado / propuesta / transición / retirado |
| Consumidores | Roku, panel, LUMIA u otros, con referencia a código |
| Autenticación | Tipo de identidad, emisión, vencimiento, renovación y revocación; sin secretos |
| Autorización y pertenencia | Roles, empresa, sucursal y dispositivo; origen confiable y validaciones |
| Entrada | Parámetros, cuerpo, tipos, límites y reglas; ejemplos depurados |
| Salida y errores | Esquema, códigos, paginación si existe y comportamiento observable |
| Efectos y concurrencia | Escrituras, transacciones, cuotas y condiciones de carrera |
| Reintentos y duplicados | Regla de idempotencia, ámbito, persistencia y caducidad acordados |
| Versionado y compatibilidad | Consumidores afectados, transición y prueba Roku |
| Pruebas | Positivas, negativas y regresión sobre SHA identificable |

## Decisiones contractuales pendientes

- Resolución confiable de empresa/sucursal y permisos; nunca confiar solo en IDs del cliente.
- Vinculación temporal, tokens mínimos revocables, caducidad offline y recuperación.
- Listas/campañas: zona horaria, prioridades, desempate, límites temporales y respaldo deterministas.
- Eventos: identidad estable, duplicados, orden, recepción tardía y semántica exacta de reproducción.
- LUMIA: correspondencia de empresa/sucursal en ambos sistemas, transporte comprobado, permisos, auditoría, reintentos y dependencias Turnos + Conector.
- Catálogo único versionado, moneda, impuestos pendientes, capacidades, cuotas y excepciones administrativas auditadas.
- Consumo concurrente, cambios de plan, retención de contenido y acceso para regularizar pagos.

Claude propone a partir del código; Codex revisa seguridad, regresión y verificabilidad; Antigravity valida que cubra sus vistas. Adrián decide políticas comerciales y de producto que requieran decisión. Registrar acuerdos en 07 antes de conectar frontend o cambiar reproductores.
