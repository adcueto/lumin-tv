# Entrega B1 — Continuidad y recuperación del reproductor

Sigue la plantilla de `06-protocolo-y-qa.md`.

## Identidad

- ID: **B1** (plan en `10-diagnostico-y-plan-modernizacion.md`) · Revisión **R2**
- Responsable: Claude (desarrollo) · Revisa: Codex · Valida en TV: Adrián
- Fecha: 2026-09-15
- Raíz: `lumin-tv` · Rama: `modernizacion-diagnostico`
- SHA base: `ea610d6` (main) · SHA candidato: el commit de esta entrega en la rama
- Estado: **ENTREGADO A QA. Sin aprobar.** La validación física es obligatoria y
  no la ejecuté.

## Alcance

**Dentro:** app Roku 5.1 → 5.2. Límite de espera en la consulta al servidor,
vigilante de `buffering`, reintentos con retroceso, apartado temporal de
archivos dañados, cache en `cachefs:` con última lista guardada, lámina de
respaldo empaquetada, indicador discreto, descarte de turnos vencidos,
descarte de "reproducir ahora" atrasados, orientación recordada entre
arranques, y eliminación de todo mensaje técnico visible a la clienta.

**Fuera:** cualquier cambio de servidor. Identificador de evento para turnos
(QA-G02, B5). Credencial por pantalla (QA-G01, B8). Reporte de eventos de
reproducción al servidor (B5/B8): esta versión sigue sin decirle al servidor
qué reprodujo.

## Archivos

| Archivo | Cambio |
|---|---|
| `roku-app/components/PlaylistTask.brs` | Reescrito: consulta asíncrona con tope de 8 s y `AsyncCancel`; retroceso 4→8→15→30 s; `conectado` con histéresis de 2 fallos; guarda la última lista buena en `cachefs:` y la sirve si arranca sin red |
| `roku-app/components/PlaylistTask.xml` | Campos nuevos `conectado`, `ultimaSincronizacion`, `desdeCache` |
| `roku-app/components/CacheTask.brs` / `.xml` | **Nuevo.** Descarga secuencial a `cachefs:` con tasa mínima, nombre temporal + renombrado, topes y desalojo |
| `roku-app/components/Cache.brs` | **Nuevo.** Nombres de cache compartidos entre escena y tarea (SHA-1 de la URL) |
| `roku-app/components/MainScene.brs` | Vigilante de `buffering`; contador de fallos con lámina y retroceso; apartado de URLs; resolución a cache; turnos vencidos; comandos viejos; capa de continuidad; orientación en registro |
| `roku-app/components/MainScene.xml` | Grupo `capaEstado` con `respaldo`, `detalle`, `indicador`; incluye `Cache.brs` |
| `roku-app/images/respaldo_vertical.png`, `respaldo_horizontal.png` | **Nuevos.** Lámina aprobada por el propietario (`b1-propuesta-visual.png`) |
| `roku-app/images/punto_ambar.png` | **Nuevo.** Indicador de 24 px |
| `roku-app/manifest` | 5.1 build 56 → **5.2 build 58** (R1 fue build 57) |
| `docs/reproductor-continuidad.md` | **Nuevo.** Comportamiento por escenario, parámetros y las 13 pruebas físicas |

## Contratos

Sin cambios. Consumo idéntico de `GET /playlist.json?id=…`. Se leen campos
que ya existían (`turno.ts`, `turno.duracion`, `comando.n`, `vertical`,
`giro`). El servidor 6.9 no se toca. App 5.1 y 5.2 conviven contra el mismo
servidor.

## Comportamiento antes / después

Detallado por escenario en `docs/reproductor-continuidad.md`, sección "Los
seis escenarios". Resumen del defecto reportado:

- **Antes:** `GetToString()` sin tope bloqueaba el bucle de 4 s; `onVideoState`
  no atendía `buffering`, así que el video se quedaba cargando sin fin; la
  clienta veía la URL del servidor en pantalla.
