# LUMIN TV — Plataforma de señalización digital

Sistema de pantallas para los salones LUMIN Belleza (Querétaro, MX):
publicidad administrada por sucursal, turnos en pantalla, campañas
programadas y control remoto desde el celular.

## Componentes
- **roku-app/** — App BrightScript/SceneGraph para las TVs Roku
  (canal "LUMIN Belleza TV" en la tienda). v5.2 (5.1 en la flota)
- **servidor/** — Servidor Python (stdlib) con panel web PWA, API de
  turnos para el POS, campañas y estadísticas. v6.10. Corre en
  /opt/lumin-tv del VPS (systemd `lumin-tv` + nginx en
  tv.luminbelleza.com).
- **vigilante/** — Script para Raspberry Pi (uno por sucursal):
  enciende las TVs y abre la app en horario vía Roku ECP. v1.0
- **docs/** — Diseño de software y plan de evolución por fases.

## Despliegue rápido
- Servidor: reemplazar `/opt/lumin-tv/servidor_lumin.py` y
  `systemctl restart lumin-tv`.
- App: empaquetar zip de `roku-app/` e instalar por modo desarrollador,
  o subir el .pkg al portal de Roku como actualización del canal.
- Vigilante: ver `vigilante/README-instalacion.md`.

## Sucursales
home · plaza-de-la-mujer · juriquilla · campanario · plaza-victoria
