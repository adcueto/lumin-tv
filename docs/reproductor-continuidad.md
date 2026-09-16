# Reproductor Roku — continuidad y recuperación (app 5.2 build 59)

Qué hace la app cuando falla la red o un archivo, qué garantiza y qué no.
Referencia para operación, para QA y para las pruebas en TV física.

## Lo que Roku permite de verdad

Verificado en la documentación de Roku antes de diseñar esto:

| Volumen | Qué pasa con él | Uso en LUMIN TV |
|---|---|---|
| `cachefs:` | Vive en **RAM**. Sobrevive a cerrar la app. **Se pierde al reiniciar el equipo** y el sistema lo desaloja si otra app necesita espacio | Copia de los medios de la lista y de la última lista buena |
| `tmp:` | Se borra al cerrar la app | No se usa |
| `pkg:` | Solo lectura, va dentro del canal | Lámina de respaldo |
| Registro | Persiste; 16–32 KB por canal | URL del servidor y orientación (unos bytes) |

**Consecuencia:** no existe almacenamiento durable de video para un canal de
Roku. La cache sirve para una caída de internet con la app abierta, no para
una TV reiniciada sin red. Eso último muestra la lámina, y **no debe
presentarse como reproducción sin conexión**.

## Los seis escenarios

| # | Escenario | Comportamiento en 5.2 | Antes (5.1) |
|---|---|---|---|
| 1 | Se cae el internet a media reproducción | El vigilante detecta `buffering` sin avance en 25 s y salta al siguiente. Lo que está en cache se sigue reproduciendo. Solo aparece el punto ámbar. Si nada es reproducible: lámina, con reintentos a 10, 20, 40, 60 s | El video se quedaba en `buffering` sin fin. Mensaje técnico con la URL del servidor en pantalla |
| 2 | Vuelve el internet | La consulta (cada 4 s, con tope de 8 s) responde, `conectado` vuelve a `true`, la lámina se retira y se retoma la lista. Los archivos apartados durante la caída se liberan | La consulta bloqueada sin tope podía tardar minutos en soltarse |
| 3 | Se reinicia la app, con internet | Recuperación normal. La cache en `cachefs:` sigue ahí y se reutiliza | Igual, sin cache |
| 3b | Se reinicia la app, **sin** internet | A los 12 s, si `cachefs:` sobrevivió, la app arranca con la última lista buena y reproduce lo que haya en cache. Comandos y turnos de esa lista guardada **no** se ejecutan. Si la cache no sobrevivió: lámina | "Cargando configuración..." indefinido |
| 4 | Se reinicia la **TV** sin internet | `cachefs:` se perdió con el reinicio. Lámina de respaldo, en la orientación recordada en el registro. **No hay publicidad: es un límite de Roku** | Mensaje técnico indefinido |
| 5 | Archivo no disponible o incompatible | Se salta. A la tercera falla seguida **con red** se aparta 10 minutos y la lista sigue sin él. Si la copia en cache falla, se borra y se reintenta por red. Si dos copias de cache fallan seguidas, la app deja de usar cache para video en esa sesión (modelo que no lo soporta) | Un `error` saltaba; un archivo que colgaba en `buffering` detenía todo |
| 6 | Conexión intermitente | El estado `conectado` solo cambia tras **dos** fallos seguidos; el intervalo de consulta crece 4 → 8 → 15 → 30 s y vuelve a 4 al primer éxito. Las fallas de archivo durante la desconexión no cuentan como archivo dañado | Cada bache disparaba el mensaje técnico |

## Turnos y comandos al reconectar

- **Turno vencido:** si `ahora − ts > duracion + 30 s`, no se anuncia. Antes se
  llamaba a alguien que ya se había ido. Si el turno sigue vigente pero lleva
  tiempo emitido, se muestra solo el tiempo que le queda.
- **Comando "reproducir ahora" emitido durante la desconexión:** se descarta al
  reconectar (sorprendería a la clienta con algo de hace media hora).
- **Pausa / continuar / silencio / sonido:** describen un estado deseado y **sí**
  se aplican al reconectar.
- **Deduplicación:** sigue por el contador `n`, como antes. El identificador de
  evento del lado del servidor (QA-G02) es del bloque B5.

## Lo que ve cada quien

| Situación | La clienta | Quien atiende |
|---|---|---|
| Todo bien | Contenido | Nada |
| Sin red, con cache | Contenido | Punto ámbar en la esquina |
| Sin red, sin cache | Lámina LUMIN "Volvemos en un momento" | Texto pequeño: "sin conexión desde HH:MM · última sincronización HH:MM" |
| Sin contenido asignado | Lámina | "sin contenido asignado" |
| Instalación con URL mal escrita | Lámina | "sin respuesta del servidor · presiona * para cambiar la URL" |

Ningún mensaje técnico en grande. El botón `*` sigue abriendo el diálogo de URL.

