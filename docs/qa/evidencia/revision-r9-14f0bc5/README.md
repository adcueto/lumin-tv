# Evidencia QA26 — 14f0bc5

Candidato exacto: 14f0bc51b5f7330a046d99ac870036747366c586, extraído con git archive. Base c42770f. Se conserva el checkout del propietario.

- b3-resultados.xml: ejecución independiente Codex, 61 pasan en 57.73 s, cero omitidos.
- adicionales-resultados.json: tres reproducciones sintéticas (env/rec 2/1,3/2,4/3; borrado 23502 en id; concurrencia 23505 como lumin_app).
- comprobaciones_adicionales.py: ejecutor de caracterización; éxito del script significa que reprodujo los defectos, no que los arregló.
- ci.json y ci-resumen.txt: CI del SHA exacto, 28 servidor/61 PG/42+21 Roku; compilación success en metadatos.
- identidad-producto.json: igualdad Git de servidor, tests de producto y Roku respecto a c42770f. hashes-candidato.json identifica los seis archivos modificados.

Para repetir: extraer candidato en carpeta `candidato` junto al script; dependencias pytest/psycopg3 y PostgreSQL16 en PATH. Crear un clúster exclusivo de QA en 127.0.0.1:55439 y definir LUMIN_ENSAYO_PG=postgresql://postgres@127.0.0.1:55439/postgres. Los ensayos destruyen/recrean lumin_ensayo: nunca usar una base compartida ni producción.

Ejecutar `python -m pytest candidato/servidor/ensayos_b3 -q -rs --junitxml=b3-resultados.xml` y después `python comprobaciones_adicionales.py`. Detener el clúster al terminar; Codex lo detuvo. Las fuentes completas/pgdata/dependencias no se incorporan a esta evidencia.

Los ensayos usan pantalla_e/lista_e mínimas. No prueban API ni reproductor futuros, ni el esquema completo B3. La anchura 33/33 es aportada por Claude; no se repitió aquí.
