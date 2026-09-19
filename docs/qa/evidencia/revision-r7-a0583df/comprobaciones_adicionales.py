"""QA del contrato nuevo: base objetivo frente a otra base, y DDL RF-26 exacto."""
import os,sys,json,re,uuid
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q/'servidor/ensayos_b3'))
import psycopg
from comun import preparar_base,dsn_rol,EMPRESA_A
from test_ensayo_sesiones import drenar_lumin_app,reabrir_entrada_lumin_app
assert os.environ['LUMIN_ENSAYO_PG']=='postgresql://postgres@127.0.0.1:55432/postgres'
preparar_base();out={}
# PostgreSQL local de QA solamente. 'postgres' es otra base del cluster desechable.
other_dsn=psycopg.conninfo.conninfo_to_dict(dsn_rol('lumin_app'));other_dsn['dbname']='postgres'
otra=psycopg.connect(**other_dsn)
target=psycopg.connect(dsn_rol('lumin_app'))
try:
 drenar_lumin_app(timeout_s=0.1)
 for nombre,c in [('objetivo',target),('otra_base',otra)]:
  try:c.execute('SELECT 1');out[nombre]='sobrevive'
  except psycopg.OperationalError:out[nombre]='terminada'
 assert out=={'objetivo':'terminada','otra_base':'terminada'}
finally:
 target.close();otra.close()
 with psycopg.connect(dsn_rol('lumin_migracion'),autocommit=True) as c:reabrir_entrada_lumin_app(c)

# Contrato de las tablas relevantes, extraído literalmente del diseño (sin producto).
doc=(Q/'docs/coordinacion/13-diseno-B3-postgresql.md').read_text(encoding='utf-8')
sql=[]
for name in ['empresa','sucursal','pantalla','lista']:
 sql.append(re.search(r'CREATE TABLE '+name+r' \([\s\S]*?\n\);',doc).group(0))
section=doc.split('### 3.2b ',1)[1].split('### 3.3 ',1)[0]
sql.append(re.search(r'```sql\n([\s\S]*?)```',section).group(1))
ddl='\n'.join(sql)
(Q/'ddl-rf26-extraido.sql').write_text(ddl,encoding='utf-8')
with psycopg.connect(dsn_rol('lumin_migracion'),autocommit=True) as c:
 c.execute('CREATE SCHEMA qa_rf26')
 c.execute('SET search_path=qa_rf26,public')
 c.execute(ddl)
 E,A,B,T,P,L1,L2,G=[uuid.uuid4() for _ in range(8)]
 c.execute("INSERT INTO empresa(id,clave,nombre) VALUES (%s,'qa','QA')",(E,))
 c.execute("INSERT INTO sucursal(id,empresa_id,clave,nombre) VALUES (%s,%s,'a','A'),(%s,%s,'b','B')",(A,E,B,E))
 c.execute("INSERT INTO pantalla(id,empresa_id,sucursal_id,id_dispositivo,numero,aprobada) VALUES (%s,%s,%s,'tv-b',1,true),(%s,%s,NULL,'pendiente',2,false)",(T,E,B,P,E))
 c.execute("INSERT INTO lista(id,empresa_id,sucursal_id,clave,nombre) VALUES (%s,%s,%s,'l1','L1'),(%s,%s,%s,'l2','L2')",(L1,E,A,L2,E,B))
 c.execute("INSERT INTO grupo_pantallas(id,empresa_id,sucursal_id,nombre) VALUES (%s,%s,%s,'Grupo A')",(G,E,A))
 c.execute('INSERT INTO grupo_pantalla_miembro(grupo_id,pantalla_id,empresa_id) VALUES (%s,%s,%s)',(G,T,E))
 c.execute('INSERT INTO lista_destino(id,empresa_id,lista_id,grupo_id) VALUES (%s,%s,%s,%s)',(uuid.uuid4(),E,L2,G))
 c.execute('INSERT INTO lista_destino(id,empresa_id,lista_id,pantalla_id) VALUES (%s,%s,%s,%s)',(uuid.uuid4(),E,L1,T))
 c.execute('INSERT INTO lista_destino(id,empresa_id,lista_id,pantalla_id) VALUES (%s,%s,%s,%s)',(uuid.uuid4(),E,L1,P))
 out['rf26_constraints']={'grupo_A_admite_tv_B':True,'grupo_A_admite_lista_B':True,'tv_B_admite_lista_A':True,'tv_sin_sucursal_admite_destino':True}
 versions=c.execute('SELECT version FROM lista ORDER BY nombre').fetchall()
 out['versiones_de_listas_distintas']=[r[0] for r in versions]
 assert out['versiones_de_listas_distintas']==[1,1]
(Q/'adicionales-resultados.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
