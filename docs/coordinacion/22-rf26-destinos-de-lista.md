# RF-26 — "Reproducir en…": destinos de una lista, grupos de pantallas y estados de entrega

Fecha: 2026-09-19 · Propuesta de Claude para decisión de Adrián y revisión de Codex ·
Estado: **diseño**, nada implementado. Responde a las cinco faltas del informe 23;
rev. 4 (2026-09-19) incorpora los problemas 2 y 3 del informe 24 (aislamiento por
sucursal en el esquema y confirmación por el par lista+versión), ensayados en
`servidor/ensayos_b3/test_ensayo_destinos.py`.

## 1. Qué pide RF-26

Desde cada lista, elegir en qué pantallas se reproduce: pantallas sueltas o
grupos de la sucursal, ver el destino efectivo, los conflictos y el estado de
entrega por pantalla. Hoy la asignación es al revés (en la pantalla se elige su
lista) y no hay grupos.

## 2. Semántica: grupo persistente frente a selección puntual

| Concepto | Qué es | Vive en |
|---|---|---|
| **Grupo** | Conjunto **con nombre** de pantallas de una sucursal ("Salas", "Con turnos"). Persistente; se edita en Pantallas. Una pantalla puede estar en varios grupos | `grupo_pantallas`, `grupo_pantalla_miembro` |
| **Destino** | La asignación de una lista a **una** pantalla o a **un** grupo | `lista_destino` |
| **Selección puntual** | Marcar pantallas sueltas en "Reproducir en…" crea un destino **por pantalla**; no crea un grupo. Si se quiere reutilizar, "guardar como grupo" | `lista_destino.pantalla_id` |

Reglas de cambio de miembros y borrado:

- Añadir una pantalla a un grupo la hace heredar los destinos del grupo **en
  el acto** (la lista efectiva se recalcula en su siguiente latido). Quitarla,
  lo mismo en sentido inverso.
- Borrar un grupo borra sus destinos (`ON DELETE CASCADE`); las pantallas
  vuelven a lo que les corresponda por la regla de §3. El panel avisa antes:
  "Estas 2 pantallas volverán a la lista al aire".
- Borrar una lista borra sus destinos; ídem. Borrar una pantalla borra su
  pertenencia a grupos y sus destinos directos.
- Mover una pantalla de sucursal la saca de todos los grupos **y destinos** de
  la sucursal de origen (lo impone el esquema, §6); el panel lo avisa al mover.

## 3. Prioridad: una sola regla, escrita

Lista efectiva de una pantalla, en este orden y sin excepciones:

1. **Destino directo** a la pantalla. Solo puede haber uno (`un_destino_por_pantalla`).
2. Si no hay, entre los grupos a los que pertenece y que tienen lista, el de
   **mayor `prioridad`**; a igual prioridad, el asignado **más recientemente**.
   La prioridad es un número por destino de grupo que el administrador ve y
   puede cambiar ("Salas manda sobre Con turnos").
3. Si no hay, la **programación** vigente (B7), cuando exista.
4. Si no hay, la **lista al aire** de la sucursal.

"Lista propia > programada > lista al aire" del prototipo anterior era
insuficiente porque no decía qué pasa entre dos grupos; esta regla lo cierra
con `prioridad` + `asignado_en`. El panel muestra siempre **por qué** una
pantalla reproduce lo que reproduce ("P2: Otoño por destino directo").

## 4. Confirmación de reemplazo

Al pulsar "Reproducir en…" con una selección, antes de guardar el panel
calcula y muestra un resumen de **pantallas únicas**: cuáles pasan a
reproducir esta lista, cuáles **no cambian** y por qué (destino directo a otra
lista, grupo de mayor prioridad), y ofrece la acción autorizada para cada
conflicto:

> Reproducirá en **P1, P3, P4, P5**.
> **P2** no cambia: tiene destino directo "Otoño".  [Reemplazar en P2]
>
> [Cancelar]  [Reproducir en 4 pantallas]

"Reemplazar" borra el destino directo anterior de esa pantalla y crea el
nuevo; queda en auditoría (`lista_destino.asignado_por`). Sin esa acción
explícita, la intención nunca es ambigua: lo que no se puede aplicar se dice.

## 5. Estados de entrega por pantalla: qué prueba cada uno

**Rev. 4 (informe 24, problema 3):** la identidad de lo entregado es siempre
el **par `(lista_id, version)`**, nunca el número solo. Dos listas distintas
pueden ir ambas por la "versión 1"; una TV que confirma "1" no dice qué lista
reproduce. Por eso la app envía y el servidor guarda el par, y la comparación
"al día" es igualdad de pares.

