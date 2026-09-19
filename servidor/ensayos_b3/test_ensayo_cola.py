"""B3-R3-03: un trabajador atrasado no puede borrar el resultado publicado por otro.

El protocolo de la revisión 3 derivaba el nombre del artefacto de
destino/nombre/digest, así que dos posesiones del mismo trabajo compartían
archivo: A escribe, vence, B escribe el MISMO archivo y publica, A recibe 0
filas y "borra su archivo"... que es el de B. Revisión 4: el artefacto lleva la
POSESIÓN en el nombre; publicar es un solo UPDATE condicionado a la posesión
que además guarda la ruta; quien pierde borra solo lo que lleva SU posesión;
los huérfanos (archivo sin referencia en la base) los recoge un barrido.

Es el contrato para B5, ensayado con la tabla `trabajo` del DDL mínimo y un
directorio temporal. No implementa trabajadores.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import psycopg
import pytest

from comun import EMPRESA_A, contexto, dsn_rol, preparar_base


def _app():
    return psycopg.connect(dsn_rol("lumin_app"))


def encolar(tipo="convertir_video", digest="d1") -> uuid.UUID:
    with _app() as c:
        cur = c.cursor(); contexto(cur, empresa=EMPRESA_A)
        tid = cur.execute("INSERT INTO trabajo (empresa_id, tipo, clave_idem) VALUES (%s, %s, %s) RETURNING id",
                          (EMPRESA_A, tipo, f"{digest}:{tipo}:sucursal-x")).fetchone()[0]
        c.commit()
    return tid


def reclamar(quien: str) -> tuple[uuid.UUID, uuid.UUID] | None:
    """Un trabajador gana; recibe (id, posesion)."""
    with _app() as c:
        cur = c.cursor(); contexto(cur, empresa=EMPRESA_A)
        fila = cur.execute(
            "UPDATE trabajo SET estado = 'en_curso', posesion = gen_random_uuid(), latido_en = now(), intentos = intentos + 1 "
            "WHERE id = (SELECT id FROM trabajo WHERE estado = 'pendiente' AND no_antes_de <= now() "
            "            ORDER BY no_antes_de FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING id, posesion").fetchone()
        c.commit()
    return fila


def ruta_artefacto(carpeta: Path, nombre: str, digest: str, posesion: uuid.UUID) -> Path:
    # <nombre>.<digest8>.<posesion8>.mp4 : único por posesión, idempotente por reintento de la MISMA posesión
    return carpeta / f"{nombre}.{digest[:8]}.{posesion.hex[:8]}.mp4"


def escribir_artefacto(ruta: Path, contenido: bytes) -> None:
    tmp = ruta.with_suffix(".tmp")
    tmp.write_bytes(contenido)
    tmp.replace(ruta)


PUBLICADO = "publicado"          # este UPDATE publico
YA_PUBLICADO = "ya_publicado"    # la MISMA posesion ya lo habia publicado: exito idempotente
PERDIDO = "perdido"              # otra posesion gano, o el trabajo fue cancelado/reabierto


def publicar(tid: uuid.UUID, posesion: uuid.UUID, ruta: Path) -> str:
    """Rev. 5 (B3-R4-02). Un solo UPDATE condicionado a la posesion; si afecta 0
    filas se distingue, en la MISMA transaccion, entre "ya lo publique yo"
    (fila hecha con mi posesion y mi ruta: exito idempotente, el archivo se
    conserva) y "perdi la posesion" (descartar lo mio)."""
    with _app() as c:
        cur = c.cursor(); contexto(cur, empresa=EMPRESA_A)
        cur.execute("UPDATE trabajo SET estado = 'hecho', terminado_en = now(), resultado = %s "
                    "WHERE id = %s AND posesion = %s AND estado = 'en_curso'", (str(ruta), tid, posesion))
        if cur.rowcount == 1:
            c.commit()
            return PUBLICADO
        fila = cur.execute("SELECT estado, posesion, resultado FROM trabajo WHERE id = %s", (tid,)).fetchone()
        c.commit()
        if fila and fila[0] == "hecho" and fila[1] == posesion and fila[2] == str(ruta):
            return YA_PUBLICADO
        return PERDIDO


def al_perder(resultado: str, ruta_mia: Path, posesion: uuid.UUID) -> None:
    """Lo que hace el trabajador con el resultado de publicar. SOLO 'perdido'
    borra; 'ya_publicado' es exito y el artefacto esta referenciado."""
    if resultado == PERDIDO:
        descartar_lo_mio(ruta_mia, posesion)


def descartar_lo_mio(ruta_mia: Path, posesion: uuid.UUID) -> None:
    """Quien pierde borra SOLO el artefacto que lleva su posesión en el nombre."""
    assert posesion.hex[:8] in ruta_mia.name
    ruta_mia.unlink(missing_ok=True)


def barrido_en_curso_vencidos(segundos: float) -> int:
    """Devuelve a pendiente los en_curso sin latido; la posesión vieja muere."""
    with psycopg.connect(dsn_rol("lumin_migracion"), autocommit=True) as c:
        cur = c.cursor()
        cur.execute("UPDATE trabajo SET estado = 'pendiente', posesion = NULL "
                    "WHERE estado = 'en_curso' AND latido_en < now() - make_interval(secs => %s)", (segundos,))
        return cur.rowcount


def barrido_huerfanos(carpeta: Path) -> list[str]:
    """Borra artefactos que ninguna fila referencia (crash tras escribir y antes del UPDATE)."""
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        referenciados = {Path(r[0]).name for r in c.execute("SELECT resultado FROM trabajo WHERE resultado IS NOT NULL")}
        en_curso = {r[0].hex[:8] for r in c.execute("SELECT posesion FROM trabajo WHERE estado = 'en_curso' AND posesion IS NOT NULL")}
    borrados = []
    for f in carpeta.glob("*.mp4"):
        if f.name in referenciados:
            continue
        if any(p in f.name for p in en_curso):     # un trabajador vivo puede estar a punto de publicarlo
            continue
        f.unlink(); borrados.append(f.name)
    return borrados


def estado(tid: uuid.UUID):
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        return c.execute("SELECT estado, resultado FROM trabajo WHERE id = %s", (tid,)).fetchone()


@pytest.fixture
def base():
    preparar_base()


def test_rev3_el_nombre_compartido_pierde_el_resultado(base, tmp_path):
    """Reproduce B3-R3-03 con el protocolo de la revisión 3 (nombre sin posesión)."""
    tid = encolar()
    tid_a, pos_a = reclamar("A")
    ruta_compartida = tmp_path / "video.d1.mp4"
    escribir_artefacto(ruta_compartida, b"A")
    barrido_en_curso_vencidos(0)                    # A "vence" (latido viejo)
    tid_b, pos_b = reclamar("B")
    escribir_artefacto(ruta_compartida, b"B")       # mismo nombre
    assert publicar(tid_b, pos_b, ruta_compartida) == PUBLICADO
    assert publicar(tid_a, pos_a, ruta_compartida) == PERDIDO
    ruta_compartida.unlink()                        # "A borra su archivo" según el contrato viejo
    assert estado(tid) == ("hecho", str(ruta_compartida)) and not ruta_compartida.exists(), \
        "hecho sin archivo: el defecto que señaló Codex"


def test_rev4_a_vencido_b_publicado_a_descartado(base, tmp_path):
    tid = encolar()
    tid_a, pos_a = reclamar("A")
    ruta_a = ruta_artefacto(tmp_path, "video", "d1", pos_a)
    escribir_artefacto(ruta_a, b"A")
    assert barrido_en_curso_vencidos(0) == 1
    tid_b, pos_b = reclamar("B")
    assert tid_b == tid and pos_b != pos_a
    ruta_b = ruta_artefacto(tmp_path, "video", "d1", pos_b)
    assert ruta_b != ruta_a
    escribir_artefacto(ruta_b, b"B")
    assert publicar(tid_b, pos_b, ruta_b) == PUBLICADO
    r = publicar(tid_a, pos_a, ruta_a)
    assert r == PERDIDO                             # 0 filas y la fila es de B
    al_perder(r, ruta_a, pos_a)
    assert estado(tid) == ("hecho", str(ruta_b))
    assert ruta_b.exists() and ruta_b.read_bytes() == b"B" and not ruta_a.exists()
    assert barrido_huerfanos(tmp_path) == []       # nada que limpiar: lo publicado se respeta


def test_rev4_caida_tras_escribir_antes_del_update(base, tmp_path):
    tid = encolar()
    tid_a, pos_a = reclamar("A")
    ruta_a = ruta_artefacto(tmp_path, "video", "d1", pos_a)
    escribir_artefacto(ruta_a, b"A")
    # A muere aquí: archivo en disco, fila en_curso con su posesión
    assert barrido_huerfanos(tmp_path) == []       # mientras la posesión esté viva no se toca
    assert barrido_en_curso_vencidos(0) == 1       # vence
    assert barrido_huerfanos(tmp_path) == [ruta_a.name]   # ahora sí es huérfano
    tid_b, pos_b = reclamar("B")
    ruta_b = ruta_artefacto(tmp_path, "video", "d1", pos_b)
    escribir_artefacto(ruta_b, b"B")
    assert publicar(tid_b, pos_b, ruta_b) == PUBLICADO
    assert estado(tid) == ("hecho", str(ruta_b)) and ruta_b.exists()


def test_reproduccion_r4_02_el_contrato_viejo_borraba_lo_publicado(base, tmp_path):
    """Con la regla de la rev. 4 ("0 filas => descartar lo mio"), un reintento de
    la misma posesion tras una confirmacion cuya respuesta se perdio borraba el
    archivo publicado. Se reproduce con el UPDATE crudo, sin la distincion nueva."""
    tid = encolar()
    _, pos = reclamar("A")
    r1 = ruta_artefacto(tmp_path, "video", "d1", pos)
    escribir_artefacto(r1, b"A")
    assert publicar(tid, pos, r1) == PUBLICADO
    with _app() as c:                                   # el reintento "viejo": solo mira rowcount
        cur = c.cursor(); contexto(cur, empresa=EMPRESA_A)
        cur.execute("UPDATE trabajo SET estado = 'hecho' WHERE id = %s AND posesion = %s AND estado = 'en_curso'", (tid, pos))
        cero_filas = cur.rowcount == 0
        c.commit()
    assert cero_filas
    descartar_lo_mio(r1, pos)                            # lo que ordenaba el contrato viejo
    assert estado(tid) == ("hecho", str(r1)) and not r1.exists(), "hecho sin archivo: B3-R4-02"


def test_rev5_reintento_de_la_misma_posesion_es_exito_idempotente(base, tmp_path):
    tid = encolar()
    _, pos = reclamar("A")
    r1 = ruta_artefacto(tmp_path, "video", "d1", pos)
    escribir_artefacto(r1, b"A")
    escribir_artefacto(r1, b"A")                       # reescribir es inocuo
    assert publicar(tid, pos, r1) == PUBLICADO
    # se perdio la respuesta: el trabajador repite el recorrido completo
    escribir_artefacto(r1, b"A")
    r = publicar(tid, pos, r1)
    assert r == YA_PUBLICADO
    al_perder(r, r1, pos)                                # no borra nada
    assert estado(tid) == ("hecho", str(r1)) and r1.exists() and r1.read_bytes() == b"A"
    assert barrido_huerfanos(tmp_path) == []             # el artefacto esta referenciado


def test_rev5_reintento_tras_perder_la_posesion_sigue_descartando_lo_propio(base, tmp_path):
    """El control de trabajador vencido de otra posesion se conserva."""
    tid = encolar()
    _, pos_a = reclamar("A")
    ra = ruta_artefacto(tmp_path, "video", "d1", pos_a); escribir_artefacto(ra, b"A")
    barrido_en_curso_vencidos(0)
    _, pos_b = reclamar("B")
    rb = ruta_artefacto(tmp_path, "video", "d1", pos_b); escribir_artefacto(rb, b"B")
    assert publicar(tid, pos_b, rb) == PUBLICADO
    r = publicar(tid, pos_a, ra)
    assert r == PERDIDO
    al_perder(r, ra, pos_a)
    assert not ra.exists() and rb.exists() and estado(tid) == ("hecho", str(rb))
    # y un reintento de B despues de eso sigue siendo exito idempotente
    assert publicar(tid, pos_b, rb) == YA_PUBLICADO and rb.exists()


def test_cancelar_en_curso_hace_perder_la_posesion(base, tmp_path):
    tid = encolar()
    _, pos = reclamar("A")
    with _app() as c:
        cur = c.cursor(); contexto(cur, empresa=EMPRESA_A)
        cur.execute("UPDATE trabajo SET estado = 'cancelado', posesion = NULL WHERE id = %s", (tid,)); c.commit()
    r = ruta_artefacto(tmp_path, "video", "d1", pos)
    escribir_artefacto(r, b"A")
    res = publicar(tid, pos, r)
    assert res == PERDIDO
    al_perder(res, r, pos)
    assert estado(tid) == ("cancelado", None) and not r.exists()
