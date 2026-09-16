#!/usr/bin/env python3
"""Inventario de SOLO LECTURA para las decisiones D1 y D2 del diseño de B3.

    python3 inventario_decisiones.py /opt/lumin-tv

Lee tvs.json, sucursales.json y usuarios.json y muestra:

  D1  pantallas con numero repetido: id (parcial), sucursal, zona, ultimo
      contacto, desfase de rotacion actual y el numero que tomaria cada una
      con la regla propuesta (conserva el numero la de menor 'indice' de
      registro; la otra toma el siguiente libre). El archivo NO guarda fecha
      de alta, asi que "mas antigua" no se puede acreditar: se muestra lo que
      hay para que la decision sea de Adrian.

  D2  usuarios cuyo permiso efectivo hoy no coincide con lo que declaran:
      sucursales vacias (alcanzan TODAS), claves inexistentes (alcanzan la
      primera permitida) y el alcance efectivo resultante.

No escribe nada. No muestra hashes, sales ni tokens. Los identificadores de
pantalla se recortan a sus ultimos 6 caracteres, como hace el panel.
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path


def leer(base: Path, nombre: str, defecto):
    p = base / nombre
    if not p.exists():
        return defecto
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"  [aviso] no se pudo leer {nombre}: {e}")
        return defecto


def hace(segundos: int) -> str:
    if segundos < 0:
        return "?"
    if segundos < 3600:
        return f"hace {segundos // 60} min"
    if segundos < 86400:
        return f"hace {segundos // 3600} h"
    return f"hace {segundos // 86400} d"


def inventario_pantallas(tvs: dict, claves_sucursal: dict) -> list[dict]:
    ahora = int(time.time())
    filas = []
    for id_tv, info in tvs.items():
        if not isinstance(info, dict):
            continue
        indice = int(info.get("indice", 0) or 0)
        filas.append({
            "id": id_tv,
            "corto": id_tv[-6:],
            "indice": indice,
            "numero": indice + 1,
            "sucursal": info.get("sucursal", "") or "(pendiente)",
            "sucursal_nombre": claves_sucursal.get(info.get("sucursal", ""), ""),
            "zona": info.get("zona", "") or "",
            "aprobada": bool(info.get("aprobada", True)),
            "visto": hace(ahora - int(info.get("visto", 0) or 0)) if info.get("visto") else "nunca",
            "turnos": bool(info.get("turnos", False)),
            "lista": info.get("lista", "") or "(heredada)",
        })
    filas.sort(key=lambda f: (f["numero"], f["id"]))
    return filas


def duplicados_d1(filas: list[dict]) -> list[list[dict]]:
    por_numero = defaultdict(list)
    for f in filas:
        por_numero[f["numero"]].append(f)
    return [grupo for n, grupo in sorted(por_numero.items()) if len(grupo) > 1]


def propuesta_d1(filas: list[dict], grupos: list[list[dict]]) -> list[dict]:
    """Regla propuesta: en cada grupo conserva el numero la primera por orden de
    'indice' y luego de id (orden estable); las demas toman el siguiente numero
    libre. Es una PROPUESTA: la decision es del propietario."""
    usados = {f["numero"] for f in filas}
    siguiente = max(usados) + 1 if usados else 1
    cambios = []
    for grupo in grupos:
        grupo = sorted(grupo, key=lambda f: (f["indice"], f["id"]))
        for f in grupo[1:]:
            while siguiente in usados:
                siguiente += 1
            cambios.append({**f, "numero_propuesto": siguiente})
            usados.add(siguiente)
            siguiente += 1
    return cambios


def inventario_usuarios(usuarios: dict, sucursales: list[dict]) -> list[dict]:
    claves = [s["clave"] for s in sucursales if isinstance(s, dict) and "clave" in s]
    todas = set(claves)
    primera = claves[0] if claves else ""
    filas = []
    for nombre, u in usuarios.items():
        if not isinstance(u, dict):
            continue
        rol = u.get("rol", "usuario")
        declaradas = list(u.get("sucursales", []) or [])
        validas = [c for c in declaradas if c in todas]
        invalidas = [c for c in declaradas if c not in todas]
        if rol == "admin":
            efectivas, motivo = sorted(todas), "administrador"
        elif not declaradas:
            efectivas, motivo = sorted(todas), "LISTA VACIA -> hoy alcanza TODAS (QA-F01)"
        elif validas:
            efectivas, motivo = validas, "declaradas"
            if invalidas:
                motivo += f"; se ignoran claves inexistentes {invalidas}"
        else:
            efectivas, motivo = [primera], f"SOLO CLAVES INEXISTENTES {invalidas} -> hoy cae en la primera '{primera}' (QA-F01)"
        filas.append({
            "usuario": nombre,
            "rol": rol,
            "declaradas": declaradas,
            "efectivas": efectivas,
            "motivo": motivo,
            "revisar": rol != "admin" and (not declaradas or not validas or bool(invalidas)),
        })
    filas.sort(key=lambda f: (not f["revisar"], f["usuario"]))
    return filas


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    base = Path(sys.argv[1])
    tvs = leer(base, "tvs.json", {})
    sucursales = leer(base, "sucursales.json", [])
    usuarios = leer(base, "usuarios.json", {})
    claves_sucursal = {s["clave"]: s.get("nombre", "") for s in sucursales
                       if isinstance(s, dict) and "clave" in s}

    print(f"Inventario de solo lectura sobre {base}  ·  {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"pantallas: {len(tvs)}   sucursales: {len(sucursales)}   usuarios: {len(usuarios)}")

    # ------------------------------------------------------------ D1
    filas = inventario_pantallas(tvs, claves_sucursal)
    grupos = duplicados_d1(filas)
    print("\n== D1 · Pantallas con numero repetido ==")
    if not grupos:
        print("  ninguno")
    else:
        for grupo in grupos:
            print(f"\n  numero {grupo[0]['numero']} (P{grupo[0]['numero']}) lo comparten {len(grupo)} pantallas:")
            for f in sorted(grupo, key=lambda f: (f["indice"], f["id"])):
                print(f"    ...{f['corto']}  sucursal={f['sucursal']:<20} zona={f['zona']:<16} "
                      f"visto={f['visto']:<12} indice(desfase)={f['indice']}  "
                      f"turnos={'si' if f['turnos'] else 'no'}  lista={f['lista']}")
        cambios = propuesta_d1(filas, grupos)
        print("\n  Propuesta (NO aplicada; decide Adrian). Conserva el numero la de menor indice:")
        for c in cambios:
            print(f"    ...{c['corto']}  {c['sucursal']:<20} zona={c['zona']:<16} "
                  f"P{c['numero']} -> P{c['numero_propuesto']}")
        print("  Nota: tvs.json no guarda fecha de alta; 'visto' es el ultimo contacto, no la antiguedad.")
        print("  Efecto en rotacion: hoy las del mismo numero arrancan la lista en la misma posicion;")
        print("  en B3 el desfase se guarda aparte y se puede reasignar sin tocar el numero visible.")

    print("\n== Todas las pantallas (referencia) ==")
    for f in filas:
        print(f"  P{f['numero']:<3} ...{f['corto']}  {f['sucursal']:<20} zona={f['zona']:<16} "
              f"{'aprobada' if f['aprobada'] else 'PENDIENTE':<9} visto={f['visto']}")

    # ------------------------------------------------------------ D2
    print("\n== D2 · Usuarios cuyo alcance efectivo requiere decision ==")
    us = inventario_usuarios(usuarios, sucursales)
    revisar = [u for u in us if u["revisar"]]
    if not revisar:
        print("  ninguno: todos los operadores declaran solo sucursales existentes")
    for u in revisar:
        print(f"\n  {u['usuario']}  rol={u['rol']}")
        print(f"    declaradas : {u['declaradas'] or '[]'}")
        print(f"    efectivas  : {u['efectivas']}")
        print(f"    motivo     : {u['motivo']}")
        print(f"    a decidir  : que sucursales debe tener de verdad (B3 migra lo EFECTIVO de hoy,")
        print(f"                 explicito; B4 aplica lo que decidas)")
    print("\n== Todos los usuarios (referencia, sin credenciales) ==")
    for u in us:
        print(f"  {u['usuario']:<20} rol={u['rol']:<8} efectivas={u['efectivas']}")
    print("\nNo se modifico ningun archivo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
