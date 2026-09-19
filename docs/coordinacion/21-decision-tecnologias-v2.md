# Decisión — Tecnologías de LUMIN TV v2

Fecha: 2026-09-19 · Decide: Adrián · Propone: Claude · Registra: Claude

Adrián aprobó el par **FastAPI + React** para la API v2 (B5) y el panel (B6).
Con eso, la pila queda así. Nada de esta tabla autoriza a implementar un
bloque: cada uno sigue su encargo, su revisión de Codex y su autorización.

| Capa | Tecnología | Estado |
|---|---|---|
| Reproductor (TV) | BrightScript / SceneGraph en Roku; BrighterScript 0.73 para compilar; `brs` 0.47 para el arnés fuera del dispositivo | En uso (B1, B5a) |
| Base de datos | PostgreSQL 16 con Row Level Security y roles `lumin_migracion` / `lumin_app` / `lumin_espejo`; UUID; llaves compuestas `(id, empresa_id)` | Diseñado y ensayado (B3 rev. 4) |
| Acceso a datos | Python 3.12, psycopg 3, SQLAlchemy 2, Alembic; paquete `lumin_datos/` con repositorios y `Contexto` obligatorio | Decidido; se programa al aprobarse B3 |
| Servidor HTTP actual | Python estándar (`ThreadingHTTPServer`), 6.10.x | En uso hasta B5 |
| API v2 | **FastAPI + Pydantic** sobre uvicorn, detrás de nginx, servicio `systemd`; conserva las rutas 6.x para TVs y POS | **Aprobado 2026-09-19** (B5) |
| Panel web | **React 18 + TypeScript + Vite**, TanStack Query, CSS propio con los tokens de la marca (rosa `#EFAFC7`, dorado `#C8A96A`, tinta `#1F1F1F`, Poppins), instalable como PWA | **Aprobado 2026-09-19** (B6); láminas antes de código |
| Autenticación | Cookie `HttpOnly` con hash en base; Argon2id con recifrado gradual; permisos explícitos por sucursal; credencial por pantalla | Diseñado (B3/B4/B8) |
| Medios | Disco local servido por la app → nginx `X-Accel-Redirect` → S3 compatible solo con volumen que lo justifique | Decidido (B3 §8a) |
| Trabajos | Cola en PostgreSQL (`FOR UPDATE SKIP LOCKED`, posesión), un trabajador `systemd`; sin Redis ni Celery | Diseñado y ensayado (B3 §8b) |
| Pruebas y CI | pytest contra el servidor real; ensayos contra PostgreSQL; arnés `brs`; GitHub Actions con guardián de omitidos; Codex como QA | En uso |
| Operación | VPS Ubuntu, `systemd`, nginx con TLS, bitácora rotativa, `pg_dump` nocturno + `rclone` | En uso / previsto en B3 |

Fuera, a propósito: microservicios, colas externas, Docker en el VPS (solo
desarrollo y CI), y cualquier activación de una segunda empresa antes de B8.

## Consecuencias inmediatas

1. Las láminas del panel (B6) se diseñan como componentes React reutilizables
   y se presentan a Adrián antes de escribir código de interfaz.
2. El esqueleto de la API v2 se toma del SaaS pausado (`lumin-tv-saas`,
   commit `b9c1f83`); sus 36 pruebas cuentan como evidencia aportada hasta
   que Codex las repita.
3. El panel React se puede servir como archivos estáticos por el servidor
   actual, consumiendo la API que ya existe, antes del corte a PostgreSQL; el
   cambio a la API v2 es de conexión, no de interfaz. El panel viejo se queda
   en su ruta hasta que el nuevo esté aprobado.
