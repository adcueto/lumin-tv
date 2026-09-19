"""RF-26 (informe 24): aislamiento por SUCURSAL de grupos, miembros y destinos,
y confirmación de entrega identificable.

Hallazgo 2: el DDL de §3.2b rev. 6 solo ataba grupo→sucursal; miembros y
destinos solo comprobaban empresa. Una TV de Juriquilla podía entrar en un
grupo de Plaza, y una lista de Plaza asignarse a un grupo de Juriquilla. Se
reproduce con ese DDL y se demuestra que el de rev. 7 (llaves compuestas
`(id, sucursal_id)` en pantalla, grupo y lista, propagadas a miembro y
destino) lo rechaza.

Hallazgo 3: dos listas pueden tener "versión 1"; confirmar solo el número no
identifica la lista. La confirmación es el par (lista_id, version) y la
columna de la pantalla lo guarda como par.

Informe 25 (sobre la rev. 7):
 1. El par distingue listas, no asignaciones sucesivas de la MISMA lista:
    con L1 -> L2 -> L1 una confirmación vieja de (L1, 1) parece "al día".
    Rev. 8: cada vez que el servidor sirve una lista a una pantalla crea una
    ENTREGA con número consecutivo por pantalla; la TV devuelve ese número y
    "al día" es igualdad de entregas, no de pares.
 2. `lista_version` no llevaba `empresa_id`: una pantalla podía confirmar una
    versión de una lista de otra empresa. Rev. 8: `empresa_id` en el historial
    y en todas las llaves que lo referencian.
 3. Precisión: mover una pantalla de sucursal NO limpia en cascada; la base
    rechaza el movimiento hasta que se borren miembros y destinos. Es lo que
    el ensayo demuestra y lo que el documento debía decir.

Informe 26 (sobre la rev. 8):
 RF26-QA-04 dos peticiones simultáneas de la misma TV calculaban el mismo
            consecutivo con `max(seq)+1`; una fallaba por clave duplicada.
            Rev. 9: contador `entrega_ultima` en la fila de la pantalla,
            tomada con `FOR UPDATE`: las peticiones de una TV se serializan.
 RF26-QA-05 cada consulta creaba otra entrega aunque no cambiara nada, y la
            recepción quedaba siempre una atrás (2/1, 3/2…). Rev. 9: entregar
            es idempotente: si la entrega vigente ya es (lista, version) se
            devuelve su número; solo un cambio crea una entrega nueva.
 RF26-QA-06 borrar una lista referenciada fallaba: `ON DELETE SET NULL` sobre
            la llave compuesta (id, entrega_x) intentaba anular también `id`.
            Rev. 9: `ON DELETE SET NULL (entrega_x)` (lista de columnas,
            PostgreSQL 15+); el contador no se reinicia, así que un número
            borrado nunca se reutiliza y una TV que lo devuelva recibe
            "entrega desconocida" y una entrega nueva en su próxima consulta.

Ensayo de esquema con datos sintéticos; no es implementación de B6/B7.
"""

from __future__ import annotations

import threading
import time
import uuid

import psycopg
import pytest
from psycopg import errors

from comun import EMPRESA_A, EMPRESA_B, contexto, dsn_rol, preparar_base

PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000a1")
JURI = uuid.UUID("00000000-0000-0000-0000-0000000000a2")
TV_PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000b1")
TV_JURI = uuid.UUID("00000000-0000-0000-0000-0000000000b2")
LISTA_PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000c1")
LISTA_JURI = uuid.UUID("00000000-0000-0000-0000-0000000000c2")
GRUPO_PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000d1")
GRUPO_JURI = uuid.UUID("00000000-0000-0000-0000-0000000000d2")
SUC_B = uuid.UUID("00000000-0000-0000-0000-0000000000a9")        # sucursal de la OTRA empresa
LISTA_B = uuid.UUID("00000000-0000-0000-0000-0000000000c9")      # lista de la OTRA empresa

# Tablas auxiliares mínimas (pantalla y lista no están en ddl_minimo.sql)
BASE_COMUN = """
CREATE TABLE pantalla_e (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, sucursal_id uuid NOT NULL,
  UNIQUE (id, empresa_id), UNIQUE (id, sucursal_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id)
);
CREATE TABLE lista_e (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, sucursal_id uuid NOT NULL, version int NOT NULL DEFAULT 1,
  UNIQUE (id, empresa_id), UNIQUE (id, sucursal_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id)
);
"""

# ---- §3.2b tal como estaba en la rev. 6 (solo empresa en miembro/destino)
DDL_REV6 = BASE_COMUN + """
CREATE TABLE grupo_pantallas (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, sucursal_id uuid NOT NULL, nombre text NOT NULL,
  UNIQUE (sucursal_id, nombre), UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE TABLE grupo_pantalla_miembro (
  grupo_id uuid NOT NULL, pantalla_id uuid NOT NULL, empresa_id uuid NOT NULL,
  PRIMARY KEY (grupo_id, pantalla_id),
  FOREIGN KEY (grupo_id, empresa_id) REFERENCES grupo_pantallas(id, empresa_id) ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, empresa_id) REFERENCES pantalla_e(id, empresa_id) ON DELETE CASCADE
);
CREATE TABLE lista_destino (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, lista_id uuid NOT NULL, pantalla_id uuid, grupo_id uuid,
  prioridad int NOT NULL DEFAULT 0,
  CHECK ((pantalla_id IS NULL) <> (grupo_id IS NULL)),
  FOREIGN KEY (lista_id, empresa_id) REFERENCES lista_e(id, empresa_id) ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, empresa_id) REFERENCES pantalla_e(id, empresa_id) ON DELETE CASCADE,
  FOREIGN KEY (grupo_id, empresa_id) REFERENCES grupo_pantallas(id, empresa_id) ON DELETE CASCADE
);
"""

