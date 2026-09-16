"""INV-01: la herramienta de inventario no debe convertir datos ausentes o
invalidos en un diagnostico vacio exitoso, y los alias de pantalla deben ser
inequivocos. Todo con datos sinteticos; la herramienta es de solo lectura."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERRAMIENTA = Path(__file__).resolve().parents[1] / "herramientas" / "inventario_decisiones.py"

CENTINELAS = ("HASH_CENTINELA_9f3a", "SAL_CENTINELA_77", "TOKEN_CENTINELA_ab12")


def correr(base):
    p = subprocess.run([sys.executable, str(HERRAMIENTA), str(base)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def escribir(base: Path, tvs=None, sucursales=None, usuarios=None, crudo=None):
    base.mkdir(parents=True, exist_ok=True)
    crudo = crudo or {}
    for nombre, datos in (("tvs.json", tvs), ("sucursales.json", sucursales), ("usuarios.json", usuarios)):
        if nombre in crudo:
            (base / nombre).write_text(crudo[nombre], encoding="utf-8")
        elif datos is not None:
            (base / nombre).write_text(json.dumps(datos), encoding="utf-8")


def huellas(base: Path):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.iterdir())}


def datos_completos():
    tvs = {
        "roku-AAAA-123456": {"indice": 5, "sucursal": "centro", "zona": "recepcion", "visto": 1, "turnos": True},
        "roku-BBBB-123456": {"indice": 5, "sucursal": "centro", "zona": "recepcion", "visto": 1},
        "roku-CCCC-000001": {"indice": 0, "sucursal": "norte", "zona": "sala"},
    }
    sucursales = [{"clave": "centro", "nombre": "Centro"}, {"clave": "norte", "nombre": "Norte"}]
    usuarios = {
        "admin": {"rol": "admin", "hash": CENTINELAS[0], "sal": CENTINELAS[1], "sucursales": []},
        "ana": {"rol": "usuario", "hash": CENTINELAS[0], "sal": CENTINELAS[1], "sucursales": []},
        "beto": {"rol": "usuario", "hash": CENTINELAS[0], "sal": CENTINELAS[1], "sucursales": ["inexistente"]},
        "carla": {"rol": "usuario", "hash": CENTINELAS[0], "sal": CENTINELAS[1], "sucursales": ["norte"], "token": CENTINELAS[2]},
    }
    return tvs, sucursales, usuarios


# ---------------------------------------------------------------- INV-01

def test_directorio_inexistente_no_produce_inventario(tmp_path):
    codigo, salida = correr(tmp_path / "no-existe")
    assert codigo == 2
    assert "INVENTARIO NO GENERADO" in salida
    assert "no es un directorio" in salida
    assert "== D1" not in salida and "ninguno:" not in salida


def test_falta_un_archivo_obligatorio(tmp_path):
    tvs, sucursales, _ = datos_completos()
    escribir(tmp_path, tvs=tvs, sucursales=sucursales)  # sin usuarios.json
    codigo, salida = correr(tmp_path)
    assert codigo == 2
    assert "falta usuarios.json" in salida
    assert "== D1" not in salida


def test_json_invalido(tmp_path):
    tvs, sucursales, usuarios = datos_completos()
    escribir(tmp_path, tvs=tvs, sucursales=sucursales, usuarios=usuarios,
             crudo={"tvs.json": '{"roku-1": {"indice": 1'})
    codigo, salida = correr(tmp_path)
    assert codigo == 2
    assert "tvs.json no es JSON valido" in salida
    assert "== D1" not in salida


def test_esquema_incorrecto(tmp_path):
    tvs, sucursales, usuarios = datos_completos()
    escribir(tmp_path, tvs=[], sucursales=sucursales, usuarios=usuarios)  # lista en vez de objeto
    codigo, salida = correr(tmp_path)
    assert codigo == 2
    assert "tvs.json deberia ser un objeto" in salida

    escribir(tmp_path, tvs=tvs, sucursales=[{"nombre": "sin clave"}], usuarios=usuarios)
    codigo, salida = correr(tmp_path)
    assert codigo == 2
    assert "sucursales.json" in salida and "clave" in salida

    escribir(tmp_path, tvs={"roku-1": "texto"}, sucursales=sucursales, usuarios=usuarios)
    codigo, salida = correr(tmp_path)
    assert codigo == 2
    assert "no es un objeto" in salida


def test_vacio_valido_se_distingue_de_faltante(tmp_path):
    escribir(tmp_path, tvs={}, sucursales=[], usuarios={})
    codigo, salida = correr(tmp_path)
    assert codigo == 0
    assert "0 pantallas  (archivo valido, vacio)" in salida
    assert "0 usuarios  (archivo valido, vacio)" in salida
    assert "sin pantallas registradas (archivo vacio)" in salida
    assert "sin usuarios registrados (archivo vacio)" in salida
    # y NO la frase que sugiere que se revisaron operadores
    assert "todos los operadores declaran" not in salida


# ---------------------------------------------------------------- alias y contenido

def test_alias_unicos_y_propuesta_distinguible(tmp_path):
    tvs, sucursales, usuarios = datos_completos()
    escribir(tmp_path, tvs=tvs, sucursales=sucursales, usuarios=usuarios)
    codigo, salida = correr(tmp_path)
    assert codigo == 0
    # los dos IDs comparten el sufijo 123456: el alias debe extenderse
    assert "AAAA-123456" in salida and "BBBB-123456" in salida
    assert "P6 -> P7" in salida
    assert "identificador menor" in salida  # explicacion corregida del desempate
    # mapeo alias -> id completo
    assert "roku-AAAA-123456" in salida and "roku-BBBB-123456" in salida


def test_d2_marca_los_casos_qa_f01(tmp_path):
    tvs, sucursales, usuarios = datos_completos()
    escribir(tmp_path, tvs=tvs, sucursales=sucursales, usuarios=usuarios)
    _, salida = correr(tmp_path)
    assert "ana  rol=usuario" in salida and "LISTA VACIA" in salida
    assert "beto  rol=usuario" in salida and "SOLO CLAVES INEXISTENTES" in salida
    assert "carla  rol=usuario" not in salida.split("== Todos los usuarios")[0]


def test_no_muestra_credenciales_ni_modifica_archivos(tmp_path):
    tvs, sucursales, usuarios = datos_completos()
    escribir(tmp_path, tvs=tvs, sucursales=sucursales, usuarios=usuarios)
    antes = huellas(tmp_path)
    codigo, salida = correr(tmp_path)
    assert codigo == 0
    for c in CENTINELAS:
        assert c not in salida
    assert huellas(tmp_path) == antes
    assert set(tmp_path.iterdir()) == {tmp_path / "tvs.json", tmp_path / "sucursales.json", tmp_path / "usuarios.json"}
