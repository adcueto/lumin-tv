"""B3-R2-03: contrato rol / tabla / operación / política, ejecutado.

Con los roles reales del DDL mínimo se comprueba que GRANT y política
permiten JUNTOS cada operación que el diseño necesita, y que niegan juntos lo
que no debe pasar: mutación de negocio + marca en una transacción como
lumin_app, escritura de auditoría, ciclo del espejo como lumin_espejo,
migración y respaldo/restauración como lumin_migracion, y los controles
negativos entre empresas. También se demuestra por qué NO se usa FORCE ROW
LEVEL SECURITY: con FORCE el propietario deja de estar exento y pg_dump como
lumin_migracion devolvería tablas vacías.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid

import psycopg
import pytest
from psycopg import errors

from comun import EMPRESA_A, EMPRESA_B, USUARIO_1, BASE, CLAVE_ENSAYO, contexto, dsn_admin, dsn_rol, preparar_base


@pytest.fixture
def base():
    preparar_base()
    # datos de las dos empresas, sembrados por el propietario (como haría migrar_json)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (%s, %s, 'plaza', 'Plaza A'), (%s, %s, 'plaza', 'Plaza B')",
                  (uuid.uuid4(), EMPRESA_A, uuid.uuid4(), EMPRESA_B))


def cuenta(cur, sql, *params):
    return cur.execute(sql, params).fetchone()[0]


# ------------------------------------------------------------ lumin_app

def test_app_mutacion_mas_marca_en_una_transaccion(base):
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        contexto(cur, empresa=EMPRESA_A, usuario=USUARIO_1)
        cur.execute("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (%s, %s, 'norte', 'Norte')",
                    (uuid.uuid4(), EMPRESA_A))
        cur.execute("INSERT INTO espejo_marca DEFAULT VALUES")           # outbox: GRANT INSERT + política INSERT
        cur.execute("INSERT INTO auditoria (empresa_id, usuario_id, accion) VALUES (%s, %s, 'sucursal.crear')",
                    (EMPRESA_A, USUARIO_1))                                # auditoría con empresa propia
        cur.execute("INSERT INTO auditoria (empresa_id, accion) VALUES (NULL, 'login.fallido')")  # sin empresa (login)
        c.commit()
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        assert cuenta(c.cursor(), "SELECT count(*) FROM espejo_marca WHERE procesada_en IS NULL") == 1
        assert cuenta(c.cursor(), "SELECT count(*) FROM auditoria") == 2


def test_app_no_puede_auditar_a_nombre_de_otra_empresa(base):
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        contexto(cur, empresa=EMPRESA_A)
        with pytest.raises(errors.InsufficientPrivilege):
            cur.execute("INSERT INTO auditoria (empresa_id, accion) VALUES (%s, 'x')", (EMPRESA_B,))


def test_app_no_lee_outbox_ni_auditoria(base):
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        contexto(cur, empresa=EMPRESA_A)
        with pytest.raises(errors.InsufficientPrivilege):
            cur.execute("SELECT count(*) FROM espejo_marca")
        c.rollback()
        cur = c.cursor()
        with pytest.raises(errors.InsufficientPrivilege):
            cur.execute("SELECT count(*) FROM auditoria")


def test_app_controles_negativos_entre_empresas(base):
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        # (1) sin contexto: cero filas, sin error
        assert cuenta(cur, "SELECT count(*) FROM sucursal") == 0
        assert cuenta(cur, "SELECT count(*) FROM empresa") == 0
        c.commit()
        # (2) con contexto de A: solo A
        cur = c.cursor()
        contexto(cur, empresa=EMPRESA_A)
        assert [r[0] for r in cur.execute("SELECT nombre FROM sucursal")] == ["Plaza A"]
        assert cuenta(cur, "SELECT count(*) FROM empresa") == 1
        # (3) INSERT de una fila de B con contexto de A: rechazado por WITH CHECK
        with pytest.raises(errors.InsufficientPrivilege):
            cur.execute("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (%s, %s, 'sur', 'Sur B')",
                        (uuid.uuid4(), EMPRESA_B))
        c.rollback()
        # (4) UPDATE / DELETE de B con contexto de A: 0 filas y fila intacta
        cur = c.cursor()
        contexto(cur, empresa=EMPRESA_A)
        cur.execute("UPDATE sucursal SET nombre = 'pisada' WHERE empresa_id = %s", (EMPRESA_B,))
        assert cur.rowcount == 0
        cur.execute("DELETE FROM sucursal WHERE empresa_id = %s", (EMPRESA_B,))
        assert cur.rowcount == 0
        c.commit()
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        assert cuenta(c.cursor(), "SELECT count(*) FROM sucursal WHERE empresa_id = %s AND nombre = 'Plaza B'", EMPRESA_B) == 1


def test_app_reutilizacion_de_conexion_no_filtra_contexto(base):
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor(); contexto(cur, empresa=EMPRESA_A)
        assert cuenta(cur, "SELECT count(*) FROM sucursal") == 1; c.commit()
        cur = c.cursor(); contexto(cur, empresa=EMPRESA_B)
        assert [r[0] for r in cur.execute("SELECT nombre FROM sucursal")] == ["Plaza B"]; c.commit()
        cur = c.cursor()                    # tercera transacción SIN contexto
        assert cuenta(cur, "SELECT count(*) FROM sucursal") == 0; c.commit()


def test_app_sesiones_y_login(base):
    """§3.5: arranque de la autenticación con una sesión migrada (empresa_id NULL)."""
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("INSERT INTO sesion (token_hash, usuario_id, empresa_id, expira_en) VALUES ('h1', %s, NULL, now() + interval '1 day')", (USUARIO_1,))
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        contexto(cur, token_hash="h1")                      # solo el hash de la cookie
        fila = cur.execute("SELECT usuario_id, empresa_id FROM sesion").fetchone()
        assert fila == (USUARIO_1, None) and cur.rowcount == 1
        contexto(cur, usuario=USUARIO_1)                     # ahora se conoce el usuario
        assert cuenta(cur, "SELECT count(*) FROM usuario") == 1
        c.commit()
        cur = c.cursor()
        contexto(cur, fase="login", nombre_usuario="admin")  # login por nombre, sin usuario_id
        assert cuenta(cur, "SELECT count(*) FROM usuario") == 1
        c.commit()
        cur = c.cursor()
        contexto(cur, nombre_usuario="admin")                # mismo nombre SIN fase: nada
        assert cuenta(cur, "SELECT count(*) FROM usuario") == 0


def test_app_no_puede_escalar(base):
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        with pytest.raises(errors.InsufficientPrivilege):
            c.execute("SET ROLE lumin_migracion")
        c.rollback()
        with pytest.raises(errors.InsufficientPrivilege):
            c.execute("SET ROLE lumin_espejo")
        c.rollback()
        fila = c.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user").fetchone()
        assert fila == (False, False)


# ------------------------------------------------------------ lumin_espejo

def test_espejo_lee_todo_y_solo_escribe_su_estado(base):
    with psycopg.connect(dsn_rol("lumin_app")) as a:
        cur = a.cursor(); contexto(cur, empresa=EMPRESA_A)
        cur.execute("INSERT INTO espejo_marca DEFAULT VALUES"); a.commit()
    with psycopg.connect(dsn_rol("lumin_espejo")) as e:
        cur = e.cursor()                                     # sin contexto alguno
        assert cuenta(cur, "SELECT count(*) FROM sucursal") == 2          # las dos empresas
        assert cuenta(cur, "SELECT count(*) FROM empresa") == 2
        ids = [r[0] for r in cur.execute("SELECT id FROM espejo_marca WHERE procesada_en IS NULL")]
        assert len(ids) == 1
        cur.execute("UPDATE espejo_marca SET procesada_en = now() WHERE id = ANY(%s)", (ids,))
        assert cur.rowcount == 1
        cur.execute("UPDATE espejo_estado SET generacion = generacion + 1, marcas_cubiertas = %s", (ids,))
        assert cur.rowcount == 1
        e.commit()
        for sql in ("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (gen_random_uuid(), %s, 'z', 'Z')",
                    "UPDATE sucursal SET nombre = 'x'",
                    "DELETE FROM sucursal",
                    "INSERT INTO espejo_marca DEFAULT VALUES",
                    "DELETE FROM espejo_marca",
                    "UPDATE espejo_marca SET creada_en = now()"):
            with pytest.raises(errors.InsufficientPrivilege):
                e.execute(sql, (EMPRESA_A,) if "%s" in sql else None)
            e.rollback()


# ------------------------------------------------------------ lumin_migracion

def test_migracion_ve_todo_sin_contexto_y_respalda(base, tmp_path):
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        assert cuenta(c.cursor(), "SELECT count(*) FROM sucursal") == 2
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        pytest.skip("pg_dump no disponible en este entorno")
    info = psycopg.conninfo.conninfo_to_dict(dsn_admin())
    env = dict(os.environ, PGPASSWORD=CLAVE_ENSAYO)
    volcado = tmp_path / "ensayo.dump"
    subprocess.run([pg_dump, "-h", info.get("host", "127.0.0.1"), "-p", str(info.get("port", 5432)),
                    "-U", "lumin_migracion", "-Fc", "-f", str(volcado), BASE], check=True, env=env)
    # restaurar en una base nueva y comprobar que las filas de las DOS empresas viajaron
    with psycopg.connect(dsn_admin(), autocommit=True) as adm:
        adm.execute("DROP DATABASE IF EXISTS lumin_ensayo_restaurada WITH (FORCE)")
        adm.execute("CREATE DATABASE lumin_ensayo_restaurada OWNER lumin_migracion")
    subprocess.run([shutil.which("pg_restore"), "-h", info.get("host", "127.0.0.1"), "-p", str(info.get("port", 5432)),
                    "-U", "lumin_migracion", "-d", "lumin_ensayo_restaurada", str(volcado)], check=True, env=env)
    info2 = dict(info, user="lumin_migracion", password=CLAVE_ENSAYO, dbname="lumin_ensayo_restaurada")
    with psycopg.connect(psycopg.conninfo.make_conninfo(**info2)) as r:
        assert cuenta(r.cursor(), "SELECT count(*) FROM sucursal") == 2
        assert cuenta(r.cursor(), "SELECT count(*) FROM pg_policies WHERE tablename = 'sucursal'") == 2  # políticas viajan


def test_por_que_no_force_rls(base):
    """Con FORCE, el propietario también queda sujeto a RLS y, sin política
    para él, ve cero filas: migración, verificación y pg_dump quedarían vacíos."""
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("ALTER TABLE sucursal FORCE ROW LEVEL SECURITY")
        try:
            assert cuenta(c.cursor(), "SELECT count(*) FROM sucursal") == 0
        finally:
            c.execute("ALTER TABLE sucursal NO FORCE ROW LEVEL SECURITY")
        assert cuenta(c.cursor(), "SELECT count(*) FROM sucursal") == 2


def test_ninguna_tabla_sin_rls_ni_politica_para_app(base):
    """Guardián de catálogo: toda tabla del esquema tiene RLS activa; toda
    tabla a la que lumin_app puede acceder tiene al menos una política suya."""
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        sin_rls = [r[0] for r in c.execute(
            "SELECT relname FROM pg_class WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace AND NOT relrowsecurity")]
        assert sin_rls == []
        con_grant = {r[0] for r in c.execute(
            "SELECT DISTINCT table_name FROM information_schema.role_table_grants WHERE grantee = 'lumin_app'")}
        con_politica = {r[0] for r in c.execute(
            "SELECT DISTINCT tablename FROM pg_policies WHERE 'lumin_app' = ANY(roles)")}
        assert con_grant - con_politica == set(), f"tablas con GRANT y sin política para lumin_app: {con_grant - con_politica}"
