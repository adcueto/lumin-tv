# LUMIN TV: comparación de producto, costos e integración

Fecha de consulta: 15 de septiembre de 2026. Investigación documental; no se ejecutaron pruebas de competidores ni se solicitaron cotizaciones. Precios sujetos a cambio, condiciones del proveedor y disponibilidad por país. Este documento incorpora el alcance que Adrián precisó durante la conversación; no reemplaza los informes históricos.

## 1. Conclusión para decidir

LUMIN TV ya cubre una parte importante de la operación básica: contenido, listas, varias pantallas, sucursales, mensajes y turnos. Esas funciones tienen equivalentes en el mercado. La oportunidad a validar es entregar una combinación fácil de instalar y operar en Roku y de activar dentro de Belia, con costo total predecible.

TVQue es una referencia directa por Roku, mensajes y números de pedido. OptiSigns sirve para comparar amplitud e integración; Yodeck para costo y continuidad; ScreenCloud para operación y monitoreo; Navori para integración empresarial. Floop y Visora aportan referencias de oferta dirigida a México. La presencia pública no demuestra cuota de mercado, satisfacción ni ventas.

Prioridades: continuidad y recuperación, separación segura de empresas, evidencia de reproducción y conector confiable. Después, simplificar instalación/publicación y mejorar la gestión de campañas. Editores y plantillas quedan fuera por decisión del propietario.

## 2. Base real de LUMIN TV

| Capacidad | Evidencia y alcance |
|---|---|
| Varias listas y TV | Reportadas por Adrián; biblioteca, listas y pantallas también observadas en la auditoría del código |
| Promociones/precios distintos por sucursal | Reportado; sucursales presentes en el código. No demuestra actualización automática de precios dentro de imágenes o videos |
| Turnos sobre publicidad | Reportado funcionando con POS; receptor y superposición observados. No se probó aquí el circuito completo en hardware |
| Franja inferior de mensajes | Reportada y manejo de mensajes observado en Roku |
| Tienda Roku | Publicación reportada por Adrián; no se verificaron ficha, territorios ni versión instalada |
| Uso de tres meses en LUMIN | Experiencia reportada, sin medición instrumental de disponibilidad |
| Pérdida de internet | Adrián reporta videos cargando indefinidamente; brecha confirmada por experiencia de uso, sin reproducción propia en esta investigación |
| Programación | Auditoría previa encontró fechas, días y horas; no proponerla como función inexistente |
| Multiempresa, cobro y permisos | La versión auditada no implementaba empresa/suscripción; permisos presentaron hallazgos reproducidos |

La auditoría fue sobre `ea610d6fbea8dac7c330f0ba134cf41e5d92fcdc`, no necesariamente sobre la versión hoy instalada. Fuente local: [auditoría de código](../coordinacion/09-auditoria-codigo.md). Se debe comprobar versión antes de afirmar que sus hallazgos siguen presentes.

## 3. Productos y diferencias útiles

### OptiSigns

