# RF-26 — "Reproducir en…": destinos de una lista, grupos de pantallas y estados de entrega

Fecha: 2026-09-19 · Propuesta de Claude para decisión de Adrián y revisión de Codex ·
Estado: **diseño**, nada implementado. Responde a las cinco faltas del informe 23;
rev. 4 (2026-09-19) incorpora los problemas 2 y 3 del informe 24 (aislamiento por
sucursal en el esquema y confirmación por el par lista+versión); rev. 5 (2026-09-19)
responde al informe 25: la confirmación identifica una **entrega numerada** por
pantalla (no solo el par), el historial de versiones es por empresa, y mover una
pantalla exige limpiar sus relaciones (la base no lo hace en cascada); rev. 6
(2026-09-19) responde al informe 26: servir es idempotente y serializado por
pantalla, y borrar una lista no rompe las pantallas que la reproducían. Ensayado en
`servidor/ensayos_b3/test_ensayo_destinos.py` (17).

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
- Borrar una lista borra sus destinos, su historial de versiones y sus entregas; las pantallas que la reproducían quedan sin entrega vigente y reciben una nueva (la lista al aire) en su próxima consulta. Borrar una pantalla borra su
  pertenencia a grupos y sus destinos directos.
- Mover una pantalla de sucursal **exige** quitarla antes de todos los grupos
  y destinos de la sucursal de origen: la base rechaza el movimiento mientras
  queden (§6); el servidor lo hace en una sola transacción y el panel lo avisa
  en el cuadro de "Mover a…" ("saldrá de Salas y dejará de reproducir Promos").

## 3. Prioridad: una sola regla, escrita

Lista efectiva de una pantalla, en este orden y sin excepciones:

1. **Destino directo** a la pantalla. Solo puede haber uno (`un_destino_por_pantalla`).
2. Si no hay, entre los grupos a los que pertenece y que tienen lista, el de
   **mayor `prioridad`**; a igual prioridad, el asignado **más recientemente**
   (`asignado_en`); si aun así empatan (mismo instante, posible en una
   asignación en lote), el de **menor `grupo_id`**: el orden total es
   `ORDER BY prioridad DESC, asignado_en DESC, grupo_id ASC LIMIT 1` y no
   depende del plan de consulta (pendiente conservado del informe 25). Un
   empate en `prioridad` entre grupos que comparten pantallas es, además, un
   **conflicto** que el panel muestra y pide resolver; el orden anterior solo
   garantiza que, mientras tanto, todas las pantallas y el servidor resuelvan
   igual. La prioridad es un número por destino de grupo que el administrador
   ve y puede cambiar ("Salas manda sobre Con turnos").
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

**Rev. 5 (informe 25, problema 1).** Lo que se confirma no es un contenido
sino una **entrega**. Cada vez que el servidor sirve una lista a una pantalla
crea una entrega con número consecutivo **por pantalla** (1, 2, 3…) que
registra el par `(lista_id, version)` servido y cuándo. La respuesta a la TV
lleva ese número (`entrega`), la TV lo devuelve en el latido (`en=`) y en la
confirmación de reproducción, y el servidor guarda tres números por pantalla:
enviada, recibida, reproduciendo. "Al día" es **igualdad de números de
entrega**. El par solo no bastaba: dos listas distintas pueden ir por la
"versión 1" (informe 24) y, sobre todo, dos asignaciones sucesivas de la
**misma** lista (L1 → L2 → L1) tienen el mismo par, así que una confirmación
de la primera asignación parecía "al día" en la tercera (informe 25).

| Estado | Qué significa exactamente | Cómo se sabe | Disponible desde |
|---|---|---|---|
| **enviada** | La entrega vigente de esa pantalla es *n* = (L, N) y cada respuesta la lleva mientras no cambie nada | `pantalla_entrega` + `pantalla.entrega_env = n`; la respuesta de `/playlist.json` lleva `entrega`, `lista_id` y `version`. **Servir es idempotente** (rev. 6): la TV consulta cada minuto y recibe el mismo *n* hasta que cambie la lista o su versión; solo entonces nace *n+1*. Las peticiones simultáneas de una misma TV se serializan en la fila de la pantalla | B6 con el servidor actual |
| **recibida** | La TV **declaró** en un latido posterior que tiene aplicada la entrega *n* | La app manda `en=n` en el latido (parámetro nuevo, mismo mecanismo que B5a); el servidor anota `entrega_rec = n` solo si *n* es mayor que el anotado. Que la TV pida la playlist **no** cuenta: solo cuenta que **diga** qué entrega aplicó | B5b (app build siguiente + servidor) |
| **reproduciendo** | La TV confirmó que está reproduciendo un elemento de la entrega *n* | Confirmación de reproducción (propuesta 7, evento idempotente por elemento, con `en`); `entrega_conf = n`, monótono | Propuesta 7 |

