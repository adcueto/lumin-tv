# Entrega B5a — Estado real de la pantalla y operación remota (parte 1)

Sigue la plantilla de `06-protocolo-y-qa.md`.

## Identidad

- ID: **B5a** (adelanto de B5 "API v2 / estado real" del plan
  `10-diagnostico-y-plan-modernizacion.md`, solo la parte que no necesita
  PostgreSQL) · Revisión **R2**
- Responsable: Claude (desarrollo) · Revisa: Codex
- Fecha: 2026-09-19
- Raíz: `lumin-tv` · Rama: `modernizacion-diagnostico`
- SHA base: `ce2818f` · SHA candidato: el commit de esta entrega
- Estado: **ENTREGADO A QA. Sin aprobar.** Pantalla de diagnóstico: **solo
  propuesta visual**, sin código, pendiente de la aprobación de Adrián.

## Alcance

Las propuestas 1 y 4 de la lista acordada con Adrián (2026-09-19), completas;
la 3 como imagen para aprobar.

**Dentro:**

1. **Estado real en el latido.** La app manda, en la misma petición
   `GET /playlist.json?id=…` de siempre, parámetros opcionales cortos:
   versión de la app, modelo, sistema, IP local, qué reproduce, MB en cache,
   si está sirviendo desde cache/sin red, último error y hace cuánto. El
   servidor 6.10.1 los guarda en `tvs.json` bajo `estado` y `/api/tvs` los
   expone; el panel los muestra bajo cada pantalla. Una app anterior no manda
   nada y todo sigue igual.
2. **Comandos `recargar` y `vaciar_cache`** desde el panel (solo admin).
   Recargar equivale a volver a abrir la app sin tocar la TV; vaciar borra los
   medios en cache (no la lista guardada) y los vuelve a bajar.
3. **Propuesta visual** de la pantalla de diagnóstico
   (`b5a-propuesta-diagnostico.png`). Sin código hasta que se apruebe.

**Fuera, y declarado:** subida del registro al servidor (propuesta 2), la
pantalla de diagnóstico en código, verificación de archivos por huella (6),
confirmación de reproducciones (7), credencial por pantalla (B8), horarios
(B7), cualquier cambio de persistencia (B3).

## Archivos

| Archivo | Cambio |
|---|---|
| `roku-app/components/PlaylistTask.brs/.xml` | Campo `estado` (entrada) y `consultarAhora`; `parametrosDeEstado()` añade los parámetros al latido; datos fijos del equipo con `roDeviceInfo`/`roAppInfo` |
| `roku-app/components/MainScene.brs` | `m.estadoTv` + `publicarEstado()`; se anota qué se reproduce (`reproducirSiguiente`, `onVideoState` con `contentIndex`), los errores de video y de cache, la lámina; comandos `recargar` y `vaciar_cache` |
| `roku-app/components/CacheTask.brs/.xml` | Campos `vaciar`/`vaciado`; `vaciarCache()` borra medios, conserva la lista guardada, cancela la descarga en curso |
| `roku-app/manifest` | build **61** |
| `roku-app/pruebas/planificacion.brs` | Escenario nuevo: vaciar cache (42 comprobaciones) |
| `servidor/servidor_lumin.py` | 6.10.1: `ESTADO_TV_CAMPOS`, `estado_tv_de(params)`, `registrar_tv(id, estado)`, `estado` en `pantallas()`, acciones `recargar`/`vaciar_cache`, panel: línea de estado y dos botones admin |
| `servidor/tests/test_b5a_estado.py` | **Nuevo.** 5 pruebas (suite: 26) |
| `docs/coordinacion/b5a-propuesta-diagnostico.png` | Propuesta visual |

## Contratos

`GET /playlist.json`: la **respuesta** no cambia (prueba
`test_contrato_playlist_igual_con_o_sin_estado`: misma respuesta con y sin
parámetros). La **petición** gana parámetros opcionales, ignorados por 6.9.
`POST /api/tv/comando`: dos acciones nuevas; las demás y el 400 por acción
desconocida se conservan. `/api/tvs`: campo nuevo `estado` (objeto, puede
estar vacío). La app 5.2 build 61 funciona contra 6.9 y 6.10 (los parámetros
se descartan); la 5.1 y la 5.2 build 60 funcionan contra 6.10.1 (sin estado).

