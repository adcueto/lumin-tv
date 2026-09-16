#!/usr/bin/env python3
"""Inventario de SOLO LECTURA para las decisiones D1 y D2 del diseño de B3.

    python3 inventario_decisiones.py /opt/lumin-tv

Lee tvs.json, sucursales.json y usuarios.json y muestra:

  D1  pantallas con numero repetido: alias, sucursal, zona, ultimo contacto,
      desfase de rotacion actual y el numero que tomaria cada una con la regla
      propuesta (conserva el numero la primera por 'indice' y, a igualdad de
      indice, la de identificador menor: es un orden estable, NO antiguedad).
      El archivo no guarda fecha de alta, asi que "mas antigua" no se puede
      acreditar: se muestra lo que hay para que la decision sea de Adrian.

  D2  usuarios cuyo permiso efectivo hoy no coincide con lo que declaran:
      sucursales vacias (alcanzan TODAS), claves inexistentes (alcanzan la
      primera permitida) y el alcance efectivo resultante.

Validacion (INV-01): los tres archivos son obligatorios y deben tener el
esquema esperado. Si falta alguno, no se puede leer o no tiene la forma
esperada, la herramienta NO imprime conclusiones y termina con codigo 2.
Un archivo valido pero vacio se informa como tal, distinto de "faltante".

No escribe nada. No muestra hashes, sales ni tokens. Los identificadores de
pantalla se recortan al sufijo mas corto (minimo 6 caracteres) que los deja
distintos entre si; el mapeo alias -> id completo se imprime al final para
que la tabla de decision sea inequivoca.
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

SALIDA_OK = 0
SALIDA_USO = 2
SALIDA_DATOS = 2


class DatosInvalidos(Exception):
    pass


# --------------------------------------------------------------- lectura

def leer_obligatorio(base: Path, nombre: str, tipo: type, descripcion: str):
    p = base / nombre
    if not p.is_file():
        raise DatosInvalidos(f"falta {nombre} en {base}")
    try:
        texto = p.read_text(encoding="utf-8")
    except OSError as e:
        raise DatosInvalidos(f"no se pudo leer {nombre}: {e}") from e
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as e:
        raise DatosInvalidos(f"{nombre} no es JSON valido: linea {e.lineno}, columna {e.colno}") from e
    if not isinstance(datos, tipo):
        raise DatosInvalidos(f"{nombre} deberia ser {descripcion}; es {type(datos).__name__}")
    return datos


def validar_esquema(tvs: dict, sucursales: list, usuarios: dict) -> None:
    for id_tv, info in tvs.items():
        if not isinstance(id_tv, str) or not id_tv:
            raise DatosInvalidos("tvs.json: identificador de pantalla vacio o no textual")
        if not isinstance(info, dict):
            raise DatosInvalidos(f"tvs.json: la pantalla {id_tv[-6:]!r} no es un objeto")
        try:
            int(info.get("indice", 0) or 0)
        except (TypeError, ValueError):
            raise DatosInvalidos(f"tvs.json: 'indice' no numerico en la pantalla ...{id_tv[-6:]}")
    for i, s in enumerate(sucursales):
        if not isinstance(s, dict) or not isinstance(s.get("clave"), str) or not s["clave"]:
            raise DatosInvalidos(f"sucursales.json: la entrada {i} no tiene 'clave' textual")
    for nombre, u in usuarios.items():
        if not isinstance(u, dict):
            raise DatosInvalidos(f"usuarios.json: el usuario {nombre!r} no es un objeto")
        if "sucursales" in u and u["sucursales"] is not None and not isinstance(u["sucursales"], list):
            raise DatosInvalidos(f"usuarios.json: 'sucursales' de {nombre!r} no es una lista")


def cargar(base: Path) -> tuple[dict, list, dict]:
    if not base.is_dir():
        raise DatosInvalidos(f"{base} no es un directorio")
    tvs = leer_obligatorio(base, "tvs.json", dict, "un objeto {id: pantalla}")
    sucursales = leer_obligatorio(base, "sucursales.json", list, "una lista de sucursales")
    usuarios = leer_obligatorio(base, "usuarios.json", dict, "un objeto {usuario: datos}")
    validar_esquema(tvs, sucursales, usuarios)
    return tvs, sucursales, usuarios


# --------------------------------------------------------------- utiles

def hace(segundos: int) -> str:
    if segundos < 0:
        return "?"
    if segundos < 3600:
        return f"hace {segundos // 60} min"
    if segundos < 86400:
        return f"hace {segundos // 3600} h"
    return f"hace {segundos // 86400} d"


def alias_unicos(ids: list[str], minimo: int = 6) -> dict[str, str]:
    """Sufijo mas corto (>= minimo) que distingue todos los identificadores."""
    if not ids:
        return {}
    largo = minimo
    tope = max(len(i) for i in ids)
    while largo < tope:
        sufijos = {i[-largo:] for i in ids}
        if len(sufijos) == len(set(ids)):
            break
        largo += 1
    return {i: i[-largo:] for i in ids}


def cantidad(n: int, que: str) -> str:
    return f"{n} {que}" + ("  (archivo valido, vacio)" if n == 0 else "")


# --------------------------------------------------------------- D1

def inventario_pantallas(tvs: dict, claves_sucursal: dict) -> list[dict]:
    ahora = int(time.time())
    alias = alias_unicos(list(tvs.keys()))
    filas = []
    for id_tv, info in tvs.items():
        indice = int(info.get("indice", 0) or 0)
        filas.append({
            "id": id_tv,
            "alias": alias[id_tv],
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
    """Regla propuesta: en cada grupo conserva el numero la primera por
    (indice, id); las demas toman el siguiente numero libre. Como las
    pantallas de un grupo comparten numero, casi siempre comparten indice: el
    desempate real es el identificador. Es una PROPUESTA: decide el propietario."""
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


# --------------------------------------------------------------- D2

def inventario_usuarios(usuarios: dict, sucursales: list[dict]) -> list[dict]:
    claves = [s["clave"] for s in sucursales]
    todas = set(claves)
    primera = claves[0] if claves else ""
    filas = []
    for nombre, u in usuarios.items():
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


# --------------------------------------------------------------- informe

def imprimir_informe(base: Path, tvs: dict, sucursales: list, usuarios: dict) -> None:
    claves_sucursal = {s["clave"]: s.get("nombre", "") for s in sucursales}

    print(f"Inventario de solo lectura sobre {base}  ·  {time.strftime('%Y-%m-%d %H:%M')}")
    print("Archivos leidos y validados: tvs.json, sucursales.json, usuarios.json")
    print(f"  {cantidad(len(tvs), 'pantallas')}")
    print(f"  {cantidad(len(sucursales), 'sucursales')}")
    print(f"  {cantidad(len(usuarios), 'usuarios')}")

    filas = inventario_pantallas(tvs, claves_sucursal)
    grupos = duplicados_d1(filas)
    print("\n== D1 · Pantallas con numero repetido ==")
    if not tvs:
        print("  sin pantallas registradas (archivo vacio): nada que decidir en D1")
    elif not grupos:
        print("  ninguno: todos los numeros son distintos")
    else:
        for grupo in grupos:
            print(f"\n  numero {grupo[0]['numero']} (P{grupo[0]['numero']}) lo comparten {len(grupo)} pantallas:")
            for f in sorted(grupo, key=lambda f: (f["indice"], f["id"])):
                print(f"    {f['alias']:<12} sucursal={f['sucursal']:<20} zona={f['zona']:<16} "
                      f"visto={f['visto']:<12} indice(desfase)={f['indice']}  "
                      f"turnos={'si' if f['turnos'] else 'no'}  lista={f['lista']}")
        cambios = propuesta_d1(filas, grupos)
        print("\n  Propuesta (NO aplicada; decide Adrian). Conserva el numero la primera por")
        print("  indice y, a igualdad de indice, la de identificador menor (orden estable,")
        print("  no antiguedad):")
        for c in cambios:
            print(f"    {c['alias']:<12} {c['sucursal']:<20} zona={c['zona']:<16} "
                  f"P{c['numero']} -> P{c['numero_propuesto']}")
        print("  Nota: tvs.json no guarda fecha de alta; 'visto' es el ultimo contacto, no la antiguedad.")
        print("  Efecto en rotacion: hoy las del mismo numero arrancan la lista en la misma posicion;")
        print("  en B3 el desfase se guarda aparte y se puede reasignar sin tocar el numero visible.")

    print("\n== Todas las pantallas (referencia) ==")
    if not filas:
        print("  (ninguna)")
    for f in filas:
        print(f"  P{f['numero']:<3} {f['alias']:<12} {f['sucursal']:<20} zona={f['zona']:<16} "
              f"{'aprobada' if f['aprobada'] else 'PENDIENTE':<9} visto={f['visto']}")

    print("\n== D2 · Usuarios cuyo alcance efectivo requiere decision ==")
    us = inventario_usuarios(usuarios, sucursales)
    revisar = [u for u in us if u["revisar"]]
    if not usuarios:
        print("  sin usuarios registrados (archivo vacio): nada que decidir en D2")
    elif not revisar:
        print("  ninguno: todos los operadores declaran solo sucursales existentes")
    for u in revisar:
        print(f"\n  {u['usuario']}  rol={u['rol']}")
        print(f"    declaradas : {u['declaradas'] or '[]'}")
        print(f"    efectivas  : {u['efectivas']}")
        print(f"    motivo     : {u['motivo']}")
        print("    a decidir  : que sucursales debe tener de verdad (B3 migra lo EFECTIVO de hoy,")
        print("                 explicito; B4 aplica lo que decidas)")
    print("\n== Todos los usuarios (referencia, sin credenciales) ==")
    if not us:
        print("  (ninguno)")
    for u in us:
        print(f"  {u['usuario']:<20} rol={u['rol']:<8} efectivas={u['efectivas']}")

    if filas:
        print("\n== Alias -> identificador completo de pantalla ==")
        for f in sorted(filas, key=lambda f: f["alias"]):
            print(f"  {f['alias']:<12} {f['id']}")
    print("\nNo se modifico ningun archivo.")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return SALIDA_USO
    base = Path(sys.argv[1])
    try:
        tvs, sucursales, usuarios = cargar(base)
    except DatosInvalidos as e:
        print(f"INVENTARIO NO GENERADO: {e}")
        print("Se requieren tvs.json, sucursales.json y usuarios.json legibles y con el esquema esperado.")
        print("No se imprimen conclusiones parciales para no dar por revisadas D1/D2 sin datos.")
        return SALIDA_DATOS
    imprimir_informe(base, tvs, sucursales, usuarios)
    return SALIDA_OK


if __name__ == "__main__":
    raise SystemExit(main())
