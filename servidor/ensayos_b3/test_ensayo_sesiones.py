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

from comun import BASE, USUARIO_1, contexto, dsn_rol, preparar_base

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


class DrenajeIncompleto(ReversionBloqueada):
    pass


def cerrar_entrada_lumin_app(conn) -> None:
    """Paso 1 del drenaje: ningun escritor nuevo. REVOKE CONNECT impide
    conexiones nuevas de lumin_app; las ya abiertas se tratan en el paso 2."""
    conn.execute(f"REVOKE CONNECT ON DATABASE {BASE} FROM lumin_app")


def reabrir_entrada_lumin_app(conn) -> None:
    conn.execute(f"GRANT CONNECT ON DATABASE {BASE} TO lumin_app")


def _backends_app(cur):
    """TODAS las conexiones de lumin_app (pid, estado, con transaccion viva)."""
    return cur.execute(
        "SELECT pid, state, backend_xid IS NOT NULL OR state LIKE 'idle in transaction%%' OR state = 'active' "
        "FROM pg_stat_activity WHERE usename = 'lumin_app' AND pid <> pg_backend_pid()").fetchall()


def drenar_lumin_app(timeout_s: float = 30.0) -> None:
    """Drenaje rev. 6 (B3-R4-01, segunda vuelta). Contrato:
      1. cerrar la entrada (REVOKE CONNECT): ninguna conexion nueva;
      2. gracia: esperar hasta timeout_s a que ninguna conexion de lumin_app
         tenga una transaccion capaz de confirmar (activa, idle in transaction
         o con xid). Es cortesia con lo que ya estaba a medias, no la barrera;
      3. la barrera: TERMINAR TODAS las sesiones de lumin_app, tambien las
         'idle' (una conexion de pool ya abierta no necesita CONNECT para
         empezar una transaccion nueva: Codex lo reprodujo). Una sesion
         terminada hace rollback, nunca commit;
      4. verificar que queda CERO sesiones de lumin_app; si no, DrenajeIncompleto
         y la reversion se bloquea. Con la entrada cerrada, cero sesiones ahora
         significa cero escritores para siempre hasta que se reabra.
    Solo se toca el rol lumin_app de ESTA base. La entrada se reabre solo si el
    llamador lo pide (al abortar la reversion o al volver a 6.11)."""
    import time as _t
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        cerrar_entrada_lumin_app(c)
        cur = c.cursor()
        fin = _t.monotonic() + timeout_s
        while _t.monotonic() < fin and any(viva for _, _, viva in _backends_app(cur)):
            _t.sleep(0.05)
        for pid, _, _ in _backends_app(cur):
            cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
        fin2 = _t.monotonic() + 5.0
        while _t.monotonic() < fin2:
            restantes = [pid for pid, _, _ in _backends_app(cur)]
            if not restantes:
                return
            _t.sleep(0.05)
        raise DrenajeIncompleto(f"sesiones de lumin_app que siguen abiertas tras terminar: {restantes}")


def sesiones_app_abiertas() -> int:
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        return len(_backends_app(c.cursor()))


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
        drenar_lumin_app(timeout_s=1.0)          # DrenajeIncompleto => ReversionBloqueada
        with psycopg.connect(dsn_espejo or dsn_rol("lumin_espejo"), connect_timeout=2) as c:
            c.execute("SELECT 1")
        sesiones = regenerar_sesiones(congelado)
        motivo = "verificado contra PostgreSQL tras drenar"
    except DrenajeIncompleto:
        raise
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


def _abrir_transaccion_app(evento_listo, evento_soltar, resultado, *, dormir=False):
    """Hilo: abre una mutacion como lumin_app y la deja SIN confirmar hasta que
    se le indique (idle in transaction) o ejecuta una consulta larga (activa)."""
    import uuid
    from comun import EMPRESA_A, mutar_sucursal
    try:
        with psycopg.connect(dsn_rol("lumin_app")) as a:
            mutar_sucursal(a, EMPRESA_A, "tardia-" + uuid.uuid4().hex[:6], "Tardia", confirmar=False)
            evento_listo.set()
            if dormir:
                a.execute("SELECT pg_sleep(30)")
            evento_soltar.wait(10)
            a.commit()
            resultado["commit"] = True
    except Exception as e:  # noqa: BLE001 - el ensayo quiere el tipo exacto
        resultado["error"] = type(e).__name__
    finally:
        evento_listo.set()


