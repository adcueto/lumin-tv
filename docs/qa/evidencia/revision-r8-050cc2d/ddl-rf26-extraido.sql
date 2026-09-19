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
-- Requisito previo en las tablas de §3.1/§3.2 (además de UNIQUE (id, empresa_id)):
ALTER TABLE pantalla ADD UNIQUE (id, sucursal_id);
ALTER TABLE lista    ADD UNIQUE (id, sucursal_id);

CREATE TABLE grupo_pantallas (                    -- grupo PERSISTENTE, por sucursal
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  nombre       text NOT NULL,
  UNIQUE (sucursal_id, nombre),
  UNIQUE (id, empresa_id),
  UNIQUE (id, sucursal_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE TABLE grupo_pantalla_miembro (
  grupo_id     uuid NOT NULL,
  pantalla_id  uuid NOT NULL,
  sucursal_id  uuid NOT NULL,                       -- la de AMBOS: lo garantizan las dos FK compuestas
  empresa_id   uuid NOT NULL,
  PRIMARY KEY (grupo_id, pantalla_id),
  FOREIGN KEY (grupo_id,    sucursal_id) REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla(id, sucursal_id)        ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
-- Asignacion de una lista a un destino. Un destino es UNA pantalla o UN grupo,
-- y lista y destino son de la MISMA sucursal.
CREATE TABLE lista_destino (
  id           uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  lista_id     uuid NOT NULL,
  pantalla_id  uuid,                                -- exactamente uno de los dos
  grupo_id     uuid,
  prioridad    int  NOT NULL DEFAULT 0,             -- desempate explicito entre grupos
  asignado_por uuid, asignado_en timestamptz NOT NULL DEFAULT now(),
  CHECK ((pantalla_id IS NULL) <> (grupo_id IS NULL)),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (lista_id,    sucursal_id) REFERENCES lista(id, sucursal_id)           ON DELETE CASCADE,
  FOREIGN KEY (pantalla_id, sucursal_id) REFERENCES pantalla(id, sucursal_id)        ON DELETE CASCADE,
  FOREIGN KEY (grupo_id,    sucursal_id) REFERENCES grupo_pantallas(id, sucursal_id) ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id, empresa_id)  REFERENCES sucursal(id, empresa_id)
);
CREATE UNIQUE INDEX un_destino_por_pantalla ON lista_destino (pantalla_id) WHERE pantalla_id IS NOT NULL;
CREATE UNIQUE INDEX una_lista_por_grupo     ON lista_destino (grupo_id)    WHERE grupo_id IS NOT NULL;

-- Entrega por pantalla. La identidad de lo entregado es el PAR (lista, version):
-- dos listas distintas pueden ir ambas por la "version 1". Las versiones son un
-- historial append-only: la lista avanza sin dejar colgadas confirmaciones viejas.
ALTER TABLE lista ADD COLUMN version int NOT NULL DEFAULT 1;      -- +1 en cada cambio de elementos/orden
CREATE TABLE lista_version (
  lista_id   uuid NOT NULL REFERENCES lista(id) ON DELETE CASCADE,
  version    int  NOT NULL,
  creada_en  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (lista_id, version)                                -- se inserta al crear la lista y en cada +1
);
ALTER TABLE pantalla
  ADD COLUMN lista_env_id  uuid, ADD COLUMN lista_env_version  int,  -- la que el servidor le sirvio por ultima vez
  ADD COLUMN lista_rec_id  uuid, ADD COLUMN lista_rec_version  int,  -- la que la TV declaro en su latido (B5b)
  ADD COLUMN lista_conf_id uuid, ADD COLUMN lista_conf_version int,  -- la que la TV confirmo reproduciendo (propuesta 7)
  ADD CONSTRAINT env_par  CHECK ((lista_env_id  IS NULL) = (lista_env_version  IS NULL)),
  ADD CONSTRAINT rec_par  CHECK ((lista_rec_id  IS NULL) = (lista_rec_version  IS NULL)),
  ADD CONSTRAINT conf_par CHECK ((lista_conf_id IS NULL) = (lista_conf_version IS NULL)),
  ADD FOREIGN KEY (lista_env_id,  lista_env_version)  REFERENCES lista_version(lista_id, version) ON DELETE SET NULL,
  ADD FOREIGN KEY (lista_rec_id,  lista_rec_version)  REFERENCES lista_version(lista_id, version) ON DELETE SET NULL,
  ADD FOREIGN KEY (lista_conf_id, lista_conf_version) REFERENCES lista_version(lista_id, version) ON DELETE SET NULL;
