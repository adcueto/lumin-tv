"""B5a — estado real en el latido y comandos de operacion remota (6.10.1).

Contra el servidor real. Lo que se protege:
  - un latido SIN parametros (app 5.1/5.2 anteriores) sigue igual y no crea `estado`;
  - un latido CON parametros guarda el estado con topes y lo expone /api/tvs;
  - `eh` (hace cuanto fue el error) se guarda como instante absoluto `error_en`;
  - los comandos `recargar` y `vaciar_cache` se aceptan, viajan en la playlist
    con `n` creciente, y una accion desconocida sigue siendo 400;
  - el contrato de /playlist.json no cambia por reportar estado.
"""

import time
from urllib.parse import urlencode

from arnes import Servidor


def latido(s, id_tv, **estado):
    q = {"id": id_tv, **estado}
    return s.get("/playlist.json?" + urlencode(q))


def aprobar(s, id_tv):
    admin = s.login()
    st, _, _, _ = s.post("/api/tv/aprobar", {"id": id_tv}, cookie=admin)
    assert st == 200, st
    return admin


def test_latido_sin_parametros_no_crea_estado():
    with Servidor() as s:
        st, _, _, _ = latido(s, "TV-VIEJA")
        assert st == 200
        assert "estado" not in s.json("tvs.json")["TV-VIEJA"]


def test_latido_con_estado_lo_guarda_con_topes_y_lo_expone():
    with Servidor() as s:
        latido(s, "TV-B5A", v="5.2.61", m="Roku Express 4K", os="12.5.1.4100",
               ip="192.168.1.50", r="promo-otono.mp4", c="123", e="video error x.mp4", eh="40", k="1")
        e = s.json("tvs.json")["TV-B5A"]["estado"]
        assert e["version"] == "5.2.61" and e["modelo"] == "Roku Express 4K"
        assert e["sistema"] == "12.5.1.4100" and e["ip"] == "192.168.1.50"
        assert e["reproduciendo"] == "promo-otono.mp4" and e["cache_mb"] == 123
        assert e["error"] == "video error x.mp4" and e["desde_cache"] is True
        assert "error_hace" not in e and abs(e["error_en"] - (int(time.time()) - 40)) <= 2
        # topes: nada mas largo de lo declarado, y numeros basura ignorados
        latido(s, "TV-B5A", v="x" * 100, r="y" * 500, c="no-numero", eh="tampoco")
        e = s.json("tvs.json")["TV-B5A"]["estado"]
        assert len(e["version"]) == 16 and len(e["reproduciendo"]) == 80
        assert "cache_mb" not in e and "error_en" not in e
        # expuesto en /api/tvs una vez aprobada
        admin = aprobar(s, "TV-B5A")
        st, tvs, _, _ = s.get("/api/tvs", cookie=admin)
        assert st == 200
        mia = [t for t in tvs if t["id"] == "TV-B5A"][0]
        assert mia["estado"]["version"] == "x" * 16


def test_el_estado_se_reemplaza_en_cada_latido():
    with Servidor() as s:
        latido(s, "TV-B5A", v="5.2.61", r="a.mp4", e="video error a.mp4", eh="5")
        latido(s, "TV-B5A", v="5.2.61", r="b.mp4")   # el error ya no se reporta
        e = s.json("tvs.json")["TV-B5A"]["estado"]
        assert e["reproduciendo"] == "b.mp4" and "error" not in e


def test_comandos_recargar_y_vaciar_cache_viajan_en_la_playlist():
    with Servidor() as s:
        latido(s, "TV-C")
        admin = aprobar(s, "TV-C")
        _, p0, _, _ = latido(s, "TV-C")
        n0 = p0["comando"]["n"]
        for accion in ("recargar", "vaciar_cache"):
            st, _, _, _ = s.post("/api/tv/comando", {"id": "TV-C", "accion": accion}, cookie=admin)
            assert st == 200, (accion, st)
            _, p, _, _ = latido(s, "TV-C")
            assert p["comando"]["accion"] == accion
            assert p["comando"]["n"] > n0
            n0 = p["comando"]["n"]
        st, _, _, _ = s.post("/api/tv/comando", {"id": "TV-C", "accion": "reiniciar_tv"}, cookie=admin)
        assert st == 400
        # estos comandos no tocan pausada/silencio
        t = s.json("tvs.json")["TV-C"]
        assert not t.get("pausada") and not t.get("silencio")


