# Diagnóstico, inventario y plan de modernización de LUMIN TV

Fecha: 2026-09-15 · Autor: Claude (desarrollo) · Revisa: Codex (QA) · Decide: Adrián
Rama de trabajo: `modernizacion-diagnostico` · Base: `main` en `ea610d6`

Este documento es la primera entrega del cambio de alcance: modernizar LUMIN TV
como base del futuro producto comercial. No contiene código de migración ni
cambios en la aplicación que opera hoy.

---

## 1. Diagnóstico del repositorio y versión base

### 1.1 Estado real encontrado

| Qué | Valor |
|---|---|
| Repositorio local | `C:\Users\adcueto\Claude\lumin-tv` |
| Rama | `main`, sincronizada con `origin/main` |
| Versión base de este trabajo | **`ea610d6` — "servidor v6.9: renombrar contenido desde la Biblioteca"** |
| Servidor | `servidor/servidor_lumin.py`, 2,569 líneas |
| App Roku | `manifest` 5.1 build 56, `ui_resolutions=fhd` |

### 1.2 Cambios pendientes en tu copia local — atención

Hay tres cosas sin commitear que conviene resolver antes de seguir:

1. **Dos archivos borrados en el árbol de trabajo:**
   `roku-app/images/mm_icon_focus_hd.png` y `mm_icon_focus_sd.png`.
   Son los iconos del menú del canal, y el `manifest` los declara en
   `mm_icon_focus_hd` / `mm_icon_focus_sd`. **Si ese borrado se commitea, el
   paquete del canal queda inconsistente.** No los toqué. Hay que decidir si
   fue intencional o si se restauran con `git restore`.
2. **`docs/coordinacion/` está sin seguimiento.** El paquete de Codex —
   auditoría, contratos, protocolo de QA y los 9 casos de caracterización —
   existe solo en tu disco. Si esa carpeta es la referencia compartida del
   equipo, debería estar versionada, o se pierde y se desincroniza.
3. **El README está desactualizado:** dice servidor v6.7 y la rama va en v6.9.

### 1.3 La rama `fase1-sqlite-respaldos` de la sesión anterior

Antes del cambio de alcance quedó commiteada localmente una rama con la Fase 1
del documento de julio: migración de los JSON a **SQLite**, respaldo nocturno y
bitácora. **No la borré y no la voy a mezclar.**

Pero hay que decidir qué pasa con ella, porque la nueva dirección técnica dice
PostgreSQL:

> **Recomendación: no mezclarla tal cual.** Ir JSON → SQLite → PostgreSQL son
> dos migraciones de los mismos datos, con dos ventanas de riesgo y dos
> procedimientos de reversión, para terminar donde se quiere llegar de todos
> modos. Conviene ir directo de JSON a PostgreSQL.

Lo que **sí** vale la pena rescatar de esa rama, porque no depende de la base de
datos y mejora la operación actual desde ya:

- La bitácora de errores a archivo con rotación (hoy los fallos se tragan en
  silencio: `except: pass`).
- Cuatro carreras corregidas: `crear_sesion`, `cerrar_sesion`, `crear_usuario` y
  `marcar_girado` hacían leer-modificar-escribir sin tomar el candado.
- La cola de conexiones del servidor, que está en el valor por defecto de
  Python (**5**): con la flota golpeando a la vez, el sistema operativo tira
  conexiones y la TV o el panel ven "conexión reiniciada". Medido: con 60
  peticiones simultáneas se perdían 6; subiéndola a 64, ninguna de 120.
- El diseño del respaldo nocturno, adaptando la copia de la base a `pg_dump`.

Eso es el bloque **B2** del plan.

### 1.4 Contraste con los hallazgos de QA de Codex

Revisé `docs/coordinacion/09-auditoria-codigo.md` contra el código de `ea610d6`.
**Los seis hallazgos siguen presentes.** Ninguno está corregido en `main`.

