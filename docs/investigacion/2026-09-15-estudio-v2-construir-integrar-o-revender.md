# Estudio v2: construir, integrar o vender servicios de pantallas

Fecha: 15 de septiembre de 2026. Responsable: Codex.
Revisión documental ampliada. Complementa el estudio de nombre y dominios; no es una prueba de producto ni validación comercial mediante entrevistas.

## Decisión investigada

Determinar si conviene desarrollar un SaaS completo, integrar el POS Belia con un proveedor, ofrecer servicios sobre una plataforma, contratar marca blanca o conservar LUMIN TV como herramienta interna. La existencia de competidores no demuestra inviabilidad; tampoco demuestra que haya demanda para otra app.

## Contexto aportado

Adrián opera LUMIN en Querétaro, desarrolla un POS de belleza llamado Belia y dispone de una Roku TV de pruebas con LUMIN TV. Modelo y versión de OS pendientes. Busca abaratar anuncios, menús y turnos usando televisiones de consumo. LUMIN TV tiene código propio existente; no se da por listo como SaaS multiempresa. El usuario considera completo el panel de OptiSigns tras explorarlo; esto no sustituye pruebas en su equipo.

## Hallazgos que cambian la comparación

### 1. Hay un competidor directamente enfocado en Roku

[TVQue](https://www.tvque.com/services.html) anuncia contenido, números de pedido y texto superpuesto en Roku sin equipo especial. Su [tarifario](https://www.tvque.com/s/ui5/dspricing.html) muestra Business USD 7/TV/mes, Company USD 10 y Enterprise USD 15. Business carece de programación y subida de videos; Company añade programación pero no subida de videos. Debe compararse el plan que cumpla cada tarea, no solo el menor precio. Sus afirmaciones de arranque/control remoto requieren comprobación física: no se extrapolan a todos los Roku.

Consecuencia: Roku + anuncios + llamados no puede presentarse como una idea exclusiva. Falta comparar la profundidad del flujo de turnos, no solo la capacidad de mostrar números.

### 2. Integrar Belia requiere verificar costo y capacidad real de la API

[OptiSigns documenta](https://support.optisigns.com/hc/en-us/articles/4414563797139-Generate-Manage-an-OptiSigns-API-Key) que generar una clave requiere Pro Plus o superior, ser propietario o superadministrador y no utilizar un portal white-label. Su [tarifario](https://www.optisigns.com/pricing) publica Pro Plus a USD 15/pantalla/mes con pago mensual y USD 13.50 equivalentes con pago anual.

La existencia de una API no confirma que se puedan superponer llamados sobre video con la latencia, privacidad y recuperación deseadas en Roku. Verificar operaciones, webhooks/polling, idempotencia, límites, plan y capacidad específica del reproductor. No se ha conectado Belia ni ejecutado una llamada de prueba.

### 3. Vender con marca propia no exige necesariamente desarrollar el motor

[Yodeck ofrece marca blanca](https://www.yodeck.com/white-label/), con portal personalizado y gestión comercial propia. Su [FAQ de socios](https://www.yodeck.com/docs/partner-manual/yodeck-partner-network-faq/) distingue afiliado, revendedor y marca blanca, e indica una cuota anual para esta última. No publica allí todos los precios mayoristas; margen, mínimos y condiciones quedan por cotizar. El programa permite explorar una operación comercial, no garantiza rentabilidad.

[ScreenCloud](https://screencloud.com/partners) también contempla integraciones y reventa. [OptiSigns](https://www.optisigns.com/partners-contact) ofrece contacto para asociaciones; no se infieren derechos de reventa, descuentos ni marca blanca a partir de tener una cuenta normal o un portal con logotipo.

### 4. Existe una opción intermedia de software abierto

[Xibo](https://xibosignage.com/open-source) ofrece un núcleo CMS abierto bajo AGPLv3. Su [página de precios](https://xibosignage.com/pricing) diferencia autoalojamiento y reproductores comerciales. No asumir que todo el sistema, todas las plataformas o el mantenimiento son gratuitos. El encaje Roku y las condiciones de una oferta propia quedan por verificar; no es una recomendación de migración inmediata.

## Matriz de rutas de negocio

| Ruta | Beneficio posible | Costos/riesgos | Condición para elegirla |
|---|---|---|---|
| Usar una plataforma solo en LUMIN | Resolver operación rápidamente | Licencias y dependencia | Cumple tareas en la TV a costo aceptable |
| Integración Belia + proveedor | Concentrar desarrollo en el flujo del salón | API, plan requerido, soporte, dependencia | Prueba técnica viable y clientes que paguen por el flujo |
| Servicio gestionado | Cobrar instalación, contenido y soporte | Horas humanas, visitas, permisos comerciales | Margen positivo después del trabajo real |
| Marca blanca | Portal propio sin recrear todo el motor | Cuotas, mínimos, dependencia y migración | Cotización y contrato sostienen el margen |
| Plataforma propia especializada | Control del producto y del flujo | Desarrollo, seguridad, dispositivos y operación permanente | Problema comprobado no resuelto suficientemente por las anteriores |
| SaaS generalista completo | Mayor amplitud potencial | Mayor alcance y competencia | Evidencia comercial suficiente y capacidad de mantenimiento; hoy no demostradas |

## Diferencias por validar

- Integración Belia: llamada desde estación, publicidad simultánea y regreso correcto; no confundir nombre del cliente/folio con integración completa.
- Facilidad: minutos desde registro a primer anuncio, pasos para cambios y necesidad de soporte.
- Contenido: crear una promoción desde foto/precio/vigencia sin diseñar desde cero. Los competidores ya tienen plantillas; solo una prueba permite afirmar mayor facilidad.
- Confiabilidad económica: equipos concretos disponibles en México, recuperación tras red/energía y mantenimiento.
- Servicio local: acompañamiento que el cliente quiera pagar; español o moneda MXN por sí solos no prueban ventaja sostenible.

## Economía: no confundir precio con margen

Ingresos mensuales por cliente = suscripción + servicios recurrentes aceptados.
Contribución mensual = ingresos netos - licencias externas - infraestructura variable - comisiones - costo directo de soporte y contenido.
Resultado operativo = contribución total - costos fijos, incluido mantenimiento/desarrollo y adquisición de clientes.

Para comparar a 12 meses: hardware + instalación + 12 × licencias/servicios + soporte + reposiciones razonablemente estimadas. Distinguir TV existente de TV comprada; comparar la misma necesidad de funciones y plataformas.

Escenarios propuestos para la hoja económica futura: 10, 50 y 100 clientes; 1 y 3 pantallas por cliente; sensibilidades de 15/30/60 minutos de soporte mensual. Son escenarios, no demanda ni cargas observadas. Faltan cotizaciones mayoristas, costo laboral, uso de medios y adquisición de clientes para calcular márgenes con evidencia.

El catálogo anterior de MXN 249/599/1199 es una hipótesis. No fijarlo antes de saber qué funciones requiere el cliente, cuánto soporte consume y qué alternativa real compara. No convertir USD sin fecha y fuente del tipo de cambio.

## Plan de validación y criterio de decisión

1. Documentar modelo/OS de la Roku y conservar LUMIN TV como línea base recuperable.
2. Comparar LUMIN TV, OptiSigns y TVQue en ese equipo. Yodeck se evalúa documentalmente y, si requiere hardware distinto, se cotiza y prueba en otra configuración; no asumir app nativa Roku.
3. Usar idénticos medios y tareas: registro/vinculación, primer anuncio, edición móvil, horario, turno, corte de red, reinicio y jornada prolongada. No modificar producción para comparar.
4. Registrar plan, precio, accesorios, tiempo, fallos e intervención. Una promesa del proveedor se etiqueta diferente a un resultado reproducido.
5. Entrevistar 5 salones y 5 restaurantes como muestra exploratoria. Contrastar problema actual, alternativa utilizada, presupuesto y aceptación de piloto pagado. No se ha contactado a nadie.
6. Proponer como umbral inicial 3 pilotos pagados ajenos a LUMIN y una ventaja medible en la tarea principal antes de ampliar el SaaS. Es un criterio sugerido para acordar, no una regla estadística ni una venta existente.

## Recomendación actual

Mantener LUMIN TV, probar competidores y realizar una prueba acotada del flujo Belia antes de comprometer el desarrollo generalista. Si un proveedor resuelve lo necesario, considerar compra/integración/servicio. Si aparece una carencia repetida que clientes pagan por resolver y la economía cierra, construir esa especialización.

No se concluye que haya que abandonar ni que necesariamente haya que construir. La decisión final depende de pruebas de TV, límites contractuales, cotizaciones y demanda que aún faltan. No se compraron suscripciones, contactaron proveedores, instalaron aplicaciones ni modificaron repositorios operativos en esta investigación.
