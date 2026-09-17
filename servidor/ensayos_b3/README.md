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
| `test_ensayo_sesiones.py` (9) | B3-R2-02, B3-R3-02 | Con el servidor 6.10 real: los dos defectos reproducidos (copia congelada; último espejo tras una revocación posterior) y `revertir`: bloquea sin PostgreSQL, emergencia cierra todas, normal usa el estado final; drenaje que espera y cancela |
| `test_ensayo_cola.py` (5) | B3-R3-03 | Reproducción del defecto (nombre compartido → `hecho` sin archivo); artefacto por posesión: A vencido / B publicado / A descartado, caída tras escribir y antes del `UPDATE`, idempotencia, cancelación |

## Ejecutar

Necesita un PostgreSQL 16 **de ensayo** (local, vacío; nunca el de producción)
y `psycopg` 3 (`pip install psycopg[binary]`). La variable apunta a un rol que
pueda crear roles y bases; los ensayos crean y destruyen `lumin_ensayo`.

```bash
cd servidor
LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres \
  .venv/bin/python -m pytest ensayos_b3 -q
```

Sin la variable, los 39 ensayos se **omiten** (no pasan): no hay resultado
inventado. Resultado en el entorno de desarrollo (PostgreSQL 16.13, psycopg
3.2.3): 39 pasan en 9.2 s; sin variable, 39 omitidos. El rol de la variable
necesita poder crear roles y bases y conceder `pg_signal_backend` y
`pg_read_all_stats` (un superusuario de la instancia de ensayo).

## Lo que estos ensayos NO son

- No son la migración, ni el servidor 6.11, ni el hilo espejo definitivo.
- No usan el esquema completo de §3 del diseño: solo `empresa`, `sucursal`,
  `usuario`, `membresia`, `sesion`, `auditoria`, `trabajo`, `espejo_marca`,
  `espejo_estado`. La matriz de §3.5 dice tabla por tabla qué está ensayado y
  qué es contrato.
- No miden rendimiento ni prueban concurrencia masiva; prueban el orden
  exacto de eventos que rompe un protocolo y el que lo resuelve.