# ---- §3.2b rev. 7: la sucursal viaja en todas las llaves
DDL_REV7 = BASE_COMUN + """
CREATE TABLE grupo_pantallas (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, sucursal_id uuid NOT NULL, nombre text NOT NULL,
  UNIQUE (sucursal_id, nombre), UNIQUE (id, empresa_id), UNIQUE (id, sucursal_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE TABLE grupo_pantalla_miembro (
  grupo_id uuid NOT NULL, pantalla_id uuid NOT NULL, sucursal_id uuid NOT NULL, empresa_id uuid NOT NULL,
  PRIMARY KEY (grupo_id, pantalla_id),
  FOREIGN KEY (grupo_id, sucursal_id)    REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla_e(id, sucursal_id)      ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
CREATE TABLE lista_destino (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, sucursal_id uuid NOT NULL,
  lista_id uuid NOT NULL, pantalla_id uuid, grupo_id uuid, prioridad int NOT NULL DEFAULT 0,
  CHECK ((pantalla_id IS NULL) <> (grupo_id IS NULL)),
  FOREIGN KEY (lista_id, sucursal_id)    REFERENCES lista_e(id, sucursal_id)         ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla_e(id, sucursal_id)      ON DELETE CASCADE,
  FOREIGN KEY (grupo_id, sucursal_id)    REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
CREATE UNIQUE INDEX un_destino_por_pantalla ON lista_destino (pantalla_id) WHERE pantalla_id IS NOT NULL;
CREATE UNIQUE INDEX una_lista_por_grupo     ON lista_destino (grupo_id)    WHERE grupo_id IS NOT NULL;
-- Confirmación identificable: el par (lista, versión). Las versiones son un
-- historial append-only, para que una lista pueda avanzar sin dejar colgadas
-- las confirmaciones que apuntan a versiones anteriores.
CREATE TABLE lista_version (
  lista_id uuid NOT NULL REFERENCES lista_e(id) ON DELETE CASCADE,
  version  int  NOT NULL,
  creada_en timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (lista_id, version)
);
ALTER TABLE pantalla_e
  ADD COLUMN lista_conf_id uuid, ADD COLUMN lista_conf_version int,
  ADD CONSTRAINT conf_par CHECK ((lista_conf_id IS NULL) = (lista_conf_version IS NULL)),
  ADD FOREIGN KEY (lista_conf_id, lista_conf_version) REFERENCES lista_version(lista_id, version) ON DELETE SET NULL;
"""

# ---- §3.2b rev. 8 (informe 25): historial por empresa y ENTREGAS numeradas
DDL_REV8 = BASE_COMUN + """
CREATE TABLE grupo_pantallas (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, sucursal_id uuid NOT NULL, nombre text NOT NULL,
  UNIQUE (sucursal_id, nombre), UNIQUE (id, empresa_id), UNIQUE (id, sucursal_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE TABLE grupo_pantalla_miembro (
  grupo_id uuid NOT NULL, pantalla_id uuid NOT NULL, sucursal_id uuid NOT NULL, empresa_id uuid NOT NULL,
  PRIMARY KEY (grupo_id, pantalla_id),
  FOREIGN KEY (grupo_id, sucursal_id)    REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla_e(id, sucursal_id)      ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
CREATE TABLE lista_destino (
  id uuid PRIMARY KEY, empresa_id uuid NOT NULL, sucursal_id uuid NOT NULL,
  lista_id uuid NOT NULL, pantalla_id uuid, grupo_id uuid, prioridad int NOT NULL DEFAULT 0,
  CHECK ((pantalla_id IS NULL) <> (grupo_id IS NULL)),
  FOREIGN KEY (lista_id, sucursal_id)    REFERENCES lista_e(id, sucursal_id)         ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla_e(id, sucursal_id)      ON DELETE CASCADE,
  FOREIGN KEY (grupo_id, sucursal_id)    REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
CREATE UNIQUE INDEX un_destino_por_pantalla ON lista_destino (pantalla_id) WHERE pantalla_id IS NOT NULL;
CREATE UNIQUE INDEX una_lista_por_grupo     ON lista_destino (grupo_id)    WHERE grupo_id IS NOT NULL;
-- Historial de versiones, POR EMPRESA (informe 25, problema 2)
CREATE TABLE lista_version (
  lista_id   uuid NOT NULL,
  version    int  NOT NULL,
  empresa_id uuid NOT NULL,
  creada_en  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (lista_id, version),
  UNIQUE (lista_id, version, empresa_id),
  FOREIGN KEY (lista_id, empresa_id) REFERENCES lista_e(id, empresa_id) ON DELETE CASCADE
);
-- ENTREGA: cada vez que el servidor sirve (lista, version) a una pantalla, una
-- fila con numero consecutivo por pantalla (informe 25, problema 1). La TV
-- devuelve el numero; "al dia" es igualdad de numeros, no de pares.
CREATE TABLE pantalla_entrega (
  pantalla_id uuid   NOT NULL,
  seq         bigint NOT NULL,
  empresa_id  uuid   NOT NULL,
  lista_id    uuid   NOT NULL,
  version     int    NOT NULL,
  enviada_en  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (pantalla_id, seq),
  FOREIGN KEY (pantalla_id, empresa_id)        REFERENCES pantalla_e(id, empresa_id)                  ON DELETE CASCADE,
  FOREIGN KEY (lista_id, version, empresa_id)  REFERENCES lista_version(lista_id, version, empresa_id) ON DELETE CASCADE
);
ALTER TABLE pantalla_e
  ADD COLUMN entrega_env  bigint,      -- ultima entrega servida
  ADD COLUMN entrega_rec  bigint,      -- ultima que la TV declaro aplicada (B5b)
  ADD COLUMN entrega_conf bigint,      -- ultima que la TV confirmo reproduciendo (propuesta 7)
  ADD FOREIGN KEY (id, entrega_env)  REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL,
  ADD FOREIGN KEY (id, entrega_rec)  REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL,
  ADD FOREIGN KEY (id, entrega_conf) REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL;
-- RLS del historial y de las entregas (informe 25, RF26-QA-03): misma politica por
-- empresa que el resto; historial y entregas son append-only para lumin_app.
ALTER TABLE pantalla_e       ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_e          ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_version    ENABLE ROW LEVEL SECURITY;
ALTER TABLE pantalla_entrega ENABLE ROW LEVEL SECURITY;
GRANT SELECT, UPDATE  ON pantalla_e       TO lumin_app;
GRANT SELECT, UPDATE  ON lista_e          TO lumin_app;
GRANT SELECT, INSERT  ON lista_version    TO lumin_app;
GRANT SELECT, INSERT  ON pantalla_entrega TO lumin_app;
CREATE POLICY pantalla_app ON pantalla_e FOR ALL TO lumin_app
  USING (empresa_id = lumin.gc('empresa_id')::uuid) WITH CHECK (empresa_id = lumin.gc('empresa_id')::uuid);
CREATE POLICY lista_app ON lista_e FOR ALL TO lumin_app
  USING (empresa_id = lumin.gc('empresa_id')::uuid) WITH CHECK (empresa_id = lumin.gc('empresa_id')::uuid);
CREATE POLICY lista_version_app ON lista_version FOR ALL TO lumin_app
  USING (empresa_id = lumin.gc('empresa_id')::uuid) WITH CHECK (empresa_id = lumin.gc('empresa_id')::uuid);
CREATE POLICY pantalla_entrega_app ON pantalla_entrega FOR ALL TO lumin_app
  USING (empresa_id = lumin.gc('empresa_id')::uuid) WITH CHECK (empresa_id = lumin.gc('empresa_id')::uuid);
"""

