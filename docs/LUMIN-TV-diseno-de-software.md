# LUMIN TV — Diseño de software para escalar

*Documento de arquitectura · Julio 2026 · Preparado para Adrián (LUMIN Belleza)*

---

## 1. La respuesta corta a "¿cambiamos de lenguaje?"

No, y es importante entender por qué. El lenguaje de programación casi nunca es lo que impide escalar: Instagram, YouTube y Spotify sirvieron a cientos de millones de usuarios con Python en su corazón. Lo que sí limita el crecimiento de un sistema son su almacenamiento de datos, su estructura interna, la ausencia de pruebas y de respaldos, y el proceso con el que se despliegan cambios. Reescribir LUMIN TV en otro lenguaje hoy significaría de dos a cuatro meses de trabajo para terminar exactamente con las mismas funciones que ya tienes, estrenando errores nuevos en el camino — es el error clásico conocido como "la reescritura desde cero", y ha matado más productos que cualquier bug. La app de las pantallas, además, no tiene alternativa: Roku obliga a BrightScript, así que ese componente seguirá igual sin importar lo que hagamos del lado del servidor.

La estrategia correcta es una **evolución por fases**: conservar los contratos que ya funcionan (la URL de playlist que consultan las TVs y los endpoints /api/ que usan el panel y el POS) y modernizar por debajo, pieza por pieza, sin que la flota se entere jamás.

## 2. Dónde estamos y qué le duele al sistema actual

El sistema hoy es un monolito de Python puro (sin frameworks) con archivos JSON como base de datos, un panel web embebido como texto dentro del mismo archivo, la app BrightScript en las TVs, y un VPS único con nginx y systemd. Para el tamaño actual ha sido la decisión correcta: simple, sin dependencias, fácil de reemplazar con un solo archivo.

Sus límites reales, en orden de riesgo: los **archivos JSON** como base de datos (el incidente de las pantallas que pedían código otra vez nació ahí; el candado lo contuvo, pero una base de datos real lo elimina de raíz), la **ausencia de respaldos automáticos** (hoy un disco dañado en el VPS pierde contenido y configuración), el **panel de 2,000+ líneas en un solo archivo** (cada cambio visual es cirugía delicada, como el bug del botón Programar), la **falta de un entorno de pruebas** (los cambios se prueban en tu TV de casa, y el episodio del USB mostró el costo), y el hecho de que **los videos se sirven desde el mismo proceso** que atiende el panel y las TVs, lo que con 15-20 pantallas empezará a competir por recursos.

## 3. Arquitectura objetivo

```
  TVs Roku          Panel (PWA)         POS / Sistemas externos
 (BrightScript)   (Vue, móvil-primero)   (tickets → turnos)
      │                  │                     │
      └──────────────────┼─────────────────────┘
                         ▼
              nginx (HTTPS, tv.luminbelleza.com)
                         │
        ┌────────────────┼──────────────────┐
        ▼                ▼                  ▼
   API (FastAPI)   Archivos de video   Miniaturas/láminas
   validación,     servidos directo    generadas (Pillow)
   sesiones, roles      por nginx
        │
        ▼
   Base de datos (SQLite → PostgreSQL)
   pantallas · sucursales · usuarios · campañas
   turnos · contadores · programación
        │
        ▼
   Trabajador de medios (cola)
   ffmpeg: conversión, giro, calidad ligera
```

Los tres contratos sagrados que no cambian nunca, para que las TVs y el POS sigan funcionando sin tocarse: `GET /playlist.json?id=...` con su respuesta actual (incluidos `pendiente`, `comando` y `turno`), `POST/PUT /api/turno` con el cuerpo que ya usa el POS, y las URLs de video `/videos/<sucursal>/<archivo>`.

## 4. Plan por fases

**Fase 1 — Cimientos (1-2 semanas, riesgo bajo, se puede hacer ya).** Migrar los JSON a **SQLite**: es una base de datos real (transacciones, integridad, imposible corromperla con escrituras simultáneas) que vive en un solo archivo, no requiere instalar ningún servidor y Python la trae integrada. Un script de migración lee tus JSON actuales y llena la base una sola vez. Al mismo tiempo: **respaldo automático nocturno** (un cron que empaqueta base de datos + videos y lo sube a un almacenamiento externo — Backblaze B2 o similar cuesta centavos), y **bitácora de errores** a archivo para diagnosticar sin adivinar. Este paso elimina la categoría entera de bugs de concurrencia y te da paracaídas ante desastres. El resto del código sigue igual.

**Fase 2 — Estructura profesional (3-4 semanas, cuando la Fase 1 esté estable).** Reemplazar el servidor artesanal por **FastAPI** (Python moderno): validación automática de todo lo que entra, manejo de sesiones probado, y documentación OpenAPI generada sola — esta última te da gratis la página de referencia que le entregas al desarrollador del POS en lugar de explicarle los contratos por WhatsApp. Separar el panel a un **frontend Vue** independiente, diseñado móvil-primero (se acaban los bugs de "en el celular se ve feo"), organizado en componentes chicos en lugar de un archivo gigante. El servidor viejo y el nuevo pueden convivir tras nginx durante la transición, endpoint por endpoint.

**Fase 3 — Escala real (cuando pases de ~15 pantallas o vendas publicidad en serio).** PostgreSQL en lugar de SQLite si hay múltiples procesos; los videos a **almacenamiento de objetos con CDN** (Cloudflare R2: los videos se sirven desde servidores cercanos a cada sucursal y tu VPS deja de cargar ese peso — este es el verdadero botón de escala para el problema del internet lento); una **cola de trabajo** para que ffmpeg procese subidas sin bloquear al servidor; despliegue con **Docker** y dos entornos: *staging* con una TV canaria (tu TV de casa, formalizada) que recibe cada versión 48 horas antes que la flota; y **monitoreo** externo que te avisa por Telegram/correo si el servidor o una sucursal se caen, antes de que te lo cuente una empleada.

## 5. Riesgos y reglas del camino

Lo que no hay que hacer: reescribir todo de golpe, cambiar de lenguaje por moda, o agregar tecnología que nadie del equipo pueda operar un domingo a las 9 pm con una sucursal en negro. Cada fase debe entrar a producción completa y estable antes de abrir la siguiente, y toda migración necesita marcha atrás documentada (los JSON originales se conservan congelados hasta un mes después de la migración a SQLite).

¿Cuándo sí consideraría otro lenguaje? Si algún día contratas un equipo de desarrollo cuya experiencia esté en otro stack (TypeScript/Node sería el candidato natural, porque el panel ya vive en JavaScript), o si apareciera un requisito de rendimiento que Python genuinamente no alcance — escenario improbable para este dominio incluso con cientos de pantallas. La decisión sería entonces de equipo, no de tecnología.

## 6. Recomendación

Ejecutar la Fase 1 ahora: es corta, de bajo riesgo, y ataca los dos miedos legítimos que este proyecto ya vivió en carne propia (corrupción de datos y ausencia de respaldos). Evaluar la Fase 2 cuando el negocio de publicidad arranque, porque la documentación automática del API y un panel mantenible valdrán dinero en ese momento. La Fase 3 se activa con el crecimiento, no antes: sobre-construir hoy sería pagar por escala que aún no existe.