- **Después:** ninguna llamada de red bloquea más de 8 s; `buffering` tiene
  vigilante de 25 s; tras una vuelta completa sin nada reproducible se muestra
  la lámina y se reintenta a 10/20/40/60 s; la clienta ve la lámina o el
  contenido, nunca texto técnico.

## Migraciones

No aplica. El registro del dispositivo gana dos claves (`vertical`, `giro`,
unos bytes); `serverUrl` no cambia.

## Verificación

| Prueba | Resultado |
|---|---|
| Compilación con BrighterScript 0.73.5, nivel `info` | **0 diagnósticos** en los 8 archivos (`.brs`, `.xml`, `manifest`) |
| Línea base 5.1 con el mismo compilador | 0 diagnósticos (el compilador no es más laxo con lo nuevo) |
| Revisión propia de la lógica tras compilar | 4 ajustes aplicados, documentados en el código: el vigilante no se apaga con `stopped` (evento en cola tras `play`); una falla sin red no cuenta contra el archivo; los apartados se limpian al reconectar; la lámina de instalación conserva la pista de `*` |

**No ejecutado — y por qué no cuenta como aprobado:** no hay equipo Roku en
este entorno. El compilador valida sintaxis y referencias, no que el nodo de
video reproduzca desde `cachefs:` ni que `SetMinimumTransferRate` cancele como
se espera en cada modelo. Las 13 pruebas físicas F1–F13 están en
`docs/reproductor-continuidad.md` con pasos y criterio de aprobación.

## Riesgos que QA debe intentar refutar

1. **Reproducción de video desde `cachefs:`.** Roku recomienda `cachefs:` para
   imágenes; para video es plausible pero no lo he visto documentado. La app se
   auto-protege (dos fallas seguidas de copia local y deja de usar cache para
   video en la sesión), pero hay que probarlo por modelo (F12).
2. **Reloj del equipo vs. `ts` del servidor.** El descarte de turnos vencidos
   compara con la hora del Roku. Un equipo con hora mal sincronizada podría
   descartar turnos válidos. Tolerancia de 30 s. Si aparece, la solución de
   fondo es que el servidor mande `ahora` en la respuesta (B5).
3. **Orden de eventos en el vigilante.** El `stop` previo a `play` emite un
   `stopped` encolado; por eso `stopped` no apaga el vigilante. Si algún modelo
   emite los estados en otro orden, el vigilante podría quedar activo durante
   una foto: la escena lo apaga explícitamente al intercambiar fotos, pero
   conviene vigilar F13.
4. **Memoria.** 250 MB en `cachefs:` es RAM compartida. En equipos de gama baja
   podría desalojarse antes; la app lo tolera (consulta existencia al
   reproducir), pero se notaría como "la cache no dura".
5. **Lista guardada al arrancar sin red.** Si la copia de la lista sobrevivió
   pero los medios no, la app intentará reproducir, fallará una vuelta y
   mostrará la lámina: correcto pero tarda hasta 25 s por video en detectarlo.

## Instrucciones de validación

1. Empaquetar `roku-app/` (zip de `manifest`, `source/`, `components/`,
   `images/`) e instalar por modo desarrollador en la TV de pruebas.
2. Ejecutar F1–F13 de `docs/reproductor-continuidad.md` en ese orden.
3. Anotar modelo, versión de Roku OS y resultado por prueba.
4. **No** subir el `.pkg` a la tienda ni actualizar la flota hasta que Codex
   apruebe con esa evidencia.

## Reversión

Volver a instalar el paquete 5.1 build 56 (`git checkout main -- roku-app/`).
El servidor no cambió, así que no hay nada que revertir del lado del VPS. Las
dos claves nuevas del registro son inertes para 5.1.

## Operaciones

- Commit en `modernizacion-diagnostico`: realizado.
- Push de la rama: realizado desde la máquina del propietario, autorizado en
  conversación ("usar el repositorio").
- Despliegue a la flota, a la tienda de Roku o al VPS: **NO realizado, no
  autorizado.**


---

## Revisión R2 — respuesta a `12-qa-B1-ceadf1d.md` (Codex, 2026-09-16)