| Hallazgo | Sigue vigente | Dónde | Bloque que lo cierra |
|---|---|---|---|
| QA-F01 permisos vacíos conceden todas las sucursales | Sí | `servidor_lumin.py:215-219`, `706-711` | B4 |
| QA-F02 operador traslada pantalla a sucursal ajena | Sí | `1409-1425` | B4 |
| QA-F03 credencial de administrador fija en el código | Sí | `33-34`, `152-159` | B4 |
| QA-F04 estadísticas cuentan peticiones incluso con 404 | Sí | `775-783` | B5 |
| QA-G01 pantallas y medios sin credencial propia | Sí | `727-807`, `PlaylistTask.brs:53-57` | B8 |
| QA-G02 turno sin idempotencia | Sí | `1345-1374` | B5 |

Coincido con los seis. Añado dos observaciones sobre el alcance de F01: además
de que `sucursales=[]` concede todas, una sucursal fuera de alcance **no da
error, se sustituye en silencio por la primera permitida**. Eso hace que un
operador crea que está trabajando en una sucursal y esté cambiando otra. Para
mí eso es más grave que el permiso amplio, porque es silencioso.

---

## 2. Inventario de funciones existentes

Tres meses de uso real. Esto **existe y funciona**; el trabajo es conservarlo.

### 2.1 Servidor (`servidor/servidor_lumin.py`, v6.9)

| Función | Estado | Referencia |
|---|---|---|
| Multi-sucursal con contenido, mensaje y pantallas propias | Completo | `sucursales()`, `dir_videos()` |
| Biblioteca de video e imagen por sucursal | Completo | `biblioteca()`, `/api/subir` |
| Varias listas de reproducción por sucursal, con lista activa | Completo | `listas_de()`, `/api/listas/*` |
| Lista asignada por pantalla individual | Completo | `lista_de_tv()` |
| Orden manual del contenido dentro de una lista | Completo | `/api/mover` |
| Alta de pantallas con aprobación por código | Completo | `registrar_tv()`, `/api/tv/aprobar` |
| Control en vivo: pausa, continuar, reproducir ya, silencio | Completo | `enviar_comando()` |
| Franja inferior de mensajes, animada y con velocidad | Completo | `leer_ajustes()`, `/api/ajustes` |
| Turnos desde el POS, con próximos y espera | Completo | `/api/turno`, `docs/API-turnos.md` |
| Programación por contenido: fechas, días, horario | Completo | `contenido_activo()` |
| Duración por imagen | Completo | `duracion_de()` |
| Conversión y giro de video con ffmpeg para TV vertical | Completo | `procesar_subida()` |
| Miniaturas | Completo | `generar_miniatura()` |
| Estadísticas por contenido (hoy / 7 días / 30 días) | **Dudoso** | Cuenta peticiones, no reproducciones (QA-F04) |
| Usuarios con rol admin/usuario y sesiones de 30 días | **Débil** | QA-F01, F03 |
| Panel web PWA instalable | Completo pero monolítico | ~1,000 líneas embebidas como texto en el mismo archivo |

### 2.2 App Roku (`roku-app/`, 5.1 build 56)

Reproducción de video e imagen, rotación para TV vertical, franja de mensajes,
panel de turnos deslizante, comandos en vivo, alta por código en pantalla, y
cambio de URL del servidor con el botón `*`. Consulta `/playlist.json` cada
4 segundos más el tiempo de red.

### 2.3 Vigilante (`vigilante/`, 1.0)

Raspberry por sucursal que enciende las TVs y abre el canal por ECP en horario.
Independiente del servidor.

### 2.4 Lo que NO existe hoy

Ni empresa como concepto, ni planes, ni menú digital, ni empleado del mes (las
muestras de `docs/muestras/` son imágenes de diseño, no un módulo), ni app
Android TV, ni pruebas automatizadas, ni CI, ni respaldos.

---

## 3. Por qué "se quedan cargando" — diagnóstico técnico

Encontré tres causas distintas. La segunda es, casi con seguridad, la que ves.

### 3.1 La consulta al servidor bloquea sin límite de espera

`PlaylistTask.brs:50` usa `xfer.GetToString()`, que es **síncrono y no tiene
`SetTimeout`**. Cuando se cae el internet, esa llamada se queda esperando el
tiempo de espera del sistema operativo, que puede ser de minutos. El bucle de
4 segundos deja de latir durante todo ese rato: la TV no se entera de nada,
no reintenta y no puede reaccionar.