# ---- §3.2b rev. 9 (informe 26): contador por pantalla, SET NULL por columna
DDL_REV9 = DDL_REV8.replace(
    "  ADD COLUMN entrega_env  bigint,      -- ultima entrega servida",
    "  ADD COLUMN entrega_ultima bigint NOT NULL DEFAULT 0,   -- contador: nunca se reinicia ni reutiliza\n"
    "  ADD COLUMN entrega_env  bigint,      -- ultima entrega servida",
).replace(
    "REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL,\n  ADD FOREIGN KEY (id, entrega_rec)",
    "REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL (entrega_env),\n  ADD FOREIGN KEY (id, entrega_rec)",
).replace(
    "REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL,\n  ADD FOREIGN KEY (id, entrega_conf)",
    "REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL (entrega_rec),\n  ADD FOREIGN KEY (id, entrega_conf)",
).replace(
    "REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL;",
    "REFERENCES pantalla_entrega(pantalla_id, seq) ON DELETE SET NULL (entrega_conf);",
)
assert DDL_REV9.count("SET NULL (entrega_") == 3 and "entrega_ultima" in DDL_REV9

# SQL que hacia el servidor en la rev. 8 (se conserva para reproducir RF26-QA-04/05).
SQL_ENTREGAR_REV8 = """
WITH n AS (SELECT coalesce(max(seq), 0) + 1 AS seq FROM pantalla_entrega WHERE pantalla_id = %(p)s),
     e AS (INSERT INTO pantalla_entrega (pantalla_id, seq, empresa_id, lista_id, version)
           SELECT %(p)s, n.seq, %(emp)s, %(l)s, %(v)s FROM n RETURNING seq)
UPDATE pantalla_e SET entrega_env = e.seq FROM e WHERE pantalla_e.id = %(p)s RETURNING e.seq
"""
# Rev. 9: la transaccion del servidor al servir /playlist.json, tal cual.
# Dos sentencias, no un JOIN: en READ COMMITTED, si el FOR UPDATE espera a otra
# transaccion, la fila de la pantalla se relee al despertar pero el JOIN con la
# entrega se evaluo con la instantanea vieja (la entrega recien confirmada no
# se ve). El arnes lo detecto: con un solo JOIN, dos peticiones simultaneas de
# la MISMA lista creaban dos entregas. Bloquear primero; leer despues.
SQL_BLOQUEAR = "SELECT entrega_ultima, entrega_env FROM pantalla_e WHERE id = %(p)s FOR UPDATE"
SQL_VIGENTE = "SELECT lista_id, version FROM pantalla_entrega WHERE pantalla_id = %(p)s AND seq = %(seq)s"
SQL_SIGUIENTE = "UPDATE pantalla_e SET entrega_ultima = entrega_ultima + 1 WHERE id = %(p)s RETURNING entrega_ultima"
SQL_INSERTAR = "INSERT INTO pantalla_entrega (pantalla_id, seq, empresa_id, lista_id, version) VALUES (%(p)s, %(seq)s, %(emp)s, %(l)s, %(v)s)"
SQL_APUNTAR = "UPDATE pantalla_e SET entrega_env = %(seq)s WHERE id = %(p)s"


def entregar(c, tv, lista, version=1, empresa=EMPRESA_A, tras_bloquear=None):
    """Servir (lista, version) a una pantalla. Idempotente: si la entrega
    vigente ya es ese par, devuelve su numero sin crear nada (RF26-QA-05). El
    FOR UPDATE de la fila de la pantalla serializa peticiones simultaneas de la
    misma TV (RF26-QA-04). `tras_bloquear` es una costura del arnes para
    detener la transaccion con el bloqueo tomado."""
    with c.transaction():
        fila = c.execute(SQL_BLOQUEAR, {"p": tv}).fetchone()
        if fila is None:
            raise LookupError("pantalla no visible")
        if tras_bloquear:
            tras_bloquear()
        _ultima, env = fila
        if env is not None and c.execute(SQL_VIGENTE, {"p": tv, "seq": env}).fetchone() == (lista, version):
            return env
        seq = c.execute(SQL_SIGUIENTE, {"p": tv}).fetchone()[0]
        c.execute(SQL_INSERTAR, {"p": tv, "seq": seq, "emp": empresa, "l": lista, "v": version})
        c.execute(SQL_APUNTAR, {"p": tv, "seq": seq})
        return seq


# Confirmar es monotono: una confirmacion mas vieja que la registrada no toca nada (0 filas).
SQL_CONFIRMAR = """
UPDATE pantalla_e SET entrega_conf = %(seq)s
 WHERE id = %(p)s AND (entrega_conf IS NULL OR entrega_conf < %(seq)s)
"""
SQL_AL_DIA = "SELECT entrega_conf IS NOT NULL AND entrega_conf = entrega_env FROM pantalla_e WHERE id = %s"


def montar(ddl: str):
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute(ddl)
        c.execute("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (%s, %s, 'plaza', 'Plaza'), (%s, %s, 'juri', 'Juriquilla')",
                  (PLAZA, EMPRESA_A, JURI, EMPRESA_A))
        c.execute("INSERT INTO pantalla_e (id, empresa_id, sucursal_id) VALUES (%s, %s, %s), (%s, %s, %s)",
                  (TV_PLAZA, EMPRESA_A, PLAZA, TV_JURI, EMPRESA_A, JURI))
        c.execute("INSERT INTO lista_e (id, empresa_id, sucursal_id) VALUES (%s, %s, %s), (%s, %s, %s)",
                  (LISTA_PLAZA, EMPRESA_A, PLAZA, LISTA_JURI, EMPRESA_A, JURI))
        # la OTRA empresa, con una lista propia en version 1 (informe 25, problema 2)
        c.execute("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (%s, %s, 'b', 'B')", (SUC_B, EMPRESA_B))
        c.execute("INSERT INTO lista_e (id, empresa_id, sucursal_id) VALUES (%s, %s, %s)", (LISTA_B, EMPRESA_B, SUC_B))
        if "pantalla_entrega" in ddl:
            c.execute("INSERT INTO lista_version (lista_id, version, empresa_id) VALUES (%s, 1, %s), (%s, 1, %s), (%s, 1, %s)",
                      (LISTA_PLAZA, EMPRESA_A, LISTA_JURI, EMPRESA_A, LISTA_B, EMPRESA_B))
        elif "lista_version" in ddl:
            c.execute("INSERT INTO lista_version (lista_id, version) VALUES (%s, 1), (%s, 1), (%s, 1)", (LISTA_PLAZA, LISTA_JURI, LISTA_B))
        c.execute("INSERT INTO grupo_pantallas (id, empresa_id, sucursal_id, nombre) VALUES (%s, %s, %s, 'Salas'), (%s, %s, %s, 'Salas')",
                  (GRUPO_PLAZA, EMPRESA_A, PLAZA, GRUPO_JURI, EMPRESA_A, JURI))


