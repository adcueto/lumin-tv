# Revisión independiente B1 — correcciones requeridas

Fecha: 2026-09-16. Repositorio inspeccionado: C:/Users/adcueto/Claude/lumin-tv.
Base: ea610d6. Candidato: ceadf1d2c66622c99d69389715ecb4ef60f8e468, rama modernizacion-diagnostico.

## Alcance y estado

La carpeta permanece en main. Se revisó la rama candidata mediante git show/diff sin checkout ni modificación del código. El diff contiene 15 archivos: reproductor Roku 5.2 build 57, caché, respaldo y documentación. No implementa todavía PostgreSQL, React ni autenticación nueva. Las referencias remotas son las guardadas localmente; no se hizo fetch.

Dictamen: CORRECCIONES REQUERIDAS para B1. Hallazgos por análisis estático del flujo; no son reproducciones ejecutadas en un Roku. Las pruebas físicas continúan pendientes. No se reejecutó el compilador BrighterScript; los cero diagnósticos de la entrega son evidencia aportada por Claude.

## Hallazgos

### B1-QA-01 [P1] El límite total de caché no se aplica a las descargas nuevas

Archivo candidato: roku-app/components/CacheTask.brs, líneas 62–76; descarga y comprobación de tamaño en la función descargar.

`desalojar` solo se llama al recibir deseados, antes de descargar. Cada descarga exitosa actualiza bytesEnCache, pero no reserva espacio ni vuelve a aplicar el límite. Con caché vacía y cuatro archivos de 70 MiB, todos pasan el límite individual de 80 MiB y se pueden acumular 280 MiB frente al tope anunciado de 250 MiB. El archivo temporal tampoco se limita durante la transferencia: se comprueba el tamaño al terminar. El desalojo del sistema operativo no sustituye un presupuesto controlado por la aplicación.

Impacto: presión de memoria compartida, desalojos inesperados y pérdida de la continuidad que B1 busca garantizar.

Corrección: controlar presupuesto antes/durante las descargas, incluir temporales y revalidar después de confirmar archivos. Mantener un margen para reproducción y definir el tratamiento de un archivo que no cabe. Probar varios archivos individualmente válidos cuya suma supera el tope y una descarga individual demasiado grande.

### B1-QA-02 [P1] La caché no se recupera de una descarga fallida con lista sin cambios

Archivo candidato: roku-app/components/CacheTask.brs, líneas 40–76; MainScene.brs, líneas 244–247 y callbacks onCacheListo/onCacheFallo.

La cola elimina cada elemento antes de intentar descargar. Si falla, solo publica fallo; no lo reencola. Cuando la cola queda vacía, espera indefinidamente un nuevo deseados. La escena solo llama pedirCache cuando cambia datos.videos y no viene de caché. Sus callbacks de caché no hacen nada y onConectado no solicita rellenarla.

Recorrido: recibir lista → fallar descargas por corte de red → recuperar conexión con la misma lista → reproducción remota puede recuperarse, pero no se vuelve a llenar la caché. Otro corte deja a la TV sin los archivos esperados. También queda sin mecanismo de reposición un archivo desalojado por Roku con lista estable. Si se arranca con playlist recuperada, la respuesta en vivo con idéntico videos tampoco programa la descarga.

Corrección: reconciliar periódicamente los medios deseados con los disponibles, especialmente tras reconexión y arranque desde caché; aplicar reintento acotado con espera creciente y cancelar trabajos obsoletos. No descargar todo en cada latido.

### B1-QA-03 [P2] Se descarta un Mostrar ahora válido posterior a la reconexión

Archivo candidato: roku-app/components/MainScene.brs, líneas 632–642; indicador activado en onConectado.

Al perder conexión se activa revisarComandoViejo. Si al reconectar llega el mismo comando conocido, el retorno de la línea 632 deja el indicador activo. El siguiente comando nuevo de reproducir, aunque lo emita el usuario después de recuperar la conexión, se descarta y su número queda marcado como procesado.

Recorrido: último comando n=5 → desconexión sin comandos nuevos → reconexión con n=5 → usuario envía reproducir n=6 → el código lo descarta. Comparar solo el siguiente número nuevo no demuestra que el comando se emitió durante la caída.

Corrección: consumir la comprobación de recuperación sobre la primera respuesta válida tras reconectar, incluso cuando no haya cambio de comando. Para una caducidad más precisa, planificar timestamp/expiración compatible con el servidor. Probar por separado comando pendiente durante caída y comando emitido después de reconexión.

## Comprobaciones ejecutadas

- git diff --check main..modernizacion-diagnostico: sin errores.
- XML del candidato: tres archivos parseados correctamente.
- Referencias pkg:/ del XML y manifest: ningún archivo ausente en el árbol del commit.
- Identidad del candidato y alcance del diff comprobados.
- Inspección de la entrega B1, tareas de caché/playlist y cambios de MainScene.

Estas comprobaciones no verifican compilación BrightScript, reproducción desde cachefs, tiempos reales, comportamiento de memoria ni los escenarios físicos F1–F13.

## Estado local ajeno al candidato

En main existen dos iconos eliminados sin commit: mm_icon_focus_hd.png y mm_icon_focus_sd.png; manifest sigue referenciándolos. Ambos están presentes en el árbol del candidato. No atribuir esos borrados a B1. Evitar empaquetar el directorio de trabajo actual como si fuera la entrega candidata. docs/coordinacion/ está sin seguimiento desde el checkout actual; esto no implica que los documentos específicos de B1 no estén versionados en la otra rama.

## Siguiente entrega solicitada

Corregir los tres hallazgos en la rama de trabajo, identificar el nuevo SHA y aportar comprobaciones de regresión centradas en estos recorridos. Después ejecutar F1–F13 en un Roku de pruebas, con modelo/OS y evidencia. No desplegar a tienda, flota o VPS con este dictamen. No se modificó el código ni se ejecutaron operaciones en producción durante esta revisión.
