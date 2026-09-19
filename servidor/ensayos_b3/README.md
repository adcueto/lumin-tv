# Ensayos de diseño B3 (no es código del producto)

Prototipos ejecutables de los tres protocolos que Codex objetó en la revisión 2
del diseño (`docs/coordinacion/13-diseno-B3-postgresql.md`). Sirven para
demostrar el diseño con PostgreSQL real y datos sintéticos **antes** de
implementar B3; no se importan desde el servidor ni tocan datos de producción.

| Archivo | Hallazgo | Qué demuestra |
|---|---|---|
| `ddl_minimo.sql` | B3-R2-03, B3-R3-01 | Roles `lumin_migracion` / `lumin_app` / `lumin_espejo`, `ENABLE` (no `FORCE`) RLS, GRANT + política por tabla y operación; `empresa.heredada`, `membresia`, `trabajo` |
| `test_ensayo_espejo.py` (6) | B3-R2-01 | El protocolo viejo (`max(id)`) pierde la transacción tardía; el nuevo (marcas pendientes + instantánea `REPEATABLE READ` + marcar después de escribir) converge, y sobrevive a los tres cortes |
| `test_ensayo_rls.py` (19) | B3-R2-03, B3-R3-01, B3-R3-04 | Cada operación con su rol real, controles negativos entre empresas, `pg_dump`/`pg_restore`, por qué no `FORCE`; orden de resolución de una sesión migrada (válida / sin membresía / otra empresa / revocada / con empresa / latido); guardián de catálogo con propietario y dos casos negativos |
| `test_ensayo_sesiones.py` (19) | B3-R2-02, B3-R3-02, B3-R4-01 (tres vueltas) | Con el servidor 6.10 real: los defectos reproducidos (copia congelada; último espejo tras una revocación posterior; cancelar no impide el commit tardío) y `revertir`: bloquea sin PostgreSQL, emergencia cierra todas, normal usa el estado final; drenaje que cierra la entrada, da gracia a lo que está a medias, termina **todas** las sesiones de `lumin_app` (también `idle`: reproducción del caso de Codex sobre la rev. 5), impide que una petición admitida antes de la barrera escriba después, no toca otros roles **ni otras bases de la instancia** (acotado por `datname`, informe 24), y bloquea si queda alguna |
| `test_ensayo_destinos.py` (16) | RF-26, informes 24 (problemas 2 y 3), 25 (RF26-QA-02/03, DOC-R7-01) y 26 (RF26-QA-04/05/06) | Reproducción con el DDL §3.2b rev. 6 (pantallas, grupos y listas de sucursales distintas se relacionan); el DDL rev. 7 con la sucursal en todas las llaves rechaza los tres cruces y acepta lo correcto; mover una pantalla de sucursal es **rechazado** hasta limpiar grupos y destinos (transacción correcta); el par `(lista_id, version)` distingue listas; reproducción de L1 → L2 → L1 con el par ("al día" falso) y de la confirmación de una lista de otra empresa; con la rev. 8 las **entregas numeradas** por pantalla (contraejemplo de Codex, atrasada/duplicada/desordenada = 0 filas, inexistente = FK, reconexión, numeración independiente) y el historial `lista_version` por empresa con RLS ejercida como `lumin_app` cierran ambos; mover es una transacción que revierte entera; reproducciones del informe 26 con el SQL de la rev. 8 (choque de dos peticiones simultáneas, una entrega por consulta, borrado de lista que falla) y su cierre en la rev. 9 (contador por pantalla con `FOR UPDATE`, servir idempotente, `SET NULL` por columna sin reutilizar números) |
| `test_ensayo_cola.py` (7) | B3-R3-03, B3-R4-02 | Reproducción de los dos defectos (nombre compartido; reintento de la misma posesión borraba lo publicado); artefacto por posesión con `publicado` / `ya_publicado` / `perdido`: A vencido / B publicado / A descartado, caída tras escribir y antes del `UPDATE`, reintento idempotente, cancelación |

## Ejecutar

Necesita un PostgreSQL 16 **de ensayo** (local, vacío; nunca el de producción)
y `psycopg` 3 (`pip install psycopg[binary]`). La variable apunta a un rol que
pueda crear roles y bases; los ensayos crean y destruyen `lumin_ensayo`.

```bash
cd servidor
LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres \
  .venv/bin/python -m pytest ensayos_b3 -q
```

Sin la variable, los 67 ensayos se **omiten** (no pasan): no hay resultado
inventado. Resultado en el entorno de desarrollo (PostgreSQL 16.13, psycopg
3.2.3): 67 pasan en 14 s; sin variable, 67 omitidos. El rol de la variable
necesita poder crear roles y bases y conceder `pg_signal_backend` y
`pg_read_all_stats` (un superusuario de la instancia de ensayo).

## Lo que estos ensayos NO son

- No son la migración, ni el servidor 6.11, ni el hilo espejo definitivo.
- No usan el esquema completo de §3 del diseño: solo `empresa`, `sucursal`,
  `usuario`, `membresia`, `sesion`, `auditoria`, `trabajo`, `espejo_marca`,
  `espejo_estado`, más `pantalla_e`/`lista_e` mínimas en el ensayo de destinos. La matriz de §3.5 dice tabla por tabla qué está ensayado y
  qué es contrato.
- No miden rendimiento ni prueban concurrencia masiva; prueban el orden
  exacto de eventos que rompe un protocolo y el que lo resuelve.
