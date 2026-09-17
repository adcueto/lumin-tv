-- DDL MINIMO para ensayar los protocolos del diseño B3 (revisión 4).
-- NO es el esquema del producto: solo las tablas necesarias para demostrar
--   (1) el espejo por marcas pendientes con instantánea consistente,
--   (2) el contrato de roles y políticas RLS,
--   (3) la regeneración de sesiones.json con revocaciones,
--   (4) el arranque de una sesión migrada contra la empresa heredada,
--   (5) la publicación de trabajos con artefacto por posesión.
-- Se ejecuta como lumin_migracion sobre una base de ensayo vacía.

CREATE SCHEMA IF NOT EXISTS lumin AUTHORIZATION lumin_migracion;

-- GUC de contexto: NULL si no está puesto, para que la comparación falle.
CREATE OR REPLACE FUNCTION lumin.gc(nombre text) RETURNS text
LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('lumin.' || nombre, true), '')
$$;

CREATE TABLE empresa (
  id        uuid PRIMARY KEY,
  clave     text NOT NULL UNIQUE,
  estado    text NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa','suspendida')),
  heredada  boolean NOT NULL DEFAULT false   -- la empresa de las rutas 6.x (LUMIN)
);
CREATE UNIQUE INDEX una_sola_activa   ON empresa ((true)) WHERE estado = 'activa';
CREATE UNIQUE INDEX una_sola_heredada ON empresa ((true)) WHERE heredada;

CREATE TABLE sucursal (
  id          uuid PRIMARY KEY,
  empresa_id  uuid NOT NULL REFERENCES empresa(id),
  clave       text NOT NULL,
  nombre      text NOT NULL,
  UNIQUE (empresa_id, clave),
  UNIQUE (id, empresa_id)
);

CREATE TABLE usuario (
  id              uuid PRIMARY KEY,
  nombre_usuario  text NOT NULL UNIQUE,
  activo          boolean NOT NULL DEFAULT true
);

CREATE TABLE membresia (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id  uuid NOT NULL REFERENCES empresa(id),
  usuario_id  uuid NOT NULL REFERENCES usuario(id),
  rol         text NOT NULL CHECK (rol IN ('admin_empresa','operador')),
  UNIQUE (empresa_id, usuario_id)
);

CREATE TABLE sesion (
  token_hash   text PRIMARY KEY,
  usuario_id   uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  empresa_id   uuid REFERENCES empresa(id),
  expira_en    timestamptz NOT NULL,
  revocada_en  timestamptz
);

CREATE TABLE auditoria (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ocurrido_en  timestamptz NOT NULL DEFAULT now(),
  empresa_id   uuid,
  usuario_id   uuid,
  accion       text NOT NULL,
  datos        jsonb NOT NULL DEFAULT '{}'
);

-- Cola de trabajos (solo lo necesario para ensayar la publicación por posesión).
CREATE TABLE trabajo (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  empresa_id    uuid NOT NULL REFERENCES empresa(id),
  tipo          text NOT NULL,
  clave_idem    text,
  posesion      uuid,
  estado        text NOT NULL DEFAULT 'pendiente'
                CHECK (estado IN ('pendiente','en_curso','hecho','fallido','cancelado')),
  intentos      int  NOT NULL DEFAULT 0,
  no_antes_de   timestamptz NOT NULL DEFAULT now(),
  latido_en     timestamptz,
  resultado     text,                       -- ruta del artefacto publicado (por posesion)
  terminado_en  timestamptz
);

-- Outbox del espejo. La transacción que muta datos inserta una fila; el hilo
-- espejo procesa las que VE (confirmadas) y las marca. Nunca se usa max(id).
CREATE TABLE espejo_marca (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  creada_en     timestamptz NOT NULL DEFAULT clock_timestamp(),
  procesada_en  timestamptz
);
CREATE INDEX espejo_marca_pendientes ON espejo_marca (id) WHERE procesada_en IS NULL;

CREATE TABLE espejo_estado (
  uno               boolean PRIMARY KEY DEFAULT true CHECK (uno),
  generacion        bigint NOT NULL DEFAULT 0,
  exportada_en      timestamptz,
  marcas_cubiertas  bigint[] NOT NULL DEFAULT '{}'
);
INSERT INTO espejo_estado DEFAULT VALUES;

-- ---------------------------------------------------------------- RLS
-- ENABLE, no FORCE: el propietario (lumin_migracion) queda exento y es el
-- único que migra, respalda y restaura. lumin_app y lumin_espejo NO son
-- propietarios de nada, así que RLS se les aplica siempre.
ALTER TABLE empresa       ENABLE ROW LEVEL SECURITY;
ALTER TABLE sucursal      ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario       ENABLE ROW LEVEL SECURITY;
ALTER TABLE membresia     ENABLE ROW LEVEL SECURITY;
ALTER TABLE trabajo       ENABLE ROW LEVEL SECURITY;
ALTER TABLE sesion        ENABLE ROW LEVEL SECURITY;
ALTER TABLE auditoria     ENABLE ROW LEVEL SECURITY;
ALTER TABLE espejo_marca  ENABLE ROW LEVEL SECURITY;
ALTER TABLE espejo_estado ENABLE ROW LEVEL SECURITY;