@pytest.fixture
def base():
    preparar_base()


def test_reproduccion_rev6_permite_cruzar_sucursales(base):
    """Con el DDL de la rev. 6, misma empresa basta: el cruce entra."""
    montar(DDL_REV6)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("INSERT INTO grupo_pantalla_miembro (grupo_id, pantalla_id, empresa_id) VALUES (%s, %s, %s)",
                  (GRUPO_PLAZA, TV_JURI, EMPRESA_A))                       # TV de Juriquilla en grupo de Plaza
        c.execute("INSERT INTO lista_destino (id, empresa_id, lista_id, grupo_id) VALUES (%s, %s, %s, %s)",
                  (uuid.uuid4(), EMPRESA_A, LISTA_PLAZA, GRUPO_JURI))        # lista de Plaza a grupo de Juriquilla
        c.execute("INSERT INTO lista_destino (id, empresa_id, lista_id, pantalla_id) VALUES (%s, %s, %s, %s)",
                  (uuid.uuid4(), EMPRESA_A, LISTA_JURI, TV_PLAZA))           # lista de Juriquilla a TV de Plaza
        assert c.execute("SELECT count(*) FROM lista_destino").fetchone()[0] == 2, "el defecto del informe 24"


def test_rev7_rechaza_todos_los_cruces_y_acepta_lo_correcto(base):
    montar(DDL_REV7)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        cruces = [
            ("INSERT INTO grupo_pantalla_miembro (grupo_id, pantalla_id, sucursal_id, empresa_id) VALUES (%s, %s, %s, %s)",
             (GRUPO_PLAZA, TV_JURI, PLAZA, EMPRESA_A)),                      # TV ajena en grupo
            ("INSERT INTO grupo_pantalla_miembro (grupo_id, pantalla_id, sucursal_id, empresa_id) VALUES (%s, %s, %s, %s)",
             (GRUPO_PLAZA, TV_JURI, JURI, EMPRESA_A)),                       # mintiendo la sucursal
            ("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, grupo_id) VALUES (%s, %s, %s, %s, %s)",
             (uuid.uuid4(), EMPRESA_A, JURI, LISTA_PLAZA, GRUPO_JURI)),      # lista ajena a grupo
            ("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, pantalla_id) VALUES (%s, %s, %s, %s, %s)",
             (uuid.uuid4(), EMPRESA_A, PLAZA, LISTA_JURI, TV_PLAZA)),        # lista ajena a TV
        ]
        for sql, params in cruces:
            with pytest.raises(errors.ForeignKeyViolation):
                c.execute(sql, params)
        # lo correcto entra
        c.execute("INSERT INTO grupo_pantalla_miembro (grupo_id, pantalla_id, sucursal_id, empresa_id) VALUES (%s, %s, %s, %s)",
                  (GRUPO_PLAZA, TV_PLAZA, PLAZA, EMPRESA_A))
        c.execute("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, grupo_id) VALUES (%s, %s, %s, %s, %s)",
                  (uuid.uuid4(), EMPRESA_A, PLAZA, LISTA_PLAZA, GRUPO_PLAZA))
        # un solo destino directo por pantalla, una lista por grupo
        c.execute("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, pantalla_id) VALUES (%s, %s, %s, %s, %s)",
                  (uuid.uuid4(), EMPRESA_A, PLAZA, LISTA_PLAZA, TV_PLAZA))
        with pytest.raises(errors.UniqueViolation):
            c.execute("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, pantalla_id) VALUES (%s, %s, %s, %s, %s)",
                      (uuid.uuid4(), EMPRESA_A, PLAZA, LISTA_PLAZA, TV_PLAZA))
        with pytest.raises(errors.UniqueViolation):
            c.execute("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, grupo_id) VALUES (%s, %s, %s, %s, %s)",
                      (uuid.uuid4(), EMPRESA_A, PLAZA, LISTA_PLAZA, GRUPO_PLAZA))


def test_mover_pantalla_de_sucursal_exige_limpiar_grupos_y_destinos(base):
    """Precision del informe 25 (problema 3): cambiar la sucursal de una TV
    NO limpia nada en cascada. Las FKs compuestas hacen que PostgreSQL RECHACE
    el UPDATE mientras queden miembros o destinos de la sucursal vieja; el
    servidor debe borrarlos explicitamente en la misma transaccion (y el panel
    avisarlo). El esquema impide hacerlo a medias, no lo hace por uno."""
    montar(DDL_REV8)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("INSERT INTO grupo_pantalla_miembro (grupo_id, pantalla_id, sucursal_id, empresa_id) VALUES (%s, %s, %s, %s)",
                  (GRUPO_PLAZA, TV_PLAZA, PLAZA, EMPRESA_A))
        c.execute("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, pantalla_id) VALUES (%s, %s, %s, %s, %s)",
                  (uuid.uuid4(), EMPRESA_A, PLAZA, LISTA_PLAZA, TV_PLAZA))
        with pytest.raises(errors.ForeignKeyViolation):                       # miembro colgando: rechazado
            c.execute("UPDATE pantalla_e SET sucursal_id = %s WHERE id = %s", (JURI, TV_PLAZA))
        c.execute("DELETE FROM grupo_pantalla_miembro WHERE pantalla_id = %s", (TV_PLAZA,))
        with pytest.raises(errors.ForeignKeyViolation):                       # destino colgando: rechazado
            c.execute("UPDATE pantalla_e SET sucursal_id = %s WHERE id = %s", (JURI, TV_PLAZA))
        # el movimiento correcto es UNA transaccion: limpiar y mover
        with c.transaction():
            c.execute("DELETE FROM grupo_pantalla_miembro WHERE pantalla_id = %s", (TV_PLAZA,))
            c.execute("DELETE FROM lista_destino WHERE pantalla_id = %s", (TV_PLAZA,))
            c.execute("UPDATE pantalla_e SET sucursal_id = %s WHERE id = %s", (JURI, TV_PLAZA))
        assert c.execute("SELECT sucursal_id FROM pantalla_e WHERE id = %s", (TV_PLAZA,)).fetchone()[0] == JURI
        assert c.execute("SELECT count(*) FROM grupo_pantalla_miembro WHERE pantalla_id = %s", (TV_PLAZA,)).fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM lista_destino WHERE pantalla_id = %s", (TV_PLAZA,)).fetchone()[0] == 0


