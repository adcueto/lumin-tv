#!/usr/bin/env python3
"""Corre la misma suite contra el servidor de otro commit, sin tocar el checkout.

Uso:
    python tests/comparar_con_base.py               # base: ea610d6 (6.9)
    python tests/comparar_con_base.py <sha>

Extrae servidor/servidor_lumin.py de ese commit con `git show` a un directorio
temporal, apunta el arnes ahi y ejecuta pytest. Imprime el SHA de cada lado y
el resumen, para pegarlo en la entrega. Corrige B2-QA-02: `git stash` no
revierte un cambio ya commiteado.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]      # raiz del repositorio
SERVIDOR = RAIZ / "servidor"
BASE_POR_DEFECTO = "ea610d6"


def sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def main() -> int:
    commit = sys.argv[1] if len(sys.argv) > 1 else BASE_POR_DEFECTO
    with tempfile.TemporaryDirectory(prefix="lumin-base-") as tmp:
        destino = Path(tmp) / "servidor_lumin.py"
        fuente = subprocess.run(
            ["git", "-C", str(RAIZ), "show", f"{commit}:servidor/servidor_lumin.py"],
            capture_output=True, check=True).stdout
        destino.write_bytes(fuente)
        commit_largo = subprocess.run(
            ["git", "-C", str(RAIZ), "rev-parse", commit],
            capture_output=True, text=True, check=True).stdout.strip()

        print(f"servidor bajo prueba : {commit_largo}  sha256={sha256(destino)}")
        print(f"arbol de trabajo     : sha256={sha256(SERVIDOR / 'servidor_lumin.py')}"
              "  (no se toca)")
        print("suite                : servidor/tests/test_b2_higiene.py\n")

        entorno = {**os.environ, "LUMIN_SERVIDOR_BAJO_PRUEBA": str(destino)}
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider",
             "-rf"],
            cwd=SERVIDOR, env=entorno)
        return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
