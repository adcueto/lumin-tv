# Diseño de B3 — PostgreSQL y modelo multiempresa

Para revisión de Adrián y Codex **antes de escribir código**.
Fecha: 2026-09-16 · Autor: Claude · Base: `modernizacion-diagnostico` (servidor 6.10, app 5.2 build 58)
Responde a los siete puntos de "Orientación para el diseño B3" de `13-qa-B2-0c00f35.md`
(Codex): §3–5 → punto 1; §6 → punto 2; §7 → punto 3; §3.4 y §7.6 → punto 4; §8a → punto 5;
§8b → punto 6; §10 → punto 7.

> Nada de este documento se ejecuta sobre producción. La migración descrita se
> ensaya sobre copias sintéticas y sobre una copia **anonimizada** de los JSON,
> y solo llega al VPS con autorización expresa, en una ventana acordada.

---

## 0. Resumen en una página

**Qué es B3.** Sustituir los 13 archivos JSON del servidor por PostgreSQL, con
un modelo que ya lleva `empresa_id` en todas las tablas de datos, sin que las
TVs, el POS ni el panel noten el cambio. LUMIN queda como la empresa 1.

**Cómo, en cuatro decisiones:**

1. **Un paquete de datos, no un servidor nuevo.** `servidor/lumin_datos/`
   (SQLAlchemy 2 + Alembic) con repositorios por entidad. El servidor 6.x
   actual pasa a usarlos en lugar de `leer_json/escribir_json`. Un solo proceso
   escribe la base. FastAPI (B5) consumirá el mismo paquete: el trabajo de datos
   se hace una vez.
2. **Aislamiento en cuatro capas**, porque las llaves compuestas solas no
   bastan: (a) llaves foráneas compuestas; (b) un `Contexto` obligatorio en cada
   repositorio que filtra por `empresa_id`; (c) **Row Level Security** de
   PostgreSQL como red de seguridad ante un `WHERE` olvidado; (d) una suite con
   **dos empresas** que ataca cada función de lectura y escritura con
   identificadores cruzados, más un guardián en pruebas que revisa cada SQL
   emitido.
3. **Los contratos no cambian.** `GET /playlist.json` byte a byte, `POST/PUT
   /api/turno` igual, `/videos/<sucursal>/<archivo>` igual porque **los archivos
   no se mueven**. El identificador Roku (`GetChannelClientId`) se conserva como
   llave natural. Las cookies de sesión vigentes siguen sirviendo. Los nombres
   de usuario y contraseñas actuales siguen funcionando.
4. **Migración con dos marchas atrás.** Ventana corta con congelación de
   escrituras; después, **escritura doble** JSON+PostgreSQL durante 7 días, de
   modo que revertir es volver a apuntar el servidor a los JSON **sin perder lo
   escrito después del cambio**. Pasada la semana, la reversión es por
   exportación PostgreSQL → JSON, ensayada.

**Qué no es B3.** No es FastAPI (B5), no es React (B6), no cambia permisos
(B4: hoy se preservan los efectivos, explícitos), no toca el reproductor, no
mueve medios, no introduce planes ni cobros.

---

## 1. Alcance

| Dentro | Fuera (bloque) |
|---|---|
| Esquema PostgreSQL con `empresa_id` | Endurecer permisos F01/F02/F03 (B4) |
| Paquete `lumin_datos/` con repositorios y `Contexto` | API v2 / FastAPI (B5) |
| Rewire de `servidor_lumin.py` a repositorios | Panel React (B6) |
| Migración JSON → PostgreSQL, respaldo, reversión, escritura doble | Mover medios a S3 / nginx (B5) |
| Suite "dos empresas" y pruebas de contrato | Credencial por pantalla (B8) |
| Instalación de PostgreSQL en el VPS, roles, `pg_dump` nocturno | Reasignar los números de pantalla ya duplicados (decisión, §9) |
| Reserva de columnas para B4/B5 (correo, `clave_evento`) | Cualquier cobro, plan o portal del propietario |

---

## 2. Arquitectura del bloque

```
                servidor_lumin.py (6.x, mismo proceso, mismos contratos)
                          │
                          │  antes: leer_json / escribir_json
                          ▼
              servidor/lumin_datos/          ← NUEVO, B3
              ├── modelos.py     SQLAlchemy 2, tablas de §3
              ├── contexto.py    Contexto(empresa_id, sucursales, rol)
              ├── repos/         una funcion por operacion, todas reciben Contexto
              ├── migrar_json.py JSON → PostgreSQL, idempotente, con informe
              ├── exportar_json.py PostgreSQL → JSON (marcha atras tardia)
              └── alembic/       migraciones versionadas
                          │
                          ▼
                    PostgreSQL 16 (mismo VPS)
                    rol de aplicacion sin superusuario → RLS activa
```

**Por qué el paquete y no un servidor nuevo.** Dos procesos escribiendo los
mismos datos (viejo en JSON, nuevo en PostgreSQL) obligan a sincronizar y
abren una ventana de inconsistencia permanente. Con el paquete hay un solo
escritor desde el primer día, y el código de manejo HTTP viejo —que B5
sustituye— es solo la red de seguridad que mantiene la operación.

**Costo declarado.** El servidor gana sus primeras dependencias externas
(`sqlalchemy`, `psycopg`, `alembic`) y un servicio (`postgresql`) en el VPS.
Es el precio de tener transacciones e integridad; el documento de julio ya lo
daba por bueno.

---

## 3. Esquema PostgreSQL

