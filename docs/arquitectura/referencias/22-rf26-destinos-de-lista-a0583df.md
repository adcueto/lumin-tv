# RF-26 — "Reproducir en…": destinos de una lista, grupos de pantallas y estados de entrega

Fecha: 2026-09-19 · Propuesta de Claude para decisión de Adrián y revisión de Codex ·
Estado: **diseño**, nada implementado. Responde a las cinco faltas del informe 23.

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
- Mover una pantalla de sucursal la saca de todos los grupos de la sucursal
  de origen (los grupos son por sucursal).

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

| Estado | Qué significa exactamente | Cómo se sabe | Disponible desde |
|---|---|---|---|
| **enviada** | El servidor guardó el destino y la próxima respuesta a esa pantalla llevará la lista en su versión N | `lista_destino` + `lista.version`; al servir `/playlist.json` se anota `pantalla.lista_version_enviada = N` | B6 con el servidor actual |
| **recibida** | La TV **declaró** en un latido posterior que tiene aplicada la versión N | La app manda `lv=N` en el latido (parámetro nuevo, mismo mecanismo que B5a); el servidor anota `lista_version_recibida`. Que la TV pida la playlist **no** cuenta: solo cuenta que **diga** qué versión aplicó | B5b (app build siguiente + servidor) |
| **reproduciendo** | La TV confirmó que está reproduciendo un elemento de la versión N | Confirmación de reproducción (propuesta 7, evento idempotente por elemento); `lista_version_reprod` | Propuesta 7 |

Hasta que exista cada mecanismo, el panel **no muestra** el estado
correspondiente (no se infiere del latido). El tiempo entre estados se mide y
se enseña ("recibida 12:41, 6 s después de enviada"); no se promete.

## 6. Impacto en el modelo (B3 §3.2b)

Tres tablas nuevas (`grupo_pantallas`, `grupo_pantalla_miembro`,
`lista_destino`), `lista.version` y tres columnas de versión en `pantalla`.
Todas con `empresa_id`, llaves compuestas y la política RLS estándar. Índices
únicos que hacen imposible la ambigüedad: un destino directo por pantalla,
una lista por grupo. Permisos: crear/editar grupos y destinos requiere
alcance sobre la sucursal (operador) y, para "reemplazar" un destino ajeno,
el mismo permiso; borrar grupos, administrador. Reutilización entre
sucursales: **no** (los grupos son por sucursal; copiar una lista a otra
sucursal es otra función). Migración desde hoy: `tvs[id].lista` se convierte
en un destino directo por pantalla; no hay grupos que migrar.

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
