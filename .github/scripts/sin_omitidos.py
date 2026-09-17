#!/usr/bin/env python3
"""Falla si un informe JUnit de pytest tiene pruebas omitidas, errores o
fallos, o menos pruebas ejecutadas que el mínimo esperado.

    python sin_omitidos.py informe.xml [--minimo N]

Motivo: los ensayos de B3 se OMITEN cuando falta la base de ensayo. Un
trabajo verde con todo omitido no es evidencia; este guardián lo convierte en
rojo. Solo lectura del XML; no toca nada más.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("informe")
    ap.add_argument("--minimo", type=int, default=1, help="pruebas ejecutadas (no omitidas) mínimas")
    a = ap.parse_args()

    raiz = ET.parse(a.informe).getroot()
    suites = [raiz] if raiz.tag == "testsuite" else list(raiz.iter("testsuite"))
    total = sum(int(s.get("tests", 0)) for s in suites)
    omitidas = sum(int(s.get("skipped", 0)) for s in suites)
    fallos = sum(int(s.get("failures", 0)) for s in suites)
    errores = sum(int(s.get("errors", 0)) for s in suites)
    ejecutadas = total - omitidas
    print(f"{a.informe}: total={total} ejecutadas={ejecutadas} omitidas={omitidas} fallos={fallos} errores={errores}")

    for caso in raiz.iter("testcase"):
        s = caso.find("skipped")
        if s is not None:
            print(f"  OMITIDA {caso.get('classname')}::{caso.get('name')}: {s.get('message', '')}")

    if fallos or errores:
        print("hay fallos o errores")
        return 1
    if omitidas:
        print("hay pruebas omitidas: no se acepta como evidencia")
        return 1
    if ejecutadas < a.minimo:
        print(f"se ejecutaron {ejecutadas} < {a.minimo} esperadas")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
