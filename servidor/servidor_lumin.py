#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LUMIN TV 4.0 — señalización digital para Roku
----------------------------------------------
- Sucursales: cada sucursal tiene su propio contenido, mensaje y pantallas.
- Pantallas con nombre de zona y control en vivo (pausa / reproducir).
- Enviar un video o foto a una pantalla específica al momento.
- Panel responsive (celular, tablet y computadora).
Las TVs consultan el servidor cada 4 segundos.

v6.10 (B2, higiene): bitacora de errores a archivo, cuatro carreras cerradas,
cola de conexiones de 5 a 64, los 404 ya no cuentan como reproduccion y las
pantallas nuevas ya no reutilizan numeros. Sin cambios de contrato.

v6.10.1 (B5a, estado real y operacion remota): el latido de la TV puede traer
parametros opcionales con su estado (version, modelo, sistema, IP, que
reproduce, MB en cache, ultimo error); se guardan en tvs.json y el panel los
muestra. Dos comandos nuevos: "recargar" y "vaciar_cache". Una app 5.1/5.2
que no manda parametros sigue funcionando igual: nada es obligatorio.
"""

import base64
import hashlib
import json
import logging
import logging.handlers
import os
import re
import shutil
import socket
import secrets
import subprocess
import sys
import threading
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import time
import unicodedata
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PUERTO = 8080

# ----- SEGURIDAD (usuario: admin) -----
CONTRASENA_PANEL = "adrian4321"

# ----- TV EN VERTICAL -----
GIRO_TV = "horario"   # si los videos salen de cabeza: "antihorario"
TV_VERTICAL = True

DURACION_IMAGEN = 10  # segundos por defecto para fotos

# Convierte TODOS los videos al mismo formato (1080p/30fps H.264).
# Transiciones más rápidas entre videos en la TV. Ponlo en False si
# prefieres conservar intactos los videos que ya vienen en H.264.
MODO_UNIFORME = True

BASE = os.path.dirname(os.path.abspath(__file__))
DIR_VIDEOS = os.path.join(BASE, "videos")
DIR_MINIATURAS = os.path.join(BASE, "miniaturas")
DIR_RAPIDOS = os.path.join(BASE, "rapidos")
ARCHIVO_SUCURSALES = os.path.join(BASE, "sucursales.json")
ARCHIVO_ORDENES = os.path.join(BASE, "ordenes.json")
ARCHIVO_LISTAS = os.path.join(BASE, "listas.json")
ARCHIVO_AJUSTES = os.path.join(BASE, "ajustes.json")
ARCHIVO_DURACIONES = os.path.join(BASE, "duraciones.json")
ARCHIVO_TVS = os.path.join(BASE, "tvs.json")
ARCHIVO_COMANDOS = os.path.join(BASE, "comandos.json")
ARCHIVO_GIRADOS = os.path.join(BASE, "girados.json")
ARCHIVO_TURNOS = os.path.join(BASE, "turnos.json")
ARCHIVO_PROGRAMACION = os.path.join(BASE, "programacion.json")
ARCHIVO_CONTADORES = os.path.join(BASE, "contadores.json")
ZONA_HORARIA = "America/Mexico_City"
ARCHIVO_USUARIOS = os.path.join(BASE, "usuarios.json")
ARCHIVO_SESIONES = os.path.join(BASE, "sesiones.json")
DIAS_SESION = 30

EXT_VIDEO = {".mp4", ".m4v", ".mov", ".mkv"}
EXT_IMAGEN = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
EXTENSIONES = EXT_VIDEO | EXT_IMAGEN

SUCURSAL_INICIAL = {"clave": "plaza-de-la-mujer", "nombre": "Plaza de la Mujer"}
SUCURSALES_BASE = [
    {"clave": "home", "nombre": "Home"},
    {"clave": "plaza-de-la-mujer", "nombre": "Plaza de la Mujer"},
    {"clave": "juriquilla", "nombre": "Juriquilla"},
    {"clave": "campanario", "nombre": "Campanario"},
    {"clave": "plaza-victoria", "nombre": "Plaza Victoria"},
]

os.makedirs(DIR_VIDEOS, exist_ok=True)
os.makedirs(DIR_MINIATURAS, exist_ok=True)
os.makedirs(DIR_RAPIDOS, exist_ok=True)

CANDADO = threading.RLock()

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

DIR_REGISTRO = os.path.join(BASE, "registro")


# ---------------- bitacora de errores ----------------
# Antes los fallos se tragaban en silencio (except: pass) y no quedaba rastro
# para diagnosticar. Ahora quedan en registro/lumin.log, con hora de Queretaro
# y rotacion para que nunca llene el disco del VPS.

class _FormatoLocal(logging.Formatter):
    def formatTime(self, registro, datefmt=None):
        t = datetime.fromtimestamp(registro.created, ZoneInfo(ZONA_HORARIA))
        return t.strftime(datefmt or "%Y-%m-%d %H:%M:%S")


def _abrir_bitacora():
    log = logging.getLogger("lumin." + os.path.basename(BASE))
    log.setLevel(logging.INFO)
    log.propagate = False
    formato = _FormatoLocal("%(asctime)s  %(levelname)-7s  %(message)s")
    try:
        os.makedirs(DIR_REGISTRO, exist_ok=True)
        archivo = logging.handlers.RotatingFileHandler(
            os.path.join(DIR_REGISTRO, "lumin.log"),
            maxBytes=2_000_000, backupCount=5, encoding="utf-8")
        archivo.setFormatter(formato)
        log.addHandler(archivo)
    except OSError:
        pass  # sin permiso de escritura: al menos queda la consola
    consola = logging.StreamHandler(sys.stderr)
    consola.setLevel(logging.WARNING)
    consola.setFormatter(formato)
    log.addHandler(consola)
    return log


bitacora = _abrir_bitacora()


# ---------------- utilidades ----------------

def ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def nombre_seguro(nombre):
    """Limpia el nombre sin perder acentos ni eñes (español)."""
    nombre = os.path.basename(str(nombre))
    nombre = nombre.replace("/", "_").replace("\\", "_")
    # se permiten letras y numeros de cualquier idioma, espacios y . _ - ( )
    nombre = "".join(
        c if (c.isalnum() or c in " ._-()") else "_"
        for c in nombre
    )
    nombre = re.sub(r"\s{2,}", " ", nombre)
    return nombre.strip(" .") or "archivo.mp4"


def clave_segura(clave):
    clave = re.sub(r"[^a-z0-9\-]", "", str(clave).lower())
    return clave or SUCURSAL_INICIAL["clave"]


def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto or "sucursal"


def leer_json(camino, defecto):
    with CANDADO:
        if os.path.exists(camino):
            try:
                with open(camino, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return defecto


def escribir_json(camino, datos):
    with CANDADO:
        temporal = camino + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(temporal, camino)


# ---------------- usuarios y sesiones ----------------

def _hash(contrasena, sal):
    return hashlib.sha256((sal + contrasena).encode()).hexdigest()


def usuarios():
    with CANDADO:
        u = leer_json(ARCHIVO_USUARIOS, {})
        if not u:
            # primer arranque: crear el administrador inicial
            sal = secrets.token_hex(8)
            u = {"admin": {"sal": sal, "hash": _hash(CONTRASENA_PANEL or "admin", sal),
                           "rol": "admin", "sucursales": []}}
            escribir_json(ARCHIVO_USUARIOS, u)
            bitacora.warning("usuario inicial 'admin' creado; cambiar su contrasena")
            print("  Usuario inicial creado: admin (cambia su contraseña pronto)")
        return u


def crear_usuario(nombre, contrasena, rol, claves):
    # Todo el leer-modificar-escribir bajo candado. Antes dos altas a la vez
    # se pisaban y una de las dos desaparecia sin aviso.
    with CANDADO:
        u = usuarios()
        nombre = re.sub(r"[^a-zA-Z0-9._\-]", "", nombre.lower())[:30]
        if not nombre or nombre in u or len(contrasena) < 4:
            return False
        sal = secrets.token_hex(8)
        u[nombre] = {"sal": sal, "hash": _hash(contrasena, sal),
                     "rol": "admin" if rol == "admin" else "usuario",
                     "sucursales": [clave_segura(c) for c in claves]}
        escribir_json(ARCHIVO_USUARIOS, u)
        return True


def verificar_credenciales(nombre, contrasena):
    u = usuarios().get(nombre.lower().strip())
    if not u:
        return False
    return _hash(contrasena, u["sal"]) == u["hash"]


def crear_sesion(nombre):
    # Bajo candado: dos logins simultaneos perdian una de las dos sesiones.
    with CANDADO:
        ses = leer_json(ARCHIVO_SESIONES, {})
        ahora = int(time.time())
        ses = {t: s for t, s in ses.items() if s.get("exp", 0) > ahora}
        token = secrets.token_urlsafe(32)
        ses[token] = {"usuario": nombre, "exp": ahora + DIAS_SESION * 86400}
        escribir_json(ARCHIVO_SESIONES, ses)
        return token


def usuario_de_token(token):
    if not token:
        return None
    ses = leer_json(ARCHIVO_SESIONES, {})
    s = ses.get(token)
    if not s or s.get("exp", 0) < int(time.time()):
        return None
    u = usuarios().get(s["usuario"])
    if not u:
        return None
    return {"usuario": s["usuario"], "rol": u.get("rol", "usuario"),
            "sucursales": u.get("sucursales", [])}


def cerrar_sesion(token):
    with CANDADO:
        ses = leer_json(ARCHIVO_SESIONES, {})
        if token in ses:
            del ses[token]
            escribir_json(ARCHIVO_SESIONES, ses)


def sucursales_permitidas(u):
    todas = sucursales()
    if u["rol"] == "admin" or not u["sucursales"]:
        return todas
    return [s for s in todas if s["clave"] in u["sucursales"]] or todas[:1]


# ---------------- sucursales ----------------

def sucursales():
    lista = leer_json(ARCHIVO_SUCURSALES, [])
    if not lista:
        lista = [SUCURSAL_INICIAL]
        escribir_json(ARCHIVO_SUCURSALES, lista)
    return lista


def existe_sucursal(clave):
    return any(s["clave"] == clave for s in sucursales())


def dir_videos(clave):
    d = os.path.join(DIR_VIDEOS, clave_segura(clave))
    os.makedirs(d, exist_ok=True)
    return d



def dir_rapidos(clave):
    d = os.path.join(DIR_RAPIDOS, clave_segura(clave))
    os.makedirs(d, exist_ok=True)
    return d


def dir_minis(clave):
    d = os.path.join(DIR_MINIATURAS, clave_segura(clave))
    os.makedirs(d, exist_ok=True)
    return d


def lista_archivos(clave):
    with CANDADO:
        carpeta = dir_videos(clave)
        en_disco = sorted(
            f for f in os.listdir(carpeta)
            if os.path.splitext(f)[1].lower() in EXTENSIONES
        )
        ordenes = leer_json(ARCHIVO_ORDENES, {})
        orden = [n for n in ordenes.get(clave, []) if n in en_disco]
        for n in en_disco:
            if n not in orden:
                orden.append(n)
        ordenes[clave] = orden
        escribir_json(ARCHIVO_ORDENES, ordenes)
        return orden


def biblioteca(clave):
    """Todos los archivos que existen en la nube para esa sucursal."""
    return lista_archivos(clave)


def _listas_crudas(clave):
    """Estructura de listas de la sucursal, creando la Principal la 1a vez."""
    todas = leer_json(ARCHIVO_LISTAS, {})
    suc = todas.get(clave)
    if not suc or not suc.get("listas"):
        suc = {"activa": "principal",
               "listas": {"principal": {"nombre": "Principal",
                                        "archivos": lista_archivos(clave)}}}
        todas[clave] = suc
        escribir_json(ARCHIVO_LISTAS, todas)
    return todas, suc


def listas_de(clave):
    with CANDADO:
        _, suc = _listas_crudas(clave)
        en_disco = set(lista_archivos(clave))
        salida = []
        for lid, l in suc["listas"].items():
            vigentes = [n for n in l.get("archivos", []) if n in en_disco]
            salida.append({"id": lid, "nombre": l.get("nombre", lid),
                           "cuantos": len(vigentes)})
        salida.sort(key=lambda x: x["nombre"].lower())
        return {"activa": suc.get("activa", "principal"), "listas": salida}


def archivos_de_lista(clave, lid=""):
    """Archivos de una lista (o de la activa), solo los que siguen en la nube."""
    with CANDADO:
        _, suc = _listas_crudas(clave)
        if lid not in suc["listas"]:
            lid = suc.get("activa", "principal")
        if lid not in suc["listas"]:
            lid = next(iter(suc["listas"]))
        en_disco = set(lista_archivos(clave))
        return [n for n in suc["listas"][lid].get("archivos", []) if n in en_disco]


def guardar_lista(clave, lid, archivos):
    with CANDADO:
        todas, suc = _listas_crudas(clave)
        if lid in suc["listas"]:
            suc["listas"][lid]["archivos"] = archivos
            todas[clave] = suc
            escribir_json(ARCHIVO_LISTAS, todas)


def lista_de_tv(clave, id_tv):
    """Lista asignada a esa pantalla; si no tiene, la activa de la sucursal."""
    asignada = leer_json(ARCHIVO_TVS, {}).get(id_tv, {}).get("lista", "")
    _, suc = _listas_crudas(clave)
    if asignada and asignada in suc["listas"]:
        return asignada
    return suc.get("activa", "principal")


def leer_ajustes(clave):
    todos = leer_json(ARCHIVO_AJUSTES, {})
    a = todos.get(clave, {})
    return {
        "mensaje": a.get("mensaje", ""),
        "animado": a.get("animado", True),
        "velocidad": a.get("velocidad", 130),
    }


def duracion_de(clave, nombre):
    todos = leer_json(ARCHIVO_DURACIONES, {})
    try:
        return max(3, min(120, int(todos.get(clave, {}).get(nombre, DURACION_IMAGEN))))
    except (TypeError, ValueError):
        return DURACION_IMAGEN


def marcar_girado(clave, nombre):
    # Bajo candado: dos subidas terminando a la vez perdian una marca de giro,
    # y el video afectado salia de cabeza en la TV.
    with CANDADO:
        g = leer_json(ARCHIVO_GIRADOS, {})
        g.setdefault(clave, {})[nombre] = True
        escribir_json(ARCHIVO_GIRADOS, g)


def esta_girado(clave, nombre):
    return leer_json(ARCHIVO_GIRADOS, {}).get(clave, {}).get(nombre, False)


def ahora_local():
    return datetime.now(ZoneInfo(ZONA_HORARIA))


def programacion_de(clave, nombre):
    return leer_json(ARCHIVO_PROGRAMACION, {}).get(clave, {}).get(nombre)


def contenido_activo(clave, nombre):
    """True si el contenido debe mostrarse ahora segun su programacion."""
    p = programacion_de(clave, nombre)
    if not p:
        return True
    ahora = ahora_local()
    hoy = ahora.date()
    try:
        if p.get("desde"):
            if hoy < date.fromisoformat(p["desde"]):
                return False
        if p.get("hasta"):
            if hoy > date.fromisoformat(p["hasta"]):
                return False
    except ValueError:
        pass
    dias = p.get("dias") or []
    if dias and ahora.weekday() not in dias:
        return False
    hini = p.get("hini", "")
    hfin = p.get("hfin", "")
    if hini and hfin:
        hora = ahora.strftime("%H:%M")
        if not (hini <= hora <= hfin):
            return False
    return True


def contar_reproduccion(clave, nombre):
    with CANDADO:
        c = leer_json(ARCHIVO_CONTADORES, {})
        hoy = ahora_local().date().isoformat()
        c.setdefault(clave, {}).setdefault(nombre, {})
        c[clave][nombre][hoy] = c[clave][nombre].get(hoy, 0) + 1
        # limpiar dias con mas de 60 dias de antiguedad
        limite = (ahora_local().date() - timedelta(days=60)).isoformat()
        for n in list(c[clave].keys()):
            c[clave][n] = {f: v for f, v in c[clave][n].items() if f >= limite}
        escribir_json(ARCHIVO_CONTADORES, c)


def generar_miniatura(clave, nombre):
    if not FFMPEG:
        return
    destino = os.path.join(dir_minis(clave), nombre + ".jpg")
    origen = os.path.join(dir_videos(clave), nombre)
    if os.path.exists(destino) or not os.path.isfile(origen):
        return
    es_imagen = os.path.splitext(nombre)[1].lower() in EXT_IMAGEN
    filtros = []
    if esta_girado(clave, nombre):
        # el video guardado viene pre-girado para la TV: enderezar la miniatura
        filtros.append("transpose=1" if GIRO_TV == "horario" else "transpose=2")
    filtros.append("scale=200:-2")
    cmd = [FFMPEG, "-y"]
    if not es_imagen:
        cmd += ["-ss", "1"]
    cmd += ["-i", origen, "-frames:v", "1", "-vf", ",".join(filtros), destino]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=120)
        if r.returncode != 0:
            bitacora.warning("miniatura fallida para %s/%s: %s", clave, nombre,
                             r.stderr.decode("utf-8", "replace")[-400:])
    except subprocess.SubprocessError as e:
        bitacora.error("ffmpeg no pudo generar la miniatura de %s/%s: %s",
                       clave, nombre, e)


# ---------------- pantallas y comandos ----------------

# Parametros opcionales del latido (app 5.2 build 61+): clave corta en la URL
# -> nombre guardado, con tope de longitud. Nada de esto es obligatorio.
ESTADO_TV_CAMPOS = {
    "v": ("version", 16), "m": ("modelo", 40), "os": ("sistema", 24),
    "ip": ("ip", 45), "r": ("reproduciendo", 80), "e": ("error", 120),
}


# Comandos que solo el administrador puede emitir (B5a). Se comprueba en la
# ruta, antes de encolar nada.
ACCIONES_SOLO_ADMIN = ("recargar", "vaciar_cache")


def estado_tv_de(params):
    """Extrae el estado reportado por la TV de los parametros del latido.
    Devuelve {} si no trae ninguno (app anterior)."""
    estado = {}
    for corto, (nombre, tope) in ESTADO_TV_CAMPOS.items():
        valor = params.get(corto, [""])[0]
        if valor:
            estado[nombre] = valor[:tope]
    try:
        if params.get("c"):
            estado["cache_mb"] = max(0, min(int(params["c"][0]), 100000))
    except ValueError:
        pass
    try:
        if params.get("eh") and "error" in estado:
            estado["error_hace"] = max(0, min(int(params["eh"][0]), 10**9))
    except ValueError:
        pass
    if params.get("k", [""])[0] == "1":
        estado["desde_cache"] = True
    return estado


def registrar_tv(id_tv, estado=None):
    with CANDADO:
        """Registra la TV; devuelve (indice, sucursal, aprobada, codigo).
        `estado` (B5a) es lo que la TV reporto en este latido; se guarda tal
        cual con la hora, para que el panel lo muestre."""
        if not id_tv:
            return 0, SUCURSAL_INICIAL["clave"], False, "000000"
        tvs = leer_json(ARCHIVO_TVS, {})
        if id_tv not in tvs:
            # pantalla nueva: queda PENDIENTE hasta que un admin la apruebe.
            # El numero es el siguiente al mayor en uso, NO la cantidad de
            # pantallas: con len() dar de baja una intermedia hacia que la
            # siguiente alta repitiera un numero (los dos "P6" del panel) y
            # ademas compartiera el desfase de rotacion de la lista.
            siguiente = max((int(t.get("indice", -1)) for t in tvs.values()), default=-1) + 1
            tvs[id_tv] = {"indice": siguiente, "sucursal": "", "zona": "",
                          "aprobada": False,
                          "codigo": str(secrets.randbelow(900000) + 100000)}
        t = tvs[id_tv]
        t["visto"] = int(time.time())
        t.setdefault("aprobada", True)  # entradas anteriores al sistema = aprobadas
        t.setdefault("codigo", "")
        t.setdefault("sucursal", sucursales()[0]["clave"])
        t.setdefault("zona", "")
        if estado:
            if "error_hace" in estado:
                # se guarda el instante absoluto del error, no "hace cuanto"
                estado["error_en"] = t["visto"] - estado.pop("error_hace")
            t["estado"] = estado
        escribir_json(ARCHIVO_TVS, tvs)
        return t["indice"], t["sucursal"], t["aprobada"], t["codigo"]


def pantallas(clave=None):
    tvs = leer_json(ARCHIVO_TVS, {})
    ahora = int(time.time())
    lista = []
    for id_tv, info in sorted(tvs.items(), key=lambda x: x[1].get("indice", 0)):
        if not info.get("aprobada", True):
            continue
        if clave and info.get("sucursal") != clave:
            continue
        lista.append({
            "id": id_tv,
            "numero": info.get("indice", 0) + 1,
            "corto": id_tv[-6:],
            "zona": info.get("zona", ""),
            "sucursal": info.get("sucursal", ""),
            "en_linea": (ahora - info.get("visto", 0)) < 30,
            "visto_hace": ahora - info.get("visto", 0),
            "turnos": info.get("turnos", False),
            "lista": info.get("lista", ""),
            "pausada": info.get("pausada", False),
            "silencio": info.get("silencio", False),
            "estado": info.get("estado", {}),
        })
    return lista


def pendientes():
    tvs = leer_json(ARCHIVO_TVS, {})
    ahora = int(time.time())
    lista = []
    for id_tv, info in tvs.items():
        if info.get("aprobada", True):
            continue
        lista.append({
            "id": id_tv,
            "corto": id_tv[-6:],
            "codigo": info.get("codigo", ""),
            "en_linea": (ahora - info.get("visto", 0)) < 30,
        })
    return lista


def enviar_comando(id_tv, accion, url="", tipo="", duracion=10):
    with CANDADO:
        if accion in ("pausa", "continuar", "silencio", "sonido"):
            tvs = leer_json(ARCHIVO_TVS, {})
            if id_tv in tvs:
                if accion == "pausa":
                    tvs[id_tv]["pausada"] = True
                elif accion == "continuar":
                    tvs[id_tv]["pausada"] = False
                elif accion == "silencio":
                    tvs[id_tv]["silencio"] = True
                else:
                    tvs[id_tv]["silencio"] = False
                escribir_json(ARCHIVO_TVS, tvs)
        comandos = leer_json(ARCHIVO_COMANDOS, {})
        previo = comandos.get(id_tv, {}).get("n", 0)
        comandos[id_tv] = {"n": previo + 1, "accion": accion, "url": url,
                           "tipo": tipo, "duracion": duracion}
        escribir_json(ARCHIVO_COMANDOS, comandos)


# ---------------- migración desde versiones anteriores ----------------

def migrar():
    # asegurar que existan las sucursales base
    lista = leer_json(ARCHIVO_SUCURSALES, [])
    claves = {s["clave"] for s in lista}
    cambio = False
    for s in SUCURSALES_BASE:
        if s["clave"] not in claves:
            lista.append(s)
            cambio = True
    if cambio:
        escribir_json(ARCHIVO_SUCURSALES, lista)
    # TVs registradas antes del sistema de aprobacion quedan aprobadas
    tvs = leer_json(ARCHIVO_TVS, {})
    cambio = False
    for info in tvs.values():
        if "aprobada" not in info:
            info["aprobada"] = True
            cambio = True
    if cambio:
        escribir_json(ARCHIVO_TVS, tvs)

    clave = sucursales()[0]["clave"]
    movidos = 0
    for f in list(os.listdir(DIR_VIDEOS)):
        origen = os.path.join(DIR_VIDEOS, f)
        if os.path.isfile(origen) and os.path.splitext(f)[1].lower() in EXTENSIONES:
            shutil.move(origen, os.path.join(dir_videos(clave), f))
            movidos += 1
    if movidos:
        print(f"  Migrados {movidos} archivo(s) a la sucursal {clave}")
    viejo_orden = os.path.join(BASE, "orden_playlist.json")
    if os.path.exists(viejo_orden):
        ordenes = leer_json(ARCHIVO_ORDENES, {})
        ordenes.setdefault(clave, leer_json(viejo_orden, []))
        escribir_json(ARCHIVO_ORDENES, ordenes)
        os.remove(viejo_orden)
    ajustes = leer_json(ARCHIVO_AJUSTES, {})
    if "mensaje" in ajustes:
        escribir_json(ARCHIVO_AJUSTES, {clave: ajustes})
    dur = leer_json(ARCHIVO_DURACIONES, {})
    if dur and all(not isinstance(v, dict) for v in dur.values()):
        escribir_json(ARCHIVO_DURACIONES, {clave: dur})
    for f in list(os.listdir(DIR_MINIATURAS)):
        origen = os.path.join(DIR_MINIATURAS, f)
        if os.path.isfile(origen):
            shutil.move(origen, os.path.join(dir_minis(clave), f))


# ---------------- conversión de video (TV vertical) ----------------

def analizar_video(camino):
    if not FFPROBE:
        return None
    try:
        salida = subprocess.run(
            [FFPROBE, "-v", "quiet", "-print_format", "json",
             "-show_streams", camino],
            capture_output=True, text=True, timeout=60,
        )
        datos = json.loads(salida.stdout)
        for s in datos.get("streams", []):
            if s.get("codec_type") == "video":
                rot = 0
                for sd in s.get("side_data_list", []) or []:
                    if "rotation" in sd:
                        rot = int(sd["rotation"])
                rot = int(s.get("tags", {}).get("rotate", rot) or rot)
                return (int(s.get("width", 0)), int(s.get("height", 0)),
                        rot % 360, s.get("codec_name", ""))
    except (subprocess.SubprocessError, json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def procesar_subida(camino):
    if os.path.splitext(camino)[1].lower() in EXT_IMAGEN:
        return None
    info = analizar_video(camino)
    if info is None:
        return None

    ancho, alto, rot, codec = info
    if rot in (90, 270):
        ancho, alto = alto, ancho

    es_vertical = alto > ancho
    necesita_codec = codec != "h264" or MODO_UNIFORME
    if not es_vertical and not necesita_codec:
        if not FFMPEG:
            return None
        temporal = camino + ".tmp.mp4"
        r = subprocess.run(
            [FFMPEG, "-y", "-i", camino, "-c", "copy",
             "-movflags", "+faststart", temporal],
            capture_output=True,
        )
        if r.returncode == 0 and os.path.getsize(temporal) > 0:
            os.replace(temporal, camino)
            return "optimizado"
        if os.path.exists(temporal):
            os.remove(temporal)
        return None
    if not FFMPEG:
        return "ffmpeg no instalado"

    filtros = []
    if es_vertical and TV_VERTICAL:
        filtros.append("transpose=2" if GIRO_TV == "horario" else "transpose=1")
    filtros.append("scale=1920:1080:force_original_aspect_ratio=decrease")
    filtros.append("pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black")

    temporal = camino + ".tmp.mp4"
    print(f"  Procesando {os.path.basename(camino)}...")
    resultado = subprocess.run(
        [FFMPEG, "-y", "-i", camino,
         "-vf", ",".join(filtros),
         "-r", "30",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart",
         temporal],
        capture_output=True,
    )
    if resultado.returncode == 0 and os.path.getsize(temporal) > 0:
        final = os.path.splitext(camino)[0] + ".mp4"
        os.replace(temporal, final)
        if final != camino and os.path.exists(camino):
            os.remove(camino)
        print("  Listo.")
        return "girado" if (es_vertical and TV_VERTICAL) else "procesado"
    if os.path.exists(temporal):
        os.remove(temporal)
    return "no se pudo procesar; se dejó el original"


# ---------------- servidor HTTP ----------------

TIPOS_MIME = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime",
              ".mkv": "video/x-matroska", ".jpg": "image/jpeg",
              ".jpeg": "image/jpeg", ".png": "image/png"}


class Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stdout.write("[%s] %s\n" % (self.address_string(), fmt % args))

    def _responder(self, codigo, cuerpo, tipo="application/json; charset=utf-8"):
        datos = cuerpo if isinstance(cuerpo, bytes) else cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def _json_body(self):
        largo = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(largo).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _token(self):
        galletas = self.headers.get("Cookie", "")
        for parte in galletas.split(";"):
            if "=" in parte:
                k, v = parte.strip().split("=", 1)
                if k == "sesion":
                    return v
        return ""

    def _usuario(self):
        return usuario_de_token(self._token())

    def _responder_cookie(self, codigo, cuerpo, cookie):
        datos = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Set-Cookie", cookie)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def _sucursal_de(self, params, u):
        permitidas = sucursales_permitidas(u)
        clave = clave_segura(params.get("sucursal", [""])[0])
        if not any(s["clave"] == clave for s in permitidas):
            clave = permitidas[0]["clave"]
        return clave

    def _tv_permitida(self, id_tv, u):
        tvs = leer_json(ARCHIVO_TVS, {})
        info = tvs.get(id_tv)
        if not info:
            return False
        return any(s["clave"] == info.get("sucursal")
                   for s in sucursales_permitidas(u))

    # --- GET ---
    def do_GET(self):
        ruta = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(ruta.query)

        # ---- rutas abiertas para las TVs ----
        if ruta.path == "/playlist.json":
            id_tv = params.get("id", [""])[0][:64]
            indice, clave, aprobada, codigo = registrar_tv(id_tv, estado_tv_de(params))
            if not aprobada:
                self._responder(200, json.dumps({
                    "pendiente": True,
                    "codigo": codigo,
                    "vertical": TV_VERTICAL,
                    "giro": GIRO_TV,
                }, ensure_ascii=False))
                return

            host = self.headers.get("Host", f"{ip_local()}:{PUERTO}")
            esquema = "https" if self.headers.get("X-Forwarded-Proto") == "https" else "http"
            lid = lista_de_tv(clave, id_tv)
            archivos = [n for n in archivos_de_lista(clave, lid)
                        if contenido_activo(clave, n)]
            if archivos:
                giro_lista = indice % len(archivos)
                archivos = archivos[giro_lista:] + archivos[:giro_lista]
            items = []
            for n in archivos:
                ext = os.path.splitext(n)[1].lower()
                tiene_mini = os.path.exists(os.path.join(dir_minis(clave), n + ".jpg"))
                items.append({
                    "title": os.path.splitext(n)[0],
                    "url": f"{esquema}://{host}/videos/{clave}/{urllib.parse.quote(n)}",
                    "tipo": "imagen" if ext in EXT_IMAGEN else "video",
                    "duracion": duracion_de(clave, n),
                    "mini": f"{esquema}://{host}/miniaturas/{clave}/{urllib.parse.quote(n)}.jpg" if tiene_mini else "",
                })
            ajustes = leer_ajustes(clave)
            comando = leer_json(ARCHIVO_COMANDOS, {}).get(id_tv, {"n": 0})
            turno = {"n": 0}
            if leer_json(ARCHIVO_TVS, {}).get(id_tv, {}).get("turnos", False):
                turno = leer_json(ARCHIVO_TURNOS, {}).get(clave, {"n": 0})
            self._responder(200, json.dumps({
                "videos": items,
                "mensaje": ajustes["mensaje"],
                "cintillo": ajustes["animado"],
                "velocidad": ajustes["velocidad"],
                "vertical": TV_VERTICAL,
                "giro": GIRO_TV,
                "comando": comando,
                "turno": turno,
            }, ensure_ascii=False))
            return

        if ruta.path.startswith("/videos/"):
            partes = ruta.path[len("/videos/"):].split("/", 1)
            if len(partes) == 2:
                clave_v = clave_segura(partes[0])
                nombre_v = nombre_seguro(urllib.parse.unquote(partes[1]))
                rango = self.headers.get("Range", "")
                # Solo cuenta si el archivo existe: antes un 404 (archivo
                # borrado, nombre mal escrito) inflaba las reproducciones.
                # Sigue siendo un conteo de DESCARGAS iniciadas, no de
                # reproducciones confirmadas: eso llega cuando la TV reporte.
                if (rango == "" or rango.startswith("bytes=0-")) and \
                        os.path.isfile(os.path.join(dir_videos(clave_v), nombre_v)):
                    contar_reproduccion(clave_v, nombre_v)
                self._servir_archivo(dir_videos(clave_v), nombre_v)
            else:
                self._responder(404, '{"error":"no existe"}')
            return


        if ruta.path.startswith("/rapidos/"):
            partes = ruta.path[len("/rapidos/"):].split("/", 1)
            if len(partes) == 2:
                self._servir_archivo(dir_rapidos(clave_segura(partes[0])),
                                     urllib.parse.unquote(partes[1]))
            else:
                self._responder(404, '{"error":"no existe"}')
            return

        if ruta.path.startswith("/miniaturas/"):
            partes = ruta.path[len("/miniaturas/"):].split("/", 1)
            if len(partes) == 2:
                camino = os.path.join(dir_minis(clave_segura(partes[0])),
                                      nombre_seguro(urllib.parse.unquote(partes[1])))
                if os.path.isfile(camino):
                    with open(camino, "rb") as f:
                        self._responder(200, f.read(), "image/jpeg")
                    return
            self._responder(404, '{"error":"no existe"}')
            return

        # ---- recursos públicos de la app instalable (PWA) ----
        if ruta.path == "/manifest.json":
            self._responder(200, MANIFEST_JSON, "application/manifest+json")
            return
        if ruta.path == "/sw.js":
            self._responder(200, SW_JS, "application/javascript")
            return
        if ruta.path == "/icono-192.png":
            self._responder(200, base64.b64decode(ICONO192_B64), "image/png")
            return
        if ruta.path == "/icono-512.png":
            self._responder(200, base64.b64decode(ICONO512_B64), "image/png")
            return

        # ---- rutas del panel (requieren sesión) ----
        u = self._usuario()
        if u is None:
            if ruta.path in ("/", "/index.html"):
                self._responder(200, LOGIN_HTML, "text/html; charset=utf-8")
            else:
                self._responder(401, '{"error":"sesion requerida"}')
            return

        if ruta.path in ("/", "/index.html"):
            self._responder(200, PANEL_HTML, "text/html; charset=utf-8")

        elif ruta.path == "/api/yo":
            self._responder(200, json.dumps(u, ensure_ascii=False))

        elif ruta.path == "/api/usuarios":
            if u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            lista = []
            for nombre, info in usuarios().items():
                lista.append({"usuario": nombre, "rol": info.get("rol", "usuario"),
                              "sucursales": info.get("sucursales", [])})
            self._responder(200, json.dumps(lista, ensure_ascii=False))

        elif ruta.path == "/api/sucursales":
            self._responder(200, json.dumps(sucursales_permitidas(u), ensure_ascii=False))

        elif ruta.path == "/api/listas":
            clave = self._sucursal_de(params, u)
            self._responder(200, json.dumps(listas_de(clave), ensure_ascii=False))

        elif ruta.path == "/api/biblioteca":
            clave = self._sucursal_de(params, u)
            _, suc = _listas_crudas(clave)
            resultado = []
            for n in biblioteca(clave):
                generar_miniatura(clave, n)
                ext = os.path.splitext(n)[1].lower()
                tiene = os.path.exists(os.path.join(dir_minis(clave), n + ".jpg"))
                donde = sorted(l.get("nombre", lid) for lid, l in suc["listas"].items()
                               if n in l.get("archivos", []))
                resultado.append({
                    "nombre": n,
                    "tipo": "imagen" if ext in EXT_IMAGEN else "video",
                    "duracion": duracion_de(clave, n),
                    "miniatura": f"/miniaturas/{clave}/" + urllib.parse.quote(n) + ".jpg" if tiene else "",
                    "listas": donde,
                })
            self._responder(200, json.dumps(resultado, ensure_ascii=False))

        elif ruta.path == "/api/lista":
            clave = self._sucursal_de(params, u)
            lid = params.get("lista", [""])[0]
            resultado = []
            for n in archivos_de_lista(clave, lid):
                generar_miniatura(clave, n)
                ext = os.path.splitext(n)[1].lower()
                tiene = os.path.exists(os.path.join(dir_minis(clave), n + ".jpg"))
                resultado.append({
                    "nombre": n,
                    "tipo": "imagen" if ext in EXT_IMAGEN else "video",
                    "duracion": duracion_de(clave, n),
                    "miniatura": f"/miniaturas/{clave}/" + urllib.parse.quote(n) + ".jpg" if tiene else "",
                    "programa": programacion_de(clave, n),
                    "activo": contenido_activo(clave, n),
                })
            self._responder(200, json.dumps(resultado, ensure_ascii=False))

        elif ruta.path == "/api/tvs":
            clave = self._sucursal_de(params, u)
            self._responder(200, json.dumps(pantallas(clave), ensure_ascii=False))

        elif ruta.path == "/api/tv/pendientes":
            if u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            self._responder(200, json.dumps(pendientes(), ensure_ascii=False))

        elif ruta.path == "/api/ajustes":
            clave = self._sucursal_de(params, u)
            self._responder(200, json.dumps(leer_ajustes(clave), ensure_ascii=False))

        elif ruta.path == "/api/estadisticas":
            clave = self._sucursal_de(params, u)
            c = leer_json(ARCHIVO_CONTADORES, {}).get(clave, {})
            hoy = ahora_local().date()
            corte7 = (hoy - timedelta(days=6)).isoformat()
            corte30 = (hoy - timedelta(days=29)).isoformat()
            hoy_iso = hoy.isoformat()
            resumen = []
            for nombre, fechas in c.items():
                resumen.append({
                    "nombre": nombre,
                    "hoy": fechas.get(hoy_iso, 0),
                    "d7": sum(v for f, v in fechas.items() if f >= corte7),
                    "d30": sum(v for f, v in fechas.items() if f >= corte30),
                })
            resumen.sort(key=lambda x: -x["d30"])
            self._responder(200, json.dumps(resumen, ensure_ascii=False))

        else:
            self._responder(404, '{"error":"no encontrado"}')

    def _servir_archivo(self, carpeta, nombre):
        nombre = nombre_seguro(nombre)
        camino = os.path.join(carpeta, nombre)
        if not os.path.isfile(camino):
            self._responder(404, '{"error":"no existe"}')
            return

        mime = TIPOS_MIME.get(os.path.splitext(nombre)[1].lower(), "application/octet-stream")
        tam = os.path.getsize(camino)
        rango = self.headers.get("Range")
        inicio, fin = 0, tam - 1

        if rango:
            m = re.match(r"bytes=(\d*)-(\d*)", rango)
            if m:
                if m.group(1):
                    inicio = int(m.group(1))
                if m.group(2):
                    fin = int(m.group(2))
            fin = min(fin, tam - 1)
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {inicio}-{fin}/{tam}")
        else:
            self.send_response(200)

        largo = fin - inicio + 1
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(largo))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        with open(camino, "rb") as f:
            f.seek(inicio)
            restante = largo
            while restante > 0:
                trozo = f.read(min(65536, restante))
                if not trozo:
                    break
                try:
                    self.wfile.write(trozo)
                except (BrokenPipeError, ConnectionResetError):
                    return
                restante -= len(trozo)

    # --- HEAD ---
    def do_HEAD(self):
        """HEAD coherente con GET para los medios (R2-B1-01).

        El reproductor pregunta el tamano de un archivo antes de bajarlo a su
        cache. Antes el servidor respondia 501. Devuelve las mismas cabeceras
        que GET (Content-Type, Content-Length, Accept-Ranges), sin cuerpo, y
        NUNCA incrementa contadores: un HEAD no es una descarga.
        """
        ruta = urllib.parse.urlparse(self.path)
        for prefijo, carpeta_de in (("/videos/", dir_videos),
                                    ("/rapidos/", dir_rapidos),
                                    ("/miniaturas/", dir_minis)):
            if ruta.path.startswith(prefijo):
                partes = ruta.path[len(prefijo):].split("/", 1)
                if len(partes) != 2:
                    break
                nombre = nombre_seguro(urllib.parse.unquote(partes[1]))
                camino = os.path.join(carpeta_de(clave_segura(partes[0])), nombre)
                if not os.path.isfile(camino):
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                mime = TIPOS_MIME.get(os.path.splitext(nombre)[1].lower(),
                                      "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(os.path.getsize(camino)))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # --- POST ---
    def do_POST(self):
        ruta = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(ruta.query)

        if ruta.path == "/api/login":
            datos = self._json_body()
            nombre = str(datos.get("usuario", "")).lower().strip()[:30]
            contrasena = str(datos.get("contrasena", ""))[:100]
            if verificar_credenciales(nombre, contrasena):
                token = crear_sesion(nombre)
                self._responder_cookie(200, '{"ok":true}',
                    f"sesion={token}; Path=/; Max-Age={DIAS_SESION*86400}; HttpOnly; SameSite=Lax")
            else:
                time.sleep(1)  # frenar intentos de fuerza bruta
                self._responder(401, '{"error":"usuario o contrasena incorrectos"}')
            return

        u = self._usuario()
        if u is None:
            self._responder(401, '{"error":"sesion requerida"}')
            return

        if ruta.path == "/api/logout":
            cerrar_sesion(self._token())
            self._responder_cookie(200, '{"ok":true}',
                "sesion=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
            return

        if ruta.path == "/api/usuarios":
            if u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            datos = self._json_body()
            ok = crear_usuario(str(datos.get("usuario", "")),
                               str(datos.get("contrasena", "")),
                               str(datos.get("rol", "usuario")),
                               datos.get("sucursales", []) or [])
            self._responder(200 if ok else 400,
                            '{"ok":true}' if ok else '{"error":"datos invalidos o usuario existente"}')
            return

        if ruta.path == "/api/usuarios/eliminar":
            if u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            nombre = str(self._json_body().get("usuario", "")).lower().strip()
            todos = usuarios()
            if nombre in todos and nombre != u["usuario"]:
                del todos[nombre]
                escribir_json(ARCHIVO_USUARIOS, todos)
            self._responder(200, '{"ok":true}')
            return

        if ruta.path == "/api/subir":
            clave = self._sucursal_de(params, u)
            nombre = nombre_seguro(params.get("nombre", ["archivo.mp4"])[0])
            if os.path.splitext(nombre)[1].lower() not in EXTENSIONES:
                nombre += ".mp4"
            largo = int(self.headers.get("Content-Length", 0))
            camino = os.path.join(dir_videos(clave), nombre)
            with open(camino, "wb") as f:
                restante = largo
                while restante > 0:
                    trozo = self.rfile.read(min(65536, restante))
                    if not trozo:
                        break
                    f.write(trozo)
                    restante -= len(trozo)
            mensaje = procesar_subida(camino)
            lista_archivos(clave)
            base_nombre = os.path.splitext(nombre)[0]
            final = ""
            for candidato in (nombre, base_nombre + ".mp4"):
                if os.path.isfile(os.path.join(dir_videos(clave), candidato)):
                    if mensaje == "girado":
                        marcar_girado(clave, candidato)
                    generar_miniatura(clave, candidato)
                    final = candidato
                    break
            if final:
                lid = params.get("lista", [""])[0][:40]
                if not lid:
                    lid = listas_de(clave)["activa"]
                actuales = archivos_de_lista(clave, lid)
                if final not in actuales:
                    guardar_lista(clave, lid, actuales + [final])
            self._responder(200, json.dumps({"ok": True, "proceso": mensaje}))


        elif ruta.path == "/api/rapido":
            clave = self._sucursal_de(params, u)
            destino = params.get("id", [""])[0]
            nombre = nombre_seguro(params.get("nombre", ["archivo.mp4"])[0])
            if os.path.splitext(nombre)[1].lower() not in EXTENSIONES:
                nombre += ".mp4"
            nombre = f"{int(time.time())}_{nombre}"
            carpeta = dir_rapidos(clave)
            camino = os.path.join(carpeta, nombre)
            largo = int(self.headers.get("Content-Length", 0))
            with open(camino, "wb") as f:
                restante = largo
                while restante > 0:
                    trozo = self.rfile.read(min(65536, restante))
                    if not trozo:
                        break
                    f.write(trozo)
                    restante -= len(trozo)
            procesar_subida(camino)
            # el proceso pudo dejarlo como .mp4
            base_n = os.path.splitext(nombre)[0]
            final = nombre
            for cand in (nombre, base_n + ".mp4"):
                if os.path.isfile(os.path.join(carpeta, cand)):
                    final = cand
                    break
            # limpiar rapidos anteriores de esta sucursal
            for viejo in os.listdir(carpeta):
                if viejo != final:
                    try:
                        os.remove(os.path.join(carpeta, viejo))
                    except OSError:
                        pass
            host = self.headers.get("Host", f"{ip_local()}:{PUERTO}")
            esquema = "https" if self.headers.get("X-Forwarded-Proto") == "https" else "http"
            url = f"{esquema}://{host}/rapidos/{clave}/{urllib.parse.quote(final)}"
            tipo = "imagen" if os.path.splitext(final)[1].lower() in EXT_IMAGEN else "video"
            duracion = 0 if tipo == "imagen" else 10  # 0 = la foto se queda fija
            if destino == "todas":
                objetivos = [t["id"] for t in pantallas(clave)]
            else:
                objetivos = [destino[:64]] if destino else []
            for d in objetivos:
                if self._tv_permitida(d, u):
                    enviar_comando(d, "reproducir", url, tipo, duracion)
            self._responder(200, json.dumps({"ok": True, "tipo": tipo}))

        elif ruta.path == "/api/sucursales":
            if u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            nombre = str(self._json_body().get("nombre", "")).strip()[:60]
            if nombre:
                lista = sucursales()
                clave = slug(nombre)
                if not any(s["clave"] == clave for s in lista):
                    lista.append({"clave": clave, "nombre": nombre})
                    escribir_json(ARCHIVO_SUCURSALES, lista)
            self._responder(200, json.dumps(sucursales(), ensure_ascii=False))

        elif ruta.path == "/api/ajustes":
            clave = self._sucursal_de(params, u)
            datos = self._json_body()
            todos = leer_json(ARCHIVO_AJUSTES, {})
            ajustes = leer_ajustes(clave)
            if "mensaje" in datos:
                ajustes["mensaje"] = str(datos["mensaje"])[:200].strip()
            if "animado" in datos:
                ajustes["animado"] = bool(datos["animado"])
            if "velocidad" in datos:
                try:
                    ajustes["velocidad"] = max(40, min(400, int(datos["velocidad"])))
                except (TypeError, ValueError):
                    pass
            todos[clave] = ajustes
            escribir_json(ARCHIVO_AJUSTES, todos)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/programar":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            nombre = nombre_seguro(datos.get("nombre", ""))
            with CANDADO:
                prog = leer_json(ARCHIVO_PROGRAMACION, {})
                desde = str(datos.get("desde", ""))[:10]
                hasta = str(datos.get("hasta", ""))[:10]
                dias = [d for d in (datos.get("dias") or []) if isinstance(d, int) and 0 <= d <= 6]
                hini = str(datos.get("hini", ""))[:5]
                hfin = str(datos.get("hfin", ""))[:5]
                if not desde and not hasta and not dias and not (hini and hfin):
                    prog.get(clave, {}).pop(nombre, None)
                else:
                    prog.setdefault(clave, {})[nombre] = {
                        "desde": desde, "hasta": hasta, "dias": dias,
                        "hini": hini, "hfin": hfin,
                    }
                escribir_json(ARCHIVO_PROGRAMACION, prog)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/duracion":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            nombre = nombre_seguro(datos.get("nombre", ""))
            try:
                segundos = max(3, min(120, int(datos.get("segundos", DURACION_IMAGEN))))
            except (TypeError, ValueError):
                segundos = DURACION_IMAGEN
            todos = leer_json(ARCHIVO_DURACIONES, {})
            todos.setdefault(clave, {})[nombre] = segundos
            escribir_json(ARCHIVO_DURACIONES, todos)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/eliminar":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            nombre = nombre_seguro(datos.get("nombre", ""))
            camino = os.path.join(dir_videos(clave), nombre)
            if os.path.isfile(camino):
                os.remove(camino)
            mini = os.path.join(dir_minis(clave), nombre + ".jpg")
            if os.path.isfile(mini):
                os.remove(mini)
            with CANDADO:
                ordenes = leer_json(ARCHIVO_ORDENES, {})
                ordenes[clave] = [n for n in ordenes.get(clave, []) if n != nombre]
                escribir_json(ARCHIVO_ORDENES, ordenes)
                todas = leer_json(ARCHIVO_LISTAS, {})
                suc = todas.get(clave)
                if suc:
                    for l in suc.get("listas", {}).values():
                        l["archivos"] = [n for n in l.get("archivos", []) if n != nombre]
                    todas[clave] = suc
                    escribir_json(ARCHIVO_LISTAS, todas)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/listas/crear":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            nombre = str(datos.get("nombre", "")).strip()[:40] or "Sin nombre"
            with CANDADO:
                todas, suc = _listas_crudas(clave)
                lid = "l" + str(int(time.time() * 1000))[-9:]
                suc["listas"][lid] = {"nombre": nombre, "archivos": []}
                todas[clave] = suc
                escribir_json(ARCHIVO_LISTAS, todas)
            self._responder(200, json.dumps({"ok": True, "id": lid}))

        elif ruta.path == "/api/listas/renombrar":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            lid = str(datos.get("id", ""))[:40]
            nombre = str(datos.get("nombre", "")).strip()[:40]
            with CANDADO:
                todas, suc = _listas_crudas(clave)
                if lid in suc["listas"] and nombre:
                    suc["listas"][lid]["nombre"] = nombre
                    todas[clave] = suc
                    escribir_json(ARCHIVO_LISTAS, todas)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/listas/eliminar":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            lid = str(datos.get("id", ""))[:40]
            with CANDADO:
                todas, suc = _listas_crudas(clave)
                if lid in suc["listas"] and len(suc["listas"]) > 1:
                    del suc["listas"][lid]
                    if suc.get("activa") == lid:
                        suc["activa"] = next(iter(suc["listas"]))
                    todas[clave] = suc
                    escribir_json(ARCHIVO_LISTAS, todas)
                    # pantallas que la tenian asignada vuelven a la activa
                    tvs = leer_json(ARCHIVO_TVS, {})
                    for info in tvs.values():
                        if info.get("lista") == lid:
                            info["lista"] = ""
                    escribir_json(ARCHIVO_TVS, tvs)
                else:
                    self._responder(400, '{"error":"no se puede eliminar la unica lista"}')
                    return
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/listas/activar":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            lid = str(datos.get("id", ""))[:40]
            with CANDADO:
                todas, suc = _listas_crudas(clave)
                if lid in suc["listas"]:
                    suc["activa"] = lid
                    todas[clave] = suc
                    escribir_json(ARCHIVO_LISTAS, todas)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/listas/contenido":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            lid = str(datos.get("id", ""))[:40]
            with CANDADO:
                todas, suc = _listas_crudas(clave)
                if lid not in suc["listas"]:
                    self._responder(400, '{"error":"lista no encontrada"}')
                    return
                actuales = list(suc["listas"][lid].get("archivos", []))
                en_disco = set(lista_archivos(clave))
                for n in (datos.get("agregar") or []):
                    n = nombre_seguro(n)
                    if n in en_disco and n not in actuales:
                        actuales.append(n)
                quitar = {nombre_seguro(n) for n in (datos.get("quitar") or [])}
                actuales = [n for n in actuales if n not in quitar]
                suc["listas"][lid]["archivos"] = actuales
                todas[clave] = suc
                escribir_json(ARCHIVO_LISTAS, todas)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/renombrar":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            viejo_n = nombre_seguro(datos.get("nombre", ""))
            propuesto = str(datos.get("nuevo", "")).strip()
            # conservar la extension original
            ext = os.path.splitext(viejo_n)[1]
            base = nombre_seguro(os.path.splitext(propuesto)[0])[:80].strip()
            if not base or not viejo_n:
                self._responder(400, '{"error":"nombre invalido"}')
                return
            nuevo_n = base + ext
            with CANDADO:
                origen = os.path.join(dir_videos(clave), viejo_n)
                destino = os.path.join(dir_videos(clave), nuevo_n)
                if not os.path.isfile(origen):
                    self._responder(404, '{"error":"no existe"}')
                    return
                if nuevo_n != viejo_n and os.path.exists(destino):
                    self._responder(409, '{"error":"ya existe otro con ese nombre"}')
                    return
                if nuevo_n != viejo_n:
                    os.rename(origen, destino)
                    mo = os.path.join(dir_minis(clave), viejo_n + ".jpg")
                    if os.path.isfile(mo):
                        os.replace(mo, os.path.join(dir_minis(clave), nuevo_n + ".jpg"))
                    # actualizar todas las referencias al nombre
                    ordenes = leer_json(ARCHIVO_ORDENES, {})
                    ordenes[clave] = [nuevo_n if n == viejo_n else n
                                      for n in ordenes.get(clave, [])]
                    escribir_json(ARCHIVO_ORDENES, ordenes)

                    todas = leer_json(ARCHIVO_LISTAS, {})
                    suc = todas.get(clave)
                    if suc:
                        for l in suc.get("listas", {}).values():
                            l["archivos"] = [nuevo_n if n == viejo_n else n
                                             for n in l.get("archivos", [])]
                        todas[clave] = suc
                        escribir_json(ARCHIVO_LISTAS, todas)

                    for archivo in (ARCHIVO_DURACIONES, ARCHIVO_GIRADOS,
                                    ARCHIVO_PROGRAMACION, ARCHIVO_CONTADORES):
                        d = leer_json(archivo, {})
                        if clave in d and viejo_n in d[clave]:
                            d[clave][nuevo_n] = d[clave].pop(viejo_n)
                            escribir_json(archivo, d)
            self._responder(200, json.dumps({"ok": True, "nombre": nuevo_n}))

        elif ruta.path == "/api/mover":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            nombre = nombre_seguro(datos.get("nombre", ""))
            dir_ = int(datos.get("dir", 0))
            lid = str(datos.get("lista", ""))[:40]
            orden = archivos_de_lista(clave, lid)
            if nombre in orden:
                i = orden.index(nombre)
                j = i + dir_
                if 0 <= j < len(orden):
                    orden[i], orden[j] = orden[j], orden[i]
                    if not lid:
                        lid = listas_de(clave)["activa"]
                    guardar_lista(clave, lid, orden)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/turno":
            datos = self._json_body()
            suc = str(datos.get("sucursal", params.get("sucursal", [""])[0]))
            clave = self._sucursal_de({"sucursal": [suc]}, u)
            with CANDADO:
                turnos = leer_json(ARCHIVO_TURNOS, {})
                previo = turnos.get(clave, {})
                try:
                    duracion = max(5, min(300, int(datos.get("duracion", 60))))
                except (TypeError, ValueError):
                    duracion = 60
                # la fila de proximos la manda el sistema de recepcion
                proximos = []
                for p in (datos.get("proximos") or [])[:3]:
                    if isinstance(p, dict):
                        proximos.append({
                            "numero": str(p.get("numero", ""))[:8].strip(),
                            "estacion": str(p.get("estacion", ""))[:20].strip(),
                        })
                turnos[clave] = {
                    "n": previo.get("n", 0) + 1,
                    "numero": str(datos.get("numero", ""))[:8].strip(),
                    "estacion": str(datos.get("estacion", ""))[:20].strip(),
                    "espera": str(datos.get("espera", ""))[:10].strip(),
                    "duracion": duracion,
                    "proximos": proximos,
                    "ts": int(time.time()),
                }
                escribir_json(ARCHIVO_TURNOS, turnos)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/tv/aprobar":
            if u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            datos = self._json_body()
            id_tv = str(datos.get("id", ""))[:64]
            clave = clave_segura(datos.get("sucursal", ""))
            if not existe_sucursal(clave):
                self._responder(400, '{"error":"sucursal invalida"}')
                return
            with CANDADO:
                tvs = leer_json(ARCHIVO_TVS, {})
                if id_tv in tvs:
                    tvs[id_tv]["aprobada"] = True
                    tvs[id_tv]["sucursal"] = clave
                    tvs[id_tv]["zona"] = str(datos.get("zona", ""))[:40].strip()
                    escribir_json(ARCHIVO_TVS, tvs)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/tv/eliminar":
            if u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            id_tv = str(self._json_body().get("id", ""))[:64]
            with CANDADO:
                tvs = leer_json(ARCHIVO_TVS, {})
                tvs.pop(id_tv, None)
                escribir_json(ARCHIVO_TVS, tvs)
                comandos = leer_json(ARCHIVO_COMANDOS, {})
                comandos.pop(id_tv, None)
                escribir_json(ARCHIVO_COMANDOS, comandos)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/tv":
            datos = self._json_body()
            id_tv = str(datos.get("id", ""))[:64]
            if not self._tv_permitida(id_tv, u):
                self._responder(403, '{"error":"sin permiso sobre esa pantalla"}')
                return
            with CANDADO:
                tvs = leer_json(ARCHIVO_TVS, {})
                if id_tv in tvs:
                    if "zona" in datos:
                        tvs[id_tv]["zona"] = str(datos["zona"])[:40].strip()
                    if "turnos" in datos:
                        tvs[id_tv]["turnos"] = bool(datos["turnos"])
                    if "lista" in datos:
                        tvs[id_tv]["lista"] = str(datos["lista"])[:40]
                    if "sucursal" in datos and existe_sucursal(clave_segura(datos["sucursal"])):
                        tvs[id_tv]["sucursal"] = clave_segura(datos["sucursal"])
                    escribir_json(ARCHIVO_TVS, tvs)
            self._responder(200, '{"ok":true}')

        elif ruta.path == "/api/tv/comando":
            datos = self._json_body()
            clave = self._sucursal_de({"sucursal": [str(datos.get("sucursal", ""))]}, u)
            accion = str(datos.get("accion", ""))
            if accion not in ("pausa", "continuar", "reproducir", "silencio", "sonido",
                              "recargar", "vaciar_cache"):
                self._responder(400, '{"error":"accion invalida"}')
                return
            # B5A-QA-01: los comandos de operacion remota son SOLO de administrador.
            # El permiso se aplica aqui, en el servidor; ocultar el boton no cuenta.
            if accion in ACCIONES_SOLO_ADMIN and u["rol"] != "admin":
                self._responder(403, '{"error":"solo admin"}')
                return
            url, tipo, dur = "", "", 10
            if accion == "reproducir":
                nombre = nombre_seguro(datos.get("nombre", ""))
                if not os.path.isfile(os.path.join(dir_videos(clave), nombre)):
                    self._responder(404, '{"error":"archivo no existe"}')
                    return
                host = self.headers.get("Host", f"{ip_local()}:{PUERTO}")
                esquema = "https" if self.headers.get("X-Forwarded-Proto") == "https" else "http"
                url = f"{esquema}://{host}/videos/{clave}/{urllib.parse.quote(nombre)}"
                tipo = "imagen" if os.path.splitext(nombre)[1].lower() in EXT_IMAGEN else "video"
                # Enviar a...: la foto se muestra sus segundos configurados y
                # regresa al bucle (la foto FIJA es la de "Mostrar al cliente")
                dur = duracion_de(clave, nombre)
            objetivo = str(datos.get("id", ""))
            if objetivo == "todas":
                destinos = [t["id"] for t in pantallas(clave)]
            else:
                destinos = [objetivo[:64]]
            for d in destinos:
                if self._tv_permitida(d, u):
                    enviar_comando(d, accion, url, tipo, dur)
            self._responder(200, '{"ok":true}')

        else:
            self._responder(404, '{"error":"no encontrado"}')


    do_PUT = do_POST


class ServidorSilencioso(ThreadingHTTPServer):
    daemon_threads = True
    # La cola de conexiones venia en 5, el valor por defecto de Python. Con la
    # flota consultando a la vez, el sistema operativo tiraba conexiones y la
    # TV o el panel veian "conexion reiniciada". Medido: 120 simultaneas.
    request_queue_size = 64

    def handle_error(self, request, client_address):
        tipo, _, _ = sys.exc_info()
        if tipo in (ConnectionResetError, BrokenPipeError,
                    ConnectionAbortedError, TimeoutError):
            return
        # antes solo se imprimia y se perdia; ahora queda en la bitacora
        bitacora.exception("error atendiendo a %s", client_address)
        super().handle_error(request, client_address)


# ---------------- panel web ----------------

LOGO_B64 = "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"

ICONO192_B64 = "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"
ICONO512_B64 = "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"

MANIFEST_JSON = """{
  "name": "LUMIN TV",
  "short_name": "LUMIN TV",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1F1F1F",
  "theme_color": "#1F1F1F",
  "icons": [
    {"src": "/icono-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/icono-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}"""

SW_JS = """self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
self.addEventListener('fetch', e => {});"""

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LUMIN TV — Iniciar sesión</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1F1F1F">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="/icono-192.png">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; }
  body { min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #F7F7F8; font: 15px/1.6 "Poppins", system-ui, sans-serif; color: #1F1F1F; padding: 20px; }
  .caja { background: #fff; border: 1px solid #ECECEC; border-radius: 16px;
    padding: 38px 32px; width: 100%; max-width: 380px; text-align: center;
    box-shadow: 0 4px 24px rgba(31,31,31,.06); }
  img { width: 76px; height: 76px; border-radius: 18px; margin-bottom: 14px; }
  h1 { font-size: 19px; font-weight: 700; letter-spacing: .1em; }
  h1 b { color: #EC3A80; }
  p { color: #6B7280; font-size: 13.5px; margin: 4px 0 24px; }
  input { width: 100%; padding: 13px 16px; border: 1px solid #ECECEC; border-radius: 12px;
    font: 400 15px "Poppins", sans-serif; margin-bottom: 12px; }
  input:focus { outline: none; border-color: #EC3A80; }
  button { width: 100%; padding: 13px; border: none; border-radius: 999px;
    background: #EC3A80; color: #fff; font: 600 15px "Poppins", sans-serif;
    cursor: pointer; margin-top: 6px; }
  button:hover { background: #F45C9C; }
  #error { color: #FF5A5F; font-size: 13px; min-height: 20px; margin-top: 10px; }
</style>
</head>
<body>
<form class="caja" id="f">
  <img src="/icono-192.png" alt="LUMIN TV">
  <h1>LUMIN <b>TV</b></h1>
  <p>Panel de anuncios</p>
  <input type="text" id="usuario" placeholder="Usuario" autocomplete="username" autocapitalize="none">
  <input type="password" id="contrasena" placeholder="Contraseña" autocomplete="current-password">
  <button type="submit">Entrar</button>
  <div id="error"></div>
</form>
<script>
document.getElementById("f").onsubmit = async e => {
  e.preventDefault();
  const r = await fetch("/api/login", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      usuario: document.getElementById("usuario").value,
      contrasena: document.getElementById("contrasena").value
    }) });
  if (r.ok) location.reload();
  else document.getElementById("error").textContent = "Usuario o contraseña incorrectos";
};
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
</script>
</body>
</html>"""


PANEL_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>LUMIN TV — Panel</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#1F1F1F">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<link rel="apple-touch-icon" href="/icono-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --rosa: #EFAFC7; --rosa-claro: #F6C8D8; --fondo: #F7F7F8; --hover: #FCE6EE;
    --dorado: #C8A96A; --tinta: #1F1F1F; --gris: #6B7280; --borde: #ECECEC;
    --rosa-fuerte: #EC3A80; --exito: #34C759; --error: #FF5A5F;
  }
  * { box-sizing: border-box; margin: 0; }
  body { background: var(--fondo); color: var(--tinta);
    font: 15px/1.6 "Poppins", "Inter", system-ui, sans-serif;
    -webkit-font-smoothing: antialiased; }
  header { background: var(--tinta);
    padding: calc(12px + env(safe-area-inset-top)) 24px 12px; display: flex;
    align-items: center; gap: 12px; position: sticky; top: 0; z-index: 10;
    box-shadow: 0 2px 10px rgba(31,31,31,.18); flex-wrap: wrap; }
  .marca { width: 38px; height: 38px; border-radius: 10px; }
  .logo { font-size: 18px; font-weight: 700; letter-spacing: .12em; color: #fff; }
  .logo b { color: var(--rosa-fuerte); }
  #sucursal { margin-left: auto; }
  .sel-oscuro { background: #2B2F35; color: #fff; border: 1px solid #3A3F46;
    border-radius: 999px; padding: 8px 14px; font: 500 13px "Poppins", sans-serif; cursor: pointer; }
  .btn-mas { background: var(--rosa-fuerte); border: none; color: #fff; width: 34px; height: 34px;
    border-radius: 50%; font-size: 18px; cursor: pointer; line-height: 1; }
  main { max-width: 820px; margin: 28px auto 80px; padding: 0 18px; display: grid; gap: 20px; }
  .card { background: #fff; border: 1px solid var(--borde); border-radius: 12px;
    padding: 22px 24px; box-shadow: 0 1px 3px rgba(31,31,31,.04); }
  h2 { font-size: 12px; font-weight: 600; text-transform: uppercase;
    letter-spacing: .12em; color: var(--gris); margin-bottom: 14px; }
  .btn { font: 500 14px "Poppins", sans-serif; border: 1px solid var(--borde);
    background: #fff; color: var(--tinta); border-radius: 999px;
    padding: 9px 18px; cursor: pointer; transition: .15s; }
  .btn:hover { background: var(--hover); border-color: var(--rosa-claro); }
  .btn-primario { background: var(--rosa-fuerte); border-color: var(--rosa-fuerte);
    color: #fff; font-weight: 600; }
  .btn-primario:hover { background: #F45C9C; border-color: #F45C9C; }
  .btn-peligro:hover { border-color: var(--error); color: var(--error); background: #fff; }
  .btn-mini { padding: 6px 12px; font-size: 13px; }
  .btn-icono { width: 44px; height: 44px; padding: 0; font-size: 16px;
    display: inline-flex; align-items: center; justify-content: center; }
  .btn-ctrl { width: 52px; height: 52px; padding: 0; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    color: var(--rosa-fuerte); border: 1.5px solid var(--rosa-claro); }
  .btn-ctrl:hover { background: var(--hover); border-color: var(--rosa-fuerte); }
  .btn-ctrl svg { width: 22px; height: 22px; }
  .zona-subida { border: 1.5px dashed var(--borde); border-radius: 12px; padding: 36px 16px;
    text-align: center; color: var(--gris); cursor: pointer; transition: .15s; }
  .zona-subida span { color: var(--rosa-fuerte); font-weight: 500; }
  .zona-subida.activa, .zona-subida:hover { border-color: var(--rosa-fuerte); background: var(--hover); }
  #progreso { margin-top: 12px; font-size: 13px; color: var(--dorado); min-height: 20px; font-weight: 500; }
  .nota { font-size: 13px; color: var(--gris); margin-top: 12px; }
  ul { list-style: none; }
  li { display: flex; align-items: center; gap: 12px; padding: 13px 0;
    border-bottom: 1px solid var(--borde); flex-wrap: wrap; }
  li:last-child { border-bottom: 0; }
  .orden { width: 26px; height: 26px; border-radius: 50%; background: var(--rosa-fuerte);
    color: #fff; font-size: 12.5px; font-weight: 600; display: flex;
    align-items: center; justify-content: center; flex-shrink: 0; }
  .mini { width: 56px; height: 56px; border-radius: 10px; object-fit: cover;
    background: var(--fondo); border: 1px solid var(--borde); flex-shrink: 0; }
  .info { flex: 1; min-width: 140px; }
  .nombre { font-weight: 500; font-size: 14px; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap; max-width: 320px; }
  .detalle { font-size: 12.5px; color: var(--gris); display: flex;
    align-items: center; gap: 6px; margin-top: 2px; flex-wrap: wrap; }
  .estado-tv { display: block; font-size: 11.5px; opacity: .85; margin-top: 2px; word-break: break-word; }
  .estado-tv.error { color: #C0392B; }
  .dur { width: 52px; padding: 4px 6px; border: 1px solid var(--borde); border-radius: 8px;
    font: 500 13px "Poppins", sans-serif; text-align: center; }
  .dur:focus { outline: none; border-color: var(--rosa-fuerte); }
  .acciones { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
  select.enviar { max-width: 150px; padding: 7px 10px; border: 1px solid var(--borde);
    border-radius: 999px; font: 500 12.5px "Poppins", sans-serif; color: var(--rosa-fuerte);
    background: #fff; cursor: pointer; }
  .vacio { color: var(--gris); padding: 18px 0; font-size: 14px; }
  .punto { width: 9px; height: 9px; border-radius: 50%; background: var(--error); flex-shrink: 0; display: inline-block; }
  .punto.on { background: var(--exito); }
  .num-tv { width: 34px; height: 34px; border-radius: 10px; background: var(--rosa-fuerte);
    color: #fff; display: flex; align-items: center; justify-content: center;
    font-weight: 600; font-size: 14px; flex-shrink: 0; }
  .zona-input { border: 1px solid transparent; border-radius: 8px; padding: 3px 8px;
    font: 500 14px "Poppins", sans-serif; color: var(--tinta); width: 100%; max-width: 220px; }
  .zona-input:hover { border-color: var(--borde); }
  .zona-input:focus { outline: none; border-color: var(--rosa-fuerte); background: #fff; }
  .fila { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  input[type=text].campo { flex: 1; min-width: 200px; padding: 11px 14px;
    border: 1px solid var(--borde); border-radius: 12px;
    font: 400 14px "Poppins", sans-serif; }
  input[type=text].campo:focus { outline: none; border-color: var(--rosa-fuerte); }
  .opciones { display: flex; gap: 20px; flex-wrap: wrap; align-items: center; margin-top: 16px; }
  .opcion { display: flex; align-items: center; gap: 10px; font-size: 14px; }
  .sw { position: relative; width: 42px; height: 24px; flex-shrink: 0; }
  .sw input { opacity: 0; width: 0; height: 0; }
  .sw i { position: absolute; inset: 0; background: var(--borde); border-radius: 24px;
    transition: .2s; cursor: pointer; }
  .sw i:before { content: ""; position: absolute; width: 18px; height: 18px;
    border-radius: 50%; background: #fff; left: 3px; top: 3px; transition: .2s;
    box-shadow: 0 1px 3px rgba(0,0,0,.15); }
  .sw input:checked + i { background: var(--rosa-fuerte); }
  .sw input:checked + i:before { transform: translateX(18px); }
  select.claro { padding: 8px 12px; border: 1px solid var(--borde); border-radius: 999px;
    font: 500 13px "Poppins", sans-serif; background: #fff; cursor: pointer; }
  .guardado { color: var(--exito); font-size: 13px; font-weight: 500; opacity: 0; transition: .3s; }
  .guardado.ver { opacity: 1; }
  /* móvil */
  @media (max-width: 640px) {
    header { padding: calc(10px + env(safe-area-inset-top)) 14px 10px; gap: 8px; }
    .campo { min-width: 100% !important; }
    .fila .btn { flex: 1; }
    select.enviar { flex: 1; max-width: none; }
    .btn-ctrl { width: 56px; height: 56px; }
    .logo { font-size: 15px; }
    main { margin-top: 16px; padding: 0 10px; gap: 14px; }
    .card { padding: 16px 14px; border-radius: 12px; }
    .nombre { max-width: 170px; }
    .acciones { width: 100%; justify-content: flex-end; }
    #sucursal { flex-basis: 100%; order: 5; display: flex; gap: 8px; }
    .sel-oscuro { flex: 1; }
  }
</style>
</head>
<body>
<header>
  <img class="marca" src="data:image/png;base64,__LOGO__" alt="LUMIN TV">
  <span class="logo">LUMIN <b>TV</b></span>
  <div id="sucursal">
    <select class="sel-oscuro" id="selSucursal"></select>
    <button class="btn-mas" id="masSucursal" title="Nueva sucursal">+</button>
    <button class="sel-oscuro" id="salir" title="Cerrar sesión">Salir</button>
  </div>
</header>
<main>

  <section class="card" id="cardPendientes" style="display:none">
    <h2>Pantallas pendientes de aprobación</h2>
    <ul id="pendientes"></ul>
    <p class="nota">Una pantalla nueva muestra su código en la TV. Verifica que el
    código coincida con el de tu pantalla física antes de aprobarla.</p>
  </section>

  <section class="card">
    <h2>Pantallas · <span id="nomSucursal"></span></h2>
    <ul id="tvs"><li class="vacio">Buscando pantallas…</li></ul>
    <p class="nota">Escribe la zona de cada pantalla (recepción, cabinas, pasillo…).
    Usa los botones para pausar o continuar lo que se ve en cada una.</p>
  </section>

  <section class="card">
    <h2>Mostrar al cliente</h2>
    <div class="fila">
      <button class="btn" id="btnRapido">Elegir foto o video</button>
      <span class="detalle" id="nomRapido" style="flex:1; min-width:120px;">Nada elegido</span>
      <select class="claro" id="pantallaRapido"></select>
      <button class="btn btn-primario" id="mostrarRapido" disabled>Mostrar ahora</button>
    </div>
    <input type="file" id="archivoRapido" accept="video/mp4,video/*,image/jpeg,image/png" hidden>
    <div id="progresoRapido" style="margin-top:10px; font-size:13px; color:var(--dorado); min-height:20px; font-weight:500;"></div>
    <p class="nota">No entra a la lista de reproducción. Las fotos se quedan fijas
    hasta que presiones ▶ en esa pantalla; los videos regresan solos al bucle al terminar.</p>
  </section>

  <section class="card">
    <h2>Anunciar turno</h2>
    <div class="fila">
      <input type="text" class="campo" id="tNumero" placeholder="N° turno (ej. C142)" style="max-width:170px">
      <input type="text" class="campo" id="tEstacion" placeholder="Estación" style="max-width:120px" inputmode="numeric">
      <input type="text" class="campo" id="tEspera" placeholder="Espera aprox. (min, opcional)" style="max-width:230px" inputmode="numeric">
      <button class="btn btn-primario" id="anunciarTurno">Anunciar</button>
    </div>
    <p class="nota">El panel se desliza desde abajo, dura 1 minuto y desaparece; solo en
    pantallas con «Turnos» activado. Tu sistema de recepción puede mandar además la lista
    de próximos por POST a /api/turno.</p>
  </section>

  <section class="card">
    <h2>Subir contenido</h2>
    <div class="zona-subida" id="zona">Arrastra tus videos o fotos aquí, o <span>haz clic para elegirlos</span><br>
    <small style="color:var(--gris)">MP4 · JPG · PNG</small></div>
    <input type="file" id="archivo" accept="video/mp4,video/*,image/jpeg,image/png" multiple hidden>
    <div id="progreso"></div>
  </section>

  <section class="card">
    <h2>Mensaje en pantalla</h2>
    <div class="fila">
      <input type="text" class="campo" id="mensaje" maxlength="200"
        placeholder="Ej. 10% de descuento en tu primera visita ✨">
      <button class="btn btn-primario" id="guardarMsg">Mostrar</button>
      <button class="btn btn-peligro" id="quitarMsg">Quitar</button>
    </div>
    <div class="opciones">
      <label class="opcion">
        <span class="sw"><input type="checkbox" id="animado"><i></i></span>
        Cintillo en movimiento
      </label>
      <label class="opcion">
        Velocidad
        <select class="claro" id="velocidad">
          <option value="80">Lenta</option>
          <option value="130" selected>Normal</option>
          <option value="200">Rápida</option>
        </select>
      </label>
      <span class="guardado" id="okMsg">Guardado ✓</span>
    </div>
  </section>

  <section class="card" id="cardUsuarios" style="display:none">
    <h2>Usuarios</h2>
    <ul id="usuarios"></ul>
    <div class="fila" style="margin-top:14px">
      <input type="text" class="campo" id="nuevoUsuario" placeholder="Usuario" style="max-width:150px" autocapitalize="none">
      <input type="password" class="campo" id="nuevaContrasena" placeholder="Contraseña" style="max-width:150px">
      <select class="claro" id="nuevoRol">
        <option value="usuario">Usuario</option>
        <option value="admin">Admin</option>
      </select>
      <select class="claro" id="nuevaSucursal"></select>
      <button class="btn btn-primario" id="crearUsuario">Crear</button>
    </div>
    <p class="nota">Los usuarios normales solo ven y controlan su sucursal.
    Los admin ven todas las sucursales y administran usuarios.</p>
  </section>

  <section class="card" id="cardStats" style="display:none">
    <h2>Estadísticas de reproducción</h2>
    <ul id="stats"></ul>
    <p class="nota">Veces que cada contenido se ha reproducido en las pantallas de esta
    sucursal. Útil para reportar a marcas anunciantes.</p>
  </section>

  <section class="card">
    <h2>Campañas programadas</h2>
    <div class="fila" id="nuevaCamp" style="flex-wrap:wrap">
      <select class="claro" id="campSel"></select>
      <span id="campCampos" style="display:contents"></span>
      <button class="btn btn-primario btn-mini" id="campCrear">Programar</button>
    </div>
    <ul id="campanas"></ul>
    <p class="nota">Lo que programes sale de la lista de todos los días y se muestra solo
    en sus días, fechas u horarios. Al quitarle la programación, regresa a la lista.</p>
  </section>

  <section class="card">
    <h2>Listas de reproducción</h2>
    <div class="fila" style="flex-wrap:wrap">
      <select class="claro" id="listaSel" style="min-width:190px"></select>
      <span id="listaAlAire" style="font-size:12.5px"></span>
      <button class="btn btn-primario btn-mini" id="listaAlAireBtn">Poner al aire</button>
      <button class="btn btn-mini" id="listaNueva">Nueva</button>
      <button class="btn btn-mini" id="listaRenombrar">Renombrar</button>
      <button class="btn btn-mini btn-peligro" id="listaBorrar">Eliminar lista</button>
    </div>
    <p class="nota">La lista «al aire» es la que ven las pantallas de esta sucursal
    (salvo las que tengan otra lista asignada). Quitar contenido de una lista NO lo
    borra: sigue guardado en la Biblioteca para reutilizarlo cuando quieras.</p>
  </section>

  <section class="card">
    <h2>Contenido de <span id="listaNombre">la lista</span></h2>
    <ul id="lista"></ul>
    <p class="nota">Con «Enviar a…» reproduces ese contenido al momento en la pantalla que elijas
    (tarda unos 4 segundos); las fotos se muestran sus segundos configurados y regresa
    el bucle. Si quieres una foto fija hasta que tú decidas, usa «Mostrar al cliente».</p>
  </section>

  <section class="card">
    <h2>Biblioteca <span id="bibCuantos" style="color:var(--gris); font-weight:400"></span></h2>
    <ul id="biblioteca"></ul>
    <p class="nota">Todo el contenido guardado en la nube de esta sucursal. «Agregar»
    lo suma a la lista que estás editando; «Renombrar» le cambia el nombre en todas
    las listas sin perder nada; «Eliminar de la nube» sí lo borra para siempre.</p>
  </section>

</main>
<script>
const $ = id => document.getElementById(id);
let sucursal = "";
let listaTvs = [];
const ICONO_PAUSA = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>';
const ICONO_PLAY = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
const ICONO_SONIDO = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3z"/><path d="M16.5 8.5a5 5 0 0 1 0 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
const ICONO_MUDO = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3z"/><path d="M16 9.5l5 5M21 9.5l-5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
let yo = { rol: "usuario" };
let todasSucursales = [];

function avisoGuardado() {
  $("okMsg").classList.add("ver");
  setTimeout(() => $("okMsg").classList.remove("ver"), 1500);
}

/* ---------- sesión y usuarios ---------- */
$("salir").onclick = async () => {
  await fetch("/api/logout", { method: "POST" });
  location.reload();
};
async function cargarYo() {
  const r = await fetch("/api/yo");
  if (!r.ok) { location.reload(); return; }
  yo = await r.json();
  if (yo.rol !== "admin") {
    $("masSucursal").style.display = "none";
  } else {
    $("cardUsuarios").style.display = "";
    cargarUsuarios();
  }
}
async function cargarUsuarios() {
  const r = await fetch("/api/usuarios");
  if (!r.ok) return;
  const us = await r.json();
  const ul = $("usuarios");
  ul.innerHTML = "";
  us.forEach(x => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="info">
        <div class="nombre">${x.usuario} ${x.rol === "admin" ? "· <b style='color:var(--dorado)'>admin</b>" : ""}</div>
        <div class="detalle">${x.rol === "admin" ? "Todas las sucursales" : (x.sucursales.join(", ") || "Todas")}</div>
      </div>
      ${x.usuario !== yo.usuario ? '<button class="btn btn-mini btn-peligro">Eliminar</button>' : ""}`;
    const b = li.querySelector("button");
    if (b) b.onclick = async () => {
      if (!confirm(`¿Eliminar al usuario "${x.usuario}"?`)) return;
      await fetch("/api/usuarios/eliminar", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario: x.usuario }) });
      cargarUsuarios();
    };
    ul.appendChild(li);
  });
  // llenar selector de sucursal para el nuevo usuario
  const rs = await fetch("/api/sucursales");
  const ss = await rs.json();
  $("nuevaSucursal").innerHTML = ss.map(s => `<option value="${s.clave}">${s.nombre}</option>`).join("");
}
$("crearUsuario").onclick = async () => {
  const usuario = $("nuevoUsuario").value.trim();
  const contrasena = $("nuevaContrasena").value;
  if (!usuario || contrasena.length < 4) { alert("Usuario y contraseña de al menos 4 caracteres"); return; }
  const r = await fetch("/api/usuarios", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, contrasena, rol: $("nuevoRol").value,
      sucursales: $("nuevoRol").value === "admin" ? [] : [$("nuevaSucursal").value] }) });
  if (r.ok) { $("nuevoUsuario").value = ""; $("nuevaContrasena").value = ""; cargarUsuarios(); avisoGuardado(); }
  else alert("No se pudo crear (¿ya existe?)");
};

/* ---------- sucursales ---------- */
async function cargarSucursales() {
  const r = await fetch("/api/sucursales");
  const s = await r.json();
  todasSucursales = s;
  const sel = $("selSucursal");
  sel.innerHTML = "";
  s.forEach(x => {
    const o = document.createElement("option");
    o.value = x.clave; o.textContent = x.nombre;
    sel.appendChild(o);
  });
  if (!sucursal) sucursal = s[0].clave;
  sel.value = sucursal;
  $("nomSucursal").textContent = s.find(x => x.clave === sucursal).nombre;
}
$("selSucursal").onchange = () => {
  sucursal = $("selSucursal").value;
  cargarSucursales(); cargarTvs(); cargar(); cargarAjustes();
};
$("masSucursal").onclick = async () => {
  const nombre = prompt("Nombre de la nueva sucursal:");
  if (!nombre) return;
  await fetch("/api/sucursales", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre }) });
  await cargarSucursales();
};

/* ---------- pantallas: estado real reportado por la TV (B5a) ---------- */
function haceTexto(seg) {
  if (seg < 60) return "hace " + seg + " s";
  if (seg < 3600) return "hace " + Math.floor(seg / 60) + " min";
  if (seg < 86400) return "hace " + Math.floor(seg / 3600) + " h";
  return "hace " + Math.floor(seg / 86400) + " d";
}
function esc(s) { return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function estadoTvHtml(t) {
  const e = t.estado || {};
  if (!e.version && !e.reproduciendo) return "";   // app anterior: no reporta
  const partes = [];
  if (e.reproduciendo) partes.push((e.desde_cache ? "▶ (sin red) " : "▶ ") + esc(e.reproduciendo));
  if (e.cache_mb !== undefined) partes.push("cache " + e.cache_mb + " MB");
  if (e.version) partes.push("app " + esc(e.version));
  if (e.modelo) partes.push(esc(e.modelo) + (e.sistema ? " · OS " + esc(e.sistema) : ""));
  if (e.ip) partes.push(esc(e.ip));
  let html = '<div class="detalle estado-tv">' + partes.join(" · ") + "</div>";
  if (e.error) {
    const hace = e.error_en ? haceTexto(Math.max(0, Math.floor(Date.now() / 1000) - e.error_en)) : "";
    html += '<div class="detalle estado-tv error">último error: ' + esc(e.error) + (hace ? " · " + hace : "") + "</div>";
  }
  return html;
}

/* ---------- pantallas ---------- */
async function cargarTvs() {
  const r = await fetch("/api/tvs?sucursal=" + sucursal);
  listaTvs = await r.json();
  const ul = $("tvs");
  ul.innerHTML = "";
  if (!listaTvs.length) {
    ul.innerHTML = '<li class="vacio">Ninguna TV en esta sucursal todavía.</li>';
    llenarPantallasRapido();
    return;
  }
  llenarPantallasRapido();
  listaTvs.forEach(t => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="num-tv">${t.numero}</span>
      <div class="info">
        <input class="zona-input" value="${t.zona || ""}" placeholder="Zona (ej. Recepción)">
        <div class="detalle"><span class="punto ${t.en_linea ? "on" : ""}"></span>
          ${t.corto} · ${t.en_linea ? "en línea" : "sin conexión"}</div>
        ${estadoTvHtml(t)}
      </div>
      <label class="opcion" style="font-size:12.5px" title="Mostrar turnos en esta pantalla">
        <span class="sw"><input type="checkbox" class="sw-turnos" ${t.turnos ? "checked" : ""}><i></i></span>
        Turnos
      </label>
      <div class="acciones">
        <select class="claro sel-lista" title="Lista que reproduce esta pantalla">
          <option value="">Lista al aire</option>
          ${listasDisponibles.map(l => `<option value="${l.id}" ${l.id === t.lista ? "selected" : ""}>${l.nombre}</option>`).join("")}
        </select>
        ${yo.rol === "admin" ? `<select class="claro sel-mover" title="Mover de sucursal">${
          todasSucursales.map(s => `<option value="${s.clave}" ${s.clave === sucursal ? "selected" : ""}>${s.nombre}</option>`).join("")
        }</select>` : ""}
        <button class="btn btn-ctrl btn-pp" title="${t.pausada ? "Continuar" : "Pausar"}">${t.pausada ? ICONO_PLAY : ICONO_PAUSA}</button>
        <button class="btn btn-ctrl btn-mute" title="Silenciar / activar sonido" style="${t.silencio ? "color:#FF5A5F" : ""}">${t.silencio ? ICONO_MUDO : ICONO_SONIDO}</button>
        ${yo.rol === "admin" ? '<button class="btn btn-ctrl btn-recargar" title="Recargar la app de esta pantalla (vuelve a pedir la lista y empieza de nuevo)">↻</button>' : ""}
        ${yo.rol === "admin" ? '<button class="btn btn-ctrl btn-vaciar" title="Vaciar la cache de esta pantalla (vuelve a descargar su contenido)">⌫</button>' : ""}
        ${yo.rol === "admin" ? '<button class="btn btn-icono btn-peligro btn-quitar" title="Eliminar pantalla">✕</button>' : ""}
      </div>`;
    const zonaIn = li.querySelector(".zona-input");
    zonaIn.onchange = async () => {
      await fetch("/api/tv", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: t.id, zona: zonaIn.value }) });
      avisoGuardado(); cargarTvs(); cargar();
    };
    const pp = li.querySelector(".btn-pp");
    pp.onclick = () => {
      t.pausada = !t.pausada;
      pp.innerHTML = t.pausada ? ICONO_PLAY : ICONO_PAUSA;
      pp.title = t.pausada ? "Continuar" : "Pausar";
      comando(t.id, t.pausada ? "pausa" : "continuar");
    };
    const rec = li.querySelector(".btn-recargar");
    if (rec) rec.onclick = () => { comando(t.id, "recargar"); avisoGuardado(); };
    const vac = li.querySelector(".btn-vaciar");
    if (vac) vac.onclick = () => { if (confirm("¿Vaciar la cache de la pantalla " + t.numero + "? Volverá a descargar su contenido.")) { comando(t.id, "vaciar_cache"); avisoGuardado(); } };
    const mute = li.querySelector(".btn-mute");
    mute.onclick = () => {
      t.silencio = !t.silencio;
      mute.innerHTML = t.silencio ? ICONO_MUDO : ICONO_SONIDO;
      mute.style.color = t.silencio ? "#FF5A5F" : "";
      comando(t.id, t.silencio ? "silencio" : "sonido");
    };
    const selLista = li.querySelector(".sel-lista");
    selLista.onchange = async () => {
      await fetch("/api/tv", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: t.id, lista: selLista.value }) });
      avisoGuardado();
    };
    const swTurnos = li.querySelector(".sw-turnos");
    swTurnos.onchange = async () => {
      await fetch("/api/tv", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: t.id, turnos: swTurnos.checked }) });
      avisoGuardado();
    };
    const mover = li.querySelector(".sel-mover");
    if (mover) mover.onchange = async () => {
      await fetch("/api/tv", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: t.id, sucursal: mover.value }) });
      avisoGuardado(); cargarTvs(); cargar();
    };
    const quitar = li.querySelector(".btn-quitar");
    if (quitar) quitar.onclick = async () => {
      if (!confirm(`¿Eliminar la pantalla ${t.numero}${t.zona ? " (" + t.zona + ")" : ""}?\nSi la TV sigue encendida con la app, volverá a aparecer como pendiente.`)) return;
      await fetch("/api/tv/eliminar", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: t.id }) });
      cargarTvs(); cargarPendientes();
    };
    ul.appendChild(li);
  });
}

async function comando(id, accion, nombre) {
  await fetch("/api/tv/comando", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, accion, nombre, sucursal }) });
  avisoGuardado();
}

/* ---------- pantallas pendientes (admin) ---------- */
async function cargarPendientes() {
  if (yo.rol !== "admin") return;
  const r = await fetch("/api/tv/pendientes");
  if (!r.ok) return;
  const ps = await r.json();
  const card = $("cardPendientes");
  if (!ps.length) { card.style.display = "none"; return; }
  card.style.display = "";
  const ul = $("pendientes");
  ul.innerHTML = "";
  ps.forEach(p => {
    const li = document.createElement("li");
    const ops = todasSucursales.map(s => `<option value="${s.clave}">${s.nombre}</option>`).join("");
    li.innerHTML = `
      <span class="num-tv" style="width:auto; padding:0 14px; letter-spacing:3px; font-size:17px;">${p.codigo}</span>
      <div class="info">
        <div class="nombre">Pantalla nueva <small style="color:var(--gris)">(${p.corto})</small></div>
        <div class="detalle"><span class="punto ${p.en_linea ? "on" : ""}"></span>
          ${p.en_linea ? "en línea, esperando aprobación" : "sin conexión"}</div>
      </div>
      <div class="acciones">
        <select class="claro sel-suc">${ops}</select>
        <input class="zona-input" placeholder="Zona" style="max-width:130px; border:1px solid var(--borde);">
        <button class="btn btn-primario btn-mini">Aprobar</button>
        <button class="btn btn-mini btn-peligro">Rechazar</button>
      </div>`;
    const sel = li.querySelector(".sel-suc");
    const zona = li.querySelector(".zona-input");
    const [aprobar, rechazar] = li.querySelectorAll(".acciones .btn");
    aprobar.onclick = async () => {
      await fetch("/api/tv/aprobar", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: p.id, sucursal: sel.value, zona: zona.value }) });
      avisoGuardado(); cargarPendientes(); cargarTvs();
    };
    rechazar.onclick = async () => {
      if (!confirm("¿Rechazar esta pantalla? No recibirá contenido.")) return;
      await fetch("/api/tv/eliminar", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: p.id }) });
      cargarPendientes();
    };
    ul.appendChild(li);
  });
}

/* ---------- lista de contenido ---------- */
function opcionesEnviar() {
  let ops = '<option value="">Enviar a…</option>';
  if (listaTvs.length > 1) ops += '<option value="todas">Todas las pantallas</option>';
  listaTvs.forEach(t => {
    ops += `<option value="${t.id}">P${t.numero}${t.zona ? " · " + t.zona : ""}</option>`;
  });
  return ops;
}

function resumenPrograma(p, activo) {
  const DIAS = ["Lu","Ma","Mi","Ju","Vi","Sá","Do"];
  const partes = [];
  if (p.dias && p.dias.length) partes.push(p.dias.map(d => DIAS[d]).join(" "));
  if (p.desde || p.hasta) partes.push(`${p.desde || "…"} → ${p.hasta || "…"}`);
  if (p.hini && p.hfin) partes.push(`${p.hini}–${p.hfin}`);
  const estado = activo
    ? '<span style="color:#2E9E5B; font-weight:600">● al aire ahora</span>'
    : '<span style="color:var(--gris)">○ fuera de horario</span>';
  return `${partes.join(" · ") || "sin condiciones"} · ${estado}`;
}

function camposCampana(p = {}) {
  const DIAS = ["Lu","Ma","Mi","Ju","Vi","Sá","Do"];
  return `
    <span style="font-size:12.5px; color:var(--gris)">Días:</span>
    ${DIAS.map((d,i) => `<label style="font-size:12.5px; display:flex; align-items:center; gap:3px">
      <input type="checkbox" class="pd" value="${i}" ${(p.dias||[]).includes(i) ? "checked" : ""}>${d}</label>`).join("")}
    <input type="date" class="claro p-desde" value="${p.desde||""}" title="Desde">
    <input type="date" class="claro p-hasta" value="${p.hasta||""}" title="Hasta">
    <input type="time" class="claro p-hini" value="${p.hini||""}" title="Hora inicio">
    <input type="time" class="claro p-hfin" value="${p.hfin||""}" title="Hora fin">`;
}

async function guardarCampana(nombre, cont) {
  const dias = [...cont.querySelectorAll(".pd:checked")].map(x => parseInt(x.value));
  await fetch("/api/programar", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, nombre, dias,
      desde: cont.querySelector(".p-desde").value,
      hasta: cont.querySelector(".p-hasta").value,
      hini: cont.querySelector(".p-hini").value,
      hfin: cont.querySelector(".p-hfin").value }) });
  avisoGuardado(); cargar();
}

let listaActual = "";
let listaActiva = "";
let listasDisponibles = [];

async function cargarListas() {
  const r = await fetch("/api/listas?sucursal=" + sucursal);
  const info = await r.json();
  listaActiva = info.activa;
  listasDisponibles = info.listas;
  if (!info.listas.some(l => l.id === listaActual)) listaActual = info.activa;
  const sel = $("listaSel");
  sel.innerHTML = info.listas.map(l =>
    `<option value="${l.id}" ${l.id === listaActual ? "selected" : ""}>${l.nombre} (${l.cuantos})</option>`).join("");
  const nom = info.listas.find(l => l.id === listaActual);
  $("listaNombre").textContent = nom ? nom.nombre : "la lista";
  const alAire = listaActual === listaActiva;
  $("listaAlAire").innerHTML = alAire
    ? '<span style="color:#2E9E5B; font-weight:600">● al aire ahora</span>'
    : '<span style="color:var(--gris)">○ en edición</span>';
  $("listaAlAireBtn").style.display = alAire ? "none" : "";
  return info;
}

async function cargar() {
  await cargarListas();

  const r = await fetch(`/api/lista?sucursal=${sucursal}&lista=${listaActual}`);
  const enLista = await r.json();
  const rb = await fetch("/api/biblioteca?sucursal=" + sucursal);
  const todos = await rb.json();

  /* --- campañas programadas (sobre toda la biblioteca) --- */
  const conProg = enLista.filter(a => a.programa);
  const sinProg = todos.filter(a => !conProg.some(c => c.nombre === a.nombre));
  const selc = $("campSel");
  selc.innerHTML = '<option value="">Elegir contenido…</option>' +
    sinProg.map(a => `<option value="${a.nombre}">${a.nombre}</option>`).join("");
  const ulc = $("campanas");
  ulc.innerHTML = "";
  conProg.forEach(a => {
    const li = document.createElement("li");
    li.style.flexWrap = "wrap";
    const mini = a.miniatura ? `<img class="mini" src="${a.miniatura}" alt="">` : `<div class="mini"></div>`;
    li.innerHTML = `
      ${mini}
      <div class="info">
        <div class="nombre">${a.nombre}</div>
        <div class="detalle">${resumenPrograma(a.programa, a.activo)}</div>
      </div>
      <div class="acciones">
        <button class="btn btn-mini">Editar</button>
        <button class="btn btn-mini btn-peligro">Quitar</button>
      </div>`;
    const [editar, quitar] = li.querySelectorAll(".acciones button");
    editar.onclick = () => {
      const previo = li.querySelector(".editor-prog");
      if (previo) { previo.remove(); return; }
      const ed = document.createElement("div");
      ed.className = "editor-prog";
      ed.style.cssText = "flex-basis:100%; width:100%; display:flex; flex-wrap:wrap; gap:8px; align-items:center; padding:12px; background:var(--fondo); border-radius:12px; margin-top:8px;";
      ed.innerHTML = camposCampana(a.programa) +
        '<button class="btn btn-mini btn-primario p-g">Guardar</button>';
      ed.querySelector(".p-g").onclick = () => guardarCampana(a.nombre, ed);
      li.appendChild(ed);
    };
    quitar.onclick = async () => {
      if (!confirm(`"${a.nombre}" dejará de tener horario y se mostrará siempre que esté en una lista al aire. ¿Continuar?`)) return;
      await fetch("/api/programar", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sucursal, nombre: a.nombre, dias: [] }) });
      avisoGuardado(); cargar();
    };
    ulc.appendChild(li);
  });
  if (!conProg.length)
    ulc.innerHTML = '<li class="vacio">Sin campañas. Elige un contenido y ponle sus días, fechas u horario.</li>';

  /* --- contenido de la lista en edición --- */
  const ul = $("lista");
  ul.innerHTML = "";
  if (!enLista.length) {
    ul.innerHTML = '<li class="vacio">Esta lista está vacía. Agrégale contenido desde la Biblioteca.</li>';
  }
  enLista.forEach((a, i) => {
    const li = document.createElement("li");
    if (a.programa && !a.activo) li.style.opacity = "0.5";
    const mini = a.miniatura ? `<img class="mini" src="${a.miniatura}" alt="">` : `<div class="mini"></div>`;
    const dur = a.tipo === "imagen"
      ? `· <input class="dur" type="number" min="3" max="120" value="${a.duracion}"> seg` : "";
    const prog = a.programa
      ? ` · <span style="color:var(--rosa-fuerte)">${resumenPrograma(a.programa, a.activo)}</span>` : "";
    li.innerHTML = `
      <span class="orden">${i + 1}</span>
      ${mini}
      <div class="info">
        <div class="nombre">${a.nombre}</div>
        <div class="detalle">${a.tipo === "imagen" ? "Foto" : "Video"} ${dur}${prog}</div>
      </div>
      <div class="acciones">
        <select class="enviar">${opcionesEnviar()}</select>
        <button class="btn btn-icono" title="Subir" ${i === 0 ? "disabled" : ""}>↑</button>
        <button class="btn btn-icono" title="Bajar" ${i === enLista.length - 1 ? "disabled" : ""}>↓</button>
        <button class="btn btn-mini" title="Quitar de esta lista (no se borra)">Quitar</button>
      </div>`;
    const durInput = li.querySelector(".dur");
    if (durInput) durInput.onchange = () => guardarDuracion(a.nombre, durInput.value);
    const enviar = li.querySelector(".enviar");
    enviar.onchange = () => {
      if (enviar.value) comando(enviar.value, "reproducir", a.nombre);
      enviar.value = "";
    };
    const [sube, baja, quita] = li.querySelectorAll("button");
    sube.onclick = () => mover(a.nombre, -1);
    baja.onclick = () => mover(a.nombre, 1);
    quita.onclick = () => cambiarEnLista({ quitar: [a.nombre] });
    ul.appendChild(li);
  });

  /* --- biblioteca --- */
  const ulb = $("biblioteca");
  ulb.innerHTML = "";
  $("bibCuantos").textContent = `· ${todos.length} en la nube`;
  if (!todos.length) {
    ulb.innerHTML = '<li class="vacio">Aún no hay contenido en esta sucursal.</li>';
    return;
  }
  const enEsta = new Set(enLista.map(a => a.nombre));
  todos.forEach(a => {
    const li = document.createElement("li");
    const mini = a.miniatura ? `<img class="mini" src="${a.miniatura}" alt="">` : `<div class="mini"></div>`;
    const donde = a.listas.length ? a.listas.join(" · ") : "en ninguna lista";
    const ya = enEsta.has(a.nombre);
    li.innerHTML = `
      ${mini}
      <div class="info">
        <div class="nombre">${a.nombre}</div>
        <div class="detalle">${a.tipo === "imagen" ? "Foto" : "Video"} · ${donde}</div>
      </div>
      <div class="acciones">
        <button class="btn btn-mini ${ya ? "" : "btn-primario"}" ${ya ? "disabled" : ""}>${ya ? "Ya en la lista" : "Agregar"}</button>
        <button class="btn btn-mini btn-renombrar">Renombrar</button>
        <button class="btn btn-mini btn-peligro">Eliminar de la nube</button>
      </div>`;
    const [agregar, renombrar, borrar] = li.querySelectorAll("button");
    renombrar.onclick = async () => {
      const sinExt = a.nombre.replace(/[.][^.]+$/, "");
      const nuevo = prompt("Nuevo nombre (sin extensión):", sinExt);
      if (nuevo === null) return;
      const limpio = nuevo.trim();
      if (!limpio || limpio === sinExt) return;
      const r = await fetch("/api/renombrar", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sucursal, nombre: a.nombre, nuevo: limpio }) });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        alert(e.error === "ya existe otro con ese nombre"
          ? "Ya hay otro contenido con ese nombre en esta sucursal."
          : "No se pudo renombrar.");
        return;
      }
      avisoGuardado(); cargar();
    };
    agregar.onclick = () => cambiarEnLista({ agregar: [a.nombre] });
    borrar.onclick = () => {
      if (!confirm(`¿Eliminar "${a.nombre}" de la nube?\nSe quitará de TODAS las listas y no se podrá recuperar.`)) return;
      eliminar(a.nombre);
    };
    ulb.appendChild(li);
  });
}

async function cambiarEnLista(cambio) {
  await fetch("/api/listas/contenido", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, id: listaActual, ...cambio }) });
  avisoGuardado(); cargar();
}

$("listaSel").onchange = () => { listaActual = $("listaSel").value; cargar(); };
$("listaAlAireBtn").onclick = async () => {
  await fetch("/api/listas/activar", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, id: listaActual }) });
  avisoGuardado(); cargar(); cargarTvs();
};
$("listaNueva").onclick = async () => {
  const nombre = prompt("Nombre de la nueva lista (ej. Día de las Madres)");
  if (!nombre) return;
  const r = await fetch("/api/listas/crear", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, nombre }) });
  const d = await r.json();
  if (d.id) listaActual = d.id;
  avisoGuardado(); cargar();
};
$("listaRenombrar").onclick = async () => {
  const nombre = prompt("Nuevo nombre de la lista");
  if (!nombre) return;
  await fetch("/api/listas/renombrar", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, id: listaActual, nombre }) });
  avisoGuardado(); cargar();
};
$("listaBorrar").onclick = async () => {
  if (!confirm("¿Eliminar esta lista? El contenido NO se borra, sigue en la Biblioteca.")) return;
  const r = await fetch("/api/listas/eliminar", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, id: listaActual }) });
  if (!r.ok) { alert("No se puede eliminar la única lista de la sucursal."); return; }
  listaActual = "";
  avisoGuardado(); cargar(); cargarTvs();
};

$("campCampos").innerHTML = camposCampana();
$("campCrear").onclick = () => {
  const n = $("campSel").value;
  if (!n) { alert("Primero elige el contenido a programar"); return; }
  guardarCampana(n, $("nuevaCamp"));
  $("campSel").value = "";
};

async function guardarDuracion(nombre, segundos) {
  await fetch("/api/duracion", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, nombre, segundos: parseInt(segundos) }) });
  avisoGuardado();
}
async function mover(nombre, dir) {
  await fetch("/api/mover", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, nombre, dir, lista: listaActual }) });
  cargar();
}

async function eliminar(nombre) {
  await fetch("/api/eliminar", { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sucursal, nombre }) });
  cargar();
}

/* ---------- conversión de fotos en el teléfono (HEIC -> JPG) ---------- */
async function prepararArchivo(f) {
  const esHeic = /[.](heic|heif)$/i.test(f.name) || f.type === "image/heic" || f.type === "image/heif";
  const esImagen = f.type.startsWith("image/") || esHeic;
  if (!esImagen) return { archivo: f, nombre: f.name };
  try {
    const url = URL.createObjectURL(f);
    const img = await new Promise((res, rej) => {
      const i = new Image();
      i.onload = () => res(i);
      i.onerror = rej;
      i.src = url;
    });
    const MAX = 1920;
    const w0 = img.naturalWidth, h0 = img.naturalHeight;
    const necesitaEscala = Math.max(w0, h0) > MAX;
    if (!esHeic && !necesitaEscala) {
      // PNG/JPG que ya está bien: se sube intacto, sin perder calidad
      URL.revokeObjectURL(url);
      return { archivo: f, nombre: f.name };
    }
    const esc = Math.min(1, MAX / Math.max(w0, h0));
    const w = Math.round(w0 * esc), h = Math.round(h0 * esc);
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    c.getContext("2d").drawImage(img, 0, 0, w, h);
    URL.revokeObjectURL(url);
    const esPng = f.type === "image/png";
    const tipoSalida = esPng ? "image/png" : "image/jpeg";
    const blob = await new Promise(res => c.toBlob(res, tipoSalida, 0.92));
    if (!blob) throw new Error("sin blob");
    const ext = esPng ? ".png" : ".jpg";
    return { archivo: blob, nombre: f.name.replace(/[.][^.]+$/, "") + ext };
  } catch (e) {
    return { archivo: f, nombre: f.name };
  }
}

/* ---------- subida ---------- */
function subir(files) {
  [...files].forEach(async f => {
    const prep = await prepararArchivo(f);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/subir?sucursal=" + sucursal + "&lista=" + listaActual + "&nombre=" + encodeURIComponent(prep.nombre));
    xhr.upload.onprogress = e => {
      if (e.lengthComputable) {
        const p = Math.round(e.loaded / e.total * 100);
        $("progreso").textContent = p < 100 ? `Subiendo ${f.name}: ${p}%` : `Procesando ${f.name}…`;
      }
    };
    xhr.onload = () => { $("progreso").textContent = ""; cargar(); };
    xhr.onerror = () => { $("progreso").textContent = "Error al subir " + f.name; };
    xhr.send(prep.archivo);
  });
}
$("zona").onclick = () => $("archivo").click();
$("archivo").onchange = e => subir(e.target.files);
$("zona").ondragover = e => { e.preventDefault(); $("zona").classList.add("activa"); };
$("zona").ondragleave = () => $("zona").classList.remove("activa");
$("zona").ondrop = e => { e.preventDefault(); $("zona").classList.remove("activa"); subir(e.dataTransfer.files); };

/* ---------- anunciar turno ---------- */
$("anunciarTurno").onclick = async () => {
  const numero = $("tNumero").value.trim();
  if (!numero) { alert("Pon el número de turno"); return; }
  const r = await fetch("/api/turno?sucursal=" + sucursal, { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      numero,
      estacion: $("tEstacion").value.trim(),
      espera: $("tEspera").value.trim()
    }) });
  if (r.ok) {
    avisoGuardado();
    $("tNumero").value = ""; $("tEstacion").value = "";
  }
};

/* ---------- estadisticas ---------- */
async function cargarStats() {
  const r = await fetch("/api/estadisticas?sucursal=" + sucursal);
  if (!r.ok) return;
  const s = await r.json();
  const card = $("cardStats");
  if (!s.length) { card.style.display = "none"; return; }
  card.style.display = "";
  const ul = $("stats");
  ul.innerHTML = `<li style="border-bottom:1px solid var(--borde)">
    <div class="info"><b style="font-size:13px">Contenido</b></div>
    <div class="detalle" style="min-width:180px; display:flex; gap:18px; justify-content:flex-end">
      <b>Hoy</b><b>7 días</b><b>30 días</b></div></li>`;
  s.slice(0, 10).forEach(x => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="info"><div class="nombre" style="font-size:13.5px">${x.nombre}</div></div>
      <div class="detalle" style="min-width:180px; display:flex; gap:18px; justify-content:flex-end">
        <span style="min-width:34px; text-align:right">${x.hoy}</span>
        <span style="min-width:44px; text-align:right">${x.d7}</span>
        <span style="min-width:48px; text-align:right; color:var(--rosa-fuerte); font-weight:600">${x.d30}</span>
      </div>`;
    ul.appendChild(li);
  });
}

/* ---------- mostrar al cliente ---------- */
let archivoRapido = null;
function llenarPantallasRapido() {
  const sel = $("pantallaRapido");
  let ops = "";
  listaTvs.forEach(t => {
    ops += `<option value="${t.id}">P${t.numero}${t.zona ? " · " + t.zona : ""}</option>`;
  });
  if (listaTvs.length > 1) ops += '<option value="todas">Todas</option>';
  sel.innerHTML = ops || '<option value="">Sin pantallas</option>';
}
$("btnRapido").onclick = () => $("archivoRapido").click();
$("archivoRapido").onchange = e => {
  archivoRapido = e.target.files[0] || null;
  $("nomRapido").textContent = archivoRapido ? archivoRapido.name : "Nada elegido";
  $("mostrarRapido").disabled = !archivoRapido;
};
$("mostrarRapido").onclick = async () => {
  if (!archivoRapido || !$("pantallaRapido").value) return;
  $("progresoRapido").textContent = "Preparando…";
  const prep = await prepararArchivo(archivoRapido);
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/rapido?sucursal=" + sucursal +
    "&id=" + encodeURIComponent($("pantallaRapido").value) +
    "&nombre=" + encodeURIComponent(prep.nombre));
  xhr.upload.onprogress = e => {
    if (e.lengthComputable) {
      const p = Math.round(e.loaded / e.total * 100);
      $("progresoRapido").textContent = p < 100 ? `Subiendo: ${p}%` : "Preparando…";
    }
  };
  xhr.onload = () => {
    $("progresoRapido").textContent = "✓ Mostrándose en la pantalla (unos segundos)";
    setTimeout(() => $("progresoRapido").textContent = "", 4000);
    archivoRapido = null;
    $("nomRapido").textContent = "Nada elegido";
    $("mostrarRapido").disabled = true;
    $("archivoRapido").value = "";
  };
  xhr.onerror = () => { $("progresoRapido").textContent = "Error al subir"; };
  xhr.send(prep.archivo);
};

/* ---------- mensaje y cintillo ---------- */
async function cargarAjustes() {
  const r = await fetch("/api/ajustes?sucursal=" + sucursal);
  const a = await r.json();
  $("mensaje").value = a.mensaje || "";
  $("animado").checked = a.animado !== false;
  $("velocidad").value = String(a.velocidad || 130);
}
async function guardarAjustes(mensajeNuevo) {
  const cuerpo = { animado: $("animado").checked, velocidad: parseInt($("velocidad").value) };
  if (mensajeNuevo !== undefined) cuerpo.mensaje = mensajeNuevo;
  await fetch("/api/ajustes?sucursal=" + sucursal, { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo) });
  if (mensajeNuevo !== undefined) $("mensaje").value = mensajeNuevo;
  avisoGuardado();
}
$("guardarMsg").onclick = () => guardarAjustes($("mensaje").value.trim());
$("quitarMsg").onclick = () => guardarAjustes("");
$("mensaje").addEventListener("keydown", e => { if (e.key === "Enter") guardarAjustes($("mensaje").value.trim()); });
$("animado").onchange = () => guardarAjustes();
$("velocidad").onchange = () => guardarAjustes();

(async () => {
  await cargarYo();
  await cargarSucursales();
  await cargarListas();
  cargarTvs(); cargar(); cargarAjustes(); cargarPendientes(); cargarStats();
  setInterval(() => { cargarTvs(); cargarPendientes(); }, 8000);
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
})();
</script>
</body>
</html>""".replace("__LOGO__", LOGO_B64)


if __name__ == "__main__":
    migrar()
    ip = ip_local()
    print("=" * 56)
    print("  LUMIN TV 6.10.1 — servidor de anuncios")
    print(f"  Bitácora:          {os.path.join(DIR_REGISTRO, 'lumin.log')}")
    print(f"  Panel de control:  http://localhost:{PUERTO}")
    print(f"  URL para las TVs:  http://{ip}:{PUERTO}")
    print("  Ctrl+C para detener")
    print("=" * 56)
    ServidorSilencioso(("0.0.0.0", PUERTO), Manejador).serve_forever()
