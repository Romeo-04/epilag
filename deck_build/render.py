"""Render docs/deck/final/index.html to per-slide PNGs and a 1920x1080 PDF.
Usage: python deck_build/render.py [--pdf]"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/deck/final/index.html"
PNG = Path(__file__).parent / "png"
PNG.mkdir(exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto(SRC.as_uri(), wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    for i, el in enumerate(pg.query_selector_all("section.slide")):
        el.screenshot(path=str(PNG / f"s{i+1:02d}.png"))
    if "--pdf" in sys.argv:
        pg.emulate_media(media="print")
        pg.pdf(path=str(ROOT / "docs/deck/final/EpiLag-PH_final_deck.pdf"), width="1920px", height="1080px", print_background=True)
    b.close()
print("rendered")
