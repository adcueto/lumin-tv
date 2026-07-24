#!/usr/bin/env python3
"""Vigilante LUMIN — para Raspberry Pi (o cualquier equipo siempre encendido).

Durante el horario del negocio, revisa cada pocos minutos las TVs Roku de la
sucursal: las enciende si están dormidas y abre la app LUMIN TV si no está
corriendo. Al cierre, las apaga (opcional). Usa el protocolo ECP de Roku
(puerto 8060) — no requiere instalar nada en las TVs.

Requisitos en cada TV (una sola vez, con el control):
  1. Configuración → Sistema → Energía → Inicio rápido: ACTIVADO
  2. Configuración → Sistema → Avanzado → Control por apps móviles →
     Acceso de red: PREDETERMINADO (o Permisivo)
  3. IP fija para cada TV (reservación DHCP en el router del local)
"""
import json
import os
import time
import datetime
import urllib.request
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "config.json"), encoding="utf-8") as f:
    CONFIG = json.load(f)


def log(mensaje):
    marca = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{marca}] {mensaje}", flush=True)


def ecp(ip, metodo, ruta, timeout=4):
    """Manda un comando ECP a la TV."""
    peticion = urllib.request.Request(
        f"http://{ip}:8060/{ruta}",
        method=metodo,
        data=b"" if metodo == "POST" else None,
    )
    with urllib.request.urlopen(peticion, timeout=timeout) as r:
        return r.read()


def buscar_app_lumin(ip):
    """Encuentra el id de la app LUMIN instalada en la TV (tienda o dev)."""
    xml = ecp(ip, "GET", "query/apps")
    objetivo = CONFIG.get("nombre_app", "lumin").lower()
    for app in ET.fromstring(xml):
        if objetivo in (app.text or "").lower():
            return app.attrib.get("id")
    return None


def app_activa(ip):
    xml = ecp(ip, "GET", "query/active-app")
    el = ET.fromstring(xml).find("app")
    if el is None:
        return "", ""
    return (el.text or ""), el.attrib.get("id", "")


def en_horario():
    ahora = datetime.datetime.now()
    dias = CONFIG.get("dias", [0, 1, 2, 3, 4, 5, 6])  # 0=lunes ... 6=domingo
    if ahora.weekday() not in dias:
        return False
    return CONFIG["abre"] <= ahora.strftime("%H:%M") < CONFIG["cierra"]


def atender_tv(ip):
    """Enciende la TV si hace falta y se asegura de que LUMIN esté corriendo."""
    try:
        ecp(ip, "POST", "keypress/PowerOn")
    except Exception:
        log(f"{ip}: no responde — ¿desconectada o sin 'Inicio rápido'?")
        return
    time.sleep(3)
    try:
        id_lumin = buscar_app_lumin(ip)
        if not id_lumin:
            log(f"{ip}: la app LUMIN no está instalada en esta TV")
            return
        nombre, id_actual = app_activa(ip)
        if id_actual != id_lumin:
            ecp(ip, "POST", f"launch/{id_lumin}")
            log(f"{ip}: abriendo LUMIN TV (estaba en: {nombre or 'pantalla de inicio'})")
    except Exception as e:
        log(f"{ip}: error {e}")


def apagar_tv(ip):
    try:
        ecp(ip, "POST", "keypress/PowerOff")
        log(f"{ip}: apagada por fin de horario")
    except Exception:
        pass


def principal():
    log("Vigilante LUMIN iniciado")
    log(f"TVs a cuidar: {', '.join(CONFIG['tvs'])}")
    log(f"Horario: {CONFIG['abre']}–{CONFIG['cierra']}")
    ya_apagadas = False
    while True:
        try:
            if en_horario():
                ya_apagadas = False
                for ip in CONFIG["tvs"]:
                    atender_tv(ip)
            elif CONFIG.get("apagar_al_cierre", True) and not ya_apagadas:
                for ip in CONFIG["tvs"]:
                    apagar_tv(ip)
                ya_apagadas = True
        except Exception as e:
            log(f"error en el ciclo: {e}")
        time.sleep(CONFIG.get("intervalo_seg", 120))


if __name__ == "__main__":
    principal()
