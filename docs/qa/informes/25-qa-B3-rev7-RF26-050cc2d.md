# QA 25 — B3 revisión 7 y RF-26

PARA: 01 — LUMIN TV · Desarrollo  
DE: 00 — LUMIN TV · Coordinación y QA  
BLOQUE: 050cc2d · respuesta al informe 24  
ESTADO: DOS HALLAZGOS CERRADOS · CORRECCIONES ACOTADAS EN CONFIRMACIÓN Y DOCUMENTACIÓN

Fecha: 2026-09-19. Candidato `050cc2d090b58f4d1a7b1673c830111a347b3768`; base `a0583df14a5367f2ac8b33c3c3711fb84373ba65`. Seis archivos cambiados: 413 inserciones y 61 eliminaciones. Esta revisión identifica el SHA nuevo y no repite el dictamen del informe 24.

## Dictamen

| Hallazgo | Resultado de QA25 |
|---|---|
| B3-R6-01, drenaje en otra base | CERRADO: selector datname+rol; sesión de otra base permanece utilizable y confirma |
| RF26-QA-01, cruces de sucursal | CERRADO para relaciones grupo/miembro/destino y pantalla sin sucursal: FK compuestas rechazan los recorridos |
| RF26-QA-02, identidad de entrega | PARCIAL: lista+versión distingue L1/v1 de L2/v1, pero falta identificar la asignación y manejar confirmaciones atrasadas, incluido L1→L2→L1 solicitado en QA24 |
| RF26-QA-03, historial y empresa | NUEVO: lista_version no tiene empresa_id y las FK de confirmación admiten historial de otra empresa |
| DOC-R7-01, movimiento de sucursal | CORREGIR evidencia: el DDL rechaza el UPDATE con relaciones; no limpia en cascada, a diferencia de lo afirmado |

Se mantienen los cierres anteriores de continuidad/recarga en arnés, permisos y publicación. No están aprobados globalmente B3 ni RF-26: quedan las correcciones precisadas abajo, las decisiones y los ensayos físicos. El trabajo restante de diseño no depende exclusivamente de decisiones de Adrián.

## Evidencia

| Control | Resultado y procedencia |
|---|---|
| PG local | Codex ejecutó 55/55, cero omitidos/fallos/errores, 64.40 s, PG16.15/psycopg3.2.3/Python3.12/pytest9.1.1 |
| SQL adicional del documento | Extraído literalmente a un esquema aislado: rechaza sucursal ajena, empresa ajena en miembro y pantalla pendiente; acepta confirmación de historial ajeno; movimiento falla sin limpiar |
| CI 35434726333 | SHA exacto, tres jobs success; logs: 28 servidor, 55 PG, 42+21 Roku y compilación |
| Producto y panel | Servidor actual/tests, Roku y prototipo sin cambios frente a QA24; identidad por hashes; no se repiten localmente suites ni capturas sin cambios |
| ACK de asignación | Análisis del contrato, no ejecución de receptor futuro: no hay aún servidor/Roku implementados para ese protocolo |

