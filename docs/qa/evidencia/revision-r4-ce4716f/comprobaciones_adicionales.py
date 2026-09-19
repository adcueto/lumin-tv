"""QA independiente de contratos escritos; usa SOLO el cluster sintético local.
No implementa B3. Ejecutar después de la suite del candidato.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'servidor/ensayos_b3'))
import psycopg
from comun import preparar_base, dsn_admin, dsn_rol, contexto, EMPRESA_A, USUARIO_1
from test_ensayo_sesiones import Servidor, migrar_sesiones, regenerar_sesiones, revocar_en_b3, token_de, valida

assert os.environ['LUMIN_ENSAYO_PG'] == 'postgresql://postgres@127.0.0.1:55432/postgres'
preparar_base()
resultados = {}

# Extensión mínima del DDL de ensayo: membresia no existe en el candidato.
# Política y orden de consulta copiados del contrato escrito §3.5.
with psycopg.connect(dsn_rol('lumin_migracion')) as c:
    c.execute('CREATE TABLE membresia (usuario_id uuid, empresa_id uuid)')
    c.execute('ALTER TABLE membresia ENABLE ROW LEVEL SECURITY')
    c.execute('GRANT SELECT ON membresia TO lumin_app')
    c.execute("CREATE POLICY membresia_app ON membresia FOR SELECT TO lumin_app USING (empresa_id = lumin.gc('empresa_id')::uuid OR usuario_id = lumin.gc('usuario_id')::uuid)")
    c.execute('INSERT INTO membresia VALUES (%s,%s)', (USUARIO_1, EMPRESA_A))
with psycopg.connect(dsn_rol('lumin_app')) as c:
    contexto(c.cursor(), usuario=USUARIO_1)
    visibles = c.execute('SELECT count(*) FROM membresia').fetchone()[0]
    literal = c.execute("SELECT 1 FROM membresia WHERE usuario_id = lumin.gc('usuario_id')::uuid AND empresa_id = lumin.gc('empresa_id')::uuid").fetchall()
    parametrizada = c.execute("SELECT 1 FROM membresia WHERE usuario_id = lumin.gc('usuario_id')::uuid AND empresa_id = %s", (EMPRESA_A,)).fetchall()
    assert visibles == 1 and literal == [] and parametrizada == [(1,)]
    resultados['B3-R3-01'] = {'membresias_visibles': visibles, 'consulta_orden_documentado': len(literal), 'consulta_empresa_parametrizada': len(parametrizada)}

# §7.6: la instantánea previa al logout vuelve a aceptarse si se fuerza la
# reversión sin comprobar el estado final de PostgreSQL. No imprime tokens.
with Servidor() as s:
    cookie = s.login()
    congelado = s.json('sesiones.json')
    migrar_sesiones(congelado)
    ultimo_espejo = regenerar_sesiones(congelado)
    revocar_en_b3(token_de(cookie))
    vigente_pg = regenerar_sesiones(congelado)
    s.modulo.escribir_json(str(s.dir / 'sesiones.json'), ultimo_espejo)
    aceptada = valida(s, cookie)
    assert vigente_pg == {} and aceptada
    resultados['B3-R3-02'] = {'revocada_en_pg': True, 'aceptada_por_610_con_ultimo_espejo': aceptada}

# §8b: modelo de intercalado de archivos, NO implementación de trabajadores.
with tempfile.TemporaryDirectory(prefix='lumin-qa-publicacion-') as d:
    artefacto = Path(d) / 'promo.digest8.mp4'
    artefacto.write_bytes(b'contenido sintetico')  # A escribe y pierde posesión
    artefacto.write_bytes(b'contenido sintetico')  # B escribe la misma versión
    estado = {'posesion': 'B', 'estado': 'hecho', 'resultado': str(artefacto)}
    filas_actualizadas_por_a = int(estado['posesion'] == 'A' and estado['estado'] == 'en_curso')
    if filas_actualizadas_por_a == 0:
        artefacto.unlink()  # descarte prescrito para el trabajador atrasado A
    assert estado['estado'] == 'hecho' and not artefacto.exists()
    resultados['B3-R3-03'] = {'modelo_contrato': True, 'estado': estado['estado'], 'archivo_existe': artefacto.exists()}

(BASE / 'comprobaciones-adicionales.json').write_text(json.dumps(resultados, indent=2), encoding='utf-8')
print(json.dumps(resultados, indent=2))
