# QA — B1 R4, servidor e inventario, diseño B3 revisión 3

PARA: 01 — LUMIN TV · Desarrollo  
DE: 00 — LUMIN TV · Coordinación y QA  
BLOQUE: B1 R4 + B2 + diseño B3 revisión 3 · ce4716f  
ESTADO: B1 SIN OBJECIONES ESTÁTICAS ABIERTAS; B3 CON CORRECCIONES ACOTADAS

Fecha: 2026-09-16. Candidato exacto: `ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.
Comparación: `78306df3f81b53328cd7fbdd07b294d3b0a1c262..ce4716f07b1a14c98c7dc6a9a4d4494b6871d3c2`.
Revisor: Codex. Rama local de referencia: `modernizacion-diagnostico`; no se hizo fetch ni se verificó un run de GitHub Actions.

## Dictamen y límites

- **B1:** se cierran R3-B1-01 y R3-B1-02 en lógica ejecutada fuera del dispositivo. El arnés corre CacheTask real con disco/reloj/transferencia simulados. No sustituye F1–F21 en Roku: roUrlTransfer, cachefs, reproducción y eventos físicos siguen pendientes. App 5.2 build 60.
- **B2/inventario:** 21 pruebas pasan con pytest, incluidas las 13 anteriores y las 8 nuevas del inventario. INV-01 queda cerrado para los casos originales: ruta/archivos faltantes, JSON inválido, forma raíz equivocada, vacío explícito y alias inequívocos. No se ejecutó inventario sobre datos reales ni se aprobaron D1/D2.
- **B3:** los 21 ensayos pasan; quedan verificadas las correcciones anteriores de marcas pendientes, regeneración normal de sesiones y permisos del DDL mínimo. Eso no aprueba el esquema completo ni los nuevos recorridos de este informe. La implementación sigue pendiente de diseño corregido, decisiones y encargo.
- **No se emite APROBADO_QA global:** CI no verificado; hardware y producto B3 no probados. No hubo migración, despliegue, commit/push ni cambios en el producto.

## Evidencia ejecutada por Codex

| Control | Resultado | Alcance |
|---|---|---|
| `pytest servidor/tests -q` | **21 passed**, 15.70 s, 0 omitidas | Servidor real aislado, fixtures sintéticos; pytest 9.1.1, Python 3.12 |
| `pytest servidor/ensayos_b3 -q` | **21 passed**, 28.21 s, 0 omitidas | PostgreSQL **16.15** Windows local y psycopg **3.2.3**; incluye pg_dump/pg_restore |
| `python roku-app/pruebas/correr.py` | **35 comprobaciones, 0 fallos** | brs **0.47.6**, Node **24.18.1**; arnés sin modificar |
| BrighterScript **0.73.5** | **0 diagnósticos**, 8 archivos BRS/XML | ProgramBuilder, sin empaquetar/desplegar; listado en compilacion.json |
| Casos adicionales QA | Tres recorridos reproducidos | Autenticación y sesión con PG/servidor real sintético; publicación mediante modelo de archivos del contrato |

El candidato se extrajo mediante `git archive` en una carpeta aislada. El checkout permaneció en main, con los dos borrados de iconos preexistentes intactos. PostgreSQL escuchó solo en `127.0.0.1:55432` y **se detuvo al terminar**. No se usaron datos, credenciales ni conexiones de producción. El volcado/restauración ocurrió solo en bases sintéticas `lumin_ensayo*`.

Evidencia: [instrucciones y resultados](../evidencia/revision-r4-ce4716f/README.md), [servidor JUnit](../evidencia/revision-r4-ce4716f/servidor-resultados.xml), [B3 JUnit](../evidencia/revision-r4-ce4716f/b3-resultados.xml), [Roku](../evidencia/revision-r4-ce4716f/roku-resultados.txt), [compilación](../evidencia/revision-r4-ce4716f/compilacion.json), [casos adicionales](../evidencia/revision-r4-ce4716f/comprobaciones-adicionales.json).

## Correcciones requeridas del diseño

Las referencias de líneas corresponden al archivo `docs/coordinacion/13-diseno-B3-postgresql.md` del SHA revisado, disponible como [copia inmutable por SHA](../../arquitectura/referencias/13-diseno-B3-postgresql-rev3-ce4716f.md).

### B3-R3-01 · P1 · El orden de resolución rechaza las sesiones migradas

**Referencia:** §3.5, líneas 448–459. El paso 4 comprueba membresía con `empresa_id = gc('empresa_id')`; el paso 5 recién asigna `lumin.empresa_id`. Para una sesión migrada el contexto está vacío y `gc` devuelve NULL: el WHERE elimina la membresía válida y se devuelve 401. La política RLS permite verla por usuario; el problema es el filtro de la consulta.

**Reproducción:** añadí al DDL mínimo una tabla membresia sintética con la política escrita en el diseño y una fila válida. Con usuario conocido y empresa sin asignar: SELECT sin ese filtro devuelve 1; consulta literal del paso 4 devuelve 0; la misma consulta con la empresa heredada como parámetro devuelve 1. El ensayo `test_app_sesiones_y_login` actual no tiene tabla membresia ni ejecuta este paso.

**Cierre:** resolver el UUID de empresa heredada y comprobar la membresía contra ese parámetro antes de asignar el contexto; o definir otro orden seguro sin consulta circular. Añadir casos sesión migrada con membresía válida, sin membresía y con membresía en otra empresa. Mantener el filtro de vigencia/revocación de la sesión.

### B3-R3-02 · P1 · La reversión forzada puede resucitar una sesión revocada

**Referencia:** §7.6, líneas 796–797; coherencia con §7.3 líneas 693–695 y §7.4-9. La ruta normal que consulta PostgreSQL y filtra la copia quedó corregida. Pero la excepción permite forzar la reversión con el último sesiones.json si PostgreSQL está inaccesible. Una sesión puede revocarse después de esa exportación y antes de la caída. Usar el último archivo vuelve a habilitarla. Tampoco se puede asegurar una antigüedad ≤2 s durante caída, bloqueo o error del exportador: el intervalo de ejecución no garantiza frescura.

**Reproducción con servidor 6.10 real aislado:** exportar sesión válida → revocarla en PG → confirmar que el filtrado actual produce `{}` → restaurar el último espejo → `/api/yo` acepta la cookie otra vez. No se necesita una interrupción física de PG para demostrar el problema del archivo elegido por la excepción.

**Cierre:** mantener bloqueo si no puede comprobarse el estado final; si existe una vía de emergencia autorizada, esta debe cerrar todas las sesiones (archivo vacío escrito de forma segura) y declarar cualquier riesgo de pérdida de otros datos. Aplicar el mismo guardián de consistencia a todas las rutas de reversión, incluida la inmediata después del humo. Definir drenaje/terminación de transacciones en vuelo antes de la última verificación. D7 puede elegir conservar las vigentes verificadas o cerrar todas; no debe presentar como preservación de revocaciones una copia cuya vigencia no se pudo verificar.

### B3-R3-03 · P2 · Un trabajador atrasado puede borrar el resultado publicado

**Referencia:** §8b, líneas 903–915. El nombre versionado se deriva de destino/nombre/digest, por lo que dos posesiones del mismo trabajo comparten archivo. A escribe; vence su posesión; B escribe ese mismo archivo y publica `hecho`; A intenta actualizar, recibe 0 filas y, según el contrato, borra «su archivo versionado». Acaba de borrar el resultado vigente de B.

**Evidencia:** modelo determinista del intercalado con un archivo sintético: estado final `hecho`, archivo inexistente. Es una objeción al protocolo escrito para B5, no un fallo de trabajadores ya implementados.

**Cierre:** artefactos por posesión/intento con publicación atómica del puntero y limpieza de huérfanos que respete referencias; o un protocolo equivalente que impida borrar un artefacto compartido/publicado. Incluir pruebas A vencido/B publicado/A descartado y caída tras archivo antes de COMMIT. Corregir el contrato en B3; implementar trabajadores solo en su bloque autorizado.

### B3-R3-04 · P2 · Ajustar las afirmaciones de cobertura RLS

**Referencia:** §3.5, líneas 420–426 y `test_ensayo_rls.py:212`. El documento dice que el guardián verifica que ninguna tabla pertenezca a app/espejo; el test actual comprueba RLS y presencia de alguna política, pero no consulta el propietario. También afirma que cada celda de la matriz está en el DDL y se ejecuta; el DDL mínimo no incluye membresia, pantalla, lista_elemento ni las otras tablas completas. El README sí declara correctamente su alcance mínimo.

**Cierre:** añadir el control de propietarios con un caso negativo que lo haga fallar y ajustar la matriz para distinguir «ensayado» de «contrato para implementación». No requiere implementar ahora todo el esquema. No describir el login completo ni la matriz completa como probados con estos 21 ensayos. Esta observación procede de inspección del test y DDL, no de ejecución del esquema completo.

## Trabajo siguiente y decisiones

1. 01 corrige estos contratos y entrega nuevo SHA con pruebas adicionales acotadas. No necesita iniciar lumin_datos ni Alembic.
2. Es razonable preparar CI y el anonimizador en paralelo **como propuesta de trabajo**, sin convertir este informe en autorización de producción. El anonimizador debe acompañarse de inventario de campos, casos sintéticos y garantías de no modificar el origen; ejecutar/exportar datos reales corresponde a D6 y a Adrián.
3. CI: identificar SHA, run y jobs; ejecutar servidor, Roku, compilación y PG16. Exigir 0 errores y 0 skips inesperados; un job verde con los 21 ensayos omitidos no sirve. No usar credenciales productivas. CI mejora reproducibilidad; un workflow escrito por Desarrollo no sustituye revisión independiente del código y resultados.
4. Adrián mantiene D1–D7; D5/copia real conservan su secuencia acordada. Recomendación QA para D7: conservar sesiones anteriores solo cuando PG permita comprobar vigencia; emergencia sin esa comprobación, cerrar todas.
5. Validar F1–F21 con paquete extraído del **SHA exacto ce4716f**, build 60, o del nuevo SHA que se asigne. No extraer del main local ni usar una rama móvil como única identidad.

## Entrega y preservación

Este informe sucede al [informe 15](15-qa-R3-y-diseno-B3-rev2-78306df.md); no reescribe su evidencia. Se actualizan backlog.json y vistas derivadas en el repositorio canónico. Los archivos están preparados localmente, sin commit ni push. Este informe no se envió a otro chat automáticamente.
