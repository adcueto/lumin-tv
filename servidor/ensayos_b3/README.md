# Ensayos de diseño B3 (no es código del producto)

Prototipos ejecutables de los tres protocolos que Codex objetó en la revisión 2
del diseño (`docs/coordinacion/13-diseno-B3-postgresql.md`). Sirven para
demostrar el diseño con PostgreSQL real y datos sintéticos **antes** de
implementar B3; no se importan desde el servidor ni tocan datos de producción.

| Archivo | Hallazgo | Qué demuestra |
|---|---|---|
| `ddl_minimo.sql` | B3-R2-03 | Roles `lumin_migracion` / `lumin_app` / `lumin_espejo`, `ENABLE` (no `FORCE`) RLS, matriz GRANT + política por tabla y operación |
| `test_ensayo_espejo.py` | B3-R2-01 | El protocolo viejo (`max(id)`) pierde la transacción tardía; el nuevo (marcas pendientes + instantánea `REPEATABLE READ` + marcar después de escribir) converge, y sobrevive a los tres cortes |
| `test_ensayo_rls.py` | B3-R2-03 | Cada operación del diseño con su rol real: mutación + marca + auditoría, ciclo del espejo, controles negativos entre empresas, `pg_dump`/`pg_restore`, por qué no `FORCE`, guardián de catálogo |
| `test_ensayo_sesiones.py` | B3-R2-02 | Con el servidor 6.10 real: reproducción del defecto (copia congelada resucita una sesión cerrada) y contrato corregido (regenerar `sesiones.json` = congelado ∩ vigentes en PostgreSQL) |

## Ejecutar

Necesita un PostgreSQL 16 **de ensayo** (local, vacío; nunca el de producción)
y `psycopg` 3 (`pip install psycopg[binary]`). La variable apunta a un rol que
pueda crear roles y bases; los ensayos crean y destruyen `lumin_ensayo`.

```bash
cd servidor
LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres \
  .venv/bin/python -m pytest ensayos_b3 -q
```

Sin la variable, los 21 ensayos se **omiten** (no pasan): no hay resultado
inventado. Resultado en el entorno de desarrollo (PostgreSQL 16.13, psycopg
3.2.3): 21 pasan en 4.3 s; sin variable, 21 omitidos.

## Lo que estos ensayos NO son

- No son la migración, ni el servidor 6.11, ni el hilo espejo definitivo.
- No usan el esquema completo de §3 del diseño: solo `empresa`, `sucursal`,
  `usuario`, `sesion`, `auditoria`, `espejo_marca`, `espejo_estado`.
- No miden rendimiento ni prueban concurrencia masiva; prueban el orden
  exacto de eventos que rompe un protocolo y el que lo resuelve.
