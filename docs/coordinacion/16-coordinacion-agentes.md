# LUMIN TV — documento común de coordinación de agentes

**ID:** LTV-COORD-001 · **Versión:** 1.7 · **Fecha:** 2026-09-19.
**Propietario:** Adrián Pérez Cueto. **Responsable del documento:** Codex, coordinación y QA.
**Finalidad:** que cada agente conozca el alcance, qué versión se está revisando, quién hace cada trabajo y cómo entregar evidencia al siguiente responsable.

## 1. Nombres de chats y responsabilidades

Nombres propuestos para el renombrado que hará Adrián. No se han renombrado ni creado chats desde este documento. Los identificadores son propios de LUMIN TV; no importan la numeración ni las autorizaciones de LUMIA.

| Nombre del chat | Agente / estado | Responsabilidad |
|---|---|---|
| **00 — LUMIN TV · Coordinación y QA** | Codex; activo en esta tarea | Mantener alcance/tablero, revisar entregas y SHA, reproducir defectos, preparar informes y encargos. |
| **01 — LUMIN TV · Desarrollo** | Claude; trabajo recibido | Backend, datos, integración, reproductor Roku y pruebas de los bloques autorizados. Responder hallazgos y entregar candidatos. |
| **02 — LUMIN TV · Frontend y UX** | Antigravity; reservado, sin encargo activo verificado | Propuestas e implementación de interfaz cuando se asigne un bloque y se acuerden contratos/archivos. |
| **03 — LUMIN TV · DevOps y Release** | Reservado; responsable no asignado | Preparar y ejecutar releases, migraciones o recuperación únicamente dentro de un encargo autorizado. |

00 combina coordinación y QA porque así está trabajando este proyecto. No es necesario abrir un chat adicional para QA ahora. Si 00 implementa código de producto en un futuro encargo, esa implementación requiere otro revisor antes de presentarse como QA independiente.

**El propietario decide:** prioridades, alcance comercial, cambios operativos de números/permisos y autorizaciones de acciones sobre producción. Un agente debe aplicar las autorizaciones ya otorgadas para el mismo alcance; no pedirlas de nuevo sin un cambio material.

## 2. Objetivo y alcance vigente

Mejorar el LUMIN TV existente, preservar su operación y su integración con el POS, y prepararlo como base del futuro producto comercial.

### Trabajo actual

- Cerrar las correcciones de continuidad/caché/reintentos de Roku (B1).
- Conservar las correcciones comprobadas del servidor actual (B2 y HEAD).
- Revisar/cerrar los hallazgos de la entrega B5a; panel nuevo en propuesta, RF-26 de playlists por TV/grupo pendiente. No activa al agente 02.
- Corregir y revisar el diseño PostgreSQL de B3 antes de implementar el bloque.
- Mantener compatibilidad de playlists, turnos, medios, pantallas, listas y sucursales, salvo cambios explícitamente acordados.

### Pendiente; no activado por este documento

- Implementación B3 hasta cerrar el diseño y las decisiones correspondientes.
- Suscripciones, cobros, registro público y portal del propietario.
- Activación comercial de varias empresas. El diseño puede prepararla; no implica que esté operativa.
- Despliegues, migraciones, publicación Roku, cambios de datos reales o modificaciones del POS LUMIA.
- Editor de diseños/plantillas: el propietario lo excluyó del enfoque del producto.
- Trabajo paralelo de frontend o DevOps sin un encargo concreto.

Los planes antiguos del SaaS y los encargos iniciales son antecedentes. No reactivarlos por encontrarlos en un archivo. Una restricción sobre producción no impide revisar código ni ejecutar pruebas sintéticas aisladas del encargo activo.

## 3. Fuente de referencia y ubicaciones

Por instrucción del propietario del 2026-09-16, **el repositorio LUMIN TV concentra código y documentación vigente**. OneDrive es archivo histórico y área anterior de QA; no mantener allí una segunda coordinación activa.

| Material | Ubicación relativa a C:/Users/adcueto/Claude/lumin-tv |
|---|---|
| Entrada de agentes | `AGENTS.md`; `CLAUDE.md` remite a la misma fuente. |
| Índice del proyecto | `docs/INDICE-PROYECTO.md` |
| Documento común vigente | `docs/coordinacion/16-coordinacion-agentes.md` |
| Encargos e intercambio | `docs/coordinacion/intercambio/` |
| Informes QA | `docs/qa/informes/` |
| Resultados y ejecutores de QA | `docs/qa/evidencia/revision-*/` |
| Diseño/entregas de Claude | Los archivos existentes de `docs/coordinacion/` **del commit candidato**; no se movieron ni sobrescribieron. |
| Copias identificadas de diseños/entregas | `docs/arquitectura/referencias/`; lectura histórica por SHA, no segunda fuente editable. |
| Investigación de producto/mercado | `docs/investigacion/`; documentos fechados, no prueba de capacidades actuales. |
| Documentación inicial conservada | `docs/coordinacion/historico-codex/`; no reactiva encargos. |
| Registro de consolidación | `docs/coordinacion/consolidacion-2026-09-16.json`, origen y hash por archivo. |