Los tres hallazgos son **CONFIRMADOS**. Eran fallos de lógica que el compilador
no podía ver y que Codex encontró por lectura del flujo. Siguen siendo, como
dice su informe, hallazgos estáticos: la validación física continúa pendiente,
y para cada corrección se añade una prueba física (F14–F17).

| ID | Decisión | Qué cambió | Dónde |
|---|---|---|---|
| B1-QA-01 [P1] presupuesto de cache no aplicado a descargas nuevas | **CONFIRMADO.** El desalojo solo corría al recibir la lista; cuatro archivos de 70 MB pasaban el tope individual y sumaban 280 MB | `descargar` pide el tamaño por `HEAD` **antes** de bajar; si no cabe, desaloja hasta hacer sitio y si aun así no cabe devuelve `sin_espacio`; **durante** la transferencia vigila el temporal cada 2 s contra el tope por archivo y el presupuesto restante y cancela si se rebasa; al confirmar, `revalidarTotal`. Los temporales cuentan en el total. Margen de 20 MB reservado para la reproducción | `CacheTask.brs`: `descargar`, `tamanoRemoto`, `revalidarTotal`, `listarCache` |
| B1-QA-02 [P1] sin reposición tras fallo con lista estable | **CONFIRMADO.** Un fallo salía de la cola sin volver; la escena solo pedía cache al cambiar la lista; al arrancar desde cache, la primera lista en vivo idéntica no programaba nada | Cola con `intentos` y `noAntesDe`: reintento a 30/60/120/240/300 s, máximo 5; 404/403/"demasiado grande" no se reintentan. La escena reconcilia al cambiar la lista, **al reconectar**, en la **primera lista en vivo tras arrancar desde cache**, y como máximo cada 60 s; nunca en cada latido. Una lista nueva cancela la descarga en curso si ese archivo ya no está en ella | `CacheTask.brs`: `aplicarDeseados`, `siguienteListo`, `esperaReintento`; `MainScene.brs`: `onPlaylistJson`, `onConectado`, `pedirCache` |
| B1-QA-03 [P2] se descartaba un "Mostrar ahora" válido tras reconectar | **CONFIRMADO.** La comprobación se hacía sobre el primer comando *nuevo*, no sobre la primera *respuesta*; si al reconectar llegaba el mismo `n`, el indicador quedaba armado y descartaba el siguiente comando legítimo | La revisión se consume en la primera respuesta tras reconectar, haya cambiado o no el comando; solo se descarta si `n` cambió durante la caída **y** es `reproducir`. Un comando emitido después ya no pasa por ahí | `MainScene.brs`: `manejarComando` |

**Comprobaciones de regresión aportadas (estáticas):** compilación con
BrighterScript a nivel `info`, 0 diagnósticos, sobre el nuevo árbol. Los
recorridos que Codex pidió probar quedan como F14 (suma supera el tope), F15
(archivo individual demasiado grande), F16 (reposición tras fallo con lista
estable) y F17 (comando posterior a reconexión, junto con F10 que cubre el
comando durante la caída), en `docs/reproductor-continuidad.md`. **No los puedo
ejecutar aquí**; son para la TV de pruebas.

**Sobre el estado local ajeno al candidato:** de acuerdo. Los dos iconos
borrados están en el árbol de trabajo de `main`, no en la rama; el paquete para
la TV debe armarse desde la rama (`git archive modernizacion-diagnostico
roku-app`), no desde el directorio de trabajo actual.

Nuevo SHA candidato: el commit de esta revisión (ver `git log -1`). `manifest`
pasa a build 58 para distinguir el paquete R2 del R1 en la TV.


---

## Revisión R3 — respuesta a `14-qa-R2-y-diseno-B3-5c96845.md` (Codex, 2026-09-16)

Los dos hallazgos abiertos de B1 R2 se **CONFIRMAN**. El primero lo reprodujo
Codex con una petición real a un servidor candidato aislado (`HEAD` → 501); el
segundo es de lectura del flujo. El efecto en la cache, en ambos casos, sigue
siendo análisis estático: no se ha ejecutado en un Roku.