Convenciones: UUID como llave primaria en todas las tablas; llaves naturales
del sistema actual conservadas en columnas `UNIQUE`; `empresa_id NOT NULL` en
toda tabla de datos; fechas `timestamptz`; nombres en español como el código.

### 3.1 Jerarquía

```sql
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
  CHECK (aprobada = false OR sucursal_id IS NOT NULL)
);
```

`numero` y `desfase_rotacion` se separan: hoy son el mismo campo y por eso dos
pantallas con número repetido arrancan la lista en la misma posición.

### 3.2 Contenido y listas

```sql
CREATE TABLE contenido (
  id              uuid PRIMARY KEY,
  empresa_id      uuid NOT NULL,
  sucursal_id     uuid NOT NULL,
  nombre_archivo  text NOT NULL,                 -- 'promo uñas.mp4' (va en la URL)
  tipo            text NOT NULL CHECK (tipo IN ('video','imagen')),
  duracion_imagen int  NOT NULL DEFAULT 10,      -- duraciones.json
  girado          boolean NOT NULL DEFAULT false,-- girados.json
  posicion        int  NOT NULL DEFAULT 0,       -- ordenes.json (orden en biblioteca)
  tamano_bytes    bigint,                        -- B5 los llena; hoy NULL
  duracion_s      numeric(8,2),
  ancho           int, alto int,
  estado          text NOT NULL DEFAULT 'listo'
                  CHECK (estado IN ('procesando','listo','fallido')),
  ruta_almacen    text,                          -- NULL = local en <clave>/<archivo>; B5 (S3) la llena
  creado_en       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (sucursal_id, nombre_archivo),
  UNIQUE (id, sucursal_id),
  UNIQUE (id, empresa_id),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id)
);

CREATE TABLE programacion (                      -- programacion.json: una por contenido
  contenido_id  uuid PRIMARY KEY,
  empresa_id    uuid NOT NULL,
  desde         date, hasta date,
  dias          smallint[] NOT NULL DEFAULT '{}',-- 0=lunes ... 6=domingo, como hoy
  hora_inicio   time, hora_fin time,
  FOREIGN KEY (contenido_id, empresa_id) REFERENCES contenido(id, empresa_id) ON DELETE CASCADE,
  CHECK ((hora_inicio IS NULL) = (hora_fin IS NULL))
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

CREATE TABLE lista_elemento (
  lista_id      uuid NOT NULL,
  contenido_id  uuid NOT NULL,
  sucursal_id   uuid NOT NULL,                   -- redundante a proposito
  posicion      int  NOT NULL,
  PRIMARY KEY (lista_id, contenido_id),
  UNIQUE (lista_id, posicion) DEFERRABLE INITIALLY DEFERRED,
  -- lista y contenido deben ser de la MISMA sucursal: lo impone la base
  FOREIGN KEY (lista_id, sucursal_id)     REFERENCES lista(id, sucursal_id)     ON DELETE CASCADE,
  FOREIGN KEY (contenido_id, sucursal_id) REFERENCES contenido(id, sucursal_id) ON DELETE CASCADE
);

ALTER TABLE sucursal ADD FOREIGN KEY (lista_activa_id, id) REFERENCES lista(id, sucursal_id);
ALTER TABLE pantalla ADD FOREIGN KEY (lista_id, sucursal_id) REFERENCES lista(id, sucursal_id);
```

`ON DELETE CASCADE` en `lista_elemento` reproduce la regla de hoy: borrar un
archivo lo quita de las listas; borrar una lista **no** borra archivos.

### 3.3 Operación

```sql
CREATE TABLE ajustes_sucursal (                  -- ajustes.json
  sucursal_id      uuid PRIMARY KEY,
  empresa_id       uuid NOT NULL,
  mensaje          text NOT NULL DEFAULT '',
  cintillo_animado boolean NOT NULL DEFAULT true,
  velocidad        int NOT NULL DEFAULT 130,
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);

CREATE TABLE comando_pantalla (                  -- comandos.json: el ULTIMO comando
  pantalla_id  uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  n            int  NOT NULL,                    -- contador monotono que dedupe la TV
  accion       text NOT NULL,
  url          text NOT NULL DEFAULT '',
  tipo         text NOT NULL DEFAULT '',
  duracion     int  NOT NULL DEFAULT 10,
  emitido_en   timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (pantalla_id, empresa_id) REFERENCES pantalla(id, empresa_id) ON DELETE CASCADE
);

CREATE TABLE turno_vigente (                     -- turnos.json: el ULTIMO turno
  sucursal_id  uuid PRIMARY KEY,
  empresa_id   uuid NOT NULL,
  n            int  NOT NULL,
  numero       text NOT NULL, estacion text NOT NULL DEFAULT '',
  espera       text NOT NULL DEFAULT '',
  duracion     int  NOT NULL DEFAULT 60,
  proximos     jsonb NOT NULL DEFAULT '[]',
  ts           bigint NOT NULL,                  -- epoch, lo que hoy lee la TV
  clave_evento text,                             -- reservado para B5 (QA-G02)
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX turno_clave_evento ON turno_vigente (empresa_id, clave_evento)
  WHERE clave_evento IS NOT NULL;

CREATE TABLE descarga_diaria (                   -- contadores.json, con su nombre real
  sucursal_id    uuid NOT NULL,
  empresa_id     uuid NOT NULL,
  nombre_archivo text NOT NULL,                  -- no FK: hay conteos de archivos ya borrados
  fecha          date NOT NULL,
  veces          int  NOT NULL DEFAULT 0,
  PRIMARY KEY (sucursal_id, nombre_archivo, fecha),
  FOREIGN KEY (sucursal_id, empresa_id) REFERENCES sucursal(id, empresa_id) ON DELETE CASCADE
);
```