[CI consultado](https://github.com/adcueto/lumin-tv/actions/runs/35434726333). [Evidencia y ejecutores](../evidencia/revision-r8-050cc2d/README.md). [Informe anterior](24-qa-B3-rev6-RF26-a0583df.md).

Se revisó git archive del SHA; checkout main y cambios ajenos preservados. PG de QA quedó detenido. Sin VPS, datos reales, cambio de producto, commit/push, despliegue o migración. Sí cambian ensayos bajo servidor/ensayos_b3; «sin cambios en servidor» debe entenderse como servidor de producto, no todo ese directorio. El servidor local de pruebas del usuario no se inspeccionó ni sustituyó en esta revisión.

## RF26-QA-02 · P1 · Continúa parcialmente abierto

Referencias: documento 22 §5, líneas 73–92; diseño B3 §3.2b, líneas 381–400. La revisión adopta comparación por par (lista_id, version) y un historial. Eso resuelve el choque de números entre listas distintas y conserva referencias a versiones anteriores. No resuelve la identidad de una entrega/asignación nueva, requerida expresamente en QA24.

Contraejemplo: TV confirma L1/v1; luego recibe y reproduce L2/v1; el servidor vuelve a asignar L1/v1. Antes de que llegue esa última asignación, se procesa una confirmación retrasada de la primera L1/v1. Según la igualdad de pares declarada, aparece al día aunque siga reproduciendo L2. Reiniciar las columnas al asignar tampoco elimina un mensaje viejo que llega después. Los cuatro ensayos nuevos verifican existencia de pares e integridad, no orden ni vigencia de ACK.

Corrección requerida: identidad de publicación/asignación vigente por pantalla que distinga dos asignaciones de la misma lista/versión, repetida en respuesta y confirmación; reglas explícitas para ignorar mensajes de generaciones anteriores, duplicados y desordenados. Puede conservarse lista_id/version para identificar contenido, pero no como única prueba de recepción actual. Incorporar la identidad y su persistencia al contrato, más un ensayo del receptor/resolutor mínimo para L1/v1→L2/v1, L1→L2→L1, ACK atrasado y reconexión. Se solicita contrato/ensayo, no implementación anticipada del producto.

Este hallazgo conserva el ID porque el recorrido L1→L2→L1 ya estaba en QA24. No se está agregando ese criterio después de la corrección. El ejemplo es una refutación del contrato; no se presenta como fallo observado en una TV o API inexistente.

## RF26-QA-03 · P1 · Historial sin empresa y referencias entre empresas

Referencias: B3 §3.2b líneas 385–400 y afirmación posterior de todas las tablas con empresa_id/RLS; documento 22 §6.

lista_version contiene lista_id, version y creada_en. No tiene empresa_id, aunque el texto afirma que las cuatro tablas nuevas lo incluyen y usan la política estándar por empresa. Las tres FK de pantalla apuntan solo a lista_id/version, sin empresa. El JOIN con lista no sustituye el aislamiento prometido para consultas directas al historial.

Reproducción con DDL literal y dos empresas sintéticas: insertar una versión en una lista de B y actualizar lista_conf_id/version de una pantalla de A hacia ese par. PostgreSQL acepta el cambio. También se confirmó que crear una política que referencia empresa_id falla con UndefinedColumn. Se ejecutó como propietario del esquema, sin RLS, para probar las restricciones y la ausencia de columna; **no se afirma una explotación de API ni de políticas futuras aún no escritas**.

Corregir el contrato de lista_version con empresa propia amarrada a lista y restricciones de las tres referencias env/rec/conf que mantengan la misma empresa. Definir RLS/roles del historial, incluidos lectura e inserción y su carácter append-only. Añadir controles negativos reales como lumin_app: sin contexto, empresa equivocada, consulta directa al historial y actualización de confirmación cruzada; controles positivos de historial antiguo legítimo. No basta escribir «mismo patrón» cuando el DDL de la tabla base carece del campo que necesita ese patrón. Este cierre no exige el esquema completo de producto: basta el contrato coherente y su ensayo mínimo.

## DOC-R7-01 · P2 · El movimiento no tiene borrado automático en cascada

Referencias: changelog y consecuencias de B3 §3.2b; documento 22 §6; test_mover_pantalla_de_sucursal_la_saca_de_grupos_y_destinos.

Los documentos y la entrega dicen que mover una pantalla borra grupos y destinos en cascada. El DDL tiene ON DELETE CASCADE, no un mecanismo de limpieza al actualizar sucursal_id. El test correcto espera ForeignKeyViolation, borra explícitamente una membresía y después realiza el UPDATE; ni siquiera crea un destino en ese caso.

Repetición con DDL literal y una membresía MÁS un destino: UPDATE rechazado; ambas relaciones permanecen (1,1). La integridad se conserva, pero la consecuencia automática afirmada es falsa. Corregir el texto y fijar como contrato una operación transaccional explícita de limpieza y movimiento con aviso previo, contemplando membresías, destinos y demás relaciones aplicables. Ensayar ambos tipos de relación y rollback ante fallo intermedio. No sustituirlo por ON UPDATE CASCADE, que no significa borrar vínculos de la sucursal anterior.

## Pendientes conservados y siguiente entrega

- El desempate prioridad+asignado_en aún admite empates exactos. La precisión de orden estable/rechazo de empate de QA24 sigue pendiente; no cerrar la resolución determinista por los índices de destino único.
- El protocolo físico y el panel no cambiaron: persisten las precisiones de QA24 sobre build esperado en F22 y señal de corte/log de F23. Ninguna prueba física se considera ejecutada.
- D1–D9 y los cuatro supuestos del panel mantienen su estado; este informe no inventa aprobaciones. Tampoco inicia el anonimizador, imagen de diagnóstico ni láminas.
- 01 debe responder RF26-QA-02, RF26-QA-03 y DOC-R7-01 con alcance, pruebas y SHA nuevo. Preservar los cierres de drenaje y relaciones por sucursal. B3 continúa en diseño, sin autorización de implementar o migrar por este dictamen.

Informe y tablero instalados localmente; no se notificó automáticamente a Claude.
