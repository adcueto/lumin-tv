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

Ensayo de esquema con datos sintéticos; no es implementación de B6/B7.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest
from psycopg import errors

from comun import EMPRESA_A, dsn_rol, preparar_base

PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000a1")
JURI = uuid.UUID("00000000-0000-0000-0000-0000000000a2")
TV_PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000b1")
TV_JURI = uuid.UUID("00000000-0000-0000-0000-0000000000b2")
LISTA_PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000c1")
LISTA_JURI = uuid.UUID("00000000-0000-0000-0000-0000000000c2")
GRUPO_PLAZA = uuid.UUID("00000000-0000-0000-0000-0000000000d1")
GRUPO_JURI = uuid.UUID("00000000-0000-0000-0000-0000000000d2")

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


def montar(ddl: str):
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute(ddl)
        c.execute("INSERT INTO sucursal (id, empresa_id, clave, nombre) VALUES (%s, %s, 'plaza', 'Plaza'), (%s, %s, 'juri', 'Juriquilla')",
                  (PLAZA, EMPRESA_A, JURI, EMPRESA_A))
        c.execute("INSERT INTO pantalla_e (id, empresa_id, sucursal_id) VALUES (%s, %s, %s), (%s, %s, %s)",
                  (TV_PLAZA, EMPRESA_A, PLAZA, TV_JURI, EMPRESA_A, JURI))
        c.execute("INSERT INTO lista_e (id, empresa_id, sucursal_id) VALUES (%s, %s, %s), (%s, %s, %s)",
                  (LISTA_PLAZA, EMPRESA_A, PLAZA, LISTA_JURI, EMPRESA_A, JURI))
        if "lista_version" in ddl:
            c.execute("INSERT INTO lista_version (lista_id, version) VALUES (%s, 1), (%s, 1)", (LISTA_PLAZA, LISTA_JURI))
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


def test_mover_pantalla_de_sucursal_la_saca_de_grupos_y_destinos(base):
    """§2 del documento 22: cambiar la sucursal de una TV no puede dejar
    miembros ni destinos colgando de la sucursal vieja. Con las FKs compuestas,
    PostgreSQL lo impide salvo que primero se limpien: es lo que hara el
    servidor, y aqui se demuestra que el esquema no deja hacerlo a medias."""
    montar(DDL_REV7)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        c.execute("INSERT INTO grupo_pantalla_miembro (grupo_id, pantalla_id, sucursal_id, empresa_id) VALUES (%s, %s, %s, %s)",
                  (GRUPO_PLAZA, TV_PLAZA, PLAZA, EMPRESA_A))
        with pytest.raises(errors.ForeignKeyViolation):
            c.execute("UPDATE pantalla_e SET sucursal_id = %s WHERE id = %s", (JURI, TV_PLAZA))
        c.execute("DELETE FROM grupo_pantalla_miembro WHERE pantalla_id = %s", (TV_PLAZA,))
        c.execute("UPDATE pantalla_e SET sucursal_id = %s WHERE id = %s", (JURI, TV_PLAZA))   # ahora si


def test_confirmacion_de_entrega_es_el_par_lista_version(base):
    """Informe 24, hallazgo 3: dos listas con 'version 1' se distinguen porque
    la confirmacion guarda (lista_id, version) y el par debe existir en el
    historial de versiones."""
    montar(DDL_REV7)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        assert c.execute("SELECT count(*) FROM lista_version WHERE version = 1").fetchone()[0] == 2   # ambiguo por numero
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