Se llama `descarga_diaria` y no "reproducciones" porque eso es lo que cuenta.
Las reproducciones confirmadas llegan con los eventos del reproductor (B5/B8) a
una tabla `evento_pantalla` que B3 **no** crea todavía.

### 3.4 Identidad

```sql
CREATE TABLE usuario (
  id              uuid PRIMARY KEY,
  nombre_usuario  text NOT NULL UNIQUE,          -- 'admin', 'pos-plaza': lo que teclean hoy
  correo          text UNIQUE,                   -- NULL hasta B4
  correo_verificado_en timestamptz,
  contrasena_hash text NOT NULL,
  contrasena_sal  text,                          -- solo mientras algoritmo = 'sha256-sal'
  algoritmo       text NOT NULL DEFAULT 'sha256-sal'
                  CHECK (algoritmo IN ('sha256-sal','argon2id')),
  activo          boolean NOT NULL DEFAULT true,
  creado_en       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE membresia (
  id          uuid PRIMARY KEY,
  empresa_id  uuid NOT NULL REFERENCES empresa(id),
  usuario_id  uuid NOT NULL REFERENCES usuario(id),
  rol         text NOT NULL CHECK (rol IN ('admin_empresa','operador')),
  UNIQUE (empresa_id, usuario_id),
  UNIQUE (id, empresa_id)
);

CREATE TABLE membresia_sucursal (                -- concesion EXPLICITA; vacio = nada
  membresia_id uuid NOT NULL,
  sucursal_id  uuid NOT NULL,
  empresa_id   uuid NOT NULL,
  PRIMARY KEY (membresia_id, sucursal_id),
  FOREIGN KEY (membresia_id, empresa_id) REFERENCES membresia(id, empresa_id) ON DELETE CASCADE,
  FOREIGN KEY (sucursal_id,  empresa_id) REFERENCES sucursal(id, empresa_id)  ON DELETE CASCADE
);

CREATE TABLE sesion (
  token_hash   text PRIMARY KEY,                 -- sha256 del valor de la cookie
  usuario_id   uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  empresa_id   uuid REFERENCES empresa(id),      -- NULL en sesiones migradas; B4 lo exige
  expira_en    timestamptz NOT NULL,
  revocada_en  timestamptz,
  creada_en    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE auditoria (
  id           uuid PRIMARY KEY,
  ocurrido_en  timestamptz NOT NULL DEFAULT now(),
  empresa_id   uuid,
  usuario_id   uuid,
  accion       text NOT NULL,
  objeto_tipo  text, objeto_id text,
  datos        jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE migracion_json (                    -- bitacora de la migracion
  id          serial PRIMARY KEY,
  ejecutada_en timestamptz NOT NULL DEFAULT now(),
  archivo     text NOT NULL, registros int NOT NULL,
  advertencias jsonb NOT NULL DEFAULT '[]'
);
```

**Contraseñas:** las actuales son `sha256(sal + contraseña)`. Se migran **tal
cual**, con `algoritmo = 'sha256-sal'`, para que nadie tenga que cambiar de
contraseña el día del corte. B4 recifra a Argon2id en el siguiente inicio de
sesión exitoso. Sin esto, la migración bloquearía la operación.

### 3.5 Row Level Security

```sql
ALTER TABLE sucursal ENABLE ROW LEVEL SECURITY;  -- y todas las tablas con empresa_id
CREATE POLICY por_empresa ON sucursal
  USING (empresa_id = current_setting('lumin.empresa_id', true)::uuid);
```

El servidor abre cada transacción con `SET LOCAL lumin.empresa_id = '…'`. Si
una consulta olvida el `WHERE`, PostgreSQL devuelve cero filas en vez de las de
otra empresa. El rol de aplicación **no** es superusuario ni tiene `BYPASSRLS`;
la migración y los respaldos usan un rol aparte. Costo: una sentencia `SET` por
transacción, y en pruebas se verifica que sin el `SET` no sale nada.

---

## 4. Mapeo JSON → PostgreSQL

| JSON (6.x) | Tabla | Notas de conversión |
|---|---|---|
| `sucursales.json` `[{clave,nombre}]` | `sucursal` | `orden` = posición en la lista; todas bajo `empresa` 'lumin' |
| `tvs.json` `{id: {indice,sucursal,zona,aprobada,codigo,visto,turnos,lista,pausada,silencio}}` | `pantalla` | `id` → `id_dispositivo`; `indice+1` → `numero`; `indice` → `desfase_rotacion`; `sucursal ''` → `sucursal_id NULL`; `lista` (lid) → `lista_id` buscando en la sucursal; `visto` epoch → `visto_en` |
| `ordenes.json` `{clave: [archivos]}` | `contenido.posicion` | El orden de la biblioteca. Archivos en disco sin entrada → se crean con posición al final (hoy `lista_archivos` hace lo mismo) |
| `listas.json` `{clave: {activa, listas: {lid: {nombre, archivos}}}}` | `lista`, `lista_elemento`, `sucursal.lista_activa_id` | Archivos referenciados que ya no existen en disco → se omiten con advertencia (hoy se filtran al leer) |
| `duraciones.json` | `contenido.duracion_imagen` | Se acota a 3–120 como hoy |
| `girados.json` | `contenido.girado` | |
| `programacion.json` | `programacion` | `dias` [0..6] igual; `hini/hfin` "HH:MM" → `time` |
| `ajustes.json` | `ajustes_sucursal` | Defectos actuales: mensaje '', animado true, 130 |
| `comandos.json` | `comando_pantalla` | Solo el último por pantalla, como hoy |
| `turnos.json` | `turno_vigente` | `ts` se conserva en epoch |
| `contadores.json` | `descarga_diaria` | Se migran los últimos 60 días (lo que hoy conserva) |
| `usuarios.json` `{nombre: {sal,hash,rol,sucursales}}` | `usuario`, `membresia`, `membresia_sucursal` | Ver §6: rol `admin` → `admin_empresa`; `usuario` → `operador` con concesiones **explícitas** |
| `sesiones.json` `{token: {usuario, exp}}` | `sesion` | `token_hash = sha256(token)`; la cookie sigue valiendo. Vencidas no se migran |