def test_confirmacion_de_entrega_es_el_par_lista_version(base):
    """Informe 24, hallazgo 3: dos listas con 'version 1' se distinguen porque
    la confirmacion guarda (lista_id, version) y el par debe existir en el
    historial de versiones."""
    montar(DDL_REV7)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        assert c.execute("SELECT count(*) FROM lista_version WHERE version = 1").fetchone()[0] == 3   # ambiguo por numero (dos de A, una de B)
        c.execute("UPDATE pantalla_e SET lista_conf_id = %s, lista_conf_version = 1 WHERE id = %s", (LISTA_PLAZA, TV_PLAZA))
        assert c.execute("SELECT lista_conf_id, lista_conf_version FROM pantalla_e WHERE id = %s", (TV_PLAZA,)).fetchone() == (LISTA_PLAZA, 1)
        with pytest.raises(errors.ForeignKeyViolation):        # version que esa lista nunca tuvo
            c.execute("UPDATE pantalla_e SET lista_conf_id = %s, lista_conf_version = 7 WHERE id = %s", (LISTA_PLAZA, TV_PLAZA))
        with pytest.raises(errors.CheckViolation):             # solo el numero, sin lista
            c.execute("UPDATE pantalla_e SET lista_conf_id = NULL, lista_conf_version = 1 WHERE id = %s", (TV_PLAZA,))
        # la lista avanza a la version 2: la confirmacion vieja sigue valida e identificable
        c.execute("INSERT INTO lista_version (lista_id, version) VALUES (%s, 2)", (LISTA_PLAZA,))
        c.execute("UPDATE lista_e SET version = 2 WHERE id = %s", (LISTA_PLAZA,))
        al_dia = c.execute(
            "SELECT p.lista_conf_version = l.version FROM pantalla_e p JOIN lista_e l ON l.id = p.lista_conf_id WHERE p.id = %s",
            (TV_PLAZA,)).fetchone()[0]
        assert al_dia is False                                  # "enviada v2, recibida v1": se ve la diferencia
        # y una confirmacion de la OTRA lista con el mismo numero no se confunde
        c.execute("UPDATE pantalla_e SET lista_conf_id = %s, lista_conf_version = 1 WHERE id = %s", (LISTA_JURI, TV_JURI))
        pares = c.execute("SELECT lista_conf_id, lista_conf_version FROM pantalla_e ORDER BY id").fetchall()
        assert pares == [(LISTA_PLAZA, 1), (LISTA_JURI, 1)]


def test_reproduccion_rev7_par_no_distingue_asignaciones_sucesivas(base):
    """Informe 25, problema 1, con el esquema de la rev. 7: L1 -> L2 -> L1.
    La TV confirmo (L1, 1) en la primera asignacion y nunca aplico L2. Al
    volver a L1, el par confirmado coincide con el enviado y el panel diria
    'al dia' sin que la TV haya confirmado nada de la tercera asignacion."""
    montar(DDL_REV7)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("ALTER TABLE pantalla_e ADD COLUMN lista_env_id uuid, ADD COLUMN lista_env_version int")
        def enviar(lista):
            c.execute("UPDATE pantalla_e SET lista_env_id = %s, lista_env_version = 1 WHERE id = %s", (lista, TV_PLAZA))
        def al_dia():
            return c.execute("SELECT (lista_conf_id, lista_conf_version) = (lista_env_id, lista_env_version) FROM pantalla_e WHERE id = %s",
                             (TV_PLAZA,)).fetchone()[0]
        enviar(LISTA_PLAZA)                                                        # L1
        c.execute("UPDATE pantalla_e SET lista_conf_id = %s, lista_conf_version = 1 WHERE id = %s", (LISTA_PLAZA, TV_PLAZA))
        assert al_dia() is True
        enviar(LISTA_JURI)                                                         # L2 (la TV no la aplica)
        assert al_dia() is False
        enviar(LISTA_PLAZA)                                                        # L1 otra vez
        assert al_dia() is True, "el defecto: 'al dia' con una confirmacion de la PRIMERA asignacion"


def test_rev8_entregas_numeradas_distinguen_asignaciones_sucesivas(base):
    """Contraejemplo de RF26-QA-02 tal cual: la TV confirma L1/v1; recibe y
    reproduce L2/v1; el servidor vuelve a asignar L1/v1; antes de que la TV la
    aplique llega una confirmacion ATRASADA de la primera L1/v1. Con entregas
    numeradas no aparece 'al dia'. Ademas: duplicados, desordenados,
    inexistentes, reconexion y numeracion independiente por pantalla."""
    montar(DDL_REV9)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        def entregar_(lista, tv=TV_PLAZA):
            return entregar(c, tv, lista)
        def confirmar(seq, tv=TV_PLAZA):
            return c.execute(SQL_CONFIRMAR, {"p": tv, "seq": seq}).rowcount
        def declarar(seq, tv=TV_PLAZA):                                            # latido: en=<seq> (B5b)
            return c.execute("UPDATE pantalla_e SET entrega_rec = %(seq)s WHERE id = %(p)s AND (entrega_rec IS NULL OR entrega_rec < %(seq)s)",
                             {"p": tv, "seq": seq}).rowcount
        def al_dia(tv=TV_PLAZA):
            return c.execute(SQL_AL_DIA, (tv,)).fetchone()[0]

        assert entregar_(LISTA_PLAZA) == 1                                          # L1/v1
        assert confirmar(1) == 1 and al_dia() is True
        assert entregar_(LISTA_JURI) == 2                                           # L2/v1
        assert al_dia() is False
        assert confirmar(2) == 1 and al_dia() is True                              # la TV reproduce L2
        assert entregar_(LISTA_PLAZA) == 3                                          # L1/v1 otra vez: OTRA entrega
        assert al_dia() is False
        assert confirmar(1) == 0, "confirmacion atrasada de la primera L1/v1: ignorada"
        assert al_dia() is False, "sigue reproduciendo L2; no aparece al dia"
        assert confirmar(2) == 0                                                   # duplicado: idempotente
        with pytest.raises(errors.ForeignKeyViolation):                            # entrega que nunca recibio
            confirmar(9)
        assert confirmar(3) == 1 and al_dia() is True                              # ahora si
        assert confirmar(3) == 0 and confirmar(2) == 0 and al_dia() is True        # duplicado y desordenado: nada
        # reconexion: la TV reinicia y en su primer latido dice que entrega tiene aplicada
        assert entregar_(LISTA_JURI) == 4                                           # mientras estaba apagada
        assert declarar(3) == 1                                                    # vuelve con la 3 aplicada
        env, rec, conf = c.execute("SELECT entrega_env, entrega_rec, entrega_conf FROM pantalla_e WHERE id = %s", (TV_PLAZA,)).fetchone()
        assert (env, rec, conf) == (4, 3, 3)                                       # el panel ve: enviada 4, recibida 3
        assert declarar(4) == 1 and confirmar(4) == 1 and al_dia() is True
        assert declarar(3) == 0                                                    # un latido viejo que llega tarde no retrocede
        # el par sigue disponible para el panel, via la entrega
        assert c.execute("SELECT e.lista_id, e.version FROM pantalla_entrega e JOIN pantalla_e p ON p.entrega_conf = e.seq AND p.id = e.pantalla_id WHERE p.id = %s",
                         (TV_PLAZA,)).fetchone() == (LISTA_JURI, 1)
        # la otra pantalla numera por su cuenta
        assert entregar_(LISTA_JURI, TV_JURI) == 1
        assert al_dia() is True and al_dia(TV_JURI) is False