### 3.2 El estado `buffering` no tiene vigilante — esta es la causa directa

`onVideoState` (`MainScene.brs`) atiende `playing`, `finished` y `error`.
**No atiende `buffering`.** Si el internet se cae a media reproducción, el nodo
de video entra en `buffering` y se queda ahí indefinidamente: ningún
temporizador lo vigila, nadie lo saca. Eso es exactamente "el video se queda
cargando" y no se recupera solo.

`m.timerReintento` existe pero solo se dispara desde `error`, no desde un
`buffering` que no avanza.

### 3.3 No hay nada guardado localmente

Todas las URLs de `/playlist.json` son remotas. El reproductor no descarga
nada. Sin internet no hay contenido que mostrar, ni de respaldo.

### 3.4 Qué permite realmente el almacenamiento de Roku

Esto cambia lo que se puede prometer, así que lo verifiqué en la documentación
de Roku antes de planear nada:

| Volumen | Persistencia real | Sirve para |
|---|---|---|
| `tmp:` | **Se borra al salir la app** | Nada duradero |
| `cachefs:` | **Está en RAM. Se evita en el reinicio del equipo, y el sistema la desaloja cuando otra app necesita espacio** | Sobrevivir una caída de internet con la app abierta |
| `pkg:` | Solo lectura, va dentro del paquete del canal | Contenido de respaldo fijo |
| Registro | Persiste, pero **16–32 KB por canal** | Configuración, no medios |

**Conclusión honesta: en Roku no existe almacenamiento durable de video para un
canal.** Tenías razón en desconfiar: descargar un video no garantiza
conservarlo. Esto define qué se puede ofrecer en cada escenario:

| Escenario | Qué se puede lograr | Qué NO |
|---|---|---|
| 1. Se cae el internet con la app abierta | **Seguir reproduciendo** lo que esté en `cachefs:`, sin quedarse cargando, con aviso discreto | Contenido nuevo |
| 2. Vuelve el internet | **Resincronizar solo** y retomar sin reiniciar la app | — |
| 3. Se reinicia la app (con internet) | Recuperación normal | — |
| 3b. Se reinicia la app (sin internet) | `cachefs:` **puede** sobrevivir; si sobrevive, arranca con lo cacheado | No se puede garantizar |
| 4. Se reinicia la TV sin internet | **Una lámina de respaldo empaquetada en `pkg:`** (logo, mensaje neutral) | **Reproducir la publicidad. Es imposible en Roku.** |

El escenario 4 no tiene solución en Roku. Si es un requisito de negocio, la
respuesta no es programar más: es un reproductor Android TV con almacenamiento
real, y eso ya está fuera del alcance de esta etapa.

### 3.5 Turnos vencidos y anuncios duplicados

`MainScene.brs:409-415` deduplica turnos solo por el contador `n`, **sin mirar
`ts`**. Al recuperar el internet, la TV recibe el turno vigente y lo anuncia
aunque tenga veinte minutos: llama a alguien que ya se fue. Hay que descartar
por antigüedad, y el servidor necesita una clave de idempotencia (QA-G02).

---

## 4. Propuesta de arquitectura y navegación

### 4.1 Arquitectura

Coincido con la dirección propuesta. Python se queda.

```
  TVs Roku            Navegador (React + TS)        POS
      │                        │                     │
      └────────────────────────┼─────────────────────┘
                               ▼
                   nginx  (HTTPS, tv.luminbelleza.com)
                    │                      │
         ┌──────────┘                      └──────────┐
         ▼                                            ▼
   API (FastAPI, modular)                    Medios servidos por nginx
   auth · pantallas · biblioteca             directo desde disco
   listas · programación · turnos            (hoy los sirve el proceso
   mensajes · sucursales · usuarios           Python y compite con el panel)
         │
         ├──────────────► PostgreSQL
         │                empresa · sucursal · pantalla · usuario
         │                contenido · lista · programación · turno
         │                evento · auditoría
         │
         └──────────────► Trabajos en segundo plano (cola en PostgreSQL)
                          ffmpeg: conversión, giro, miniaturas
```

Cuatro decisiones que quiero argumentar, no solo enunciar:

