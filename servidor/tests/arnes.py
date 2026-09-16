"""Arnés de pruebas: levanta servidor_lumin.py REAL en un directorio temporal.

No se simula nada: el servidor corre con ThreadingHTTPServer en un puerto
libre, sobre sus archivos JSON de siempre, y las pruebas le hablan por HTTP.
Así una carrera se prueba con hilos de verdad contra el manejador real.

Uso:
    with Servidor() as s:
        s.get("/playlist.json?id=TV-1")
"""

from __future__ import annotations

import http.client
import importlib.util
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
# Por defecto se prueba el servidor del arbol de trabajo. Para comparar contra
# otra version (por ejemplo la base 6.9 en ea610d6) se apunta esta variable a
# una copia aislada; ver comparar_con_base.py. Nunca se toca el checkout.
FUENTE = Path(os.environ.get("LUMIN_SERVIDOR_BAJO_PRUEBA", RAIZ / "servidor_lumin.py"))

CONTRASENA_PRUEBAS = "prueba-1234"


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Servidor:
    def __init__(self, fuente: Path = FUENTE, datos: dict | None = None):
        self.fuente = fuente
        self.datos_iniciales = datos or {}
        self.dir = Path(tempfile.mkdtemp(prefix="lumin-prueba-"))
        self.puerto = _puerto_libre()
        self.modulo = None
        self.httpd = None
        self.hilo = None

    # ---- ciclo de vida ----

    def __enter__(self):
        destino = self.dir / "servidor_lumin.py"
        shutil.copy(self.fuente, destino)
        for nombre, contenido in self.datos_iniciales.items():
            (self.dir / nombre).write_text(
                json.dumps(contenido, ensure_ascii=False), encoding="utf-8")

        spec = importlib.util.spec_from_file_location(
            f"servidor_prueba_{self.puerto}", destino)
        mod = importlib.util.module_from_spec(spec)
        # la contrasena fija del codigo (QA-F03) se sobreescribe para las pruebas
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        mod.CONTRASENA_PANEL = CONTRASENA_PRUEBAS
        mod.PUERTO = self.puerto
        mod.FFMPEG = None
        mod.FFPROBE = None
        self.modulo = mod
        if hasattr(mod, "migrar"):
            mod.migrar()

        self.httpd = mod.ServidorSilencioso(("127.0.0.1", self.puerto), mod.Manejador)
        self.hilo = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.hilo.start()
        self._esperar()
        return self

    def __exit__(self, *exc):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)
        return False

    def _esperar(self, segundos: float = 5.0):
        limite = time.time() + segundos
        while time.time() < limite:
            try:
                with socket.create_connection(("127.0.0.1", self.puerto), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.05)
        raise RuntimeError("el servidor de pruebas no arranco")

    # ---- http ----

    def peticion(self, metodo: str, ruta: str, cuerpo=None, cookie: str | None = None,
                 cabeceras: dict | None = None):
        con = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)
        h = {"Content-Type": "application/json"}
        if cookie:
            h["Cookie"] = cookie
        if cabeceras:
            h.update(cabeceras)
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
        con.request(metodo, ruta, body=datos, headers=h)
        r = con.getresponse()
        crudo = r.read()
        con.close()
        try:
            parseado = json.loads(crudo) if crudo else None
        except ValueError:
            parseado = None
        return r.status, parseado, r.getheader("Set-Cookie", ""), crudo

    def get(self, ruta, cookie=None, cabeceras=None):
        return self.peticion("GET", ruta, cookie=cookie, cabeceras=cabeceras)

    def post(self, ruta, cuerpo, cookie=None):
        return self.peticion("POST", ruta, cuerpo, cookie=cookie)

    def login(self, usuario="admin", contrasena=CONTRASENA_PRUEBAS) -> str:
        st, _, cookie, _ = self.post("/api/login", {"usuario": usuario, "contrasena": contrasena})
        assert st == 200, f"login fallo: {st}"
        return cookie.split(";")[0]

    # ---- archivos ----

    def json(self, nombre: str):
        p = self.dir / nombre
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def crear_video(self, sucursal: str, nombre: str, bytes_: int = 2048):
        d = self.dir / "videos" / sucursal
        d.mkdir(parents=True, exist_ok=True)
        (d / nombre).write_bytes(os.urandom(bytes_))
