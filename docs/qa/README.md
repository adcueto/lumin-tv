# QA de LUMIN TV

- [Último informe: 14f0bc5](informes/26-qa-B3-rev8-RF26-14f0bc5.md).
- [Evidencia R9 reproducida por Codex](evidencia/revision-r9-14f0bc5/README.md).
- [Informe previo: 050cc2d](informes/25-qa-B3-rev7-RF26-050cc2d.md).
- [Evidencia R8 reproducida por Codex](evidencia/revision-r8-050cc2d/README.md).
- [Informe previo: a0583df](informes/24-qa-B3-rev6-RF26-a0583df.md).
- [Evidencia R7 reproducida por Codex](evidencia/revision-r7-a0583df/README.md).
- [Informe previo: 3a1eaf9](informes/23-qa-B3-rev5-B5a-R2-3a1eaf9.md).
- [Evidencia R6 reproducida por Codex](evidencia/revision-r6-3a1eaf9/README.md).
- [Informe previo: 1f7782e](informes/22-qa-B3-rev4-B5a-1f7782e.md).
- [Evidencia R5 reproducida por Codex](evidencia/revision-r5-1f7782e/README.md).
- [Informe previo: ce4716f](informes/19-qa-B1-R4-B3-rev3-ce4716f.md).
- [Evidencia R4 reproducida por Codex](evidencia/revision-r4-ce4716f/README.md).
- [Informe anterior: 78306df](informes/15-qa-R3-y-diseno-B3-rev2-78306df.md).
- [Revisión previa: 5c96845](informes/14-qa-R2-y-diseno-B3-5c96845.md).
- [B2 inicial](informes/13-qa-B2-0c00f35.md) y [B1 inicial](informes/12-qa-B1-ceadf1d.md).
- [Evidencia R3: resultados](evidencia/revision-r3-78306df/resultados-candidato.json) y [manifiesto de archivos revisados](evidencia/revision-r3-78306df/hashes.json).

Los informes y resultados se conservaron byte a byte. Sus rutas históricas indican dónde se ejecutaron. La consolidación no ejecuta nuevamente esas pruebas ni cambia el dictamen.

Se incluyen solo archivos raíz de resultados/manifiestos/ejecutores de las revisiones R2/R3 y la caracterización inicial. Se excluyen fuentes extraídas candidato/base, __pycache__, medios y temporales: las fuentes se recuperan por SHA desde Git. Los hashes de esos árboles permiten comprobar identidad.

Los revisar.py conservan su versión original: al ejecutarlos generan carpetas junto a sí mismos. Para repetir QA, copiar el ejecutor a un directorio aislado fuera del árbol de producto y comprobar REPO/SHA antes de ejecutar extraer y candidato/base. No commitear sus árboles generados.