def _cuenta_tardias():
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        return c.execute("SELECT count(*) FROM sucursal WHERE clave LIKE 'tardia-%%'").fetchone()[0]


def _reabrir():
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        reabrir_entrada_lumin_app(c)


def test_reproduccion_r4_01_cancelar_no_impide_el_commit_tardio(base):
    """Lo que Codex demostro: pg_cancel_backend sobre 'idle in transaction' no
    hace nada y el commit posterior tiene exito."""
    import threading
    listo, soltar, res = threading.Event(), threading.Event(), {}
    h = threading.Thread(target=_abrir_transaccion_app, args=(listo, soltar, res)); h.start(); listo.wait(5)
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        for (pid,) in c.execute("SELECT pid FROM pg_stat_activity WHERE usename = 'lumin_app' AND state <> 'idle'").fetchall():
            c.execute("SELECT pg_cancel_backend(%s)", (pid,))
        estado = c.execute("SELECT state FROM pg_stat_activity WHERE usename = 'lumin_app'").fetchone()[0]
    assert estado == "idle in transaction"
    soltar.set(); h.join(5)
    assert res.get("commit") is True and _cuenta_tardias() == 1, "el commit tardio paso: el drenaje viejo era insuficiente"


def test_drenaje_termina_idle_in_transaction_y_el_commit_tardio_falla(base):
    import threading
    listo, soltar, res = threading.Event(), threading.Event(), {}
    h = threading.Thread(target=_abrir_transaccion_app, args=(listo, soltar, res)); h.start(); listo.wait(5)
    try:
        drenar_lumin_app(timeout_s=0.3)
        soltar.set(); h.join(5)
        assert res.get("commit") is not True and res.get("error"), res
        assert _cuenta_tardias() == 0, "nada de la transaccion terminada quedo confirmado"
    finally:
        _reabrir()


def test_drenaje_termina_una_consulta_activa(base):
    import threading
    listo, soltar, res = threading.Event(), threading.Event(), {}
    h = threading.Thread(target=_abrir_transaccion_app, args=(listo, soltar, res), kwargs={"dormir": True}); h.start(); listo.wait(5)
    time.sleep(0.2)   # que pg_sleep este corriendo
    try:
        t0 = time.monotonic()
        drenar_lumin_app(timeout_s=0.3)
        assert time.monotonic() - t0 < 5
        soltar.set(); h.join(5)
        assert res.get("commit") is not True and _cuenta_tardias() == 0
    finally:
        _reabrir()


def test_drenaje_cierra_la_entrada_a_nuevos_escritores(base):
    try:
        drenar_lumin_app(timeout_s=0.1)   # sin nadie dentro: termina enseguida, pero la puerta queda cerrada
        with pytest.raises(psycopg.OperationalError):
            psycopg.connect(dsn_rol("lumin_app"), connect_timeout=2)
    finally:
        _reabrir()
    psycopg.connect(dsn_rol("lumin_app"), connect_timeout=2).close()


def test_drenaje_espera_a_una_transaccion_que_confirma_a_tiempo(base):
    """Una transaccion que confirma dentro del plazo NO se pierde: se drena, no se mata."""
    import threading
    listo, soltar, res = threading.Event(), threading.Event(), {}
    h = threading.Thread(target=_abrir_transaccion_app, args=(listo, soltar, res)); h.start(); listo.wait(5)
    threading.Timer(0.2, soltar.set).start()
    try:
        drenar_lumin_app(timeout_s=3.0)
        h.join(5)
        assert res.get("commit") is True and _cuenta_tardias() == 1
    finally:
        _reabrir()