Reglas que el esquema y el SQL imponen (ensayadas, incluidos el contraejemplo
del informe 25 tal cual y las tres reproducciones del informe 26): consultar
sin cambios **no crea entregas** (la recepción no queda una atrás); dos
peticiones simultáneas de la misma TV **no chocan** (contador en la fila de la
pantalla, tomada con `FOR UPDATE`; con la misma lista en carrera, una sola
entrega); **borrar una lista** borra su historial y sus entregas, deja los
tres punteros de la pantalla en NULL sin tocar su id ni su contador, y la
siguiente entrega continúa la numeración (un número borrado nunca se
reutiliza; si la TV lo devuelve es "entrega desconocida", se ignora, y la TV
recibe una nueva en su próxima consulta); una confirmación o un latido **atrasado, duplicado
o desordenado** (número menor o igual que el ya anotado) no toca nada; una
entrega que esa pantalla nunca recibió se rechaza; al **reconectar**, la TV
declara en su primer latido la entrega que tiene aplicada y el panel ve la
diferencia con la enviada (enviada 4, recibida 3) hasta que la aplique; cada
pantalla numera por su cuenta; las
versiones son un historial append-only **por empresa** (`lista_version`) y
una entrega solo puede unir una pantalla y una lista de la **misma empresa**,
diga lo que diga la aplicación. Una lista puede avanzar a la versión 2
mientras una pantalla sigue en la entrega que llevaba la 1, y el panel
enseña "enviada #7 (Promos v2) · reproduciendo #6 (Promos v1)".

Hasta que exista cada mecanismo, el panel **no muestra** el estado
correspondiente (no se infiere del latido). El tiempo entre estados se mide y
se enseña ("recibida 12:41, 6 s después de enviada"); no se promete.

## 6. Impacto en el modelo (B3 §3.2b, rev. 8)

Cinco tablas nuevas (`grupo_pantallas`, `grupo_pantalla_miembro`,
`lista_destino`, `lista_version`, `pantalla_entrega`), `lista.version`, el
contador `pantalla.entrega_ultima` y tres números de entrega en `pantalla`
(`entrega_env`, `entrega_rec`, `entrega_conf`, con FK a `pantalla_entrega` y
`ON DELETE SET NULL` por columna, PostgreSQL 15+). Todas con `empresa_id` y la
política RLS estándar (por empresa); las llaves foráneas compuestas garantizan
la empresa y la sucursal **sin depender de RLS**, que no interviene en la
comprobación de llaves (informe 25, problema 2).

**Aislamiento por sucursal (informe 24, problema 2).** La rev. 6 solo ataba
el grupo a su sucursal; miembros y destinos comprobaban `empresa_id` y nada
más, así que una TV de Juriquilla podía entrar en un grupo de Plaza y una
lista de Plaza asignarse a un grupo de Juriquilla. Desde la rev. 7 la sucursal
viaja en todas las llaves: `pantalla`, `lista` y `grupo_pantallas` exponen
`UNIQUE (id, sucursal_id)`, y `grupo_pantalla_miembro` y `lista_destino`
llevan `sucursal_id` con llaves foráneas compuestas `(x_id, sucursal_id)`
hacia las tres. Un cruce de sucursal es una violación de llave foránea, no
una comprobación que el panel o la API puedan olvidar.

**Mover una pantalla de sucursal** (precisión del informe 25, problema 3):
la base **no** limpia nada en cascada; **rechaza** el cambio de `sucursal_id`
mientras la pantalla siga en algún grupo o tenga algún destino de la sucursal
vieja. "Mover" es por tanto una transacción del servidor: borrar sus
membresías y destinos, después mover; el panel avisa antes qué grupos y qué
lista pierde, y la pantalla queda con la lista al aire de la sucursal nueva
hasta que se le asigne otra. El esquema impide hacerlo a medias; no lo hace
por uno. Sus entregas anteriores se conservan (son historia de lo que
reprodujo), pero la siguiente respuesta crea una entrega nueva.

Índices únicos que hacen imposible la ambigüedad: un destino directo por
pantalla, una lista por grupo. Permisos: crear/editar grupos y destinos
requiere alcance sobre la sucursal (operador) y, para "reemplazar" un destino
ajeno, el mismo permiso; borrar grupos, administrador. Reutilización entre
sucursales: **no** (lo impide el esquema; copiar una lista a otra sucursal es
otra función). Migración desde hoy: `tvs[id].lista` se convierte en un
destino directo por pantalla, con la sucursal de la pantalla; no hay grupos ni
entregas que migrar (la primera entrega la crea el primer `/playlist.json`
tras el corte).

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