1. **Los medios salen del proceso de la aplicación.** Hoy `_servir_archivo` los
   sirve desde el mismo proceso Python que atiende el panel y las TVs. Con
   15–20 pantallas eso compite por recursos. Que los sirva nginx no cuesta
   trabajo y quita el cuello de botella entero.
2. **La cola de trabajos va sobre PostgreSQL** (`FOR UPDATE SKIP LOCKED`), no
   sobre Redis ni Celery. Una pieza menos que operar un domingo a las 9 de la
   noche. Se cambia cuando el volumen lo justifique.
3. **`empresa_id` en el modelo de datos desde el primer día**, aunque solo
   exista LUMIN. Añadirlo después obliga a reescribir todas las consultas. Y
   —el punto que marcaste— **separar por sucursal no es aislar empresas**: son
   dos ejes distintos. Una empresa nunca debe ver datos de otra; dentro de una
   empresa, un operador ve solo sus sucursales. El modelo lleva los dos.
4. **El aislamiento no se confía solo al código.** Cada tabla hija lleva su
   `empresa_id` y la llave foránea es compuesta contra `(id, empresa_id)` del
   padre, así que la base rechaza una pantalla que apunte a la sucursal de otra
   empresa. Este patrón ya lo tengo escrito y probado del trabajo anterior y se
   puede traer sin arrastrar nada comercial.

**Los tres contratos que no se rompen nunca:** `GET /playlist.json?id=…` con su
respuesta actual, `POST/PUT /api/turno` con el cuerpo que ya usa el POS, y
`/videos/<sucursal>/<archivo>`. El API v2 convive en paralelo detrás de nginx;
los reproductores instalados siguen funcionando hasta que se migren uno a uno.

### 4.2 Navegación

Once secciones, adaptadas a lo que existe de verdad:

| Sección | Qué lleva | Respaldo en el servidor actual |
|---|---|---|
| Inicio | Pantallas en línea, últimas sincronizaciones, errores, avisos | Parcial: hay `visto`, falta lo demás |
| Pantallas | Vinculación, sucursal, zona, estado, lista asignada, control en vivo | Sí |
| Biblioteca | Videos e imágenes, subir, renombrar, eliminar, miniaturas, duración | Sí |
| Listas | Crear, renombrar, ordenar, activar, asignar a pantalla | Sí |
| Programación | Fechas, días, horarios, vencimientos | Sí, mejorable |
| Mensajes | Franja inferior, animación y velocidad | Sí |
| Turnos | Estado de la integración con el POS y configuración | Parcial: hay interruptor por pantalla, no hay pantalla de estado |
| Sucursales | Alta, clave, zona horaria | Sí |
| Integraciones | Conexión con el POS: credenciales, últimas llamadas, errores | **No existe**: hay que construirlo |
| Usuarios y permisos | Invitaciones, rol, sucursales concedidas | Débil (F01/F02/F03) |
| Configuración | Datos de la empresa, preferencias | Parcial |

No propongo pantallas vacías: donde no hay respaldo, lo digo. Nada de editor
gráfico, plantillas, generación de anuncios ni catálogo de aplicaciones.

---

## 5. Plan por bloques

Bloques pequeños, cada uno desplegable por separado y con marcha atrás.

| Bloque | Qué hace | Depende de | Riesgo |
|---|---|---|---|
| **B1** Continuidad del reproductor | Timeouts, vigilante de `buffering`, reintentos, salto de archivos dañados, descarte de turnos vencidos, lámina de respaldo en `pkg:`, caché en `cachefs:` | — | Bajo en servidor, **requiere TV física** |
| **B2** Higiene del servidor actual | Bitácora, 4 carreras, cola de conexiones, contadores | — | Muy bajo |
| **B3** PostgreSQL | Esquema con `empresa_id`, migración desde JSON con respaldo y reversión, medios a nginx | B2 | **Alto: toca los datos** |
| **B4** Identidad y permisos | Sesiones seguras, verificación de correo por código, invitaciones, permisos por sucursal en servidor, alta segura del administrador | B3 | Medio |
| **B5** API v2 y estado real de pantallas | Última conexión / sincronización / reproducción por separado, eventos deduplicados, idempotencia de turnos | B3 | Medio |
| **B6** Frontend React + TypeScript | Menú lateral, las 11 secciones, rutas propias | B5 | Medio |
| **B7** Programación ampliada | Vencimientos, publicación multi-sucursal, excepciones, confirmación de recepción | B5 | Bajo |
| **B8** Credencial por pantalla | Vinculación, token revocable, protocolo v2 con convivencia | B4, B5 | **Alto: toca la flota** |