def test_revertir_se_bloquea_si_el_drenaje_no_puede_completarse(base, monkeypatch):
    """Si tras terminar aun quedara una transaccion viva (no deberia ocurrir en
    PostgreSQL, pero el contrato lo cubre), revertir no escribe nada."""
    import test_ensayo_sesiones as yo
    def falso_drenaje(timeout_s=30.0):
        raise DrenajeIncompleto("simulado")
    monkeypatch.setattr(yo, "drenar_lumin_app", falso_drenaje)
    with Servidor() as s:
        s.login()
        congelado = s.json("sesiones.json")
        antes = (s.dir / "sesiones.json").read_bytes()
        with pytest.raises(ReversionBloqueada):
            revertir(congelado, s.dir / "sesiones.json", emergencia_autorizada=True)
        assert (s.dir / "sesiones.json").read_bytes() == antes, "ni en emergencia se escribe con drenaje incompleto"


def test_reproduccion_r4_01b_idle_preexistente_podia_escribir_despues(base):
    """Lo que Codex reprodujo sobre la rev. 5: una conexion idle sobrevive al
    drenaje viejo (solo mataba transacciones vivas) y escribe despues."""
    import uuid
    from comun import EMPRESA_A, mutar_sucursal
    a = psycopg.connect(dsn_rol("lumin_app"))            # abierta, idle, sin transaccion
    try:
        with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
            cerrar_entrada_lumin_app(c)                   # el drenaje viejo: puerta cerrada...
            cur = c.cursor()
            assert not any(viva for _, _, viva in _backends_app(cur))   # ...y "nada peligroso": retornaba aqui
        mutar_sucursal(a, EMPRESA_A, "tardia-" + uuid.uuid4().hex[:6], "Tardia")   # commit=True
        assert _cuenta_tardias() == 1, "la idle preexistente escribio tras la barrera vieja"
    finally:
        a.close(); _reabrir()


def test_drenaje_termina_tambien_las_sesiones_idle(base):
    import uuid
    from comun import EMPRESA_A, mutar_sucursal
    a = psycopg.connect(dsn_rol("lumin_app"))
    try:
        assert sesiones_app_abiertas() == 1
        drenar_lumin_app(timeout_s=0.1)
        assert sesiones_app_abiertas() == 0
        with pytest.raises(psycopg.OperationalError):
            mutar_sucursal(a, EMPRESA_A, "tardia-" + uuid.uuid4().hex[:6], "Tardia")
        assert _cuenta_tardias() == 0
        with pytest.raises(psycopg.OperationalError):                 # y no puede volver a entrar
            psycopg.connect(dsn_rol("lumin_app"), connect_timeout=2)
    finally:
        try:
            a.close()
        except Exception:  # noqa: BLE001
            pass
        _reabrir()


def test_peticion_admitida_antes_de_la_barrera_que_empieza_su_sql_despues(base):
    """Un hilo HTTP ya tiene conexion del pool y 'esta pensando' cuando cae la
    barrera; cuando intenta su primer SQL, la sesion ya no existe."""
    import threading, uuid
    from comun import EMPRESA_A, mutar_sucursal
    a = psycopg.connect(dsn_rol("lumin_app"))
    barrera = threading.Event(); res = {}

    def peticion_lenta():
        barrera.wait(5)                                   # "procesando" sin haber tocado la base
        try:
            mutar_sucursal(a, EMPRESA_A, "tardia-" + uuid.uuid4().hex[:6], "Tardia")
            res["commit"] = True
        except Exception as e:  # noqa: BLE001
            res["error"] = type(e).__name__
    h = threading.Thread(target=peticion_lenta); h.start()
    try:
        drenar_lumin_app(timeout_s=0.1)
        barrera.set(); h.join(5)
        assert res.get("commit") is not True and res.get("error"), res
        assert _cuenta_tardias() == 0
    finally:
        try:
            a.close()
        except Exception:  # noqa: BLE001
            pass
        _reabrir()


def test_drenaje_no_toca_otros_roles(base):
    """Acotado al rol de aplicacion: el espejo y la migracion siguen conectados."""
    e = psycopg.connect(dsn_rol("lumin_espejo"))
    try:
        drenar_lumin_app(timeout_s=0.1)
        assert e.execute("SELECT 1").fetchone()[0] == 1
        psycopg.connect(dsn_rol("lumin_migracion"), connect_timeout=2).close()
    finally:
        e.close(); _reabrir()