Lo que **no** se migra y por qué: sesiones vencidas, contadores de más de 60
días, entradas de `ordenes`/`listas` cuyo archivo ya no está en disco. Todo lo
omitido se lista en el informe de migración y queda en los JSON congelados.

---

## 5. Conservación de identificadores y contratos

| Contrato | Cómo se conserva | Prueba |
|---|---|---|
| `GET /playlist.json?id=<GetChannelClientId>` | `pantalla.id_dispositivo` es llave natural. La respuesta se arma con las mismas llaves y el mismo orden (`videos`, `mensaje`, `cintillo`, `velocidad`, `vertical`, `giro`, `comando`, `turno`); `pendiente/codigo` igual | Fixture con JSON reales sintéticos: respuesta **byte a byte** igual antes y después, para pantalla aprobada, pendiente, con turno, con comando y con lista asignada |
| Rotación escalonada | `desfase_rotacion` migra desde `indice`; misma fórmula `desfase % len` | Misma prueba: el primer video coincide |
| `POST/PUT /api/turno` | Mismo cuerpo, mismos límites (numero ≤8, estación ≤20, espera ≤10, duración 5–300, próximos ≤3), `n` sigue incrementando por sucursal | Regresión de `docs/API-turnos.md` |
| `/videos/<clave>/<archivo>`, `/miniaturas/…`, `/rapidos/…` | **Los archivos no se mueven.** `sucursal.clave` y `contenido.nombre_archivo` son los mismos textos de hoy | Ruta a disco idéntica |
| Panel actual | Todos los `/api/*` responden igual: la forma de los JSON de respuesta se conserva aunque por dentro venga de tablas | Suite de contrato del panel sobre las 30 rutas |
| Cookies de sesión | Token en la cookie no cambia; se guarda su hash | Login antes de migrar, petición después: 200 |
| Usuario y contraseña | `nombre_usuario` y hash sha256 se conservan | Login de cada usuario migrado con su contraseña |
| Número visible de pantalla | Se conserva **salvo duplicados** (§9, decisión) | Informe de migración lista cambios |
| Vigilante (Raspberry) | Habla ECP con las TVs, no con el servidor: sin efecto | — |
| App Roku 5.1 y 5.2 | No distinguen JSON de PostgreSQL | Prueba F13 de B1 sobre servidor 6.11 |

---

## 6. Aislamiento entre empresas y permisos por sucursal

### 6.1 `Contexto`: la unidad de autorización

```python
@dataclass(frozen=True)
class Contexto:
    empresa_id: UUID
    usuario_id: UUID | None          # None para la TV y el proceso del sistema
    rol: str                         # 'admin_empresa' | 'operador' | 'pantalla' | 'sistema'
    sucursales: frozenset[UUID]      # alcance EXPLICITO. Vacio = ninguna.
```

Reglas fijas:

- **Toda** función de repositorio recibe `Contexto` y añade
  `WHERE empresa_id = ctx.empresa_id`. No existe función sin contexto.
- La TV obtiene un `Contexto` de rol `pantalla` derivado de su `id_dispositivo`,
  acotado a su empresa y su sucursal. El POS, de su sesión de usuario.
- Un identificador que llega del cliente (sucursal, pantalla, lista, archivo)
  **nunca** decide la empresa: se resuelve dentro del contexto, y si no está,
  es "no encontrado", con el mismo mensaje exista o no en otra empresa.
- Cambiar algo de sucursal exige alcance en **origen y destino** (mecanismo de
  QA-F02, listo en B3; la política se endurece en B4).

### 6.2 Qué cambia y qué no en los permisos actuales

B3 **no cambia el comportamiento efectivo** de ningún usuario actual; lo hace
explícito. Así el corte no bloquea a nadie y B4 endurece con conocimiento:

| Hoy en `usuarios.json` | Efecto hoy | Migración a B3 | B4 |
|---|---|---|---|
| `rol: admin` | Todo | `admin_empresa` de 'lumin' | igual |
| `rol: usuario`, `sucursales: [a, b]` | a y b | `operador` con concesiones a, b | igual |
| `rol: usuario`, `sucursales: []` | **todas** (QA-F01) | `operador` con concesión explícita a **todas las actuales**, marcado en el informe | Adrián decide sucursal por sucursal |
| `rol: usuario`, `sucursales: ['x-inexistente']` | la primera (QA-F01) | `operador` con concesión a la primera, marcado en el informe | ídem |

La "sustitución silenciosa" de una sucursal fuera de alcance por la primera
permitida (`_sucursal_de`) se mantiene en B3 solo para las rutas del panel
viejo y **se registra en auditoría cada vez que ocurre**, para tener la cuenta
real antes de convertirla en 403 en B4.

### 6.3 Las cuatro capas, y cómo se prueba cada una