Parámetros del latido (todos opcionales, con tope de longitud en el servidor):

| Parámetro | Guardado como | Tope |
|---|---|---|
| `v` | `version` | 16 |
| `m` | `modelo` | 40 |
| `os` | `sistema` | 24 |
| `ip` | `ip` | 45 |
| `r` | `reproduciendo` | 80 |
| `c` | `cache_mb` (entero 0–100000) | — |
| `k=1` | `desde_cache: true` | — |
| `e` | `error` | 120 |
| `eh` | `error_en` = `visto − eh` (instante absoluto) | — |

Privacidad: ningún parámetro lleva datos de clientas, turnos, credenciales ni
el mensaje del cintillo. El estado se reemplaza entero en cada latido: un
error deja de mostrarse cuando la app deja de reportarlo (tras `recargar`).

## Comportamiento antes / después

| Situación | Antes (6.10 / build 60) | Después (6.10.1 / build 61) |
|---|---|---|
| Panel, tarjeta de pantalla | "…A1B2C3 · en línea" | Además: "▶ promo.mp4 · cache 118 MB · app 5.2.61 · Roku Express 4K · OS 12.5.1 · 192.168.1.50" y, si lo hay, "último error: video buffering corte.mp4 · hace 3 min" |
| Pantalla que estuvo sin red | Solo el punto ámbar en la TV, y nada en el panel | Sin red no hay latido, así que el panel no puede saberlo en vivo; al reconectar, el primer latido trae `k=1` si sigue sirviendo desde cache o en lámina, y el panel lo muestra como "▶ (sin red) …" hasta que se normaliza |
| Soporte remoto ante una TV atorada | Ir a la sucursal o pedir que reinicien la TV | Botón ↻ Recargar (olvida bloqueos, pide la lista, empieza de nuevo); botón ⌫ Vaciar cache (con confirmación) |
| App anterior contra 6.10.1 | — | Igual que antes; sin línea de estado |

## Verificación

| Prueba | Resultado |
|---|---|
| `pytest servidor/tests` | **26 pasan** (las 21 anteriores más las 5 de B5a) |
| `comparar_con_base.py` (6.9) | 13 fallan / 13 pasan: fallan las de B2, HEAD y las 3 de B5a que exigen estado o comandos nuevos; pasan las de contrato y `test_latido_sin_parametros_no_crea_estado` |
| Arnés Roku (`brs`) | **42 comprobaciones, 0 fallos** (35 + 7 del escenario vaciar cache) |
| BrighterScript | 0 diagnósticos |
| CI | Corre en el push de esta entrega (ver el run en Actions) |

## No ejecutado

- Roku físico: nada de esto se ha visto en una TV. Pruebas físicas nuevas
  F22–F24 en `docs/reproductor-continuidad.md`.
- El panel se revisó por lectura del HTML/JS, no en navegador.
- `roDeviceInfo.GetIPAddrs()` puede devolver más de una interfaz; se toma la
  primera no vacía. Comprobar en la TV que es la de la red del salón.

## Riesgos que QA debe intentar refutar

1. Longitud de la URL del latido: hoy < 400 caracteres con todos los
   parámetros al tope. `BaseHTTPRequestHandler` acepta hasta 64 KB.
2. `tvs.json` se reescribe en cada latido desde siempre (`visto`); el estado
   añade ~300 bytes por pantalla. Con 20 pantallas es irrelevante.
3. `recargar` limpia bloqueos y fallos: si el archivo dañado sigue ahí, la
   TV lo volverá a intentar tres veces antes de apartarlo otra vez. Es lo
   esperado.
4. `vaciar_cache` durante una descarga la cancela y la trata como obsoleta;
   la escena vuelve a pedir la cache al recibir `vaciado`. Si la lista
   cambia en ese mismo instante, `aplicarDeseados` reconcilia igual.
5. El estado viaja en claro en la URL: mismo nivel de exposición que el `id`
   de la pantalla hoy. La credencial por pantalla (B8) lo cubre.

## Instrucciones de validación