**Regla de identidad:** código y diseño se identifican por SHA. Un informe anterior no aprueba un SHA nuevo. El checkout puede seguir en main mientras la entrega está en modernizacion-diagnostico: comprobar el árbol correcto. No restaurar o sobrescribir trabajo ajeno para materializar una rama.

La consolidación es documental y local. No implica commit, push, merge ni actualización de la rama candidata. Antes de integrarla, comprobar los nuevos archivos contra la rama de destino sin mezclar los borrados o cambios locales preexistentes.

Los informes históricos se conservan byte a byte: sus rutas antiguas describen dónde se ejecutó la revisión. El índice y el manifiesto permiten localizar las copias consolidadas. No corregir retrospectivamente su evidencia. Las carpetas candidato/base y cachés de las pruebas no se copiaron: se reconstruyen desde Git con los ejecutores y SHA registrados.

Si otro agente está en una VM o máquina distinta, debe disponer del repositorio/documentos o solicitar acceso concreto. Una ruta escrita no acredita que se haya leído. Si el sandbox de Codex no permite escribir en esta raíz, preparar los cambios en su espacio permitido y usar el mecanismo de aprobación de la herramienta; no volver a declarar OneDrive como fuente vigente.

## 4. Seguimiento vigente: backlog, requisitos y semáforo

Desde v1.2, **el estado de tareas se mantiene únicamente en backlog.json**. No mantener un tablero editable duplicado en este documento.

- [Semáforo](18-semaforo.md): resumen y siguiente trabajo.
- [Backlog maestro](17-backlog-maestro.md): responsables, dependencias y aceptación por tarea BL-*.
- [Requisitos del producto](../requisitos/REQUISITOS-PRODUCTO.md): catálogo RF/RNF y trazabilidad.
- [Fuente editable](backlog.json) y [generador de vistas](actualizar_tablero.py).

Último corte de evidencia: 2026-09-19, SHA 050cc2d090b58f4d1a7b1673c830111a347b3768, informe QA25. PG55 local y CI verificados; producto/panel sin cambios por hashes. Drenaje y relaciones por sucursal cerrados; RF26-QA-02/03 y DOC-R7-01 pendientes. Documentación local, sin push.

00 actualiza la fuente después de evaluar una entrega; incrementa versión/fecha, registra evidencia y ejecuta `python docs/coordinacion/actualizar_tablero.py` desde la raíz. El generador valida IDs, cobertura y dependencias y produce las tres vistas Markdown. 01/02/03 proponen cambios de estado con entrega y evidencia; no cambian un dictamen ajeno. Un nuevo SHA requiere revisar qué tareas afecta, no cerrar todas automáticamente.

Los IDs BL-* no reutilizan los LTV-* del plan inicial. Las dependencias son condiciones de planificación; no sustituyen autorizaciones. Verde es verificación acotada, no permiso de release. Los conteos no son porcentaje de esfuerzo ni avance general.

## 5. Orden de lectura al entrar o retomar un chat

1. Leer las instrucciones expresas más recientes del propietario y confirmar rol/encargo vigente. El título del chat no reemplaza esas instrucciones.
2. Leer este documento, sus secciones de alcance y estado, y las instrucciones locales aplicables al directorio de trabajo.
3. Leer el último informe del bloque y la entrega/diseño del SHA correspondiente.
4. Comprobar raíz, rama, SHA, archivos pendientes y propiedad del trabajo antes de editar o probar. No resetear, borrar, hacer stash ni restaurar archivos ajenos para limpiar el entorno.
5. Responder con el formato común indicando qué se leyó, versión, rol, alcance a realizar y bloqueos concretos. Si el encargo ya está claro/autorizado, continuar sin pedir una confirmación redundante.

Ante contradicciones: priorizar la instrucción actual del propietario dentro de las reglas de la herramienta; señalar la discrepancia documental y preparar su actualización. No importar decisiones de LUMIA/LUMIN OS solo porque comparten agentes o numeración.

## 6. Formato común de mensajes

