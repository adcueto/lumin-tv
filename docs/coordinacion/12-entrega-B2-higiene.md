# Entrega B2 — Higiene del servidor actual (6.9 → 6.10)

Sigue la plantilla de `06-protocolo-y-qa.md`.

## Identidad

- ID: **B2** (plan en `10-diagnostico-y-plan-modernizacion.md`) · Revisión **R2**
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
| Números duplicados | `registrar_tv` | `indice = len(tvs)` | `max(indice) + 1`: no reutiliza mientras exista un número mayor en uso. Si se elimina la pantalla con el número más alto, ese número sí puede volver a asignarse; la unicidad garantizada llega con `UNIQUE (empresa_id, numero)` en B3 |

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
| `qa_caracterizacion.py` de Codex contra 6.10, **sin modificar** | Se detiene en el caso del 404 (`KeyError` en su línea 62): la entrada que asume ya no existe. **No completa la corrida** |
| Copia del script con `.get()` en esa línea, fuera del repositorio | 8 de 9 reproducidos; el 404 ya no se reproduce. Es una corrida de una copia ajustada, no del script original |
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
python -m venv .venv && .venv/bin/pip install -r tests/requirements.txt
.venv/bin/python -m pytest tests -q               # arbol de trabajo: 10 passed
.venv/bin/python tests/comparar_con_base.py        # base ea610d6 (6.9): 7 failed, 3 passed
.venv/bin/python tests/comparar_con_base.py <sha>  # cualquier otro commit
```

`comparar_con_base.py` extrae `servidor_lumin.py` del commit indicado con
`git show` a un directorio temporal y apunta el arnés ahí
(`LUMIN_SERVIDOR_BAJO_PRUEBA`). **No toca el checkout** y no usa `git stash`.
Imprime el SHA largo del commit y el SHA-256 de cada archivo.

## Despliegue y reversión (cuando se autorice)

Despliegue: el mismo de siempre, reemplazar `/opt/lumin-tv/servidor_lumin.py`
y `systemctl restart lumin-tv`. Sin migración, sin cambio de datos.

Reversión: volver a poner el `servidor_lumin.py` de `ea610d6` y reiniciar.
La carpeta `registro/` es inerte para 6.9. Tiempo estimado: un minuto (estimación, no medición).

## Operaciones

- Commit en `modernizacion-diagnostico`: realizado.
- Push: realizado desde la máquina del propietario.
- Despliegue al VPS: **NO realizado, no autorizado.**


---

## Revisión R2 — respuesta a `13-qa-B2-0c00f35.md` (Codex, 2026-09-16)

Codex ejecutó las diez pruebas con sus aserciones originales (diez pasan), más
tres comprobaciones adicionales propias (cierres y altas concurrentes, candado
anidado, 120/120 en playlist). No encontró fallo funcional. Los dos hallazgos
son de rigor de la evidencia y se **CONFIRMAN**.

| ID | Decisión | Qué cambió |
|---|---|---|
| B2-QA-01 [P2] la prueba de conexiones podía ocultar excepciones | **CONFIRMADO.** Descartaba `errores` y no exigía 120 resultados | `test_conexiones_simultaneas_no_se_rechazan` exige `errores == []`, `len(salidas) == 120` y las 120 en 200. Se quitó el `import pytest` sin uso |
| B2-QA-02 [P2] el procedimiento de línea base no volvía a 6.9 | **CONFIRMADO.** `git stash` no revierte un commit | Nuevo `tests/comparar_con_base.py`: extrae el servidor del commit con `git show` a un temporal y corre la misma suite sin tocar el checkout. Salida verificada aquí: contra `ea610d6…` (sha256 `143b444d…`) **7 fallaron, 3 pasaron**; contra el árbol (sha256 `28cf6b61…`) **10 pasaron** |

Precisiones documentales aplicadas en este mismo documento: "nunca reutiliza"
corregido a "no reutiliza mientras exista un número mayor"; la corrida del
script de caracterización se describe como lo que fue (el original se detiene;
el 8/9 es de una copia ajustada); los contadores miden descargas iniciadas; el
minuto de reversión es estimación. `tests/requirements.txt` declara `pytest`
para el entorno de QA.

Pendientes que este R2 **no** cierra, como indica Codex: CI no ejecutado (sin
remoto para Actions hasta que se configure), hardware Roku no probado, y los
hallazgos de B1 que se atienden en la R2 de B1 en este mismo commit.
