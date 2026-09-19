#!/usr/bin/env python3
"""Genera capturas/ del prototipo con Playwright (Chromium). Solo documentación."""
from pathlib import Path
from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
HTML = (AQUI / "prototipo.html").as_uri()
CSS = ".etq{position:static;display:block;text-align:center;border-radius:0;padding:6px}.tabs{position:static;margin-top:8px}"
VISTAS = {"escritorio": (1366, 860, ["inicio", "pantallas", "biblioteca", "listas", "ajustes"]),
          "movil": (390, 844, ["inicio", "mostrar", "turnos"])}

with sync_playwright() as p:
    b = p.chromium.launch()
    for modo, (w, h, secciones) in VISTAS.items():
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
        pg = ctx.new_page()
        for s in secciones:
            pg.goto(HTML + "#" + s); pg.add_style_tag(content=CSS); pg.wait_for_timeout(500)
            pg.screenshot(path=str(AQUI / "capturas" / f"{modo}-{s}.png"), full_page=True)
        ctx.close()
    b.close()