def test_contrato_playlist_igual_con_o_sin_estado():
    with Servidor() as s:
        s.crear_video("plaza-de-la-mujer", "uno.mp4")
        latido(s, "TV-D")
        aprobar(s, "TV-D")
        _, sin, _, _ = latido(s, "TV-D")
        _, con, _, _ = latido(s, "TV-D", v="5.2.61", r="uno.mp4", c="3")
        assert sin == con
        assert set(con) >= {"videos", "mensaje", "cintillo", "velocidad", "comando"}


# ---------------------------------------------------------------- B5A-QA-01

SUC = "plaza-de-la-mujer"


def _operador(s, admin, nombre="karla", sucursales=(SUC,)):
    st, _, _, _ = s.post("/api/usuarios", {"usuario": nombre, "contrasena": "clave-1234",
                                           "rol": "usuario", "sucursales": list(sucursales)}, cookie=admin)
    assert st == 200, st
    return s.login(nombre, "clave-1234")


def test_operador_no_puede_recargar_ni_vaciar_cache():
    """B5A-QA-01: el permiso se aplica en el servidor, no en el boton."""
    with Servidor() as s:
        latido(s, "TV-OP")
        admin = aprobar(s, "TV-OP")
        op = _operador(s, admin)
        _, antes, _, _ = latido(s, "TV-OP")
        n0 = antes["comando"]["n"]
        for accion in ("recargar", "vaciar_cache"):
            st, cuerpo, _, _ = s.post("/api/tv/comando", {"id": "TV-OP", "accion": accion}, cookie=op)
            assert st == 403, (accion, st, cuerpo)
        # nada se encolo
        _, despues, _, _ = latido(s, "TV-OP")
        assert despues["comando"]["n"] == n0
        assert (s.json("comandos.json") or {}).get("TV-OP", {}).get("accion") not in ("recargar", "vaciar_cache")
        # el operador SI conserva los comandos de siempre en su sucursal
        st, _, _, _ = s.post("/api/tv/comando", {"id": "TV-OP", "accion": "pausa"}, cookie=op)
        assert st == 200
        # y el admin si puede
        st, _, _, _ = s.post("/api/tv/comando", {"id": "TV-OP", "accion": "recargar"}, cookie=admin)
        assert st == 200
        _, p, _, _ = latido(s, "TV-OP")
        assert p["comando"]["accion"] == "recargar"


def test_operador_de_otra_sucursal_sigue_sin_poder_mandar_comandos():
    with Servidor() as s:
        latido(s, "TV-OTRA")
        admin = aprobar(s, "TV-OTRA")
        s.post("/api/sucursales", {"clave": "juriquilla", "nombre": "Juriquilla"}, cookie=admin)
        op = _operador(s, admin, "beto", ("juriquilla",))
        # hoy el servidor responde 200 e ignora en silencio la pantalla ajena
        # (contrato 6.x, se endurece en B4); lo que importa: NADA se encola
        st, _, _, _ = s.post("/api/tv/comando", {"id": "TV-OTRA", "accion": "pausa", "sucursal": SUC}, cookie=op)
        assert st == 200
        st, _, _, _ = s.post("/api/tv/comando", {"id": "TV-OTRA", "accion": "recargar", "sucursal": SUC}, cookie=op)
        assert st == 403
        _, p, _, _ = latido(s, "TV-OTRA")
        assert p["comando"]["n"] == 0
        assert "TV-OTRA" not in (s.json("comandos.json") or {})