## Parámetros

| Parámetro | Valor | Dónde |
|---|---|---|
| Tope de la consulta al servidor | 8 s | `PlaylistTask.brs` |
| Intervalo de consulta | 4 s; retroceso a 8, 15, 30 s | `PlaylistTask.brs` |
| Fallos seguidos para marcar "sin conexión" | 2 | `PlaylistTask.brs` |
| Vigilante de `buffering` | 25 s | `MainScene.brs` |
| Reintentos desde la lámina | 10, 20, 40, 60 s | `MainScene.brs` |
| Fallas para apartar un archivo | 3, durante 10 min | `MainScene.brs` |
| Tolerancia de turno vencido | `duracion` + 30 s | `MainScene.brs` |
| Cache total / margen / por archivo | 250 MB / 20 MB reservados / 80 MB | `CacheTask.brs` |
| Presupuesto | Se comprueba **antes** de bajar (tamaño por `HEAD`; el servidor 6.10 lo responde, el 6.9 no) y cada 2 s **durante** la descarga; se revalida al confirmar | `CacheTask.brs` |
| Tamaño desconocido (sin `HEAD`) | Se reserva el tope por archivo (80 MB) y se desaloja lo más viejo hasta que quepa esa reserva | `CacheTask.brs` |
| Reintentos de descarga | 6 intentos por archivo con esperas de 30, 60, 120, 240 y 300 s. El estado (intentos, espera, terminal) vive en un registro por URL y **no** se reinicia al reconciliar | `CacheTask.brs` |
| Fallos terminales | 404/403/410 y "demasiado grande": cuarentena de 30 min y luego un ciclo nuevo. "Sin espacio": hasta que cambie la lista. "Agotado" (6 intentos): hasta que vuelva la red | `CacheTask.brs` |
| Reconciliación de cache | Al cambiar la lista, al reconectar, en la primera lista en vivo tras arrancar desde cache, y como máximo cada 60 s | `MainScene.brs` |
| Descarga colgada | < 8 KB/s durante 20 s | `CacheTask.brs` |
| Arranque sin lista | lámina a los 15 s; lista guardada a los 12 s | ambos |

## Contrato con el servidor

**Sin cambios en `GET`.** La app sigue consumiendo `GET /playlist.json?id=…` con la
misma respuesta, incluidos `comando`, `turno` (con `ts` y `duracion`, que ya
existían) y las URLs de `/videos/…` y `/miniaturas/…`. Además pregunta el
tamaño con `HEAD` a la misma URL del medio: el 6.10 lo responde (sin contar
reproducción); el 6.9 devuelve 501 y la app lo trata como tamaño desconocido.
El servidor 6.9 no necesita tocarse para desplegar la app 5.2, y la app 5.1
sigue funcionando contra el mismo servidor durante la convivencia.

---

## Validación en TV física — pendiente del propietario

Lo que sigue **no lo puedo ejecutar yo**. Compilé con el compilador de
BrightScript (cero diagnósticos), pero el comportamiento real del nodo de
video, de `cachefs:` y del reloj solo se comprueba en un equipo. Hasta
entonces, B1 está **implementado y sin aprobar**.

Preparación: una TV de pruebas (la de casa, que ya hace de canaria), la app
5.2 instalada por modo desarrollador, una sucursal de prueba con al menos dos
videos y una imagen, y la posibilidad de cortar el internet del router **sin
cortar la corriente de la TV**.

