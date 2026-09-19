"""Caracterización local; no es una suite de aprobación de seguridad.
Carga el código en un directorio temporal, sin iniciar servidor ni migraciones.
Invoca handlers en memoria; no abre sockets ni usa datos del checkout.
"""
import ast
import hashlib
import io
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

source = Path(sys.argv[1]).resolve()
raw = source.read_bytes()
code = raw.decode('utf-8-sig')
ast.parse(code)
results = []
def record(name, observed, reproduced):
    results.append(dict(case=name, observed=observed, reproduced=bool(reproduced)))

with tempfile.TemporaryDirectory(prefix='lumin-tv-qa-') as tmp:
    env = {'__name__': 'qa_isolated', '__file__': str(Path(tmp)/'server.py')}
    exec(compile(code, str(source), 'exec'), env)
    env['ip_local'] = lambda: '127.0.0.1'
    env['ahora_local'] = lambda: datetime(2026, 9, 15, 12, tzinfo=timezone.utc)
    env['FFMPEG'] = env['FFPROBE'] = None
    write = env['escribir_json']
    read = env['leer_json']
    write(env['ARCHIVO_SUCURSALES'], [{'clave':'qa-a','nombre':'QA A'}, {'clave':'qa-b','nombre':'QA B'}])
    write(env['ARCHIVO_USUARIOS'], {'qa':{'rol':'usuario','sucursales':['qa-a']}})
    write(env['ARCHIVO_SESIONES'], {'qa-synthetic-session':{'usuario':'qa','exp':4102444800}})
    write(env['ARCHIVO_TVS'], {'qa-tv':{'indice':0,'sucursal':'qa-a','aprobada':True,'turnos':True}})
    (Path(env['dir_videos']('qa-a'))/'sample.mp4').write_bytes(b'QA-SYNTHETIC-MEDIA')

    class Handler(env['Manejador']):
        def __init__(self, path, body=None, authenticated=False):
            self.path = path
            payload = json.dumps(body or {}).encode()
            self.headers = {'Content-Length':str(len(payload)), 'Host':'qa.invalid'}
            if authenticated:
                self.headers['Cookie']='sesion=qa-synthetic-session'
            self.rfile=io.BytesIO(payload)
            self.wfile=io.BytesIO()
            self.status=None
        def send_response(self, status, message=None): self.status=status
        def send_header(self, *args): pass
        def end_headers(self): pass
    def request(method, path, body=None, auth=False):
        h=Handler(path, body, auth)
        getattr(h, 'do_'+method)()
        return h.status, h.wfile.getvalue()

    for assigned in ([], ['missing']):
        allowed=[s['clave'] for s in env['sucursales_permitidas']({'rol':'usuario','sucursales':assigned})]
        record('permisos-'+str(assigned), allowed, bool(allowed))
    status, payload=request('GET','/playlist.json?id=qa-tv')
    record('playlist-sin-token', {'status':status,'has_videos':'videos' in json.loads(payload)},status==200 and 'videos' in json.loads(payload))
    status, payload=request('GET','/videos/qa-a/sample.mp4')
    record('medio-sin-sesion', {'status':status,'synthetic_bytes':payload==b'QA-SYNTHETIC-MEDIA'},status==200 and payload==b'QA-SYNTHETIC-MEDIA')
    for _ in range(2): status,_=request('GET','/videos/qa-a/missing.mp4')
    counts=read(env['ARCHIVO_CONTADORES'],{})['qa-a']['missing.mp4']
    record('contador-404-duplicado',{'status':status,'counts':counts},status==404 and sum(counts.values())==2)
    status,_=request('POST','/api/tv',{'id':'qa-tv','sucursal':'qa-b'},True)
    destination=read(env['ARCHIVO_TVS'],{})['qa-tv']['sucursal']
    record('operador-mueve-a-sucursal-ajena',{'status':status,'destination':destination},status==200 and destination=='qa-b')
    for _ in range(2): status,_=request('POST','/api/turno',{'sucursal':'qa-a','numero':'QA1'},True)
    n=read(env['ARCHIVO_TURNOS'],{})['qa-a']['n']
    record('turno-duplicado',{'status':status,'n':n},status==200 and n==2)
    status,_=request('PUT','/api/turno',{'sucursal':'qa-a','numero':'QA2'},True)
    record('put-turno-existente', {'status':status},status==200)
    status,_=request('GET','/api/tvs?sucursal=qa-a')
    record('api-admin-exige-sesion',{'status':status},status==401)

print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'python':sys.version.split()[0],
                  'scope':'in-memory handlers; synthetic temporary data; no network; fixed UTC clock',
                  'results':results},ensure_ascii=False,indent=2))
sys.exit(0 if all(r['reproduced'] for r in results) else 1)
