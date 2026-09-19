"""QA del DDL literal rev7, solo en PostgreSQL desechable."""
import os,sys,json,re,uuid
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q/'servidor/ensayos_b3'))
import psycopg
from comun import preparar_base,dsn_rol
assert os.environ['LUMIN_ENSAYO_PG']=='postgresql://postgres@127.0.0.1:55432/postgres'
preparar_base()
doc=(Q/'docs/coordinacion/13-diseno-B3-postgresql.md').read_text(encoding='utf-8')
ddl='\n'.join(re.search(r'CREATE TABLE '+n+r' \([\s\S]*?\n\);',doc).group(0) for n in ['empresa','sucursal','pantalla','lista'])
section=doc.split('### 3.2b ',1)[1].split('### 3.3 ',1)[0]
ddl+='\n'+re.search(r'```sql\n([\s\S]*?)```',section).group(1)
(Q/'ddl-rf26-extraido.sql').write_text(ddl,encoding='utf-8')
out={}
with psycopg.connect(dsn_rol('lumin_migracion'),autocommit=True) as c:
 c.execute('CREATE SCHEMA qa_rf26')
 c.execute('SET search_path=qa_rf26,public');c.execute(ddl)
 EA,EB,A,B,C,T,P,L1,L2,LB,G=[uuid.uuid4() for _ in range(11)]
 c.execute("INSERT INTO empresa(id,clave,nombre) VALUES (%s,'a','A'),(%s,'b','B')",(EA,EB))
 c.execute("INSERT INTO sucursal(id,empresa_id,clave,nombre) VALUES (%s,%s,'a','A'),(%s,%s,'b','B'),(%s,%s,'c','C')",(A,EA,B,EA,C,EB))
 c.execute("INSERT INTO pantalla(id,empresa_id,sucursal_id,id_dispositivo,numero,aprobada) VALUES (%s,%s,%s,'tv-a',1,true),(%s,%s,NULL,'pendiente',2,false)",(T,EA,A,P,EA))
 c.execute("INSERT INTO lista(id,empresa_id,sucursal_id,clave,nombre) VALUES (%s,%s,%s,'l1','L1'),(%s,%s,%s,'l2','L2'),(%s,%s,%s,'lb','LB')",(L1,EA,A,L2,EA,B,LB,EB,C))
 c.execute("INSERT INTO grupo_pantallas(id,empresa_id,sucursal_id,nombre) VALUES (%s,%s,%s,'Grupo A')",(G,EA,A))
 checks=[('grupo_lista_otra_sucursal','INSERT INTO lista_destino(id,empresa_id,sucursal_id,lista_id,grupo_id) VALUES (%s,%s,%s,%s,%s)',(uuid.uuid4(),EA,A,L2,G)),
 ('pantalla_pendiente','INSERT INTO lista_destino(id,empresa_id,sucursal_id,lista_id,pantalla_id) VALUES (%s,%s,%s,%s,%s)',(uuid.uuid4(),EA,A,L1,P)),
 ('grupo_empresa_ajena','INSERT INTO grupo_pantalla_miembro(grupo_id,pantalla_id,sucursal_id,empresa_id) VALUES (%s,%s,%s,%s)',(G,T,A,EB))]
 for name,sql,params in checks:
  try:c.execute(sql,params);out[name]='aceptado'
  except psycopg.errors.ForeignKeyViolation:out[name]='rechazado_fk'
 assert all(v=='rechazado_fk' for v in out.values())
 c.execute('INSERT INTO grupo_pantalla_miembro(grupo_id,pantalla_id,sucursal_id,empresa_id) VALUES (%s,%s,%s,%s)',(G,T,A,EA))
 c.execute('INSERT INTO lista_destino(id,empresa_id,sucursal_id,lista_id,pantalla_id) VALUES (%s,%s,%s,%s,%s)',(uuid.uuid4(),EA,A,L1,T))
 try:c.execute('UPDATE pantalla SET sucursal_id=%s WHERE id=%s',(B,T));out['movimiento']='automatico'
 except psycopg.errors.ForeignKeyViolation:out['movimiento']='rechazado_fk_sin_cascada'
 assert out['movimiento']=='rechazado_fk_sin_cascada'
 out['relaciones_conservadas']=c.execute('SELECT (SELECT count(*) FROM grupo_pantalla_miembro),(SELECT count(*) FROM lista_destino)').fetchone()
 c.execute('INSERT INTO lista_version(lista_id,version) VALUES (%s,1),(%s,1)',(L1,LB))
 c.execute('UPDATE pantalla SET lista_conf_id=%s,lista_conf_version=1 WHERE id=%s',(LB,T))
 out['confirmacion_empresa_ajena_aceptada']=c.execute('SELECT lista_conf_id=%s FROM pantalla WHERE id=%s',(LB,T)).fetchone()[0]
 cols=[r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='qa_rf26' AND table_name='lista_version'")]
 out['historial_tiene_empresa_id']='empresa_id' in cols
 try:c.execute('CREATE POLICY ensayo_empresa ON lista_version USING (empresa_id IS NOT NULL)');out['politica_empresa']='aceptada'
 except psycopg.errors.UndefinedColumn:out['politica_empresa']='columna_empresa_id_inexistente'
 assert out['confirmacion_empresa_ajena_aceptada'] and not out['historial_tiene_empresa_id']
(Q/'adicionales-resultados.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