**B1 y B2 pueden empezar hoy y no dependen de la migración.** B1 es lo que
resuelve el dolor que reportaste.

### Criterios de aceptación

**B1 — Continuidad.** Los cuatro escenarios probados y documentados con
evidencia. Con el internet cortado, la TV no se queda en "cargando": o sigue
con lo cacheado o muestra la lámina de respaldo, y en ningún caso se queda en
negro ni en bucle. Al volver el internet, resincroniza sola sin reiniciar la
app. Un archivo dañado se salta sin detener la lista. Un turno con más de N
minutos no se anuncia. **La prueba en TV física la ejecuta Adrián: yo no puedo
declararla aprobada.**

**B2 — Higiene.** Los errores que hoy se tragan quedan en bitácora con rotación.
Cada carrera tiene una prueba con hilos que falla contra el código viejo y pasa
contra el nuevo. 120 conexiones simultáneas sin pérdidas.

**B3 — PostgreSQL.** La migración corre sobre una **copia sintética
representativa**, no sobre datos reales. Los tres contratos responden byte a
byte igual que antes. Reversión ensayada y cronometrada. Respaldo verificado
restaurando en limpio. **No se ejecuta sobre producción sin tu autorización
explícita, en una ventana acordada.**

**B4 — Identidad.** Un operador sin sucursales concedidas no alcanza ninguna;
pedir una fuera de alcance es 403, nunca sustitución silenciosa. Mover algo
entre sucursales exige permiso en origen y destino. No queda ninguna credencial
en el código. El código de correo es de un solo uso, caduca, está atado al
propósito, se guarda con hash y tiene tope de intentos y de reenvíos. **Sin
registro público**: alta por administrador o invitación. **No se envía ni un
correo real hasta que autorices el entorno.**

**B5 — Estado real.** El panel distingue última conexión, última sincronización,
contenido asignado frente a recibido, y último evento de reproducción. Una
pantalla conectada **no** se presenta como prueba de que está reproduciendo. Un
404 no cuenta como reproducción. Un evento repetido cuenta una sola vez.

**B6 — Frontend.** Cada sección con rutas propias y estados de carga, vacío,
error y falta de permiso. Sin datos simulados. Los permisos se aplican en el
servidor; ocultar un botón no cuenta.

**B7 — Programación.** Conflictos resueltos por una regla determinista y
escrita. Zona horaria por sucursal. El panel confirma que la pantalla recibió
el cambio, no solo que se guardó.

**B8 — Credencial.** Vinculación con código temporal, token revocable por
pantalla. Los reproductores viejos siguen funcionando durante la convivencia,
con prueba de regresión. Migración de la flota una pantalla a la vez.

---

## 6. Lo que necesito de ti

| # | Decisión | Por qué bloquea |
|---|---|---|
| 1 | ¿Los dos iconos borrados de `roku-app/images/` fueron a propósito? | Si se commitean así, el paquete del canal queda inconsistente |
| 2 | ¿Versionamos `docs/coordinacion/`? | Hoy vive solo en tu disco |
| 3 | ¿Confirmas no mezclar la rama SQLite y rescatar solo lo independiente de la base? | Define si B2 o B3 cambian de forma |
| 4 | ¿Escenario 4 (TV reiniciada sin internet) es requisito de negocio? | Si lo es, Roku no da y habría que hablar de Android TV |
| 5 | Ventana para las pruebas físicas en una TV real | B1 no se puede cerrar sin eso |
| 6 | ¿Cuántos minutos hace que un turno esté vencido? | Parámetro de B1 |
| 7 | Entorno de correo autorizado | B4 no envía nada hasta entonces |

---

## 7. Límites que respeto en toda esta etapa

