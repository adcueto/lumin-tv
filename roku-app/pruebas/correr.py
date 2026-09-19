#!/usr/bin/env python3
"""Ejecuta los arneses fuera del dispositivo: planificacion (CacheTask.brs)
y escena (MainScene.brs).

    python3 roku-app/pruebas/correr.py                       # los dos, contra components/
    python3 roku-app/pruebas/correr.py <CacheTask.brs>       # planificacion contra otra copia
    python3 roku-app/pruebas/correr.py --escena <MainScene.brs>

Necesita el interprete brs (@rokucommunity/brs, probado con 0.47.6):

    npm install -g @rokucommunity/brs@0.47.6      # o BRS=/ruta/al/brs

Cada arnes se ejecuta con Cache_simulado.brs y el componente real indicado;
devuelve 0 solo si TODAS las lineas RESUMEN dicen "0 fallos".
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


ARNESES = {
    "planificacion": ("planificacion.brs", RAIZ / "components" / "CacheTask.brs", 1),
    "escena": ("escena.brs", RAIZ / "components" / "MainScene.brs", 1),
}


def correr_uno(brs: str, arnes: str, objetivo: Path) -> tuple[bool, int, int]:
    orden = [brs, "-n", str(AQUI / arnes), str(AQUI / "Cache_simulado.brs"), str(objetivo)]
    print(f"--- {arnes} contra {objetivo}")
    proc = subprocess.run(orden, cwd=AQUI, capture_output=True, text=True)
    salida = proc.stdout + proc.stderr
    print(salida)
    m = re.search(r"RESUMEN: (\d+) comprobaciones, (\d+) fallos", salida)
    if not m or "ERROR" in salida:
        print("el arnes no termino o el interprete reporto errores: no se acepta el resultado")
        return False, 0, 0
    return True, int(m.group(1)), int(m.group(2))


def main() -> int:
    brs = localizar_brs()
    if brs is None:
        print("no encuentro el interprete brs; instala @rokucommunity/brs@0.47.6 o exporta BRS=")
        return 2
    args = sys.argv[1:]
    tareas = []
    if args and args[0] == "--escena":
        tareas.append(("escena.brs", Path(args[1]).resolve() if len(args) > 1 else ARNESES["escena"][1]))
    elif args:
        tareas.append(("planificacion.brs", Path(args[0]).resolve()))
    else:
        tareas = [(a, o) for a, o, _ in ARNESES.values()]
    print("interprete:", brs)
    total_ok = True
    resumen = []
    for arnes, objetivo in tareas:
        if not objetivo.exists():
            print(f"no existe {objetivo}")
            return 2
        ok, comp, fallos = correr_uno(brs, arnes, objetivo)
        total_ok = total_ok and ok and fallos == 0 and comp > 0
        resumen.append(f"{arnes}: {comp} comprobaciones, {fallos} fallos")
    print("TOTAL: " + " | ".join(resumen))
    return 0 if total_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