```bash
cd servidor && .venv/bin/python -m pytest tests -q              # 26 passed
python3 roku-app/pruebas/correr.py                                # 42, 0 fallos
```

En una TV con build 61 contra un servidor 6.10.1 de pruebas: mirar la tarjeta
de la pantalla en el panel; pulsar ↻ y ver que la lista arranca desde el
primer elemento; pulsar ⌫ y ver en `telnet 8085` que se borran y vuelven a
bajar los archivos.

## Despliegue y reversión (cuando se autorice)

Servidor: reemplazar `servidor_lumin.py` y reiniciar; sin migración (`estado`
es un campo nuevo dentro de `tvs.json` que 6.9/6.10 ignoran). Reversión: el
archivo anterior; los campos `estado` quedan inertes. App: paquete del SHA
exacto, build 61.

## Operaciones

- Commit y push en `modernizacion-diagnostico`: realizados (push desde la
  máquina del propietario).
- Despliegue al VPS y a las TVs de los salones: **NO realizado, no autorizado.**

---

## Revisión R2 — respuesta a `22-qa-B3-rev4-B5a-1f7782e.md` (Codex, 2026-09-19)

Los dos hallazgos de B5a se **CONFIRMAN**. Build **62**; servidor 6.10.1 sin
cambio de versión (solo una comprobación de permiso).

| ID | Decisión | Qué cambió | Evidencia ejecutada |
|---|---|---|---|
| B5A-QA-01 [P1] los comandos admin no verificaban el rol en la API | **CONFIRMADO.** El botón se ocultaba; la ruta no comprobaba | `ACCIONES_SOLO_ADMIN = ("recargar", "vaciar_cache")`; `/api/tv/comando` responde **403 sin encolar** a cualquier rol distinto de `admin` para esas dos acciones; las demás conservan su contrato | `test_operador_no_puede_recargar_ni_vaciar_cache` (operador 403 en ambas, `n` no avanza, `comandos.json` sin rastro; `pausa` del operador sigue 200; admin 200) y `test_operador_de_otra_sucursal_sigue_sin_poder_mandar_comandos` (200 silencioso para `pausa` como hoy —contrato 6.x, se endurece en B4— y 403 para `recargar`; nada encolado). Suite: **28 pasan** |
| B5A-QA-02 [P1] `recargar` dejaba la reproducción detenida si la respuesta era idéntica | **CONFIRMADO.** Dependía de un evento del campo `playlistJson` que SceneGraph no emite si el valor no cambia | `recargar()` **reinicia la reproducción en el acto** con la última lista conocida (`ultimaListaConocida()`: la última en vivo o, si arrancó sin red, la guardada); fija `m.playlistActual` a esa huella para que una respuesta idéntica no reconstruya y una distinta sí lo haga por el camino normal; la consulta al servidor pasa a ser un refresco, no una condición. Sin lista alguna → lámina "recargando" hasta que llegue | **Arnés nuevo `roku-app/pruebas/escena.brs`**: ejecuta `MainScene.brs` real con dobles de los nodos. 21 comprobaciones, 0 fallos: respuesta idéntica (arranca desde el primer elemento, olvida bloqueos, pide refresco, la respuesta idéntica no notifica y no hace falta), respuesta distinta (se aplica una sola vez más), sin internet (reproduce lo que tiene, sin lámina, reporta `k=1`), sin lista nunca (lámina y petición), el mismo `n` no vuelve a recargar. Contra el `MainScene.brs` de `1f7782e`: **4 fallos** (`control=stop`, sigue en `c.jpg`, sin lámina) |

`correr.py` ejecuta ahora los dos arneses (planificación 42 + escena 21) y
solo devuelve 0 si ambos terminan sin fallos ni errores del intérprete. El
paso de CI usa `set -o pipefail` (recomendación de Codex). Para que el arnés
pueda correr, `guardarOrientacion` tiene un asidero `m.sinRegistro` que en la
TV no existe (mismo patrón que `m.simulacion` en CacheTask).

Límite declarado: el arnés reproduce la semántica "sin notificación si el
valor no cambia" **por construcción** (`llegaRespuesta` no llama a
`onPlaylistJson` con JSON idéntico); no es SceneGraph. F22 sigue pendiente
en equipo físico con build 62.