| Estado | Qué significa exactamente | Cómo se sabe | Disponible desde |
|---|---|---|---|
| **enviada** | El servidor guardó el destino y la próxima respuesta a esa pantalla llevará la lista L en su versión N | `lista_destino` + `lista.version`; al servir `/playlist.json` se anota `pantalla.(lista_env_id, lista_env_version) = (L, N)` y la respuesta lleva `lista_id` y `version` | B6 con el servidor actual |
| **recibida** | La TV **declaró** en un latido posterior que tiene aplicada (L, N) | La app manda `l=<lista_id>&lv=N` en el latido (parámetros nuevos, mismo mecanismo que B5a); el servidor anota `(lista_rec_id, lista_rec_version)`. Que la TV pida la playlist **no** cuenta: solo cuenta que **diga** qué par aplicó | B5b (app build siguiente + servidor) |
| **reproduciendo** | La TV confirmó que está reproduciendo un elemento de (L, N) | Confirmación de reproducción (propuesta 7, evento idempotente por elemento); `(lista_conf_id, lista_conf_version)` | Propuesta 7 |

Las versiones son un **historial append-only** (`lista_version`): cada `+1`
inserta una fila y nunca se borra ni se reescribe, así una lista puede
avanzar a la versión 2 mientras una pantalla sigue confirmando la 1, y el
panel enseña "enviada (Promos, 2) · recibida (Promos, 1)". Un par que la lista
nunca tuvo no se puede guardar (llave foránea al historial). Ensayado en
`servidor/ensayos_b3/test_ensayo_destinos.py`.

Hasta que exista cada mecanismo, el panel **no muestra** el estado
correspondiente (no se infiere del latido). El tiempo entre estados se mide y
se enseña ("recibida 12:41, 6 s después de enviada"); no se promete.

## 6. Impacto en el modelo (B3 §3.2b, rev. 7)

Cuatro tablas nuevas (`grupo_pantallas`, `grupo_pantalla_miembro`,
`lista_destino`, `lista_version`), `lista.version` y tres **pares** de
columnas en `pantalla` (`lista_env_*`, `lista_rec_*`, `lista_conf_*`, con
`CHECK` de par completo y FK al historial). Todas con `empresa_id` y la
política RLS estándar (por empresa).

**Aislamiento por sucursal (informe 24, problema 2).** La rev. 6 solo ataba
el grupo a su sucursal; miembros y destinos comprobaban `empresa_id` y nada
más, así que una TV de Juriquilla podía entrar en un grupo de Plaza y una
lista de Plaza asignarse a un grupo de Juriquilla. En la rev. 7 la sucursal
viaja en todas las llaves: `pantalla`, `lista` y `grupo_pantallas` exponen
`UNIQUE (id, sucursal_id)`, y `grupo_pantalla_miembro` y `lista_destino`
llevan `sucursal_id` con llaves foráneas compuestas `(x_id, sucursal_id)`
hacia las tres. Un cruce de sucursal es una violación de llave foránea, no
una comprobación que el panel o la API puedan olvidar. Consecuencia
comprobada: **mover una pantalla de sucursal la saca de sus grupos y de sus
destinos** en cascada (la relación es de la sucursal, no viaja con la TV); el
panel debe avisarlo en el cuadro de "Mover a…" y la pantalla queda con la
lista al aire de la sucursal nueva hasta que se le asigne otra. Ensayado con
el DDL de la rev. 6 (los tres cruces entraban) y el de la rev. 7 (los tres
fallan; lo correcto entra).

Índices únicos que hacen imposible la ambigüedad: un destino directo por
pantalla, una lista por grupo. Permisos: crear/editar grupos y destinos
requiere alcance sobre la sucursal (operador) y, para "reemplazar" un destino
ajeno, el mismo permiso; borrar grupos, administrador. Reutilización entre
sucursales: **no** (ahora lo impide el esquema; copiar una lista a otra
sucursal es otra función). Migración desde hoy: `tvs[id].lista` se convierte
en un destino directo por pantalla, con la sucursal de la pantalla; no hay
grupos que migrar.

## 7. Qué cambia en el prototipo (rev. 3)

La ficha "Reproducir en…" de Listas muestra la regla de prioridad por
pantalla, un número de prioridad editable en los destinos de grupo, y el
cuadro de confirmación de reemplazo de §4. Los estados de entrega se
etiquetan con lo que los sustenta; "recibida" y "reproduciendo" aparecen como
**diseño** hasta B5b y la propuesta 7.

## 8. Decisiones para Adrián

- **D8** ¿Grupos con nombre por sucursal (propuesta) o solo selección puntual
  sin grupos persistentes? Lo segundo es más simple y cubre "estas tres TVs";
  lo primero cubre "todas las salas" cuando entra una TV nueva.
- **D9** ¿Reemplazar un destino directo de otra lista lo puede hacer la
  operadora de la sucursal o solo el administrador? Propuesta: operadora con
  alcance sobre la sucursal; queda en auditoría.