def test_reproduccion_rev7_confirma_version_de_otra_empresa(base):
    """Informe 25, problema 2: sin empresa_id en lista_version, la FK del par
    acepta la lista de la otra empresa (RLS no interviene en la comprobacion
    de llaves foraneas)."""
    montar(DDL_REV7)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("UPDATE pantalla_e SET lista_conf_id = %s, lista_conf_version = 1 WHERE id = %s", (LISTA_B, TV_PLAZA))
        assert c.execute("SELECT lista_conf_id FROM pantalla_e WHERE id = %s", (TV_PLAZA,)).fetchone()[0] == LISTA_B, "el defecto"


def test_rev8_historial_y_entregas_por_empresa(base):
    montar(DDL_REV9)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        # una version no puede declararse con la empresa equivocada
        with pytest.raises(errors.ForeignKeyViolation):
            c.execute("INSERT INTO lista_version (lista_id, version, empresa_id) VALUES (%s, 2, %s)", (LISTA_B, EMPRESA_A))
        # una entrega a una pantalla de A con una lista de B: rechazada, diga lo que diga empresa_id
        for emp in (EMPRESA_A, EMPRESA_B):
            with pytest.raises(errors.ForeignKeyViolation):
                entregar(c, TV_PLAZA, LISTA_B, empresa=emp)
        assert c.execute("SELECT count(*) FROM pantalla_entrega").fetchone()[0] == 0
        assert c.execute("SELECT entrega_ultima FROM pantalla_e WHERE id = %s", (TV_PLAZA,)).fetchone()[0] == 0   # el fallo revirtio el contador
        # la de la propia empresa entra
        assert entregar(c, TV_PLAZA, LISTA_PLAZA) == 1


def test_rev8_historial_y_entregas_como_lumin_app(base):
    """RF26-QA-03, controles con el rol real: sin contexto nada se ve ni se
    escribe; con empresa A no se ve el historial de B ni se puede escribir en
    el (ni mintiendo el empresa_id: entonces falla la FK); una entrega cruzada
    no entra por ningun camino; el historial antiguo propio sigue legible y las
    entregas propias funcionan."""
    montar(DDL_REV9)
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        # sin contexto
        contexto(cur)
        assert cur.execute("SELECT count(*) FROM lista_version").fetchone()[0] == 0
        assert cur.execute("SELECT count(*) FROM pantalla_entrega").fetchone()[0] == 0
        with pytest.raises(errors.InsufficientPrivilege):                          # WITH CHECK de la politica
            cur.execute("INSERT INTO lista_version (lista_id, version, empresa_id) VALUES (%s, 2, %s)", (LISTA_PLAZA, EMPRESA_A))
        c.rollback()
        # empresa A
        contexto(cur, empresa=EMPRESA_A)
        assert cur.execute("SELECT count(*) FROM lista_version").fetchone()[0] == 2            # las dos de A, no la de B
        assert cur.execute("SELECT count(*) FROM lista_version WHERE lista_id = %s", (LISTA_B,)).fetchone()[0] == 0
        with pytest.raises(errors.InsufficientPrivilege):                          # historial de B con su empresa: politica
            cur.execute("INSERT INTO lista_version (lista_id, version, empresa_id) VALUES (%s, 2, %s)", (LISTA_B, EMPRESA_B))
        c.rollback(); contexto(cur, empresa=EMPRESA_A)
        with pytest.raises(errors.ForeignKeyViolation):                            # historial de B mintiendo la empresa: FK
            cur.execute("INSERT INTO lista_version (lista_id, version, empresa_id) VALUES (%s, 2, %s)", (LISTA_B, EMPRESA_A))
        c.rollback(); contexto(cur, empresa=EMPRESA_A)
        # entrega cruzada: lista de B a pantalla de A, por los dos caminos
        with pytest.raises(errors.ForeignKeyViolation):
            entregar(c, TV_PLAZA, LISTA_B, empresa=EMPRESA_A)
        c.rollback(); contexto(cur, empresa=EMPRESA_A)
        with pytest.raises(errors.InsufficientPrivilege):
            entregar(c, TV_PLAZA, LISTA_B, empresa=EMPRESA_B)
        c.rollback(); contexto(cur, empresa=EMPRESA_A)
        # confirmacion cruzada: una pantalla de B no existe para A (0 filas), aunque exista la entrega
        c.commit()
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as adm:
        adm.execute("INSERT INTO pantalla_e (id, empresa_id, sucursal_id) VALUES (%s, %s, %s)", (TV_B := uuid.uuid4(), EMPRESA_B, SUC_B))
        entregar(adm, TV_B, LISTA_B, empresa=EMPRESA_B)
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        contexto(cur, empresa=EMPRESA_A)
        assert cur.execute(SQL_CONFIRMAR, {"p": TV_B, "seq": 1}).rowcount == 0
        with pytest.raises(LookupError):                                           # ni siquiera puede servirle
            entregar(c, TV_B, LISTA_B, empresa=EMPRESA_B)
        contexto(cur, empresa=EMPRESA_A)
        # positivo: la lista propia avanza; el historial antiguo sigue legible y referenciado
        assert entregar(c, TV_PLAZA, LISTA_PLAZA) == 1
        assert cur.execute(SQL_CONFIRMAR, {"p": TV_PLAZA, "seq": 1}).rowcount == 1
        cur.execute("INSERT INTO lista_version (lista_id, version, empresa_id) VALUES (%s, 2, %s)", (LISTA_PLAZA, EMPRESA_A))
        cur.execute("UPDATE lista_e SET version = 2 WHERE id = %s", (LISTA_PLAZA,))
        assert entregar(c, TV_PLAZA, LISTA_PLAZA, version=2) == 2
        assert cur.execute("SELECT version FROM lista_version WHERE lista_id = %s ORDER BY version", (LISTA_PLAZA,)).fetchall() == [(1,), (2,)]
        assert cur.execute("SELECT e.version FROM pantalla_entrega e JOIN pantalla_e p ON p.entrega_conf = e.seq AND p.id = e.pantalla_id WHERE p.id = %s",
                           (TV_PLAZA,)).fetchone() == (1,)                          # reproduciendo v1, enviada v2
        c.commit()