| Capa | Qué impide | Prueba |
|---|---|---|
| 1. Llaves compuestas | Que una fila apunte a un padre de otra empresa | `INSERT` directo cruzado → `IntegrityError` |
| 2. `Contexto` en repositorios | Que una consulta lea o escriba fuera de la empresa | Suite "dos empresas" (§6.4) |
| 3. Row Level Security | Que un `WHERE` olvidado filtre datos | Consulta cruda sin `SET lumin.empresa_id` → 0 filas; con la empresa equivocada → 0 filas |
| 4. Guardián de SQL en pruebas | Que se cuele una consulta a tabla de empresa sin filtro | Listener `before_cursor_execute`: toda sentencia sobre tabla con `empresa_id` debe contener `empresa_id` o falla la prueba |

### 6.4 Suite "dos empresas"

Se crean `A` y `B` con estructuras gemelas: dos sucursales cada una, tres
pantallas, cuatro contenidos, dos listas, un usuario admin y un operador con una
sola sucursal. Luego, **para cada función pública del repositorio** (se
enumeran por reflexión, para que una función nueva no quede sin probar):

1. Con contexto de `A` y los identificadores de `B`: lectura → vacío / no
   encontrado; escritura → rechazada; y **la fila de `B` sigue idéntica**
   (se compara antes y después).
2. Con contexto de `A` y sus propios identificadores: funciona (control
   positivo).
3. Operador de `A` con una sucursal: lo mismo entre sus dos sucursales.

Casos que se añaden a mano porque la reflexión no los cubre:

- `playlist.json` pedida con el `id_dispositivo` de una pantalla de `A`:
  nunca contiene URLs de medios de `B`, ni el turno ni el comando de `B`,
  aunque `A` y `B` tengan sucursales con la **misma `clave`**
  (`plaza-centro` en ambas), que es el caso que más fácil se cuela.
- **Medios:** `GET /videos/<clave>/<archivo>` con una clave que existe en `A`
  y en `B` resuelve **siempre** dentro de la empresa del contexto. En B3 la
  ruta pública sigue sin credencial (QA-G01, B8), así que esta prueba fija el
  comportamiento del *servidor*: la resolución de `sucursal.clave` a
  `sucursal_id` pasa por `empresa_id`. Mientras exista una sola empresa no
  hay ambigüedad; la prueba está para que la segunda no la introduzca.
- **Credenciales de pantalla:** el código de aprobación de una pantalla de
  `B` no aprueba una de `A`; `/api/tv/aprobar` con `id_dispositivo` de `B`
  desde una sesión de `A` es "no encontrado"; una pantalla movida entre
  sucursales nunca puede aterrizar en una sucursal de otra empresa (capa 1 lo
  impide, y se verifica el `IntegrityError`).
- `/api/turno` de un usuario de `A` apuntando a una sucursal de `B` (hoy caería
  en la primera de `A`: en B3 se registra en auditoría, en B4 es 403).
- `lista_elemento` intentando meter un contenido de `B` en una lista de `A`
  (lo detiene la capa 1, y se comprueba).
- Sesión de un usuario que pertenece a `A` **y** a `B`: cada sesión nombra una
  empresa y no alcanza la otra.

---

## 7. Migración

### 7.1 Principios

- **Idempotente:** correrla dos veces deja lo mismo. Cada archivo se marca en
  `migracion_json`.
- **Con informe:** cuántos registros por archivo, qué se omitió y por qué, qué
  permisos se hicieron explícitos, qué números de pantalla cambiaron.
- **Verificable antes de abrir el tráfico:** después de migrar, el propio
  script arma `playlist.json` para cada pantalla desde PostgreSQL y desde los
  JSON, y compara byte a byte. Si una difiere, aborta.
- **Nunca sobre producción sin ensayo previo** sobre copia sintética y sobre
  copia anonimizada.

### 7.2 Ensayos (antes de cualquier fecha)

1. **Sintético:** los JSON de `servidor/tests/` ampliados con los casos raros
   (pantalla pendiente, lista con archivo borrado, usuario con `[]`, sesión
   vencida, números duplicados). Migrar, verificar, exportar de vuelta,
   comparar.
2. **Anonimizado:** una copia de los JSON reales pasada por
   `anonimizar_json.py` (hashes y sales reemplazados, tokens de sesión
   descartados, nombres de usuario mapeados a `u1..uN`). Mide tiempos y
   confirma que la estructura real no trae sorpresas. **Esta copia la genera
   Adrián en el VPS y la revisa antes de compartirla**; no salen datos
   operativos del servidor.
3. **Reversión cronometrada** en ambos: ¿cuánto tarda volver a JSON?

### 7.3 El día del corte (cuando se autorice)

```
T-1 día   pg_dump del esquema vacío; respaldo completo de /opt/lumin-tv (JSON +
          medios) verificado restaurando en limpio.
T-0       Ventana nocturna de ~15 min. Las TVs siguen reproduciendo (tienen
          lista y cache); el panel entra en solo lectura (bandera).
  1. Congelar escrituras: LUMIN_SOLO_LECTURA=1, reiniciar.
  2. Copiar los JSON a json-congelados/AAAA-MM-DD/ (no se borran).
  3. migrar_json.py --verificar   → informe + comparación byte a byte.
  4. Arrancar 6.11 con LUMIN_DATOS=postgresql y LUMIN_ESCRITURA_DOBLE=1.
  5. Comprobar: playlist de 3 pantallas reales, un turno desde el POS, login
     del panel con un usuario existente, subir una imagen.
  6. Quitar solo lectura.
T+7 días  Si todo bien: LUMIN_ESCRITURA_DOBLE=0. Los JSON dejan de escribirse.
T+30 días Se archivan los JSON congelados (no se borran).
```

### 7.4 Escrituras posteriores al cambio: las dos marchas atrás