| ID | Decisión | Qué cambió | Dónde |
|---|---|---|---|
| R2-B1-01 [P1] tamaño desconocido impide desalojar | **CONFIRMADO.** El servidor no implementaba `do_HEAD` (501, evidencia ejecutada por Codex) y `tamanoRemoto` convertía eso en 0; el único desalojo previo exigía tamaño > 0, así que contra el servidor real nunca se desalojaba antes de bajar | **Servidor 6.10:** `do_HEAD` para `/videos/`, `/rapidos/` y `/miniaturas/`: 200 con `Content-Type`, `Content-Length` y `Accept-Ranges`, sin cuerpo, 404 si no existe, **nunca incrementa el contador**. Tres pruebas nuevas (13 en la suite). **Roku:** si el tamaño es desconocido se reserva el tope por archivo (80 MB) y se desaloja lo más viejo hasta que quepa esa reserva; el desalojo ya no depende de que `HEAD` exista. `sin_espacio` queda como fallo terminal que **solo** se reintenta cuando cambia la lista (el presupuesto pudo cambiar), no en cada ciclo | `servidor_lumin.py`: `do_HEAD`; `test_b2_higiene.py`: `test_head_*`; `CacheTask.brs`: `descargar`, `registrarFallo`, `aplicarDeseados` |
| R2-B1-02 [P2] la reconciliación perdía el historial y duplicaba el activo | **CONFIRMADO.** El estado vivía en la cola; al reconstruirla, un 404 o un agotado volvían con `intentos = 0`, y la descarga activa, retirada de la cola, se reinsertaba | Registro por URL (`m.registro`) separado de la cola: `intentos`, `noAntesDe`, `terminal`, `motivo`, `hasta`. La cola es solo orden, deduplicada, y excluye a la descarga activa (`m.activo`). Reconciliar reconstruye la cola sin tocar intentos ni esperas y sin insertar el activo; solo borra del registro lo que salió de la lista. Reglas explícitas para volver a intentar un terminal: 404/403/410/"demasiado grande" → cuarentena de 30 min y luego un ciclo nuevo; `sin_espacio` → al cambiar la lista; `agotado` → al reconectar (`reconectado`, contador que la escena incrementa en `onConectado`). Máximo pasa de 5 a **6 intentos**, para que las cinco esperas anunciadas (30/60/120/240/300 s) se cumplan de verdad | `CacheTask.brs`: `entrada`, `encolar`, `aplicarDeseados`, `siguienteListo`, `registrarFallo`, `atenderMensaje`; `CacheTask.xml`: campo `reconectado`; `MainScene.brs`: `onConectado` |

Precisiones que Codex pidió y quedan aplicadas: la espera de 300 s ahora sí se
alcanza (sexto intento); "404 no se reintenta" se reformula como "404 no se
reintenta durante 30 minutos ni al reconciliar"; el activo nunca se duplica
porque `encolar` lo rechaza y `aplicarDeseados` lo salta. Se eliminaron los
`goto` que quedaban en `CacheTask.brs`.

**Evidencia de esta revisión.** Servidor: suite de 13 pruebas contra el árbol,
13 pasan (Python 3.11, arnés con servidor real). Roku: compilación con
BrighterScript a nivel `info`, 0 diagnósticos, sobre el nuevo árbol; `manifest`
pasa a **build 59**. Los recorridos de aceptación que pide Codex quedan como
F18 (tamaño desconocido con cache casi llena), F19 (404 sostenido durante
varias reconciliaciones), F20 (seis intentos con lista estable, esperas
acumuladas ≈ 12.5 min) y F21 (reconciliación durante una descarga que falla),
en `docs/reproductor-continuidad.md`. **No los puedo ejecutar aquí.**

**Sobre la convivencia.** Con la app 5.2 build 59 contra el servidor 6.9 (sin
`HEAD`) el comportamiento es el conservador: reserva de 80 MB y desalojo por
antigüedad; funciona, solo cachea menos. Contra 6.10 usa el tamaño real. Ningún
contrato de `GET` cambia.

Nuevo SHA candidato: el commit de esta revisión (ver `git log -1`).