No se despliega ni se reemplaza la aplicación que opera LUMIN sin tu
autorización. No se ejecutan migraciones sobre datos reales. No se envían
correos reales. No se declara compatibilidad de dispositivos sin equipo físico
probado. Fuera de alcance y sin empezar: registro público, planes,
suscripciones, cobros, facturación, panel del propietario, página comercial,
otros reproductores y funciones de IA.

---

## 8. Addendum — hallazgos del encargo ampliado

### 8.1 Causa de los dos equipos con número 6 (y "P6" en los selectores)

**Reproducido y confirmado. Es un defecto, no una coincidencia.**

`registrar_tv` asigna el número con `indice = len(tvs)` (`servidor_lumin.py:443`),
es decir, la cantidad de pantallas que hay *en ese momento*. Y
`/api/tv/eliminar` (`:1402`) borra la entrada con `tvs.pop(id_tv)`.

En cuanto se da de baja una pantalla **intermedia**, el conteo deja de coincidir
con el número más alto en uso, y la siguiente pantalla que se registre recibe un
número que ya existe:

```
seis pantallas dadas de alta   ->  1, 2, 3, 4, 5, 6
se elimina la tercera          ->  1, 2, 4, 5, 6
entra una TV nueva             ->  1, 2, 4, 5, 6, 6     <-- duplicado
```

El panel etiqueta las pantallas como `P` + número, así que las dos aparecen como
**P6**, exactamente como observó Codex.

**Efecto secundario, menos visible pero peor:** `indice` no es solo una etiqueta.
`playlist.json` lo usa para escalonar el arranque de la lista
(`giro_lista = indice % len(archivos)`, `:745`). Dos pantallas con el mismo
índice arrancan la lista **en la misma posición**, de modo que reproducen lo
mismo al mismo tiempo en vez de alternarse. Si en una sucursal hay dos pantallas
mostrando siempre el mismo anuncio a la vez, ésta es la razón.

**Corrección propuesta (bloque B5):** separar los dos conceptos que hoy están
mezclados en un solo campo.

- Un **identificador visible** estable y único, que no se reutiliza al dar de
  baja una pantalla y no cambia cuando se reordena la flota.
- Un **desfase de rotación** calculado aparte, que sí puede recalcularse.

El identificador técnico que usa Roku (`GetChannelClientId`) **no se toca**: es
la llave con la que la TV se reconoce ante el servidor y cambiarla obligaría a
volver a vincular toda la flota.

Nota: la rama `fase1-sqlite-respaldos` reescribió `registrar_tv` usando
`COUNT(*)`, que **conserva el mismo defecto**. Si se rescata algo de esa rama,
esta parte no.

### 8.2 "Lista al aire" no distingue herencia de asignación

`lista_de_tv` (`:326-330`) devuelve la lista asignada a la pantalla y, si no
tiene, la activa de la sucursal. El panel muestra el resultado sin decir cuál de
los dos casos es. Desde el panel no se puede saber si cambiar la lista activa de
la sucursal afectará a esa pantalla o no. La etiqueta debe decir
**"Heredada de la sucursal: Principal"** o **"Asignada a esta TV: Navidad"**.

### 8.3 Escenarios de red: de cuatro a seis

El encargo ampliado añade dos casos que hay que probar y documentar aparte:
**archivo no disponible o incompatible** y **conexión intermitente**. El segundo
es el que más daño hace en la práctica, porque una red que va y viene puede
dejar al reproductor entrando y saliendo de `buffering` sin estabilizarse nunca.
Entra en B1 con histéresis: no reintentar de inmediato, ni dar por recuperada la
conexión con una sola respuesta buena.

### 8.4 Estadísticas: cinco eventos distintos, no uno

Hoy existe un solo contador que se incrementa al pedir el archivo, incluso
cuando la respuesta es 404 (QA-F04). El encargo pide distinguir solicitud,
descarga, inicio de reproducción, finalización y error. Sólo el reproductor
puede reportar los tres últimos, así que **esto depende de B8**: hasta que la TV
mande eventos propios, el servidor no puede saber si un video se reprodujo. Lo
que sí se puede hacer antes es dejar de contar 404 y deduplicar por `Range`.

**Semántica que quedará documentada:** una reproducción no es una persona, y no
es una venta. Los reportes a anunciantes deben decir "reproducciones
registradas", nunca "vistas".
