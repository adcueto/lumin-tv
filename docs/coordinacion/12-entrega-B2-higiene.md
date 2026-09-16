# Entrega B2 — Higiene del servidor actual (6.9 → 6.10)

Sigue la plantilla de `06-protocolo-y-qa.md`.

## Identidad

- ID: **B2** (plan en `10-diagnostico-y-plan-modernizacion.md`) · Revisión R1
- Responsable: Claude (desarrollo) · Revisa: Codex
- Fecha: 2026-09-16
- Raíz: `lumin-tv` · Rama: `modernizacion-diagnostico`
- SHA base: `ea610d6` (main) · SHA candidato: el commit de esta entrega
- Estado: **ENTREGADO A QA. Sin aprobar.**

## Alcance

**Dentro:** cambios de riesgo mínimo sobre `servidor/servidor_lumin.py` que
mejoran la operación de hoy sin tocar contratos ni persistencia:

1. Bitácora de errores a archivo con rotación.
2. Cuatro carreras cerradas (`crear_sesion`, `cerrar_sesion`, `crear_usuario`,
   `marcar_girado`).
3. Cola de conexiones de 5 a 64.
4. QA-F04, parte inmediata: un 404 ya no cuenta como reproducción.
5. Prevención de nuevos números de pantalla duplicados (los dos "P6").
6. Primera suite de pruebas automatizadas del servidor, contra el servidor
   real por HTTP.

**Fuera, y declarado:** permisos (F01/F02/F03 → B4), credencial por pantalla
(G01 → B8), idempotencia de turnos (G02 → B5), reasignar los números ya
duplicados en producción (decisión de producto, B5), y cualquier cambio de
base de datos (B3). Los JSON se quedan como están.

## Archivos

| Archivo | Cambio |
|---|---|
| `servidor/servidor_lumin.py` | 2,569 → 2,646 líneas. Detalle abajo |
| `servidor/tests/arnes.py` | **Nuevo.** Levanta el servidor real en un directorio temporal, puerto libre, hilos reales |
| `servidor/tests/test_b2_higiene.py` | **Nuevo.** 10 pruebas: 7 reproducen defectos, 3 protegen contratos |
| `servidor/tests/conftest.py` | **Nuevo.** Ruta del arnés |

### Cambios en `servidor_lumin.py`, uno por uno

| Qué | Dónde | Antes | Después |
|---|---|---|---|
| Bitácora | `_abrir_bitacora()`, `bitacora` | Fallos en `except: pass`; errores del servidor solo a consola | `registro/lumin.log`, hora de Querétaro, 5 × 2 MB rotativos. `handle_error`, miniaturas fallidas y el alta del admin inicial quedan registrados |
| Carrera en logins | `crear_sesion` | Leer-modificar-escribir fuera del candado | Bajo `CANDADO` |
| Carrera en cierre | `cerrar_sesion` | Ídem | Bajo `CANDADO` |
| Carrera en altas | `crear_usuario`, `usuarios()` | Ídem | Bajo `CANDADO` |
| Carrera en giro | `marcar_girado` | Ídem | Bajo `CANDADO` |
| Cola de conexiones | `ServidorSilencioso` | `request_queue_size` = 5 (valor por defecto) | 64, más `daemon_threads` |
| 404 contado | `do_GET /videos/` | Contaba antes de comprobar el archivo | Solo cuenta si el archivo existe. **Sigue siendo conteo de descargas iniciadas, no de reproducciones confirmadas** |
| Números duplicados | `registrar_tv` | `indice = len(tvs)` | `max(indice) + 1`: nunca reutiliza |

## Contratos

Sin cambios. `GET /playlist.json`, `POST/PUT /api/turno` y `/videos/…`
responden igual; hay dos pruebas que lo exigen (`test_contrato_playlist_intacto`,
`test_contrato_turno_intacto`). La app Roku 5.1 y la 5.2 funcionan igual contra
6.9 y 6.10.

## Comportamiento antes / después — con números

Las siete pruebas de defecto **fallan contra 6.9 y pasan contra 6.10**. Esto es
lo que se observó contra 6.9, en este entorno:

| Prueba | Contra 6.9 | Contra 6.10 |
|---|---|---|
| 30 `marcar_girado` simultáneos | **sobreviven 8 de 30** (22 marcas perdidas: 22 videos saldrían de cabeza) | 30 de 30 |
| 40 logins simultáneos | conexiones reiniciadas por la cola de 5; las que entran, pierden sesiones | 41 sesiones, todas sirven |
| 20 altas de usuario simultáneas | se pisan | 20 de 20 |
| 120 conexiones a la vez | **8 rechazadas** (`Connection reset`, `TimeoutError`) | 0 rechazadas |
| 2 × GET de un video inexistente | 404 y **contador en 2** | 404 y sin contador |
| Baja de una pantalla intermedia + alta nueva | números `1,2,4,5,6,6` | `1,2,4,5,6,7` |
| Error registrado | sin archivo | `registro/lumin.log` |

## Migraciones

No aplica. No cambia ningún archivo de datos. Se crea la carpeta `registro/`
al arrancar.

## Verificación

Entorno: Python 3.11.15, contenedor aislado, datos sintéticos.
Comando: `cd servidor && python -m pytest tests -q`.

| Prueba | Resultado |
|---|---|
| Suite B2 contra 6.9 | 7 fallaron, 3 pasaron (las de contrato) — **reproducción de los defectos** |
| Suite B2 contra 6.10 | **10 pasaron**, tres corridas seguidas (5.9 s, 5.9 s, 6.5 s), sin intermitencia |
| `qa_caracterizacion.py` de Codex contra 6.9 | 9 de 9 reproducidos (coincide con `qa-resultados.json`) |
| `qa_caracterizacion.py` de Codex contra 6.10 | 8 de 9 reproducidos; `contador-404-duplicado` **ya no se reproduce** (ver nota) |
| `py_compile` | sin errores |

**Nota sobre el script de Codex.** Contra 6.10 el script original se detiene
en su línea 62 con `KeyError: 'missing.mp4'`, porque asume que el 404 crea la
entrada del contador y ahora no la crea. No modifiqué el script, como pide
`09-auditoria-codigo.md`. Para verificar los otros ocho casos usé una copia
con `.get()` en esa línea, fuera del repositorio. Codex decidirá si tolera la
ausencia en su herramienta.

El SHA-256 del `servidor_lumin.py` 6.9 en este entorno (`143b444d…`) no
coincide con el del informe de Codex (`6eae0c89…`): es el mismo commit
`ea610d6`, la diferencia son los finales de línea del checkout en Windows.

## No ejecutado

- Producción: no se tocó. `sudo lumin-deploy` no se ejecutó.
- Carga sostenida (horas) y consumo de memoria: solo ráfagas cortas.
- ffmpeg real: el arnés lo desactiva (`FFMPEG = None`); la bitácora de
  miniaturas fallidas se revisó por lectura, no por ejecución.

## Riesgos que QA debe intentar refutar

1. `usuarios()` ahora toma el candado; se llama desde `verificar_credenciales`
   y `usuario_de_token`. `CANDADO` es un `RLock`, así que la reentrada desde
   `crear_usuario` es segura, pero conviene intentar un interbloqueo con
   llamadas anidadas.
2. `max(indice) + 1` respeta números existentes: **no repara** los duplicados
   que ya hay en producción. Dos pantallas con el mismo número siguen
   compartiendo desfase de rotación hasta B5.
3. La cola de 64 no cambia el número de hilos: cada petición sigue abriendo
   un hilo. Con 20 pantallas es irrelevante; con 200 no lo sería.
4. La bitácora escribe en `BASE/registro/`. Si el usuario del servicio no
   tuviera permiso, se degrada a consola sin fallar. Verificar permisos en
   `/opt/lumin-tv` antes del despliegue.

## Instrucciones de validación

```bash
cd servidor
python -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest tests -q          # esperado: 10 passed
git stash -- servidor_lumin.py               # (opcional) volver a 6.9
.venv/bin/python -m pytest tests -q          # esperado: 7 failed, 3 passed
git stash pop
```

## Despliegue y reversión (cuando se autorice)

Despliegue: el mismo de siempre, reemplazar `/opt/lumin-tv/servidor_lumin.py`
y `systemctl restart lumin-tv`. Sin migración, sin cambio de datos.

Reversión: volver a poner el `servidor_lumin.py` de `ea610d6` y reiniciar.
La carpeta `registro/` es inerte para 6.9. Tiempo: un minuto.

## Operaciones

- Commit en `modernizacion-diagnostico`: realizado.
- Push: realizado desde la máquina del propietario.
- Despliegue al VPS: **NO realizado, no autorizado.**