Publica listas, horarios, múltiples usuarios y zonas; niveles superiores añaden permisos, aprobación y reportes. Standard cuesta US$10 por pantalla/mes o US$9 equivalentes con pago anual. Pro Plus cuesta US$15 mensual o US$13.50 anual. Hay una oferta gratuita limitada por dispositivos y funciones. [Precios](https://www.optisigns.com/pricing).

Tiene franja desplazable mediante zonas, pero su documentación excluye Roku y Apple TV del modo de pantalla dividida. Por eso no se deben trasladar todas las funciones del catálogo a Roku. El video + franja + turno de LUMIN en un mismo Roku merece una prueba comparativa específica. [Zonas](https://support.optisigns.com/hc/en-us/articles/360026559573-How-to-Create-and-Use-the-Split-Screen-App), [franja](https://support.optisigns.com/hc/en-us/articles/360026559613-How-to-Create-a-Scrolling-Strip-or-Bar).

La documentación de claves API exige Pro Plus o superior y excluye el portal de marca blanca; la página comercial destaca GraphQL en Enterprise. Confirmar alcance y condiciones para una integración comercial, sin dar por hecho que la suscripción permite reventa. [Clave API](https://support.optisigns.com/hc/en-us/articles/4414563797139-Generate-Manage-an-OptiSigns-API-Key).

OptiSync documenta una integración con Clover, precios/disponibilidad y datos por tienda. Requiere configurar autenticación, fuente, correspondencia de campos y, para actualizaciones cercanas al tiempo real, webhook. No es un conector Belia terminado ni prueba de latencia de turnos. [Ejemplo POS](https://support.optisigns.com/hc/en-us/articles/31860170199955-Integrating-Point-of-Sale-POS-Systems-to-Build-Digital-Menu-Boards-with-OptiSync).

### Yodeck

Ofrece una cuenta de una pantalla gratuita; Basic US$8 y Premium US$12 por pantalla/mes. Premium incluye API. El anual incluye reproductores bajo sus condiciones; entrega e importación en México quedan por verificar. [Precios](https://www.yodeck.com/pricing/), [API](https://www.yodeck.com/academy/api-token/).

Documenta franja de texto/RSS. Sus equipos compatibles incluyen Raspberry Pi, Android, web, Tizen y otros; Roku nativo no figura en la lista consultada. Usar una TV Roku mediante HDMI y otro reproductor es un escenario distinto de instalar una app Roku. [Franja](https://www.yodeck.com/docs/user-manual/on-screen-ticker/), [equipos](https://www.yodeck.com/docs/user-manual/what-are-the-requirements-for-using-yodeck/).

Su guía indica reproducción local sin internet durante al menos 30 días, con corte entre 30 y 40 días y posibles desfases de reloj; contenido web y emisiones en vivo tienen restricciones. La guía no demuestra comportamiento idéntico de todos sus reproductores. [Sin conexión](https://www.yodeck.com/docs/user-manual/does-yodeck-work-offline/).

### ScreenCloud

Core US$20 y Pro US$30 por pantalla/mes equivalentes con pago anual. Publica administración de pantallas, almacenamiento, API GraphQL y funciones superiores de datos e interacción. [Precios](https://screencloud.com/pricing).

Tiene franja mediante Noticeboard/Quick Post y zonas. Confirma que no dispone de reproductor Roku; haría falta hardware compatible adicional para esa TV. [Franja](https://help.screencloud.com/en/articles/10121482-how-to-make-a-scrolling-ticker-tape-using-noticeboard-2-0), [sistemas no compatibles](https://help.screencloud.com/en/articles/10115414-devices-and-operating-systems-that-are-not-supported-by-or-recommended-with-screencloud).

Documenta caché para medios descargados, pero advierte que ciertos equipos no arrancan sin internet tras un corte eléctrico. Esto obliga a probar pérdida de red y reinicio por separado. [Modo sin conexión](https://help.screencloud.com/en/articles/10121054-offline-support-playing-without-an-internet-connection-using-screencloud).

### TVQue

Competidor cercano: app Roku, varias ubicaciones, videos, texto superpuesto y números de pedido. Publica control/estado remoto, pero no verificamos su método, fiabilidad ni equivalencia con un turno automático desde POS. No confirmar una API en las fuentes revisadas no significa que no exista. [Producto](https://www.tvque.com/services.html).

Business US$7/TV/mes excluye programación y carga de videos. Company US$10 añade programación, pero tampoco carga videos. Enterprise US$15 añade carga de videos; HD Enterprise requiere consulta. No comparar un plan de US$7 con LUMIN reproduciendo videos cargados como si fueran equivalentes. [Planes](https://www.tvque.com/s/ui5/dspricing.html).

### Navori

Essential ofrece gestión y monitoreo; Professional añade campañas, automatización y APIs. No se obtuvo un importe legible y verificable para Essential; Professional se cotiza. [Licencias](https://navori.com/pricing/).

Documenta REST API para contenido, usuarios, equipos, datos y sistemas de filas. La referencia técnica menciona un complemento API, por lo que hay que confirmar su inclusión en una cotización actual. Es evidencia de que las integraciones de turnos ya existen en el sector. No se comprobó app Roku nativa. [API comercial](https://navori.com/app/api/), [referencia técnica](https://na.navori.com/navoriservice/apidocumentation/).

### Referencias dirigidas a México

**Floop:** anuncia MXN49 por pantalla adicional/mes, primera pantalla gratis seis meses, listas, horarios, usuarios, sucursales y 5 GB. Su FAQ también expresa US$2.50; falta comprobar moneda efectiva, precio de la primera pantalla después de la promoción y condiciones en checkout. Publicita Android/Fire TV; no verificamos API ni Roku nativo. No se validaron testimonios, escala ni cifras de ahorro. [Oferta](https://floop.media/).

**Visora:** publica paquetes de 2 pantallas por US$29, 4 por US$59 y 10 por US$159 mensuales. La tabla reserva programación a Pro/Business; Starter no la incluye. Publica caché y API personalizada en Enterprise; Roku nativo no aparece en los equipos enumerados. [Planes](https://www.visora.mx/pricing), [moneda USD confirmada por el proveedor](https://www.visora.mx/blog/cuanto-cuesta-senalizacion-digital-mexico).

## 4. Qué ya tienes y qué conviene mejorar

| Área | Lectura competitiva | Acción propuesta |
|---|---|---|
| Listas, varias TV, sucursales | Funciones esperadas en esta categoría | Preservarlas y medir facilidad; no rehacerlas por novedad |
| Franja inferior | Tiene equivalentes; compatibilidad varía | Demostrar convivencia con video y turnos en Roku |
| Turnos Belia | Valor de integración lista, no invención de los turnos | Activación por sucursal y contrato estable |
| Reproducción sin conexión | Brecha frente a ofertas con caché | Prioridad 1: salida de carga infinita, respaldo y reconexión |
| Estado de pantalla | Estar conectada no garantiza que reproduzca | Separar conexión, descarga, versión de lista y último evento del reproductor |
| Campañas por sucursal | Ya existe segmentación básica | Revisar vencimiento, copia masiva, excepciones y vista previa antes de extender |
| Estadísticas | Solicitar un archivo no demuestra reproducción ni ventas | Eventos del reproductor deduplicados; ventas atribuidas por separado |
| Multiempresa | Necesidad para comercializar una plataforma compartida | Aislar datos, medios y dispositivos; permisos probados |
| Cobro | No es función del reproductor, pero sí del negocio SaaS | Planes, límites, cobros y estados de suscripción coherentes |

### Advertencia técnica concreta sobre Roku

Debo precisar la recomendación anterior de simplemente descargar videos: Roku documenta que `tmp:` se pierde al salir de la app y `cachefs:` usa RAM, puede ser desalojado y se pierde al reiniciar. No equivale a almacenamiento persistente. [Sistema de archivos Roku](https://developer.roku.com/dev/docs/file-system).

Separar dos compromisos: (1) tolerar una desconexión mientras la app sigue abierta; (2) recuperar videos tras reiniciar sin internet. Estudiar memoria, códecs, tamaño de archivos y respaldo empaquetado por modelo. Si un cliente exige persistencia completa y el equipo no la permite, evaluar un reproductor con almacenamiento local como opción comercial, incluyendo su costo. Una imagen de respaldo evita la carga infinita, pero no equivale a continuar la campaña de video.

## 5. Integración sencilla como producto

La facilidad debe medirse para tres personas:

1. Dueño: instala, vincula con código, elige sucursal, publica contenido y comprueba recepción.
2. Usuario de Belia: activa TV en la misma experiencia; no configura claves de proveedores ni mantiene dos catálogos de sucursales manualmente.
3. Desarrollador externo: dispone de credenciales por empresa/sucursal, documentación, entorno de prueba y ejemplos para anunciar, actualizar y cancelar turnos.

Propuesta de conector: identificador único para que un reintento no repita el anuncio, vencimiento para descartar eventos viejos, confirmación de recepción distinta de visualización y control de acceso por sucursal. La lógica de espera/atención sigue perteneciendo al POS. Son requisitos propuestos, no capacidades nuevas ya verificadas.

Una API accesible facilita integración, pero cada POS tiene contratos y permisos propios. Conector Belia incluido en su oferta; conectores externos con alcance y precio definidos. No prometer cualquier POS ni reventa de licencias de terceros sin verificar condiciones.

## 6. Costos comparables

Ejercicio de licencia para 3 TV durante 12 meses, sin impuestos, hardware, internet, instalación ni desarrollo. No son implementaciones funcionalmente idénticas.

| Opción | Cálculo | USD/año |
|---|---|---:|
| OptiSigns Standard anual | 3 × 9 × 12 | 324 |
| OptiSigns Pro Plus anual, referencia API | 3 × 13.50 × 12 | 486 |
| Yodeck Premium, referencia API | 3 × 12 × 12 | 432 |
| ScreenCloud Core anual | 3 × 20 × 12 | 720 |
| TVQue Enterprise mensual, videos | 3 × 15 × 12 | 540 |

Fuentes: precios enlazados en la sección 3. El caso Yodeck usa tres licencias pagadas, no descuenta una pantalla gratuita de una cuenta multipantalla; revisar [reglas de planes](https://www.yodeck.com/docs/user-manual/pricing-plans-screens/). No convertimos dólares a pesos con un tipo de cambio supuesto. Las cifras API no incluyen construir el conector.

Para comparar LUMIN: costo anual = suscripción + equipo adicional + instalación + integración + mantenimiento. Incluir cualquier dispositivo auxiliar necesario para arranque/control, no solo la TV.

Para fijar nuestro precio: costo directo mensual por empresa = nube asignada + almacenamiento + transferencia de videos + procesamiento + cobro + soporte. El margen resultante todavía debe cubrir desarrollo, adquisición de clientes y gastos generales. No declarar que MXN249 es barato o rentable sin medir esos costos. Floop y las opciones gratuitas impiden fundamentar la estrategia solo en precio mínimo.

## 7. Prioridad de trabajo

**Primero: operación comercial confiable.** Recuperación ante red/carga; evaluación del almacenamiento Roku; separación de empresas y corrección de permisos sobre versión actual; credenciales revocables por equipo; publicación verificable y conector sin anuncios duplicados.

**Después: menos trabajo para el cliente.** Vinculación guiada, acciones por grupo/sucursal, caducidad comprobada, estado entendible y límites/planes transparentes. Medir antes si estos flujos ya existen y cuánto necesitan mejorar.

**Luego: valor comercial medible.** QR/código por promoción o registro de origen en Belia, distinguiendo consultas, ventas atribuidas y causalidad. La pantalla puede ayudar a vender según la experiencia de LUMIN; no hay porcentaje incremental medido.

**IA opcional:** extraer fechas/precios de un anuncio para sugerir una revisión o traducir instrucciones a una programación que el usuario confirma. No editar los videos ni publicar automáticamente cambios de precio. No es una ventaja exclusiva ni prioridad sobre estabilidad. Reglas simples deben resolver vencimiento y segmentación.

## 8. Prueba práctica para resolver las incógnitas

Comparar primero LUMIN y TVQue en el mismo Roku; OptiSigns tanto en Roku como en un dispositivo compatible con zonas; Yodeck en su equipo compatible. Registrar modelo, sistema operativo, plan, región, fecha y equipo auxiliar. Mantener iguales los archivos y las tareas.

| Prueba | Evidencia requerida |
|---|---|
| Instalar/vincular | Tiempo, pasos, intervención y costo |
| Publicar lista por sucursal | Tiempo hasta recepción; comprobar que otra sucursal no cambia |
| Video + franja + turno | Video de ejecución, demora y continuidad de audio/video |
| Cortar internet y restaurar | Qué sigue visible, espera máxima y recuperación automática |
| Reiniciar sin internet | Resultado separado de una simple desconexión |
| Archivo incompatible | Mensaje útil y continuidad del resto de la lista |
| Reintentar/cancelar turno | Sin duplicados ni avisos vencidos |
| Medir una semana de operación | Fallos, minutos de soporte y consumo de transferencia |

No se realizaron estas pruebas en esta investigación. Tampoco se contactaron proveedores, compraron planes, modificaron apps ni interrumpió la operación de LUMIN.

## Decisión recomendada

Mantener el servicio independiente de TV y su integración dentro de Belia. Evitar una reconstrucción generalista. La próxima inversión debe cerrar brechas de confiabilidad y comercialización y demostrar que la instalación y operación completas resultan más simples o rentables para el segmento elegido. TVQue debe estar en la siguiente prueba: compartir Roku y avisos lo hace especialmente relevante.