```text
PARA: 01 — LUMIN TV · Desarrollo
DE: 00 — LUMIN TV · Coordinación y QA
BLOQUE: B1 R3 + diseño B3 revisión 2 · SHA 78306df3
ESTADO: CORRECCIONES ACOTADAS ANTES DE APROBAR

OBJETIVO:
[Resultado concreto del encargo.]

ALCANCE:
[Qué se autoriza/prepara/revisa y los límites pertinentes.]

REFERENCIA:
[Ruta absoluta del informe o entrega, versión, rama y SHA completo.]

ACCIONES / RESPUESTA POR HALLAZGO:
[ID, corrección o explicación sustentada; no basta decir “resuelto”.]

EVIDENCIA:
[Quién ejecutó, entorno, comando, resultado y archivo de evidencia.]

PENDIENTES Y SIGUIENTE RESPONSABLE:
[Qué falta, quién sigue y criterio para cerrar.]
```

Usar solo los campos necesarios para un mensaje corto, pero conservar siempre **PARA / DE / BLOQUE / ESTADO**. Una afirmación recibida de otro agente se marca como evidencia aportada hasta comprobarla.

### Estados permitidos y significado

- **PROPUESTA:** no implementada ni aprobada.
- **EN DESARROLLO:** dentro de un encargo autorizado; no entregado aún.
- **ENTREGADO A QA:** candidato identificable disponible para revisar.
- **CORRECCIONES REQUERIDAS:** hallazgos abiertos para ese alcance/SHA.
- **PENDIENTE DE DECISIÓN:** especificar decisión y propietario; continuar trabajo independiente permitido.
- **PENDIENTE DE PRUEBA FÍSICA:** no afirmar funcionamiento en equipo real.
- **DISEÑO APROBADO:** solo documento y revisión identificados; no equivale a software aprobado ni autoriza producción.
- **QA APROBADO PARA EL ALCANCE:** candidato y criterios concretos con evidencia suficiente; limitaciones explícitas.
- **DESPLIEGUE AUTORIZADO:** requiere instrucción del propietario para versión, destino y alcance; un dictamen QA no lo sustituye.

## 7. Entrega de desarrollo y revisión independiente

01 entrega: ID/bloque, raíz física, rama, SHA base y candidato completos, diff, archivos, comportamiento antes/después, migración/reversión si aplica, pruebas ejecutadas, limitaciones y respuesta por hallazgo. Si no hay commit, identificarlo como candidato sin commit con manifiesto de hashes; no presentarlo como congelado.

00 revisa: alcance exacto, contratos afectados, fallos reproducibles, regresión pertinente y coherencia de la evidencia. Distinguir:

- inspección estática;
- ejecución real con datos sintéticos;
- pruebas de servidor aislado;
- PostgreSQL real;
- compilación;
- equipo Roku físico;
- CI asociado al SHA;
- evidencia aportada por otro agente.

No convertir un ejecutor directo en pytest, una compilación en validación Roku, o un script de caracterización que reproduce defectos en una suite de producto verde. Un fallo reproducido no se cierra porque otras pruebas pasen. La ausencia de CI se declara; cualquier control equivalente debe acordarse para el alcance correspondiente.

## 8. Escritura, Git y trabajo simultáneo

| Material/operación | Responsable y límite |
|---|---|
| Documento común, tablero e informes QA | 00 mantiene su versión; otros agentes proponen cambios en su entrega. No modificar el dictamen de otro. |
| Código, pruebas de producto y diseño B3 | 01 en su encargo y rama identificada. Comprometer/publicar esa rama solo dentro de la autorización aplicable; este documento no concede permisos nuevos de merge o release. |
| Evidencia aislada de QA | 00 en carpetas revision-*; sin sustituir fuente del candidato. |
| Frontend | 02 únicamente tras asignación; contratos y archivos acordados con 01. |
| Producción, migraciones y publicación | Propietario autoriza; responsable de ejecución identificado en el encargo. |

Los commits/push reportados por Claude no convierten a Codex en operador Git ni autorizan a cualquiera a integrar. No cambiar remotos, credenciales o configuración global como parte de una revisión ordinaria.

No escribir sobre los mismos archivos simultáneamente. Si se activa trabajo paralelo, acordar base y límites; usar ramas/worktrees separados cuando corresponda. Los agentes no se asignan por sí mismos tareas nuevas fuera del bloque. La disponibilidad de un agente/herramienta no constituye delegación.

## 9. Intercambio entre chats

Por ahora la coordinación usa **archivos compartidos y mensajes transferidos por Adrián**. Crear un archivo o pegar un borrador no significa que otro agente haya sido notificado. No hay vigilancia ni comunicación automática configurada.

Para intercambiar una entrega persistente, guardar un archivo nuevo en `docs/coordinacion/intercambio/` con nombre `AAAA-MM-DD-HHMM-remitente-destinatario-bloque.md`. Usar hora con zona o indicar zona en el cuerpo. No sobrescribir mensajes anteriores. El receptor puede dejar un acuse nuevo citando mensaje, versión/SHA y acción tomada; no hace falta reescribir la entrega original.

