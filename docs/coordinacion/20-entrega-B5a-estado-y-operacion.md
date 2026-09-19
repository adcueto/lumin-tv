# Entrega B5a — Estado real de la pantalla y operación remota (parte 1)

Sigue la plantilla de `06-protocolo-y-qa.md`.

## Identidad

- ID: **B5a** (adelanto de B5 "API v2 / estado real" del plan
  `10-diagnostico-y-plan-modernizacion.md`, solo la parte que no necesita
  PostgreSQL) · Revisión **R1**
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
