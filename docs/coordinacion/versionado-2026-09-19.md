# Versionado de coordinación y QA

PARA: 01 — LUMIN TV · Desarrollo  
DE: 00 — LUMIN TV · Coordinación y QA  
BLOQUE: publicación de documentación hasta QA25  
ESTADO: COMMIT PREPARADO PARA PUSH POR INSTRUCCIÓN DEL PROPIETARIO

Fecha: 2026-09-19. Adrián solicitó explícitamente commit y push para versionar y preparar pruebas de servidor, con adrianjpca@gmail.com. Esta instrucción autoriza la publicación Git de este paquete documental. La cuenta autenticada comprobada es adcueto, con ese correo.

- Rama de destino: modernizacion-diagnostico.
- Padre del commit: 050cc2d090b58f4d1a7b1673c830111a347b3768.
- Contenido: entradas de agentes, requisitos, backlog/semáforo, informes QA12–25, evidencia acotada, referencias y antecedentes de investigación/coordinación.
- Código de producto y CI: idénticos al padre; el nuevo commit incorpora documentación y evidencia.
- Se preserva la versión de docs/coordinacion/10-diagnostico-y-plan-modernizacion.md de la rama, frente a una copia local más antigua. La imagen b1-propuesta-visual.png ya coincide y no requiere cambio.
- Los dos borrados locales de iconos Roku no se incluyen.

La preparación usa un worktree aislado. El checkout principal permanece en main; los archivos locales previos se conservan. Las frases de los informes históricos «sin commit/push» describen su revisión original; este registro documenta la publicación posterior solicitada. El hash y el estado efectivo de publicación se consultan en Git/GitHub, no se anticipan aquí.

El último dictamen sigue siendo [QA25](../qa/informes/25-qa-B3-rev7-RF26-050cc2d.md). Versionar este paquete no cierra RF26-QA-02/03 ni DOC-R7-01. Tampoco ejecuta un despliegue, migración o prueba en el servidor del usuario. Para ensayos usar la rama y SHA identificados, conservando las condiciones del [semáforo](18-semaforo.md).
