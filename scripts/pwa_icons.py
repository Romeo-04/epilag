"""App icons for the installable web app (site/public/icons/), drawn from site/public/favicon.svg.
icon-{192,512}.png keep the favicon's rounded square; maskable-512.png fills the square edge to edge with the
logo inside the safe zone, so Android can crop it to any shape. Usage: python scripts/pwa_icons.py"""
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SVG = (ROOT / "site" / "public" / "favicon.svg").read_text(encoding="utf-8")
OUT = ROOT / "site" / "public" / "icons"


def html(svg: str, size: int, pad: float) -> str:
    svg = svg.replace("<svg ", '<svg width="100%" height="100%" ', 1)
    return (f'<html><body style="margin:0;background:#08754F"><div style="width:{size}px;height:{size}px;display:grid;'
            f'place-items:center"><div style="width:{size * (1 - 2 * pad)}px;height:{size * (1 - 2 * pad)}px">'
            f'{svg}</div></div></body></html>')


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    flat = re.sub(r'<rect[^>]*rx="5"[^>]*/>', "", SVG, count=1)  # logo only, on the page's full-bleed green
    jobs = [("icon-192.png", 192, SVG, 0.0, True), ("icon-512.png", 512, SVG, 0.0, True), ("maskable-512.png", 512, flat, 0.16, False)]
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, size, svg, pad, transparent in jobs:
            pg = b.new_page(viewport={"width": size, "height": size})
            doc = html(svg, size, pad)
            if transparent:
                doc = doc.replace("background:#08754F", "background:transparent")
            pg.set_content(doc)
            pg.screenshot(path=str(OUT / name), omit_background=transparent)
            print(OUT / name)
        b.close()


if __name__ == "__main__":
    main()