| # | Prueba | Pasos | Pasa si |
|---|---|---|---|
| F1 | Caída a media reproducción | Con la lista sonando, desconectar el WAN del router. Esperar 2 min | La pantalla nunca se queda en "cargando". Aparece el punto ámbar. Lo que ya se había reproducido antes sigue en rotación. Sin mensaje técnico |
| F2 | Todo falla | Misma situación, pero con una lista recién asignada que aún no se haya reproducido (cache vacía) | Antes de 2 min aparece la lámina LUMIN con el texto pequeño "sin conexión desde…". No queda en negro ni en bucle |
| F3 | Recuperación | Reconectar el WAN | Antes de 40 s la lámina se retira sola, el punto ámbar desaparece y la lista retoma. Sin reiniciar la app |
| F4 | Reinicio de app sin red | Con cache poblada (F1 pasada), salir del canal con Home, cortar el WAN, volver a entrar | Antes de 20 s reproduce desde cache (escenario 3b). Anotar el modelo y si funcionó: es la prueba de que `cachefs:` sobrevive al cierre en ese equipo |
| F5 | Reinicio de TV sin red | Con el WAN cortado, apagar y encender la TV | Muestra la lámina en la orientación correcta. **Se espera que NO haya publicidad**: si la hubiera, anotarlo, sería mejor de lo documentado |
| F6 | Archivo dañado | Subir a la lista un archivo `.mp4` que no sea video (renombrar un `.txt`) | El resto de la lista sigue. El archivo malo no vuelve a intentarse en 10 min. Después se reintenta solo |
| F7 | Intermitente | Cortar y reconectar el WAN cada 10 s durante 2 min | El punto ámbar no parpadea en cada corte. Sin mensajes técnicos. Al estabilizarse, retoma en menos de 40 s |
| F8 | Turno vencido | Cortar el WAN, mandar un turno desde el POS con `duracion: 30`, esperar 2 min, reconectar | El turno **no** se anuncia |
| F9 | Turno vigente tras reconectar | Cortar el WAN, mandar un turno con `duracion: 300`, reconectar a los 60 s | El turno se anuncia y dura unos 4 min, no 5 |
| F10 | Comando viejo | Cortar el WAN, pulsar "Mostrar al cliente" en el panel, reconectar | La foto **no** se muestra. Luego, con red, pulsar de nuevo: sí se muestra |
| F11 | Pausa durante la caída | Cortar el WAN, pulsar "Pausa" en el panel, reconectar | La TV se pausa al reconectar |
| F12 | Video desde cache | Con cache poblada y red presente, mirar en el log del dispositivo (`telnet IP 8085`) si las URLs reproducidas empiezan por `cachefs:/` | Si reproduce desde cache: anotar modelo. Si falla dos veces y pasa a red: anotar modelo también; la app se auto-protege, pero conviene saber en qué equipos no sirve |
| F14 | Presupuesto de cache (B1-QA-01) | Lista con 4 videos de ~70 MB cada uno (suma 280 MB > 250 MB) | Nunca hay más de ~230 MB en `cachefs:` (250 − margen). Alguno queda sin cachear y se reproduce por red; no hay desalojo por el sistema ni cierre de la app |
| F15 | Archivo individual demasiado grande | Un video de 100 MB en la lista | Contra 6.10, `HEAD` lo descarta sin bajarlo; contra 6.9 se cancela al superar 80 MB durante la bajada. En ambos casos se reproduce por red y el resto de la lista sí se cachea; no se vuelve a intentar en 30 min |
| F16 | Reposición tras fallo (B1-QA-02) | Cortar el WAN justo al asignar una lista nueva; esperar 1 min; reconectar; **no** tocar la lista | En los 5 min siguientes la cache se llena sola (verificar con `telnet IP 8085` los mensajes de descarga). Un segundo corte ya se sobrevive con cache |
| F17 | Comando posterior a reconexión (B1-QA-03) | Cortar el WAN sin mandar comandos; reconectar; esperar 20 s; pulsar "Mostrar al cliente" | La foto **sí** se muestra (antes se descartaba). Y F10 sigue pasando: un comando emitido *durante* el corte se descarta |
| F18 | Tamaño desconocido con cache casi llena (R2-B1-01) | Contra un servidor **6.9** (sin `HEAD`), lista con tres videos de ~70 MB reproducida hasta llenar la cache; cambiar a una lista con un video nuevo de ~30 MB | El nuevo se descarga igual: en el log (`telnet IP 8085`) se ve el desalojo de uno de los viejos antes de bajar. Repetir contra **6.10**: el desalojo es el justo para el tamaño real |
| F19 | 404 sostenido (R2-B1-02) | En la lista, un video cuyo archivo se borró del servidor. Dejar la TV 10 min con la lista sin cambios | En el log aparece **un solo** intento (`http_404`); las reconciliaciones periódicas no lo vuelven a intentar. Pasados 30 min, un intento más |
| F20 | Seis intentos con lista estable (R2-B1-02) | Bloquear en el router solo el puerto del servidor (no todo el WAN, para que `/playlist.json` siga si se sirve aparte) o, más simple: cortar el WAN justo al asignar una lista nueva y dejarlo cortado 15 min | Exactamente 6 intentos del mismo archivo con esperas crecientes (30, 60, 120, 240, 300 s) y luego `agotado`. Al reconectar, vuelve a intentarse desde cero y termina descargando |
| F21 | Reconciliación durante una descarga que falla (R2-B1-02) | Con un archivo grande (~70 MB) bajando por una red lenta, cambiar dos veces otra parte de la lista (p. ej. el cintillo) en menos de 60 s | El log muestra una sola descarga activa de ese archivo; no aparece un segundo intento paralelo ni se reinicia el contador de intentos |
| F13 | Regresión de lo que ya funcionaba | Cintillo animado y fijo, cambio de velocidad, lista asignada a esa TV, turno normal con próximos y espera, silencio/sonido, "Enviar a…" con foto de 15 s | Todo igual que en 5.1 |

Registrar para cada prueba: modelo de Roku, versión de Roku OS, resultado y,
si falló, qué se vio. Con eso Codex decide, y con eso se sabrá qué modelos
reproducen desde cache y cuáles no antes de prometer nada.
