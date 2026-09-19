# LTV-QA-002 — Auditoría inicial de código y caracterización

Fecha: 2026-09-15. Base: main `ea610d6fbea8dac7c330f0ba134cf41e5d92fcdc`.
Servidor SHA256: `6eae0c89fcfd7534c30f4bfdc8765bdc77cbd1b28b7b9fdb95cce0b8ba646599`.
Dictamen: CORRECCIONES REQUERIDAS; sin aprobación SaaS. La aplicación principal no se modificó.

## Acceso e instrucciones

Clonado desde la URL indicada por Adrián. Git limpio al terminar el clonado. El sandbox presenta distinta identidad de propietario: se usó `git -c safe.directory=C:/Users/adcueto/Claude/lumin-tv` por comando, sin modificar configuración global.
No se encontraron AGENTS.md/CLAUDE.md ni protocolo de coordinación en el árbol. Se leyeron README y los tres documentos existentes. El diseño de julio es una propuesta histórica, no implementación ni aprobación actual. No se reescribió ese documento.
La ruta exacta de LUMIA continúa inexistente; no se inspeccionó otro checkout. No hay evidencia de conector LUMIA ejecutándose: solo contrato receptor de turnos y guía ECP.

## Arquitectura y funciones observadas

- Backend: un archivo Python de 2569 líneas con ThreadingHTTPServer, puerto configurado 8080. Persistencia JSON, RLock y reemplazo de archivos temporales; no ORM/base SQL. El candado por lectura/escritura no demuestra transacciones completas en todas las operaciones.
- Inicio con efectos: crea directorios al cargar; `migrar()` solo en ejecución principal incorpora sucursales LUMIN, aprueba dispositivos antiguos y mueve/elimina archivos históricos. No se ejecutó esa migración.
- Identidad: roles admin/usuario, sesiones con cookie por 30 días y almacenamiento JSON. Sin modelo Empresa, plan, suscripción o permisos de dispositivo en el código inspeccionado.
- Panel PWA real embebido desde línea 1559: selector de sucursal, gestión de pantallas, biblioteca/listas, mensajes, turnos, usuarios, programación y estadísticas. Conecta con fetch; no se verificó render visual ni accesibilidad en navegador.
- Programación por archivo, zona horaria global America/Mexico_City, fechas/días/horas; no motor de campañas con prioridad y zona por sucursal (369–394).
- Turnos: un anuncio vigente por sucursal con contador n y hasta 3 próximos aportados por cliente; no cola ni máquina de estados de atención. Espera es texto recibido, no cálculo (1345–1374).
- Roku: BrightScript/SceneGraph, manifest 5.1 build 56. PlaylistTask usa GetChannelClientId y GET playlist cada ciclo de espera de 4 segundos más tiempo de red; no garantía máxima de 4 segundos. MainScene maneja imagen/video, rotación, mensajes, comandos y turnos superpuestos; consulta inicial ignora comandos/turnos antiguos. Compatibilidad física y caché offline no verificadas.
- Comandos backend: pausa, continuar, reproducir, silencio y sonido. Reiniciar aplicación/equipo no son acciones de esa API. El vigilante separado usa ECP LAN para encender, lanzar y apagar Roku según horario.
- No se encontraron app Android, planes/cuotas, portal SaaS multiempresa, menú dinámico ni gestión de empleado del mes. Las imágenes de muestra de reconocimientos no implementan un módulo.
- No hay tests ni workflows CI versionados en el árbol clonado. README menciona VPS/nginx/systemd; infraestructura y despliegue real no auditados.

## Hallazgos y reproducción

Todas las referencias de líneas siguientes corresponden a servidor/servidor_lumin.py del SHA indicado. Severidad contextual al objetivo SaaS. No se afirma exposición verificada en producción.

### QA-F01 — Alta: permisos vacíos o inválidos conceden sucursales