**Dentro de los 7 días — escritura doble.** Con `LUMIN_ESCRITURA_DOBLE=1` el
servidor escribe en PostgreSQL (fuente de verdad para leer) **y** actualiza los
JSON con las mismas funciones de 6.10. Revertir es: parar, arrancar 6.10
apuntando a los JSON, listo. **Todo lo escrito después del corte está en los
JSON.** Tiempo: un minuto. Costo: el latido de las TVs sigue reescribiendo
`tvs.json` esa semana, como hoy.

**Después de los 7 días — exportación.** `exportar_json.py` vuelca PostgreSQL a
los 13 JSON con el formato exacto de 6.x (probado con el mismo comparador de
ida y vuelta). Revertir es: solo lectura, exportar, arrancar 6.10. Tiempo:
minutos. Lo escrito después del corte viene de la base, así que también se
conserva.

**Lo que ninguna marcha atrás cubre:** columnas nuevas que no existen en el
formato JSON (`tamano_bytes`, `clave_evento`, correos de B4). Se documenta que
una reversión tardía pierde exactamente eso y nada más.

### 7.6 Contraseñas y sesiones: compatibilidad y revocación (punto 4 de Codex)

| Qué | Decisión en B3 | Por qué |
|---|---|---|
| Contraseñas `sha256(sal+pwd)` | Se migran tal cual con `algoritmo='sha256-sal'`. **Nadie cambia de contraseña el día del corte** | Bloquear a las recepcionistas la noche del corte es el peor resultado posible |
| Recifrado | B4: en el siguiente login correcto se verifica con sha256, se recifra con Argon2id y se cambia `algoritmo`. Se registra en auditoría | La transición dura lo que tarde cada persona en volver a entrar |
| Contraseña fija del código (QA-F03) | **Sigue existiendo en B3** para el bootstrap del `admin`. Se declara. B4 la elimina y obliga a rotar la del `admin` | B3 no toca autenticación por alcance |
| Sesiones vigentes | Se migran (`token_hash = sha256(token)`, misma `exp`); **no se revocan**. La cookie de cada quien sigue sirviendo | Igual: cero fricción el día del corte |
| Sesiones vencidas | No se migran | Basura |
| Revocación masiva | **Sí ocurre, pero en B4**, cuando entren el nuevo hash y la sesión por ámbito: ahí se cierra todo y cada quien vuelve a entrar una vez, avisado | Una sola interrupción, cuando trae algo a cambio |

### 7.5 Respaldo desde el día uno

El diseño de respaldo de la rama SQLite se adapta: `pg_dump --format=custom`
nocturno + `rclone` de medios, rotación local 14 días, remoto 90. Se instala
**antes** del corte y se prueba restaurando en limpio. Sin respaldo probado, no
hay corte.

---

## 8a. Medios: entrega y autorización (punto 5 de Codex)

**Decisión para B3: los archivos siguen en disco local, en las mismas rutas,
servidos por el mismo proceso.** Cambiar el almacenamiento y la entrega en el
mismo bloque que la base de datos duplica el riesgo de un corte que ya es el
más delicado de todo el plan.

Lo que B3 sí deja listo para B5:

- `contenido` tiene columna `ruta_almacen text` (NULL en B3 = ruta local
  derivada de `sucursal.clave/nombre_archivo`). B5 la llena al mover a S3.
- La URL pública no cambia nunca: `/videos/<clave>/<archivo>` es un contrato.
  Quien la sirva por detrás (proceso Python hoy, nginx o CDN mañana) es
  invisible para las TVs.

**Cómo se servirán los medios en B5 sin saltarse el aislamiento:**

| Opción | Aislamiento | Costo | Veredicto |
|---|---|---|---|
| Proceso Python (hoy) | Puede comprobar credencial de pantalla (B8) en cada petición | Compite con el panel por CPU y hilos | Se mantiene en B3 |
| nginx directo a disco | **Ninguno**: cualquiera con la URL descarga. Es lo que hay hoy (QA-G01) | Cero | **Rechazado como destino** |
| nginx con `X-Accel-Redirect` | La aplicación autoriza (credencial de pantalla, empresa, sucursal) y nginx entrega el archivo desde una ruta interna no expuesta | Una petición ligera a la app por archivo | **Propuesto para B5** |
| S3 compatible con URL firmada | La app firma por pantalla y por tiempo; el almacenamiento no sabe de empresas | Costo por transferencia; CDN opcional | Destino cuando el volumen lo justifique (P-008/D-007) |

Justificación de local frente a S3 ahora: cinco sucursales, decenas de
archivos, un VPS con disco de sobra y sin CDN. S3 resuelve un problema de
tráfico que hoy no existe y añade una dependencia externa y un costo mensual.
Se activa cuando haya evidencia (bitácora de B2 + estadísticas de B5) de que
el proceso compite por recursos, o cuando entre la segunda empresa.

**Prefijo por empresa desde ya:** las rutas nuevas que B5 cree en disco o en
S3 llevarán `<empresa.clave>/<sucursal.clave>/…`. Las actuales de LUMIN se
quedan donde están (contrato) y se registran con su ruta real en
`ruta_almacen`; una migración de archivos, si se decide, es un bloque aparte
con su propia reversión.

## 8b. Cola de trabajos en PostgreSQL (punto 6 de Codex)

B3 **no** ejecuta trabajos en segundo plano: la conversión con ffmpeg sigue
siendo síncrona dentro de `/api/subir`, como hoy. Pero crea la tabla para que
B5 mueva ahí la conversión sin otra migración:

```sql
CREATE TABLE trabajo (
  id             uuid PRIMARY KEY,
  empresa_id     uuid NOT NULL,
  tipo           text NOT NULL,                  -- 'convertir_video', 'miniatura'
  carga          jsonb NOT NULL,                 -- entrada del trabajo
  clave_idem     text,                           -- idempotencia: (empresa_id, tipo, clave_idem)
  estado         text NOT NULL DEFAULT 'pendiente'
                 CHECK (estado IN ('pendiente','en_curso','hecho','fallido','cancelado')),
  intentos       int  NOT NULL DEFAULT 0,
  max_intentos   int  NOT NULL DEFAULT 3,
  no_antes_de    timestamptz NOT NULL DEFAULT now(),
  tomado_por     text,                           -- identificador del trabajador
  tomado_en      timestamptz,
  latido_en      timestamptz,                    -- el trabajador lo renueva cada 30 s
  terminado_en   timestamptz,
  error          text,
  creado_en      timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX trabajo_idem ON trabajo (empresa_id, tipo, clave_idem) WHERE clave_idem IS NOT NULL;
CREATE INDEX trabajo_pendientes ON trabajo (no_antes_de) WHERE estado = 'pendiente';
```

Protocolo, escrito ahora para que B5 no lo improvise:

- **Reclamar:** `UPDATE trabajo SET estado='en_curso', tomado_por=$w, tomado_en=now(),
  latido_en=now() WHERE id = (SELECT id FROM trabajo WHERE estado='pendiente' AND
  no_antes_de <= now() ORDER BY creado_en FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *`.
  Una transacción, un trabajador gana, los demás no bloquean.
- **Idempotencia:** `clave_idem` = hash de (sucursal, nombre_archivo,
  tamaño). Reencolar lo mismo no crea dos trabajos.
- **Reintentos:** al fallar, `intentos+1`, `no_antes_de = now() + 2^intentos
  minutos`, `estado='pendiente'` mientras `intentos < max_intentos`; después
  `fallido` con `error`, visible en el panel (B6).
- **Recuperación tras caída del trabajador:** un barrido cada minuto devuelve
  a `pendiente` los `en_curso` con `latido_en` de hace más de 3 minutos. El
  trabajo se ejecuta otra vez; por eso la conversión escribe a un nombre
  temporal y renombra al final, igual que la cache del Roku.
- **Cancelar:** borrar el contenido pone sus trabajos pendientes en
  `cancelado`; un trabajador que termine un trabajo cancelado descarta el
  resultado.
- **Un trabajador**, como proceso `systemd` aparte, en el mismo VPS. Redis o
  Celery no se introducen sin una necesidad concreta.

## 8. Cambios en el VPS

| Qué | Detalle |
|---|---|
| PostgreSQL 16 | Paquete de la distribución, escucha solo en `localhost` |
| Base y roles | `lumin_tv`; rol `lumin_app` (sin superusuario, sin `BYPASSRLS`); rol `lumin_migracion` para Alembic y respaldos |
| Dependencias Python | `sqlalchemy`, `psycopg[binary]`, `alembic` en un venv en `/opt/lumin-tv/.venv`; el `systemd` apunta al Python del venv |
| Secretos | `/etc/default/lumin-tv` con `LUMIN_BASE_DATOS_URL`; nada en el código (QA-F03 sigue en pie para la contraseña del panel hasta B4, y se declara) |
| Despliegue | `lumin-deploy` gana un paso: `alembic upgrade head` antes de reiniciar. Se revisa ese script antes de tocarlo |

---

## 9. Decisiones que necesito de Adrián

| # | Decisión | Mi propuesta |
|---|---|---|
| D1 | Números de pantalla duplicados hoy en producción: `UNIQUE (empresa_id, numero)` no admite dos P6 | La pantalla más antigua conserva el número; la otra toma el siguiente libre. El informe de migración lista los cambios para avisar en la sucursal |
| D2 | Usuarios con `sucursales: []`: hacer explícita la concesión a todas | Sí, y B4 la revisa contigo usuario por usuario |
| D3 | Row Level Security | Activarla desde el día uno; el costo es mínimo y elimina una clase entera de fugas |
| D4 | Duración de la escritura doble | 7 días. Más tiempo prolonga las reescrituras de JSON; menos deja poca ventana para detectar algo raro |
| D5 | Ventana del corte | Noche entre semana, después del cierre de la última sucursal |
| D6 | Copia anonimizada de los JSON reales para el ensayo | La generas tú en el VPS con el script que entrego; la revisas antes de pasármela |

---

## 10. Reutilización del SaaS pausado

Repositorio `lumin-tv-saas`, commit **`b9c1f83`** (único), en
`C:\Users\adcueto\Claude\lumin-tv-saas`. Lo listado trae 36 pruebas que
pasaron contra PostgreSQL 16 en mi entorno; **Codex no las ha revisado ni
repetido**, así que cuentan como evidencia aportada, no como aprobación. Cada
pieza entra a `lumin-tv` como código nuevo del bloque que la use, con sus
pruebas adaptadas al arnés de aquí y sujeta a la misma revisión. No se copia a
ciegas: allí el dominio empezaba de cero y aquí hay llaves naturales que
respetar.