GRANT USAGE ON SCHEMA lumin TO lumin_app, lumin_espejo;
GRANT USAGE ON SCHEMA public TO lumin_app, lumin_espejo;

-- ---- lumin_app: GRANT + política, los dos, por tabla y operación --------
GRANT SELECT                          ON empresa       TO lumin_app;
GRANT SELECT, INSERT, UPDATE, DELETE  ON sucursal      TO lumin_app;
GRANT SELECT                          ON usuario       TO lumin_app;
GRANT SELECT                          ON membresia     TO lumin_app;
GRANT SELECT, INSERT, UPDATE          ON trabajo       TO lumin_app;
GRANT SELECT, INSERT, UPDATE          ON sesion        TO lumin_app;
GRANT INSERT                          ON auditoria     TO lumin_app;
GRANT INSERT                          ON espejo_marca  TO lumin_app;
-- (las columnas identity no exigen USAGE sobre su secuencia: se comprueba en
--  el ensayo; si alguna versión lo exigiera, aquí iría el GRANT USAGE)

-- La empresa heredada es visible sin contexto: las rutas 6.x (latido de la
-- TV, /videos/) y el arranque de una sesión migrada la necesitan ANTES de
-- tener empresa en el contexto (B3-R3-01).
CREATE POLICY empresa_app ON empresa FOR SELECT TO lumin_app
  USING (id = lumin.gc('empresa_id')::uuid
         OR heredada
         OR id IN (SELECT empresa_id FROM membresia WHERE usuario_id = lumin.gc('usuario_id')::uuid));

-- Membresías: por empresa conocida, o las PROPIAS del usuario (para resolver
-- la empresa antes de asignarla).
CREATE POLICY membresia_app ON membresia FOR SELECT TO lumin_app
  USING (empresa_id = lumin.gc('empresa_id')::uuid OR usuario_id = lumin.gc('usuario_id')::uuid);

CREATE POLICY trabajo_app ON trabajo FOR ALL TO lumin_app
  USING      (empresa_id = lumin.gc('empresa_id')::uuid)
  WITH CHECK (empresa_id = lumin.gc('empresa_id')::uuid);

CREATE POLICY sucursal_app ON sucursal FOR ALL TO lumin_app
  USING      (empresa_id = lumin.gc('empresa_id')::uuid)
  WITH CHECK (empresa_id = lumin.gc('empresa_id')::uuid);

CREATE POLICY usuario_app ON usuario FOR SELECT TO lumin_app
  USING (id = lumin.gc('usuario_id')::uuid
         OR (lumin.gc('fase') = 'login' AND nombre_usuario = lumin.gc('nombre_usuario')));

-- WITH CHECK admite también la propia cookie: el logout revoca la sesión
-- durante la resolución, cuando el contexto aún solo tiene token_hash
-- (lo detectó el ensayo test_ensayo_sesiones: con solo usuario_id fallaba).
CREATE POLICY sesion_app ON sesion FOR ALL TO lumin_app
  USING      (token_hash = lumin.gc('token_hash') OR usuario_id = lumin.gc('usuario_id')::uuid)
  WITH CHECK (token_hash = lumin.gc('token_hash') OR usuario_id = lumin.gc('usuario_id')::uuid);

CREATE POLICY auditoria_app ON auditoria FOR INSERT TO lumin_app
  WITH CHECK (empresa_id IS NULL OR empresa_id = lumin.gc('empresa_id')::uuid);

CREATE POLICY marca_app ON espejo_marca FOR INSERT TO lumin_app
  WITH CHECK (true);

-- ---- lumin_espejo: lee todo, solo escribe su propio estado --------------
GRANT SELECT ON empresa, sucursal, usuario, membresia, sesion, auditoria, trabajo, espejo_marca, espejo_estado TO lumin_espejo;
GRANT UPDATE (procesada_en) ON espejo_marca  TO lumin_espejo;
GRANT UPDATE                ON espejo_estado TO lumin_espejo;

CREATE POLICY empresa_espejo   ON empresa       FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY sucursal_espejo  ON sucursal      FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY usuario_espejo   ON usuario       FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY membresia_espejo ON membresia     FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY trabajo_espejo   ON trabajo       FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY sesion_espejo    ON sesion        FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY auditoria_espejo ON auditoria     FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY marca_espejo_sel ON espejo_marca  FOR SELECT TO lumin_espejo USING (true);
CREATE POLICY marca_espejo_upd ON espejo_marca  FOR UPDATE TO lumin_espejo USING (true) WITH CHECK (true);
CREATE POLICY estado_espejo    ON espejo_estado FOR ALL    TO lumin_espejo USING (true) WITH CHECK (true);