Líneas 215–219 y 706–711. Usuario con `sucursales=[]` obtiene todas; con `['missing']` obtiene la primera. Reproducido con qa-a/qa-b. Esperado: sin asignación válida, sin acceso. Responsable Claude; estado abierto. Solicitudes fuera de ámbito también se redirigen silenciosamente a la primera permitida: revisar contrato de error.

### QA-F02 — Alta: operador traslada pantalla a sucursal ajena

Líneas 1409–1425. Handler valida pertenencia actual pero no rol admin ni permiso en destino. Fixture: operador solo qa-a, pantalla qa-tv en qa-a; POST /api/tv con destino qa-b. Observado 200 y destino persistido qa-b. Esperado: 403 y pantalla intacta. Reproducido. Selector visible solo a admin en el panel (1975) no protege la API. Responsable Claude; abierto.

### QA-F03 — Alta: bootstrap administrativo con credencial fija en código

Líneas 33–34, 152–159; hash simple en 148–149. Confirmado por revisión estática, valor omitido de este informe. Cuenta inicial usa la constante y fallback fijo; usuarios/sesiones persistidos en JSON. Cookie sin atributo Secure en 984; alcance del proxy no verificado. Responsable Claude: proponer bootstrap seguro, manejo de credenciales existentes y migración; propietario debe coordinar cualquier rotación real. No se usaron credenciales del código ni se probó acceso remoto.

### QA-F04 — Media: estadísticas cuentan peticiones incluso con 404

Líneas 775–783 incrementan contador antes de comprobar archivo. Dos GET sintéticos de un video inexistente devolvieron 404 y contador 2. Reproducción de video no establecida por estas solicitudes; reintentos/previews pueden inflar datos. Esperado: ningún 404 aumenta reproducciones; definir evento y deduplicación antes de afirmar reproducción real. Responsable Claude, texto UI Antigravity; abierto.

### QA-G01 — Alta, brecha SaaS: pantallas y medios sin credencial propia

Líneas 727–807, 435–453; PlaylistTask.brs:53–57. ID de pantalla aprobada basta para recibir playlist sin sesión/token; medio sintético conocido se entrega sin sesión. Reproducido en handlers. La aprobación por ID es comportamiento heredado, no token revocable ni aislamiento de archivos. Preparar transición compatible y acotada; no cerrar endpoints a ciegas y romper Roku.

### QA-G02 — Media, brecha del conector: turno sin idempotencia

Líneas 1345–1374. Dos POST iguales producen n=2; dos efectos de anuncio posibles ante reintento. Reproducido. El protocolo actual carece de identificador de evento/idempotencia. No equivale a un fallo contra un contrato antiguo que prometiera deduplicación; sí bloquea la garantía del nuevo conector.

## Pruebas ejecutadas y límites

Python 3.12.14. `qa_caracterizacion.py` recibe la ruta al servidor, verifica sintaxis y ejecuta el módulo con __name__ distinto de main y __file__ temporal. Crea únicamente fixtures locales; intercepta respuestas HTTP en memoria; fija reloj UTC e IP local; no ejecuta migrar, ffmpeg, servidor ni sockets.

9 casos reproducidos: permisos vacíos; permisos inválidos; playlist por ID sin token; medio sin sesión; contador de 404 duplicado; traslado no autorizado; turno duplicado; PUT turno 200; API administrativa sin sesión 401. Los dos últimos son controles positivos del comportamiento esperado. Salida cero significa caracterización reproducida, no nueve controles de seguridad aprobados.

Comando reproducible: `python docs/coordinacion/qa_caracterizacion.py servidor/servidor_lumin.py` desde el repositorio con Python disponible. Evidencia en qa-resultados.json. No cambiar este script para que el comportamiento inseguro sea criterio de aprobación; Claude debe añadir pruebas de regresión que exijan rechazo al corregirlo.

Pendientes: HTTP real/TLS/proxy, navegador, equipos Roku, codecs, Android, carga/concurrencia, recuperación/migraciones, zona horaria real y CI. No extrapolar estos resultados a producción. Ningún archivo de negocio, configuración operativa, LUMIA ni producción fue modificado.
