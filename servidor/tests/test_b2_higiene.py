"""B2 — higiene del servidor actual.

Cada prueba reproduce un defecto del servidor 6.9 y exige la conducta
corregida. Contra 6.9 fallan; contra 6.10 pasan. Se ejecutan contra el
servidor real por HTTP, con hilos reales.
"""

from __future__ import annotations

import socket
import threading
import time

from arnes import Servidor

SUC = "plaza-de-la-mujer"


def _en_paralelo(n, fn):
    """Lanza n hilos que arrancan a la vez (barrera) y recoge resultados."""
    barrera = threading.Barrier(n)
    salidas, errores = [], []

    def envoltura(i):
        barrera.wait()
        try:
            salidas.append(fn(i))
        except Exception as e:  # noqa: BLE001
            errores.append(e)

    hilos = [threading.Thread(target=envoltura, args=(i,)) for i in range(n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return salidas, errores


# ---------------------------------------------------------------- carreras

def test_logins_simultaneos_no_pierden_sesiones():
    """crear_sesion hacia leer-modificar-escribir sin candado."""
    with Servidor() as s:
        s.login()  # crea el admin inicial
        cookies, errores = _en_paralelo(40, lambda i: s.login())
        assert not errores, errores[:3]
        assert len(cookies) == 40
        guardadas = s.json("sesiones.json") or {}
        # 1 del primer login + 40 simultaneos
        assert len(guardadas) == 41, f"se perdieron sesiones: {len(guardadas)}"
        # y todas siguen sirviendo
        for c in cookies:
            assert s.get("/api/yo", cookie=c)[0] == 200


def test_altas_de_usuario_simultaneas_no_se_pisan():
    """crear_usuario hacia leer-modificar-escribir sin candado."""
    with Servidor() as s:
        admin = s.login()
        salidas, errores = _en_paralelo(
            20, lambda i: s.post("/api/usuarios", {
                "usuario": f"op{i:02d}", "contrasena": "clave-1234",
                "rol": "usuario", "sucursales": [SUC]}, cookie=admin)[0])
        assert not errores
        usuarios = s.json("usuarios.json") or {}
        creados = [u for u in usuarios if u.startswith("op")]
        assert len(creados) == 20, f"solo quedaron {len(creados)} de 20"


def test_marcas_de_giro_simultaneas_no_se_pierden():
    """marcar_girado hacia leer-modificar-escribir sin candado."""
    with Servidor() as s:
        mod = s.modulo
        _, errores = _en_paralelo(
            30, lambda i: mod.marcar_girado(SUC, f"video{i:02d}.mp4"))
        assert not errores
        girados = (s.json("girados.json") or {}).get(SUC, {})
        assert len(girados) == 30, f"se perdieron marcas: {len(girados)}"


# ------------------------------------------------------ cola de conexiones

def test_conexiones_simultaneas_no_se_rechazan():
    """request_queue_size venia en 5: el SO tiraba conexiones bajo rafaga."""
    with Servidor() as s:
        def pedir(i):
            try:
                return s.get("/playlist.json?id=TV-RAFAGA-%03d" % i)[0]
            except (ConnectionResetError, ConnectionAbortedError, socket.error) as e:
                return f"error:{type(e).__name__}"

        salidas, errores = _en_paralelo(120, pedir)
        # B2-QA-01: una excepcion que escape del trabajador no puede ocultar un
        # resultado faltante. Se exige: cero errores, exactamente 120 respuestas
        # y las 120 con HTTP 200.
        assert not errores, f"excepciones en trabajadores: {errores[:3]}"
        assert len(salidas) == 120, f"faltan respuestas: {len(salidas)} de 120"
        rechazadas = [x for x in salidas if x != 200]
        assert not rechazadas, f"{len(rechazadas)} no fueron 200: {rechazadas[:3]}"


# ------------------------------------------------ QA-F04 (parte inmediata)

def test_un_404_no_cuenta_como_reproduccion():
    """El contador se incrementaba ANTES de comprobar que el archivo existe."""
    with Servidor() as s:
        st, *_ = s.get(f"/videos/{SUC}/no-existe.mp4")
        assert st == 404
        st, *_ = s.get(f"/videos/{SUC}/no-existe.mp4")
        assert st == 404
        contadores = (s.json("contadores.json") or {}).get(SUC, {})
        assert "no-existe.mp4" not in contadores, contadores


def test_una_descarga_real_si_cuenta_una_vez():
    """Control positivo: el conteo de peticiones completas sigue funcionando."""
    with Servidor() as s:
        s.crear_video(SUC, "promo.mp4")
        assert s.get(f"/videos/{SUC}/promo.mp4")[0] == 200
        # una peticion Range parcial (no desde 0) no cuenta
        assert s.get(f"/videos/{SUC}/promo.mp4",
                     cabeceras={"Range": "bytes=100-200"})[0] in (200, 206)
        c = (s.json("contadores.json") or {}).get(SUC, {}).get("promo.mp4", {})
        assert sum(c.values()) == 1


# ------------------------------------------- numeros de pantalla duplicados

def test_dar_de_baja_una_pantalla_no_duplica_numeros():
    """indice = len(tvs) reutilizaba numeros tras eliminar una intermedia."""
    with Servidor() as s:
        for n in range(6):
            assert s.get(f"/playlist.json?id=TV-{n}")[0] == 200
        admin = s.login()
        # aprobar todas para que aparezcan en el panel
        for n in range(6):
            s.post("/api/tv/aprobar", {"id": f"TV-{n}", "sucursal": SUC, "zona": f"z{n}"},
                   cookie=admin)
        assert s.post("/api/tv/eliminar", {"id": "TV-2"}, cookie=admin)[0] == 200

        s.get("/playlist.json?id=TV-NUEVA")
        s.post("/api/tv/aprobar", {"id": "TV-NUEVA", "sucursal": SUC, "zona": "nueva"},
               cookie=admin)

        _, pantallas, _, _ = s.get(f"/api/tvs?sucursal={SUC}", cookie=admin)
        numeros = sorted(p["numero"] for p in pantallas)
        assert len(numeros) == len(set(numeros)), f"numeros duplicados: {numeros}"
        assert max(numeros) == 7  # la nueva toma el siguiente libre, no reutiliza


# ------------------------------------------------------------- bitacora

def test_los_errores_quedan_en_bitacora():
    with Servidor() as s:
        s.modulo.bitacora.error("prueba de bitacora %s", "ok")
        for h in s.modulo.bitacora.handlers:
            if hasattr(h, "flush"):
                h.flush()
        registro = s.dir / "registro" / "lumin.log"
        assert registro.exists(), "no se creo registro/lumin.log"
        assert "prueba de bitacora ok" in registro.read_text(encoding="utf-8")


# -------------------------------------------------- lo que NO debe cambiar

def test_contrato_playlist_intacto():
    with Servidor() as s:
        s.crear_video(SUC, "a.mp4")
        st, p, _, _ = s.get("/playlist.json?id=TV-C")
        assert st == 200 and p.get("pendiente") is True and len(p["codigo"]) == 6
        admin = s.login()
        s.post("/api/tv/aprobar", {"id": "TV-C", "sucursal": SUC, "zona": "r"}, cookie=admin)
        st, p, _, _ = s.get("/playlist.json?id=TV-C")
        assert st == 200
        assert set(p) == {"videos", "mensaje", "cintillo", "velocidad", "vertical",
                          "giro", "comando", "turno"}
        assert set(p["videos"][0]) == {"title", "url", "tipo", "duracion", "mini"}


def test_contrato_turno_intacto():
    with Servidor() as s:
        admin = s.login()
        st, r, _, _ = s.post("/api/turno", {
            "sucursal": SUC, "numero": "L142", "estacion": "U4", "espera": "5",
            "proximos": [{"numero": "L143", "estacion": "U1"}]}, cookie=admin)
        assert st == 200 and r == {"ok": True}
        t = (s.json("turnos.json") or {})[SUC]
        assert t["numero"] == "L142" and t["n"] == 1 and "ts" in t
