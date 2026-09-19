#!/usr/bin/env python3
"""UI-QA-01: el documento no debe ser mas ancho que el viewport en 360, 390 y 1366 px.
Devuelve 1 si alguna seccion desborda. Solo documentacion; usa Playwright."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML = (Path(__file__).resolve().parent / "prototipo.html").as_uri()
SECCIONES = ("inicio", "pantallas", "mostrar", "turnos", "biblioteca", "listas", "ajustes",
             "programacion", "mensajes", "sucursales", "integraciones")
malos = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (360, 390, 1366):
        pg = b.new_context(viewport={"width": w, "height": 800}).new_page()
        for s in SECCIONES:
            pg.goto(HTML + "#" + s); pg.wait_for_timeout(120)
            sw = pg.evaluate("document.documentElement.scrollWidth")
            print(f"{w:5} {s:14} ancho documento {sw}")
            if sw != w:
                malos.append((w, s, sw))
    b.close()
raise SystemExit(1 if malos else 0)
