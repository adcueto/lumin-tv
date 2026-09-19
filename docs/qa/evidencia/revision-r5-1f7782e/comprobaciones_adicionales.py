"""Reproducciones independientes en fixtures sintéticos. No implementa producto."""
import json,os,sys,tempfile
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q/'servidor/ensayos_b3'))
sys.path.insert(0,str(Q/'servidor/tests'))
from arnes import Servidor
from comun import preparar_base,dsn_rol,contexto,EMPRESA_A,mutar_sucursal
from test_ensayo_sesiones import drenar_lumin_app
from test_ensayo_cola import encolar,reclamar,ruta_artefacto,escribir_artefacto,publicar,descartar_lo_mio,estado
import psycopg
assert os.environ['LUMIN_ENSAYO_PG']=='postgresql://postgres@127.0.0.1:55432/postgres'
out={}
with Servidor() as s:
    admin=s.login()
    suc='plaza-de-la-mujer'
    assert s.post('/api/usuarios',{'usuario':'operadorqa','contrasena':'solo-prueba-123','rol':'usuario','sucursales':[suc]},cookie=admin)[0]==200
    operador=s.login('operadorqa','solo-prueba-123')
    s.get('/playlist.json?id=QA-TV')
    assert s.post('/api/tv/aprobar',{'id':'QA-TV','sucursal':suc},cookie=admin)[0]==200
    acciones=[]
    for accion in ('recargar','vaciar_cache'):
        status=s.post('/api/tv/comando',{'id':'QA-TV','accion':accion,'sucursal':suc},cookie=operador)[0]
        delivered=s.get('/playlist.json?id=QA-TV')[1]['comando']['accion']
        assert status==200 and delivered==accion
        acciones.append({'accion':accion,'rol':'usuario','http':status,'comando_en_playlist':delivered})
    out['B5A-QA-01']=acciones
    s.crear_video(suc,'qa.mp4')
    s.modulo.guardar_lista(suc,'principal',['qa.mp4'])
    s.post('/api/tv/comando',{'id':'QA-TV','accion':'recargar'},cookie=admin)
    a=s.get('/playlist.json?id=QA-TV')[3]
    b=s.get('/playlist.json?id=QA-TV')[3]
    assert a==b
    assert len(json.loads(a)['videos']) == 1
    out['B5A-QA-02']={'dos_respuestas_http_identicas_tras_recargar':True,'bytes':len(a),'limite':'observador Roku revisado por XML y contrato oficial; no TV física'}

preparar_base()
with psycopg.connect(dsn_rol('lumin_app')) as a:
    mutar_sucursal(a,EMPRESA_A,'tardia-qa','QA',confirmar=False)
    pid=a.info.backend_pid
    drenar_lumin_app(timeout_s=0.1)
    with psycopg.connect(dsn_rol('lumin_migracion'),autocommit=True) as c:
        state=c.execute('SELECT state FROM pg_stat_activity WHERE pid=%s',(pid,)).fetchone()[0]
        before=c.execute("SELECT count(*) FROM sucursal WHERE clave='tardia-qa'").fetchone()[0]
    a.commit()
    with psycopg.connect(dsn_rol('lumin_migracion')) as c:
        after=c.execute("SELECT count(*) FROM sucursal WHERE clave='tardia-qa'").fetchone()[0]
    assert state=='idle in transaction' and before==0 and after==1
    out['B3-R4-01']={'drenaje_retorno':True,'estado_posterior':state,'filas_antes':before,'filas_despues_commit_tardio':after}

preparar_base()
with tempfile.TemporaryDirectory(prefix='lumin-qa-r5-') as d:
    tid=encolar();_,pos=reclamar('A')
    r=ruta_artefacto(Path(d),'video','d1',pos)
    escribir_artefacto(r,b'QA sintetico')
    first=publicar(tid,pos,r)
    retry=publicar(tid,pos,r)
    if not retry:descartar_lo_mio(r,pos)
    final=estado(tid)[0]
    assert first and not retry and final=='hecho' and not r.exists()
    out['B3-R4-02']={'publicacion_inicial':first,'repeticion_misma_posesion':retry,'estado':final,'archivo_existe':r.exists()}
(Q/'comprobaciones-adicionales.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(out,indent=2,ensure_ascii=False))