No enviar mensajes por otros canales sin autorización aplicable. Si el agente no tiene acceso al repositorio local, Adrián puede transferir el archivo o conceder acceso; señalar qué copia/revisión se usó. Una copia no se convierte automáticamente en nueva referencia editable.

## 10. Mensaje para iniciar cada chat

```text
PARA: [00, 01, 02 o 03 y nombre del rol]
DE: Adrián — Propietario
BLOQUE: Coordinación LUMIN TV
ESTADO: LECTURA INICIAL Y CONTINUIDAD

Lee este documento antes de continuar:
C:\Users\adcueto\Claude\lumin-tv\docs\coordinacion\16-coordinacion-agentes.md

Confirma la versión leída, tu rol y el bloque vigente. Lee también el informe
referenciado para ese bloque. Mantén las autorizaciones y límites del encargo
actual; no reactives tareas históricas. Si no puedes leer la ruta, indícalo.
Usa PARA / DE / BLOQUE / ESTADO en tus entregas y responde por ID de hallazgo.
```

## 11. Índice de la revisión actual e historial

- Actual: [QA B3 rev7 / RF-26](../qa/informes/25-qa-B3-rev7-RF26-050cc2d.md).
- Histórico: [QA B3 rev6 / RF-26](../qa/informes/24-qa-B3-rev6-RF26-a0583df.md).
- Histórico: [QA B3 rev5 / B5a R2 / panel rev2](../qa/informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md).
- Histórico: [QA B3 rev4 / B5a / panel](../qa/informes/22-qa-B3-rev4-B5a-1f7782e.md).
- Histórico: [QA B1 R4 / B3 rev3](../qa/informes/19-qa-B1-R4-B3-rev3-ce4716f.md).
- Histórico: [QA R3 / B3 rev2](../qa/informes/15-qa-R3-y-diseno-B3-rev2-78306df.md).
- Previa: [QA R2 / B3](../qa/informes/14-qa-R2-y-diseno-B3-5c96845.md).
- [QA B2 inicial](../qa/informes/13-qa-B2-0c00f35.md).
- [QA B1 inicial](../qa/informes/12-qa-B1-ceadf1d.md).
- Diseño revisado: [copia rev7 por SHA](../arquitectura/referencias/13-diseno-B3-postgresql-rev7-050cc2d.md); original en el commit candidato.
- Evidencia: [índice QA](../qa/README.md).
- Antecedentes: [documentación inicial](historico-codex/README.md); no desplaza el alcance vigente.

### Cambios de este documento

| Versión | Fecha | Cambio | Autor |
|---|---|---|---|
| 1.7 | 2026-09-19 | QA25 050cc2d: PG55 y CI; cierres de drenaje y sucursal, confirmación/historial y documento de movimiento pendientes. | Codex |
| 1.6 | 2026-09-19 | QA24 a0583df: cierre idle, alcance por base y RF-26 con correcciones; PG50/UI33/CI verificados. D8/D9 pendientes. | Codex |
| 1.5 | 2026-09-19 | QA 3a1eaf9: cuatro cierres acotados, drenaje idle pendiente, CI y anchos del panel comprobados; protocolo físico y RF-26 pendientes. | Codex |
| 1.4 | 2026-09-19 | QA 1f7782e: informe 22, CI comprobado, B5a y diseño B3 con correcciones; propuesta de panel inspeccionada. RF-26 conservado. | Codex |
| 1.3 | 2026-09-16 | QA ce4716f: evidencia ejecutada, informe 19, actualización de referencias y tablero v1.1. Sin cambios de producto ni Git. | Codex |
| 1.2 | 2026-09-16 | Requisitos, backlog y semáforo por petición de Adrián; fuente única backlog.json y vistas generadas. Estado separado del protocolo. Sin cambios de producto ni Git. | Codex |
| 1.1 | 2026-09-16 | Por solicitud de Adrián, fuente vigente dentro del repositorio; informes/evidencia/investigación consolidados, entradas AGENTS/CLAUDE y OneDrive histórico. Sin cambios de producto ni Git. | Codex |
| 1.0 | 2026-09-16 | Documento común solicitado por Adrián; nombres propuestos, roles existentes, alcance actual, estado del SHA 78306df, protocolo y rutas. Sin renombrado de chats ni envío a otros agentes. | Codex |

Cuando cambie el alcance o el estado, 00 actualizará la versión/fecha y este historial, citando la instrucción o evidencia que lo sustenta. No convertir recomendaciones técnicas en decisiones del propietario.
