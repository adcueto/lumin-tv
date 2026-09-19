import sys,json
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q/'servidor/tests'))
from arnes import Servidor
rows=[]
for label,src in [('base',Q.parent/'revision-r5-1f7782e/servidor/servidor_lumin.py'),('candidato',Q/'servidor/servidor_lumin.py')]:
 with Servidor(fuente=src) as s:
  admin=s.login();s.get('/playlist.json?id=QA')
  s.post('/api/tv/aprobar',{'id':'QA','sucursal':'plaza-de-la-mujer'},cookie=admin)
  s.post('/api/usuarios',{'usuario':'qaop','contrasena':'qa-sintetico','rol':'usuario','sucursales':['plaza-de-la-mujer']},cookie=admin)
  op=s.login('qaop','qa-sintetico')
  for method in ['POST','PUT']:
   for accion in ['recargar','vaciar_cache']:
    for role,cookie in [('usuario',op),('admin',admin)]:
     antes=s.get('/playlist.json?id=QA')[1]['comando']['n']
     code=s.peticion(method,'/api/tv/comando',{'id':'QA','accion':accion},cookie=cookie)[0]
     despues=s.get('/playlist.json?id=QA')[1]['comando']['n']
     rows.append(dict(fuente=label,metodo=method,accion=accion,rol=role,http=code,avance_n=despues-antes))
     assert code==(403 if label=='candidato' and role=='usuario' else 200)
     assert (despues==antes)==(label=='candidato' and role=='usuario')
(Q/'permisos-resultados.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps({'casos':len(rows),'resultado':'base admite; candidato deniega operador sin encolar y permite admin; POST y PUT'}))