| Archivo en `lumin-tv-saas` | Destino en LUMIN TV | Bloque | Qué se adapta |
|---|---|---|---|
| `api/lumin_saas/modelos/tenancy.py` (164 líneas) | `lumin_datos/modelos.py` | **B3** | Añadir `id_dispositivo`, `numero`, `desfase_rotacion`, `clave` de sucursal, `contenido`, `lista`, `lista_elemento`, `programacion`, operación. Las llaves compuestas ya están |
| `api/lumin_saas/modelos/identidad.py` (306) | `lumin_datos/modelos.py` | **B3** (tablas) / B4 (uso) | `nombre_usuario` como llave natural; `algoritmo` de contraseña; `Sesion.empresa_id` opcional en la migración |
| `api/lumin_saas/servicios/permisos.py` (184) | `lumin_datos/contexto.py` | **B3** | `ActorEmpresa` → `Contexto`; añadir rol `pantalla` y `sistema`; la regla "vacío = nada" queda escrita pero B3 migra concesiones explícitas |
| `api/lumin_saas/db.py` (80) — `conexion_autonoma` | `lumin_datos/db.py` | **B3** | Igual; se suma el `SET LOCAL lumin.empresa_id` por transacción |
| `api/tests/test_permisos_y_aislamiento.py` (212) | `servidor/tests/test_dos_empresas.py` | **B3** | Base de la suite "dos empresas"; se cambia el arranque por el arnés del servidor real |
| `api/lumin_saas/seguridad/limites.py` (85) | `lumin_datos/limites.py` | B4 | Tal cual, ya resuelve el problema de la reversión del contador |
| `api/lumin_saas/seguridad/secretos.py` (100) | `servidor/seguridad.py` | B4 | Añadir verificación `sha256-sal` para la transición y recifrado a Argon2id |
| `api/lumin_saas/servicios/codigos.py` (220) | B4 | B4 | Tal cual: emisión, un solo uso arbitrado por `rowcount`, intentos en conexión autónoma |
| `api/lumin_saas/servicios/sesiones.py` (144) | B4 | B4 | Ámbitos `empresa`/`alta`; el de `plataforma` se deja fuera hasta el portal del propietario |
| `api/lumin_saas/servicios/autenticacion.py` (474) | B4 | B4 | **Parcial:** registro público NO (fuera de alcance); invitaciones, recuperación, acceso por código SÍ |
| `api/lumin_saas/correo/__init__.py` (108) | B4 | B4 | Adaptadores memoria/consola/SMTP tal cual |
| `api/tests/test_limites_y_concurrencia.py`, `test_registro_y_codigos.py` | B4 | B4 | Adaptar al arnés |
| `api/lumin_saas/rutas/*`, `plataforma.py`, `consola.py` | — | fuera | Portal del propietario y alta de superadministrador: pendientes por decisión |
| `.github/workflows/ci.yml` | `.github/workflows/ci.yml` | **B3** | PostgreSQL 16 como servicio, `alembic upgrade`/`downgrade`, pytest |

Lo que no se reutiliza de la rama `fase1-sqlite-respaldos`: su `registrar_tv`
(conserva el defecto de los números) y todo lo que asume SQLite. Su diseño de
respaldo sí, adaptado a `pg_dump` (§7.5).

---

## 11. Criterios de aceptación de B3

1. Las 30 rutas del panel y los 3 contratos responden **igual** que 6.10 sobre
   el mismo juego de datos: pruebas byte a byte, no "parecido".
2. Suite "dos empresas" en verde, con el guardián de SQL activo y RLS
   verificada sin `SET`.
3. Migración sobre copia sintética y sobre copia anonimizada: informe sin
   errores, comparación byte a byte de `playlist.json` por pantalla, ida y
   vuelta JSON → PG → JSON idéntica (salvo lo declarado en §7.4).
4. Reversión ensayada por las dos vías y cronometrada.
5. `alembic downgrade base` y vuelta a `head` en CI, contra PostgreSQL 16.
6. Concurrencia sobre PostgreSQL: 40 latidos + 20 turnos + 200 descargas
   simultáneos sin pérdida ni duplicado (mismos números que B2, ahora contra la
   base).
7. Respaldo `pg_dump` nocturno instalado y restaurado en limpio una vez.
8. La app Roku 5.1 y 5.2 pasan F13 contra 6.11 en la TV de pruebas.
9. Codex no tiene hallazgos abiertos.

---

## 12. Riesgos

| Riesgo | Mitigación |
|---|---|
| El rewire de ~40 puntos de acceso del monolito introduce regresiones sutiles | Pruebas de contrato byte a byte sobre fixtures que cubren cada rama de cada ruta; el diff de `servidor_lumin.py` se revisa ruta por ruta |
| PostgreSQL caído = sistema caído (hoy los JSON nunca "se caen") | `systemd` con dependencia y reinicio; las TVs siguen con caché (B1); alerta en la bitácora; el respaldo nocturno |
| Rendimiento del latido (20 pantallas × cada 4 s) | Es un `UPDATE` de una columna; medido en B2-SaaS a 836/s. Índice por `id_dispositivo` |
| RLS mal configurada bloquea todo | Prueba de arranque que falla si el rol tiene `BYPASSRLS` o si `SET` no surte efecto |
| Migrar contraseñas sha256 "perpetúa" QA-F03 | Es temporal y declarado: B4 recifra en el siguiente login y obliga a rotar la del admin inicial |
| El script de anonimización deja algo sensible | Lo revisa Adrián antes de compartir la copia; la copia vive solo en el entorno de pruebas y se borra al terminar |

---

## 13. Lo que pido para cerrar la revisión

- Las seis decisiones de §9.
- Objeciones de Codex al esquema (§3), en especial a `descarga_diaria` sin
  FK, a `sesion.empresa_id` nulo en migración, y a la política de §6.2.
- Confirmación de que el ensayo con copia anonimizada es aceptable dentro de
  D-006 ("sin alteración de datos reales").

Hasta entonces, **no escribo código de B3**.
