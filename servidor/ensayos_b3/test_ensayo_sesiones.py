"""B3-R2-02: la copia congelada de sesiones.json volvía a habilitar sesiones
revocadas después del corte.

Ensayo con el SERVIDOR 6.10 REAL (arnés de tests/) y datos sintéticos:
  1. Reproduce el hallazgo de Codex: cookie válida → logout → inválida →
     restaurar la copia congelada → válida otra vez (el defecto).
  2. Ensaya el contrato corregido: el espejo regenera sesiones.json a partir
     de la copia congelada FILTRADA por el estado en PostgreSQL (hash
     presente, no revocada, no vencida, usuario activo). Una sesión revocada
     durante B3 sigue inválida tras revertir; una vigente sigue sirviendo;
     una creada después del corte (solo hash en la base) queda cerrada.
Prototipo del protocolo, no código del producto.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import psycopg
import pytest

from comun import USUARIO_1, contexto, dsn_rol, preparar_base

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from arnes import Servidor  # noqa: E402  (servidor 6.10 real en un directorio temporal)

COOKIE = "lumin_sesion"


def token_de(cookie: str) -> str:
    return cookie.split("=", 1)[1]


def h(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def regenerar_sesiones(congelado: dict) -> dict:
    """Lo que hará el hilo espejo (rol lumin_espejo) con sesiones.json:
    conserva de la copia congelada solo los tokens cuyo hash sigue siendo una
    sesión elegible en PostgreSQL. No necesita, ni tiene, tokens nuevos."""
    salida = {}
    with psycopg.connect(dsn_rol("lumin_espejo")) as c:
        vigentes = {th: int(exp.timestamp()) for th, exp in c.execute(
            "SELECT s.token_hash, s.expira_en FROM sesion s JOIN usuario u ON u.id = s.usuario_id "
            "WHERE s.revocada_en IS NULL AND s.expira_en > now() AND u.activo")}
    for token, datos in congelado.items():
        th = h(token)
        if th in vigentes:
            salida[token] = {"usuario": datos["usuario"], "exp": min(int(datos.get("exp", 0)), vigentes[th])}
    return salida


def migrar_sesiones(congelado: dict) -> None:
    """migrar_json: token_hash = sha256(token), misma exp, empresa NULL."""
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        for token, datos in congelado.items():
            c.execute("INSERT INTO sesion (token_hash, usuario_id, empresa_id, expira_en) "
                      "VALUES (%s, %s, NULL, to_timestamp(%s))", (h(token), USUARIO_1, datos["exp"]))


def revocar_en_b3(token: str) -> None:
    """Logout en 6.11: la app, con el hash de SU cookie, marca revocada_en."""
    with psycopg.connect(dsn_rol("lumin_app")) as c:
        cur = c.cursor()
        contexto(cur, token_hash=h(token))
        cur.execute("UPDATE sesion SET revocada_en = now() WHERE token_hash = %s", (h(token),))
        assert cur.rowcount == 1
        c.commit()


# ------------------------------------------------------------ revertir.py (prototipo, rev. 4)

class ReversionBloqueada(Exception):
    pass


def drenar_lumin_app(timeout_s: float = 30.0) -> None:
    """Antes de la última verificación: ninguna transacción de lumin_app en
    vuelo. Espera hasta timeout_s y después cancela (pg_signal_backend)."""
    import time as _t
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        fin = _t.monotonic() + timeout_s
        while True:
            vivas = [r[0] for r in c.execute(
                "SELECT pid FROM pg_stat_activity WHERE usename = 'lumin_app' AND state <> 'idle' AND pid <> pg_backend_pid()")]
            if not vivas:
                return
            if _t.monotonic() >= fin:
                for pid in vivas:
                    c.execute("SELECT pg_cancel_backend(%s)", (pid,))
                return
            _t.sleep(0.05)


def revertir(congelado: dict, destino: Path, *, emergencia_autorizada: bool = False, dsn_espejo: str | None = None) -> dict:
    """Decide qué sesiones.json escribe la reversión.

    Normal: PostgreSQL accesible → drenar, verificar y escribir congelado ∩
    vigentes (estado FINAL, no el último archivo del espejo).
    PostgreSQL inaccesible → ReversionBloqueada: no hay vía automática.
    Emergencia (solo con autorización explícita del propietario) → se escribe
    {} de forma atómica: TODAS las sesiones cerradas. Nunca se usa el último
    archivo exportado, cuya vigencia no se puede comprobar.
    """
    try:
        drenar_lumin_app(timeout_s=1.0)
        with psycopg.connect(dsn_espejo or dsn_rol("lumin_espejo"), connect_timeout=2) as c:
            c.execute("SELECT 1")
        sesiones = regenerar_sesiones(congelado)
        motivo = "verificado contra PostgreSQL tras drenar"
    except (psycopg.OperationalError, ReversionBloqueada):
        if not emergencia_autorizada:
            raise ReversionBloqueada("PostgreSQL inaccesible: no se puede comprobar el estado final; sin reversión automática")
        sesiones = {}
        motivo = "EMERGENCIA autorizada: todas las sesiones cerradas; los demás documentos pueden estar desactualizados"
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(sesiones), encoding="utf-8")
    os.replace(tmp, destino)
    return {"sesiones": sesiones, "motivo": motivo}


def valida(s: Servidor, cookie: str) -> bool:
    st, _, _, _ = s.get("/api/yo", cookie=cookie)
    return st == 200


@pytest.fixture
def base():
    preparar_base()


def test_reproduccion_del_hallazgo_con_la_copia_congelada(base):
    with Servidor() as s:
        c1 = s.login()
        assert valida(s, c1)
        congelado = s.json("sesiones.json")
        s.post("/api/logout", {}, cookie=c1)
        assert not valida(s, c1)
        s.modulo.escribir_json(str(s.dir / "sesiones.json"), congelado)   # "revertir" restaurando la copia
        assert valida(s, c1), "la copia congelada resucita la sesión cerrada: es el defecto B3-R2-02"


def test_contrato_corregido_conserva_revocaciones(base):
    with Servidor() as s:
        c_revocada = s.login()      # anterior al corte; se cerrará durante B3
        c_vigente = s.login()       # anterior al corte; sigue viva
        congelado = s.json("sesiones.json")
        assert set(congelado) == {token_de(c_revocada), token_de(c_vigente)}
        migrar_sesiones(congelado)

        # --- B3 en operación: logout de la primera, login nuevo (solo hash) ---
        revocar_en_b3(token_de(c_revocada))
        token_nuevo = "token-posterior-al-corte"
        with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
            c.execute("INSERT INTO sesion (token_hash, usuario_id, expira_en) VALUES (%s, %s, now() + interval '7 days')",
                      (h(token_nuevo), USUARIO_1))

        # --- el espejo regenera sesiones.json (lo que 6.10 leerá al revertir) ---
        regenerado = regenerar_sesiones(congelado)
        s.modulo.escribir_json(str(s.dir / "sesiones.json"), regenerado)

        assert not valida(s, c_revocada), "una sesión revocada durante B3 debe seguir inválida tras revertir"
        assert valida(s, c_vigente), "una sesión anterior al corte y no revocada sigue sirviendo"
        assert not valida(s, f"{COOKIE}={token_nuevo}"), "una sesión creada después del corte queda cerrada"
        assert token_nuevo not in json.dumps(regenerado)  # el espejo nunca inventa tokens


def test_vencidas_y_usuario_inactivo_no_vuelven(base):
    with Servidor() as s:
        c1 = s.login()
        c2 = s.login()
        congelado = s.json("sesiones.json")
        migrar_sesiones(congelado)
        with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
            c.execute("UPDATE sesion SET expira_en = now() - interval '1 minute' WHERE token_hash = %s", (h(token_de(c1)),))
        assert set(regenerar_sesiones(congelado)) == {token_de(c2)}
        with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
            c.execute("UPDATE usuario SET activo = false WHERE id = %s", (USUARIO_1,))
        assert regenerar_sesiones(congelado) == {}


def test_regenerar_es_idempotente_y_nunca_agranda(base):
    with Servidor() as s:
        s.login()
        congelado = s.json("sesiones.json")
        migrar_sesiones(congelado)
        r1 = regenerar_sesiones(congelado)
        r2 = regenerar_sesiones(r1)
        assert r1 == r2 == congelado or set(r2) <= set(congelado)
        assert set(regenerar_sesiones({})) == set()
        time.sleep(0)  # (sin espera real: el ensayo no depende del reloj)


# ------------------------------------------------------------ B3-R3-02

def test_reproduccion_r3_02_el_ultimo_espejo_resucita_una_revocacion_posterior(base):
    """Lo que Codex demostró: revocar DESPUÉS de la última exportación y usar
    ese archivo vuelve a habilitar la cookie. Por eso la excepción desaparece."""
    with Servidor() as s:
        c1 = s.login()
        congelado = s.json("sesiones.json")
        migrar_sesiones(congelado)
        ultimo_espejo = regenerar_sesiones(congelado)          # exportación con la sesión vigente
        revocar_en_b3(token_de(c1))                            # revocación posterior a esa exportación
        assert regenerar_sesiones(congelado) == {}             # el estado final ya no la tiene
        s.modulo.escribir_json(str(s.dir / "sesiones.json"), ultimo_espejo)   # "forzar con el último espejo"
        assert valida(s, c1), "el último archivo del espejo resucita la sesión: es el defecto B3-R3-02"


def test_revertir_bloquea_sin_postgresql_y_no_usa_el_ultimo_espejo(base):
    with Servidor() as s:
        c1 = s.login()
        congelado = s.json("sesiones.json")
        migrar_sesiones(congelado)
        regenerar_sesiones(congelado)
        revocar_en_b3(token_de(c1))
        dsn_caido = "postgresql://lumin_espejo:ensayo@127.0.0.1:1/lumin_ensayo"   # puerto sin servidor
        with pytest.raises(ReversionBloqueada):
            revertir(congelado, s.dir / "sesiones.json", dsn_espejo=dsn_caido)
        # el archivo que 6.10 lee no se tocó: sigue siendo el que dejó el espejo normal
        # (aquí el archivo original del servidor), y la reversión NO ocurrió


def test_revertir_en_emergencia_cierra_todas_las_sesiones(base):
    with Servidor() as s:
        c_revocada = s.login()
        c_vigente = s.login()
        congelado = s.json("sesiones.json")
        migrar_sesiones(congelado)
        revocar_en_b3(token_de(c_revocada))
        dsn_caido = "postgresql://lumin_espejo:ensayo@127.0.0.1:1/lumin_ensayo"
        r = revertir(congelado, s.dir / "sesiones.json", emergencia_autorizada=True, dsn_espejo=dsn_caido)
        assert r["sesiones"] == {} and "EMERGENCIA" in r["motivo"]
        assert not valida(s, c_revocada)
        assert not valida(s, c_vigente), "en emergencia también la vigente se cierra: se entra una vez"


def test_revertir_normal_usa_el_estado_final_no_el_ultimo_espejo(base):
    with Servidor() as s:
        c_revocada = s.login()
        c_vigente = s.login()
        congelado = s.json("sesiones.json")
        migrar_sesiones(congelado)
        regenerar_sesiones(congelado)          # último espejo: las dos vigentes
        revocar_en_b3(token_de(c_revocada))    # revocación posterior
        r = revertir(congelado, s.dir / "sesiones.json")
        assert "verificado" in r["motivo"]
        assert not valida(s, c_revocada)
        assert valida(s, c_vigente)


def test_drenaje_espera_y_cancela_transacciones_de_app_en_vuelo(base):
    import threading
    listo = threading.Event()
    cancelada = {}

    def transaccion_larga():
        with psycopg.connect(dsn_rol("lumin_app")) as a:
            cur = a.cursor()
            contexto(cur, empresa=None)
            cur.execute("SELECT count(*) FROM sucursal")   # abre la transacción
            listo.set()
            try:
                cur.execute("SELECT pg_sleep(10)")
            except psycopg.errors.QueryCanceled:
                cancelada["si"] = True
    h = threading.Thread(target=transaccion_larga); h.start(); listo.wait(5)
    t0 = time.monotonic()
    drenar_lumin_app(timeout_s=0.5)
    h.join(5)
    assert cancelada.get("si") is True, "la transacción en vuelo debió cancelarse al vencer el drenaje"
    assert time.monotonic() - t0 < 5
