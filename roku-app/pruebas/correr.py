#!/usr/bin/env python3
"""Ejecuta el arnes de planificacion de CacheTask.brs fuera del dispositivo.

    python3 roku-app/pruebas/correr.py            # contra components/CacheTask.brs
    python3 roku-app/pruebas/correr.py <ruta.brs> # contra otra copia (p. ej. de otro commit)

Necesita el interprete brs (@rokucommunity/brs, probado con 0.47.6):

    npm install -g @rokucommunity/brs@0.47.6      # o BRS=/ruta/al/brs

Ejecuta planificacion.brs + Cache_simulado.brs + el CacheTask.brs indicado
con el interprete y devuelve 0 solo si la linea RESUMEN dice "0 fallos".
Lo que este arnes NO prueba esta escrito al principio de planificacion.brs.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent


def localizar_brs() -> str | None:
    if os.environ.get("BRS"):
        return os.environ["BRS"]
    for candidato in (shutil.which("brs"),
                      RAIZ / "node_modules" / ".bin" / "brs",
                      RAIZ.parent / "node_modules" / ".bin" / "brs"):
        if candidato and Path(candidato).exists():
            return str(candidato)
    return None


def main() -> int:
    objetivo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else RAIZ / "components" / "CacheTask.brs"
    brs = localizar_brs()
    if brs is None:
        print("no encuentro el interprete brs; instala @rokucommunity/brs@0.47.6 o exporta BRS=")
        return 2
    if not objetivo.exists():
        print(f"no existe {objetivo}")
        return 2
    orden = [brs, "-n", str(AQUI / "planificacion.brs"), str(AQUI / "Cache_simulado.brs"), str(objetivo)]
    print("interprete:", brs)
    print("objetivo  :", objetivo)
    proc = subprocess.run(orden, cwd=AQUI, capture_output=True, text=True)
    salida = proc.stdout + proc.stderr
    print(salida)
    m = re.search(r"RESUMEN: (\d+) comprobaciones, (\d+) fallos", salida)
    if not m:
        print("el arnes no termino (sin linea RESUMEN); revisa errores del interprete arriba")
        return 1
    comprobaciones, fallos = int(m.group(1)), int(m.group(2))
    if "ERROR" in salida:
        print("el interprete reporto errores de ejecucion: no se acepta el resultado")
        return 1
    return 0 if fallos == 0 and comprobaciones > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