def test_mover_pantalla_es_una_transaccion_que_revierte_entera(base):
    """DOC-R7-01: 'mover' = borrar membresias y destinos + UPDATE, en una sola
    transaccion. Si el movimiento falla a medias (aqui: sucursal de otra
    empresa), NADA se borra."""
    montar(DDL_REV9)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("INSERT INTO grupo_pantalla_miembro (grupo_id, pantalla_id, sucursal_id, empresa_id) VALUES (%s, %s, %s, %s)",
                  (GRUPO_PLAZA, TV_PLAZA, PLAZA, EMPRESA_A))
        c.execute("INSERT INTO lista_destino (id, empresa_id, sucursal_id, lista_id, pantalla_id) VALUES (%s, %s, %s, %s, %s)",
                  (uuid.uuid4(), EMPRESA_A, PLAZA, LISTA_PLAZA, TV_PLAZA))
        with pytest.raises(errors.ForeignKeyViolation):
            with c.transaction():
                c.execute("DELETE FROM grupo_pantalla_miembro WHERE pantalla_id = %s", (TV_PLAZA,))
                c.execute("DELETE FROM lista_destino WHERE pantalla_id = %s", (TV_PLAZA,))
                c.execute("UPDATE pantalla_e SET sucursal_id = %s WHERE id = %s", (SUC_B, TV_PLAZA))   # falla: otra empresa
        cuenta = c.execute("SELECT (SELECT count(*) FROM grupo_pantalla_miembro WHERE pantalla_id = %s), (SELECT count(*) FROM lista_destino WHERE pantalla_id = %s), (SELECT sucursal_id FROM pantalla_e WHERE id = %s)",
                           (TV_PLAZA, TV_PLAZA, TV_PLAZA)).fetchone()
        assert cuenta == (1, 1, PLAZA), "rollback entero: relaciones y sucursal intactas"


def _en_hilo(fn):
    caja = {}
    def cuerpo():
        try:
            caja["r"] = fn()
        except Exception as e:                       # noqa: BLE001 - el ensayo inspecciona la excepcion
            caja["e"] = e
    h = threading.Thread(target=cuerpo); h.start()
    caja["h"] = h
    return caja


def test_reproduccion_rev8_dos_peticiones_simultaneas_chocan(base):
    """RF26-QA-04 con el SQL de la rev. 8: dos transacciones leen max(seq)=0,
    ambas calculan 1; la segunda espera a la primera y falla por clave duplicada."""
    montar(DDL_REV8)
    a = psycopg.connect(dsn_rol("lumin_migracion"))                # sin autocommit: la transaccion queda abierta
    b = psycopg.connect(dsn_rol("lumin_migracion"))
    try:
        assert a.execute(SQL_ENTREGAR_REV8, {"p": TV_PLAZA, "emp": EMPRESA_A, "l": LISTA_PLAZA, "v": 1}).fetchone()[0] == 1
        caja = _en_hilo(lambda: b.execute(SQL_ENTREGAR_REV8, {"p": TV_PLAZA, "emp": EMPRESA_A, "l": LISTA_JURI, "v": 1}).fetchone()[0])
        time.sleep(0.3)
        assert caja["h"].is_alive(), "B espera a A sobre la clave (1)"
        a.commit()
        caja["h"].join(5)
        assert isinstance(caja.get("e"), errors.UniqueViolation), "el defecto del informe 26"
    finally:
        b.rollback(); a.close(); b.close()


def test_rev9_peticiones_simultaneas_se_serializan_y_no_duplican(base):
    """RF26-QA-04: el FOR UPDATE de la fila de la pantalla serializa. Con
    listas distintas: 1 y 2, sin choque. Con la MISMA lista: 1 y 1, una sola
    fila (idempotencia bajo carrera, RF26-QA-05)."""
    montar(DDL_REV9)
    a = psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True)
    b = psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True)
    try:
        suelta = threading.Event()
        ca = _en_hilo(lambda: entregar(a, TV_PLAZA, LISTA_PLAZA, tras_bloquear=lambda: suelta.wait(5)))
        time.sleep(0.2)                                                            # A tiene el bloqueo
        cb = _en_hilo(lambda: entregar(b, TV_PLAZA, LISTA_JURI))
        time.sleep(0.3)
        assert cb["h"].is_alive(), "B espera el bloqueo de la pantalla"
        suelta.set(); ca["h"].join(5); cb["h"].join(5)
        assert (ca.get("r"), cb.get("r")) == (1, 2), (ca, cb)
        # misma lista en carrera: la segunda ve la entrega vigente y no crea otra
        suelta = threading.Event()
        ca = _en_hilo(lambda: entregar(a, TV_JURI, LISTA_JURI, tras_bloquear=lambda: suelta.wait(5)))
        time.sleep(0.2)
        cb = _en_hilo(lambda: entregar(b, TV_JURI, LISTA_JURI))
        time.sleep(0.2)
        suelta.set(); ca["h"].join(5); cb["h"].join(5)
        assert (ca.get("r"), cb.get("r")) == (1, 1), (ca, cb)
        assert a.execute("SELECT count(*) FROM pantalla_entrega WHERE pantalla_id = %s", (TV_JURI,)).fetchone()[0] == 1
    finally:
        a.close(); b.close()


def test_reproduccion_rev8_cada_consulta_crea_otra_entrega(base):
    """RF26-QA-05 con el SQL de la rev. 8: la TV consulta cada minuto sin que
    cambie nada; la recepcion queda siempre una atras (2/1, 3/2, 4/3)."""
    montar(DDL_REV8)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        atras = []
        for _ in range(3):
            seq = c.execute(SQL_ENTREGAR_REV8, {"p": TV_PLAZA, "emp": EMPRESA_A, "l": LISTA_PLAZA, "v": 1}).fetchone()[0]
            c.execute("UPDATE pantalla_e SET entrega_rec = %s WHERE id = %s", (seq, TV_PLAZA))       # la TV la aplica...
            seq2 = c.execute(SQL_ENTREGAR_REV8, {"p": TV_PLAZA, "emp": EMPRESA_A, "l": LISTA_PLAZA, "v": 1}).fetchone()[0]  # ...y vuelve a consultar
            atras.append((seq2, seq))
        assert atras == [(2, 1), (4, 3), (6, 5)], "el defecto: nunca al dia"


