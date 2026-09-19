"""QA aislada del candidato; no modifica el repositorio original."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = Path('C:/Users/adcueto/Claude/lumin-tv')
BASE = Path(__file__).resolve().parent
SHA = '78306df3f81b53328cd7fbdd07b294d3b0a1c262'

def git(*args):
    return subprocess.check_output(['git', '-c', f'safe.directory={REPO.as_posix()}', '-C', str(REPO), *args])

def extraer():
    archivos = git('ls-tree', '-r', '--name-only', SHA).decode().splitlines()
    seleccion = [p for p in archivos if p.startswith(('servidor/tests/', 'servidor/herramientas/', 'roku-app/', 'docs/coordinacion/')) or p == 'servidor/servidor_lumin.py']
    hashes = {}
    for p in seleccion:
        contenido = git('show', f'{SHA}:{p}')
        destino = BASE / 'candidato' / p
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        hashes[p] = hashlib.sha256(contenido).hexdigest()
    anterior = BASE / 'base' / 'servidor_lumin.py'
    anterior.parent.mkdir(exist_ok=True)
    anterior.write_bytes(git('show', 'ea610d6:servidor/servidor_lumin.py'))
    (BASE / 'hashes.json').write_text(json.dumps({'sha': SHA, 'files': hashes}, indent=2), encoding='utf-8')
    xmls = list((BASE / 'candidato' / 'roku-app').rglob('*.xml'))
    for p in xmls:
        ET.parse(p)
    print(f'Extraccion: {len(seleccion)} archivos. XML: {len(xmls)} validos.')

def pruebas(version):
    tests = BASE / 'candidato' / 'servidor' / 'tests'
    fuente = (BASE / 'base' / 'servidor_lumin.py') if version == 'base' else (tests.parent / 'servidor_lumin.py')
    os.environ['LUMIN_SERVIDOR_BAJO_PRUEBA'] = str(fuente)
    sys.path.insert(0, str(tests))
    spec = importlib.util.spec_from_file_location('qa_tests', tests / 'test_b2_higiene.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    resultados = []
    for nombre, funcion in list(vars(modulo).items()):
        if nombre.startswith('test_') and callable(funcion):
            salida = io.StringIO()
            try:
                with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(salida):
                    funcion()
                resultado = {'test': nombre, 'status': 'PASS'}
            except Exception as e:
                resultado = {'test': nombre, 'status': 'FAIL', 'error': type(e).__name__, 'detail': str(e)}
            resultados.append(resultado)
            print(json.dumps(resultado, ensure_ascii=False), flush=True)
    (BASE / f'resultados-{version}.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{version}: {sum(r["status"] == "PASS" for r in resultados)}/{len(resultados)} PASS')

if __name__ == '__main__':
    if sys.argv[1] == 'extraer':
        extraer()
    else:
        pruebas(sys.argv[1])
