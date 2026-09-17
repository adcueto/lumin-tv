"""Infraestructura de los ensayos de diseño B3.

Necesita un PostgreSQL 16 de ENSAYO (nunca producción) y la variable

    LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55432/postgres

con un rol capaz de crear roles y bases. Cada ensayo crea la base
`lumin_ensayo` desde cero (se borra si existe), corre `ddl_minimo.sql` como
`lumin_migracion` y trabaja con datos sintéticos. Sin la variable, los
ensayos se omiten con un aviso; no se inventa un resultado.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest

AQUI = Path(__file__).resolve().parent
DDL = AQUI / "ddl_minimo.sql"
BASE = "lumin_ensayo"
ROLES = ("lumin_migracion", "lumin_app", "lumin_espejo")
CLAVE_ENSAYO = "ensayo"  # solo para la base local de ensayo

EMPRESA_A = uuid.UUID("00000000-0000-0000-0000-00000000000a")
EMPRESA_B = uuid.UUID("00000000-0000-0000-0000-00000000000b")
USUARIO_1 = uuid.UUID("00000000-0000-0000-0000-000000000101")               # membresía en A (heredada)
USUARIO_AJENO = uuid.UUID("00000000-0000-0000-0000-000000000102")           # membresía solo en B
USUARIO_SIN_MEMBRESIA = uuid.UUID("00000000-0000-0000-0000-000000000103")   # sin membresía


def dsn_admin() -> str:
    dsn = os.environ.get("LUMIN_ENSAYO_PG")
    if not dsn:
        pytest.skip("LUMIN_ENSAYO_PG no definido: ensayo de diseño omitido (no ejecutado)")
    return dsn


def dsn_rol(rol: str) -> str:
    base = psycopg.conninfo.conninfo_to_dict(dsn_admin())
    base.update(user=rol, password=CLAVE_ENSAYO, dbname=BASE)
    return psycopg.conninfo.make_conninfo(**base)


def preparar_base() -> None:
    """Base limpia + roles + DDL. Idempotente."""
    with psycopg.connect(dsn_admin(), autocommit=True) as c:
        for rol in ROLES:
            existe = c.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (rol,)).fetchone()
            if not existe:
                extra = "NOINHERIT" if rol != "lumin_migracion" else ""
                from psycopg import sql
                c.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE " + extra)
                          .format(sql.Identifier(rol), sql.Literal(CLAVE_ENSAYO)))
        # revertir.py necesita cancelar transacciones de lumin_app en vuelo (drenaje)
        c.execute("GRANT pg_signal_backend, pg_read_all_stats TO lumin_migracion")
        c.execute(f"DROP DATABASE IF EXISTS {BASE} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {BASE} OWNER lumin_migracion")
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute(DDL.read_text(encoding="utf-8"))
        c.execute("INSERT INTO empresa (id, clave, estado, heredada) VALUES (%s, 'lumin', 'activa', true), (%s, 'otra', 'suspendida', false)",
                  (EMPRESA_A, EMPRESA_B))
        c.execute("INSERT INTO usuario (id, nombre_usuario) VALUES (%s, 'admin'), (%s, 'ajeno'), (%s, 'huerfano')",
                  (USUARIO_1, USUARIO_AJENO, USUARIO_SIN_MEMBRESIA))
        c.execute("INSERT INTO membresia (empresa_id, usuario_id, rol) VALUES (%s, %s, 'admin_empresa'), (%s, %s, 'operador')",
                  (EMPRESA_A, USUARIO_1, EMPRESA_B, USUARIO_AJENO))


def contexto(cur, empresa=None, usuario=None, token_hash=None, fase=None, nombre_usuario=None):
    """SET LOCAL del contexto, como hará el servidor al abrir cada transacción."""
    for nombre, valor in (("empresa_id", empresa), ("usuario_id", usuario), ("token_hash", token_hash),
                          ("fase", fase), ("nombre_usuario", nombre_usuario)):
        cur.execute("SELECT set_config(%s, %s, true)", (f"lumin.{nombre}", "" if valor is None else str(valor)))


def mutar_sucursal(conn, empresa, clave, nombre, *, confirmar=True):
    """Una mutación de negocio + su marca, en la misma transacción, como lumin_app."""
    cur = conn.cursor()
    contexto(cur, empresa=empresa)
    cur.execute("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (%s, %s, %s, %s)",
                (uuid.uuid4(), empresa, clave, nombre))
    cur.execute("INSERT INTO espejo_marca DEFAULT VALUES")
    if confirmar:
        conn.commit()