def test_rev9_consultar_sin_cambios_no_crea_entregas(base):
    """RF26-QA-05: entregar es idempotente mientras (lista, version) no cambie;
    la TV que consulta cada minuto sigue al dia. Cambiar la version o la lista
    crea la entrega siguiente; volver atras tambien (es otra asignacion)."""
    montar(DDL_REV9)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        def declarar(seq):
            return c.execute("UPDATE pantalla_e SET entrega_rec = %(seq)s WHERE id = %(p)s AND (entrega_rec IS NULL OR entrega_rec < %(seq)s)",
                             {"p": TV_PLAZA, "seq": seq}).rowcount
        def recibida_al_dia():
            return c.execute("SELECT entrega_rec IS NOT NULL AND entrega_rec = entrega_env FROM pantalla_e WHERE id = %s", (TV_PLAZA,)).fetchone()[0]
        assert entregar(c, TV_PLAZA, LISTA_PLAZA) == 1
        assert declarar(1) == 1 and recibida_al_dia() is True
        for _ in range(5):                                                         # cinco consultas mas: nada cambia
            assert entregar(c, TV_PLAZA, LISTA_PLAZA) == 1
            assert declarar(1) == 0 and recibida_al_dia() is True
        assert c.execute("SELECT count(*) FROM pantalla_entrega").fetchone()[0] == 1
        # la lista avanza a v2: entrega nueva, la TV queda atras hasta aplicarla
        c.execute("INSERT INTO lista_version (lista_id, version, empresa_id) VALUES (%s, 2, %s)", (LISTA_PLAZA, EMPRESA_A))
        assert entregar(c, TV_PLAZA, LISTA_PLAZA, version=2) == 2 and recibida_al_dia() is False
        assert declarar(2) == 1 and recibida_al_dia() is True
        assert entregar(c, TV_PLAZA, LISTA_JURI) == 3                              # otra lista
        assert entregar(c, TV_PLAZA, LISTA_PLAZA, version=2) == 4                  # volver: otra asignacion


def test_reproduccion_rev8_borrar_lista_referenciada_falla(base):
    """RF26-QA-06 con el DDL de la rev. 8: el SET NULL de la llave compuesta
    (id, entrega_env) intenta anular tambien id."""
    montar(DDL_REV8)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute(SQL_ENTREGAR_REV8, {"p": TV_PLAZA, "emp": EMPRESA_A, "l": LISTA_PLAZA, "v": 1})
        with pytest.raises(errors.NotNullViolation):
            c.execute("DELETE FROM lista_e WHERE id = %s", (LISTA_PLAZA,))


def test_rev9_borrar_lista_anula_solo_las_entregas_y_no_reutiliza_numeros(base):
    """RF26-QA-06: con SET NULL por columna la lista se borra, la pantalla
    conserva su id y su contador; la siguiente entrega continua la numeracion,
    y una TV que devuelva el numero borrado recibe 'entrega desconocida'."""
    montar(DDL_REV9)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        assert entregar(c, TV_PLAZA, LISTA_PLAZA) == 1
        c.execute(SQL_CONFIRMAR, {"p": TV_PLAZA, "seq": 1})
        c.execute("UPDATE pantalla_e SET entrega_rec = 1 WHERE id = %s", (TV_PLAZA,))
        c.execute("DELETE FROM lista_e WHERE id = %s", (LISTA_PLAZA,))            # ahora si
        assert c.execute("SELECT id, entrega_env, entrega_rec, entrega_conf, entrega_ultima FROM pantalla_e WHERE id = %s",
                         (TV_PLAZA,)).fetchone() == (TV_PLAZA, None, None, None, 1)
        assert c.execute("SELECT count(*) FROM pantalla_entrega").fetchone()[0] == 0
        # la TV sigue devolviendo la 1: entrega desconocida (FK). El servidor la ignora;
        # en su proxima consulta recibe la entrega 2, nunca otra vez la 1.
        with pytest.raises(errors.ForeignKeyViolation):
            c.execute(SQL_CONFIRMAR, {"p": TV_PLAZA, "seq": 1})
        assert entregar(c, TV_PLAZA, LISTA_JURI) == 2
        assert c.execute(SQL_CONFIRMAR, {"p": TV_PLAZA, "seq": 2}).rowcount == 1
        assert c.execute(SQL_AL_DIA, (TV_PLAZA,)).fetchone()[0] is True


def test_rev9_abortar_y_revertir_no_dejan_punteros_incorrectos(base):
    """Criterios de aceptacion de RF26-QA-04 y RF26-QA-06 (informe 26): una
    peticion abortada a medias no mueve entrega_env ni gasta el contador; un
    borrado de lista que se revierte deja las tres referencias intactas; y
    nada de esto toca la identidad ni los numeros de OTRAS pantallas."""
    montar(DDL_REV9)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        assert entregar(c, TV_PLAZA, LISTA_PLAZA) == 1
        assert entregar(c, TV_JURI, LISTA_JURI) == 1
        c.execute("UPDATE pantalla_e SET entrega_rec = 1, entrega_conf = 1 WHERE id IN (%s, %s)", (TV_PLAZA, TV_JURI))
        def foto(tv):
            return c.execute("SELECT id, entrega_ultima, entrega_env, entrega_rec, entrega_conf FROM pantalla_e WHERE id = %s", (tv,)).fetchone()
        antes = (foto(TV_PLAZA), foto(TV_JURI))
        # 1) peticion abortada despues de tomar el bloqueo (la costura lanza): nada cambia
        class Corte(Exception):
            pass
        def cortar():
            raise Corte()
        with pytest.raises(Corte):
            entregar(c, TV_PLAZA, LISTA_JURI, tras_bloquear=cortar)
        # 2) peticion que falla dentro (lista de otra empresa) tras haber incrementado el contador: revierte entera
        with pytest.raises(errors.ForeignKeyViolation):
            entregar(c, TV_PLAZA, LISTA_B)
        assert (foto(TV_PLAZA), foto(TV_JURI)) == antes, "ni entrega_env ni el contador se movieron"
        # 3) borrado de lista revertido: las tres referencias siguen apuntando a la entrega 1
        with pytest.raises(Corte):
            with c.transaction():
                c.execute("DELETE FROM lista_e WHERE id = %s", (LISTA_PLAZA,))
                assert foto(TV_PLAZA)[2:] == (None, None, None)              # dentro: ya anuladas
                raise Corte()
        assert (foto(TV_PLAZA), foto(TV_JURI)) == antes
        # 4) borrado confirmado: solo la pantalla que reproducia esa lista pierde sus punteros
        c.execute("DELETE FROM lista_e WHERE id = %s", (LISTA_PLAZA,))
        assert foto(TV_PLAZA) == (TV_PLAZA, 1, None, None, None)
        assert foto(TV_JURI) == antes[1]
