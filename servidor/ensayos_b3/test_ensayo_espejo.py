"""B3-R2-01: el espejo derivado no puede guiarse por max(espejo_marca.id).

Ensayo del protocolo, con dos conexiones reales y el orden exacto que pidió
Codex: A reserva marca y queda abierta · B reserva y confirma · corre el
espejo · A confirma. El protocolo viejo (max(id) > ultima_aplicada) pierde A
para siempre; el nuevo (marcas PENDIENTES leídas dentro de una instantánea
REPEATABLE READ y marcadas después de escribir) converge solo. Se añaden los
tres cortes: tras escribir los archivos y antes de marcar, a mitad de los
archivos, y fallo al persistir el marcador en disco.

Prototipo del protocolo, no código del producto (B3 no se implementa aún).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
import pytest

from comun import EMPRESA_A, dsn_rol, mutar_sucursal, preparar_base


# ------------------------------------------------------------ exportadores

def _documentos(cur) -> dict[str, object]:
    """Los 'documentos' del espejo en este ensayo: dos, para poder cortar a la mitad."""
    empresas = [dict(id=str(i), clave=c, estado=e) for i, c, e in
                cur.execute("SELECT id, clave, estado FROM empresa ORDER BY clave")]
    sucursales = [dict(empresa=str(e), clave=c, nombre=n) for e, c, n in
                  cur.execute("SELECT empresa_id, clave, nombre FROM sucursal ORDER BY empresa_id, clave")]
    return {"empresas.json": empresas, "sucursales.json": sucursales}


def _escribir_atomico(ruta: Path, datos) -> None:
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")
    os.replace(tmp, ruta)


class EspejoViejo:
    """Protocolo de la revisión 2: exporta si max(id) > ultima_aplicada."""

    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        self.ultima = 0

    def ciclo(self) -> bool:
        with psycopg.connect(dsn_rol("lumin_espejo")) as c:
            m = c.execute("SELECT coalesce(max(id), 0) FROM espejo_marca").fetchone()[0]
            if m <= self.ultima:
                return False
            docs = _documentos(c.cursor())
        for nombre, datos in docs.items():
            _escribir_atomico(self.carpeta / nombre, datos)
        self.ultima = m
        return True


class Espejo:
    """Protocolo de la revisión 3.

    1. Una transacción REPEATABLE READ (instantánea única) lee las marcas
       PENDIENTES que ve —solo las confirmadas— y TODOS los documentos.
       Cada marca visible confirmó junto con sus datos, así que la
       instantánea contiene exactamente lo que esas marcas anuncian.
    2. Escribe cada archivo entero o nada (temporal + os.replace).
    3. Solo entonces marca procesadas ESAS marcas y avanza espejo_estado.
    4. Escribe json-espejo.estado con la generación.
    Una marca de una transacción todavía abierta no se ve, no se marca, y se
    procesa en el ciclo siguiente a su confirmación. No se usa max(id).
    Al arrancar, el primer ciclo exporta siempre, haya o no pendientes.
    """

    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        self.arranque = True

    def instantanea(self):
        with psycopg.connect(dsn_rol("lumin_espejo")) as c:
            c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            cur = c.cursor()
            pendientes = [r[0] for r in cur.execute(
                "SELECT id FROM espejo_marca WHERE procesada_en IS NULL ORDER BY id")]
            docs = _documentos(cur)
            generacion = cur.execute("SELECT generacion FROM espejo_estado").fetchone()[0]
        return pendientes, docs, generacion

    def ciclo(self, *, escribir_hasta: int | None = None, marcar: bool = True,
              escribir_estado: bool = True) -> bool:
        pendientes, docs, generacion = self.instantanea()
        if not pendientes and not self.arranque:
            return False
        self.arranque = False
        for i, (nombre, datos) in enumerate(docs.items()):
            if escribir_hasta is not None and i >= escribir_hasta:
                return True  # "caída" a mitad de los archivos
            _escribir_atomico(self.carpeta / nombre, datos)
        if not marcar:
            return True  # "caída" tras escribir y antes de marcar
        with psycopg.connect(dsn_rol("lumin_espejo")) as c:
            c.execute("UPDATE espejo_marca SET procesada_en = now() WHERE id = ANY(%s)", (pendientes,))
            c.execute("UPDATE espejo_estado SET generacion = generacion + 1, exportada_en = now(), "
                      "marcas_cubiertas = %s", (pendientes,))
            generacion += 1
            c.commit()
        if escribir_estado:
            _escribir_atomico(self.carpeta / "json-espejo.estado", {"generacion": generacion})
        return True

    def sincronizado(self) -> tuple[bool, str]:
        """La definición operativa de 'sincronizado' (la usa revertir.py)."""
        pendientes, docs, generacion = self.instantanea()
        if pendientes:
            return False, f"marcas pendientes: {pendientes}"
        for nombre, datos in docs.items():
            ruta = self.carpeta / nombre
            if not ruta.exists() or json.loads(ruta.read_text(encoding="utf-8")) != datos:
                return False, f"{nombre} difiere de la exportación en memoria"
        estado = self.carpeta / "json-espejo.estado"
        if not estado.exists() or json.loads(estado.read_text(encoding="utf-8")).get("generacion") != generacion:
            return False, "json-espejo.estado no coincide con espejo_estado"
        return True, "sincronizado"


def en_disco(carpeta: Path) -> set[str]:
    p = carpeta / "sucursales.json"
    if not p.exists():
        return set()
    return {s["clave"] for s in json.loads(p.read_text(encoding="utf-8"))}


def en_base() -> set[str]:
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        return {r[0] for r in c.execute("SELECT clave FROM sucursal")}


# ------------------------------------------------------------------ pruebas

@pytest.fixture
def base():
    preparar_base()


def test_protocolo_viejo_pierde_la_transaccion_tardia(base, tmp_path):
    """Reproduce B3-R2-01 tal como lo describió Codex."""
    espejo = EspejoViejo(tmp_path)
    with psycopg.connect(dsn_rol("lumin_app")) as a, psycopg.connect(dsn_rol("lumin_app")) as b:
        mutar_sucursal(a, EMPRESA_A, "a", "A", confirmar=False)   # 1. A reserva marca 1, abierta
        mutar_sucursal(b, EMPRESA_A, "b", "B")                    # 2. B reserva marca 2 y confirma
        assert espejo.ciclo() is True                              # 3. espejo: max=2 > 0
        assert en_disco(tmp_path) == {"b"}
        a.commit()                                                 # 4. A confirma
    assert espejo.ciclo() is False                                 # 5. max sigue en 2: no exporta
    assert en_disco(tmp_path) == {"b"} and en_base() == {"a", "b"}, "el espejo viejo quedó divergente"


def test_protocolo_nuevo_converge_con_el_mismo_orden(base, tmp_path):
    espejo = Espejo(tmp_path)
    assert espejo.ciclo() is True  # arranque: exporta el estado inicial
    with psycopg.connect(dsn_rol("lumin_app")) as a, psycopg.connect(dsn_rol("lumin_app")) as b:
        mutar_sucursal(a, EMPRESA_A, "a", "A", confirmar=False)
        mutar_sucursal(b, EMPRESA_A, "b", "B")
        assert espejo.ciclo() is True
        assert en_disco(tmp_path) == {"b"}
        ok, motivo = espejo.sincronizado()
        assert ok, motivo  # con A abierta, lo confirmado SÍ está sincronizado
        a.commit()
    ok, motivo = espejo.sincronizado()
    assert not ok and "pendientes" in motivo  # la marca de A ahora se ve y está pendiente
    assert espejo.ciclo() is True
    assert en_disco(tmp_path) == {"a", "b"} == en_base()
    assert espejo.sincronizado()[0]
    with psycopg.connect(dsn_rol("lumin_migracion")) as c:
        assert c.execute("SELECT count(*) FROM espejo_marca WHERE procesada_en IS NULL").fetchone()[0] == 0
        assert c.execute("SELECT generacion FROM espejo_estado").fetchone()[0] == 3
    assert espejo.ciclo() is False  # sin pendientes no hay trabajo


def test_marca_de_transaccion_abortada_no_queda_pendiente(base, tmp_path):
    espejo = Espejo(tmp_path)
    espejo.ciclo()
    with psycopg.connect(dsn_rol("lumin_app")) as a:
        mutar_sucursal(a, EMPRESA_A, "x", "X", confirmar=False)
        a.rollback()
    assert espejo.ciclo() is False
    assert espejo.sincronizado()[0]


def test_caida_tras_escribir_y_antes_de_marcar(base, tmp_path):
    espejo = Espejo(tmp_path)
    espejo.ciclo()
    with psycopg.connect(dsn_rol("lumin_app")) as a:
        mutar_sucursal(a, EMPRESA_A, "a", "A")
    assert espejo.ciclo(marcar=False) is True
    assert en_disco(tmp_path) == {"a"}
    ok, motivo = espejo.sincronizado()
    assert not ok and "pendientes" in motivo   # los archivos están bien pero la marca sigue viva
    assert espejo.ciclo() is True              # se rehace entero (idempotente) y se marca
    assert espejo.sincronizado()[0]


def test_caida_a_mitad_de_los_archivos(base, tmp_path):
    espejo = Espejo(tmp_path)
    espejo.ciclo()
    with psycopg.connect(dsn_rol("lumin_app")) as a:
        mutar_sucursal(a, EMPRESA_A, "a", "A")
    assert espejo.ciclo(escribir_hasta=1) is True   # escribió empresas.json, no sucursales.json
    assert en_disco(tmp_path) == set()
    ok, motivo = espejo.sincronizado()
    assert not ok
    assert espejo.ciclo() is True
    assert en_disco(tmp_path) == {"a"} and espejo.sincronizado()[0]


def test_fallo_al_persistir_el_marcador_en_disco(base, tmp_path):
    espejo = Espejo(tmp_path)
    espejo.ciclo()
    with psycopg.connect(dsn_rol("lumin_app")) as a:
        mutar_sucursal(a, EMPRESA_A, "a", "A")
    assert espejo.ciclo(escribir_estado=False) is True  # base marcada, disco atrasado
    ok, motivo = espejo.sincronizado()
    assert not ok and "json-espejo.estado" in motivo    # revertir.py se bloquearía aquí
    # regla de arranque: un espejo nuevo (reinicio del servicio) exporta una vez sin condiciones
    reiniciado = Espejo(tmp_path)
    assert reiniciado.ciclo() is True
    assert reiniciado.sincronizado()[0]
