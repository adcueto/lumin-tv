CREATE TABLE empresa (
  id            uuid PRIMARY KEY,
  clave         text NOT NULL UNIQUE,            -- 'lumin'
  nombre        text NOT NULL,
  estado        text NOT NULL DEFAULT 'activa'
                CHECK (estado IN ('activa','suspendida','cancelada')),
  zona_horaria  text NOT NULL DEFAULT 'America/Mexico_City',
  creada_en     timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE sucursal (
  id            uuid PRIMARY KEY,
  empresa_id    uuid NOT NULL REFERENCES empresa(id),
  clave         text NOT NULL,                   -- 'plaza-de-la-mujer' (va en las URLs)
  nombre        text NOT NULL,
  zona_horaria  text,                            -- NULL = la de la empresa
  activa        boolean NOT NULL DEFAULT true,
  orden         int NOT NULL DEFAULT 0,
  lista_activa_id uuid,                          -- FK compuesta mas abajo
  creada_en     timestamptz NOT NULL DEFAULT now(),
  UNIQUE (empresa_id, clave),
  UNIQUE (id, empresa_id)                        -- ancla para FKs compuestas
);
CREATE TABLE pantalla (
  id               uuid PRIMARY KEY,
  empresa_id       uuid NOT NULL,
  sucursal_id      uuid,                         -- NULL mientras esta pendiente
  id_dispositivo   text NOT NULL UNIQUE,         -- GetChannelClientId: NO CAMBIA
  numero           int  NOT NULL,                -- visible en el panel (P6)
  desfase_rotacion int  NOT NULL DEFAULT 0,      -- antes era el mismo campo que numero
  zona             text NOT NULL DEFAULT '',
  aprobada         boolean NOT NULL DEFAULT false,
  codigo_aprobacion text NOT NULL DEFAULT '',
  visto_en         timestamptz,
  turnos_habilitados boolean NOT NULL DEFAULT false,
  lista_id         uuid,                         -- asignada; NULL = hereda de sucursal
  pausada          boolean NOT NULL DEFAULT false,
  silenciada       boolean NOT NULL DEFAULT false,
  creada_en        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (empresa_id, numero),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id),
  CHECK (aprobada = false OR sucursal_id IS NOT NULL),
  -- B3-QA-05: una pantalla pendiente (sucursal NULL) no puede tener lista;
  -- y la lista, si la hay, es de la MISMA empresa aunque la FK por sucursal
  -- no aplique por el NULL (MATCH SIMPLE).
  CHECK (lista_id IS NULL OR sucursal_id IS NOT NULL)
);
CREATE TABLE lista (
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  clave        text NOT NULL,                    -- 'principal', 'navidad' (lid actual)
  nombre       text NOT NULL,
  creada_en    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (sucursal_id, clave),
  UNIQUE (id, sucursal_id),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id)
);
CREATE TABLE grupo_pantallas (                    -- grupo PERSISTENTE, por sucursal
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  nombre       text NOT NULL,
  UNIQUE (sucursal_id, nombre),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE TABLE grupo_pantalla_miembro (
  grupo_id     uuid NOT NULL,
  pantalla_id  uuid NOT NULL,
  empresa_id   uuid NOT NULL,
  PRIMARY KEY (grupo_id, pantalla_id),
  FOREIGN KEY (grupo_id,    empresa_id) REFERENCES grupo_pantallas(id, empresa_id) ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, empresa_id) REFERENCES pantalla(id, empresa_id)        ON DELETE CASCADE
);
-- Asignacion de una lista a un destino. Un destino es UNA pantalla o UN grupo.
CREATE TABLE lista_destino (
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  lista_id     uuid NOT NULL,
  pantalla_id  uuid,                                -- exactamente uno de los dos
  grupo_id     uuid,
  prioridad    int  NOT NULL DEFAULT 0,             -- desempate explicito entre grupos
  asignado_por uuid, asignado_en timestamptz NOT NULL DEFAULT now(),
  CHECK ((pantalla_id IS NULL) <> (grupo_id IS NULL)),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (lista_id,    empresa_id) REFERENCES lista(id, empresa_id)           ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, empresa_id) REFERENCES pantalla(id, empresa_id)        ON DELETE CASCADE,
  FOREIGN KEY (grupo_id,    empresa_id) REFERENCES grupo_pantallas(id, empresa_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX un_destino_por_pantalla ON lista_destino (pantalla_id) WHERE pantalla_id IS NOT NULL;
CREATE UNIQUE INDEX una_lista_por_grupo     ON lista_destino (grupo_id)    WHERE grupo_id IS NOT NULL;
-- Entrega por pantalla: que version de lista le corresponde, cual pidio y cual confirmo
ALTER TABLE lista    ADD COLUMN version int NOT NULL DEFAULT 1;   -- +1 en cada cambio de elementos/orden
ALTER TABLE pantalla ADD COLUMN lista_version_enviada   int,       -- la que el servidor le sirvio por ultima vez
                     ADD COLUMN lista_version_recibida  int,       -- la que la TV declaro en su latido (B5b)
                     ADD COLUMN lista_version_reprod    int;       -- la que la TV confirmo reproduciendo (propuesta 7)
