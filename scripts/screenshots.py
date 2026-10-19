"""Capture screenshots of the built site for the README, the film and the deck.

Serves docs/ on a local port (as GitHub Pages serves it, under /epilag/) and drives Chrome with Playwright:
the landing page, every app view (latest forecast and the 2 June 2019 replay), and the Dengue Drill (title,
briefing, round 2 board, round report), at 1440 px, plus a few phone views at 390 px. App pages are captured at
their full height with the viewport grown to fit, so the sticky sidebar spans the whole image.
Build the site first (cd site && npm run build). Usage: python scripts/screenshots.py [name ...]
"""
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "screenshots"
REPLAY = "&panel=province&mode=replay&origin=2019-06-02&h=4"

# name, path, width, full height
SHOTS = [
    ("landing", "", 1440, False),
    ("landing_phone", "", 390, False),
    ("home", "web/?page=home", 1440, True),
    ("home_replay_2019", f"web/?page=home{REPLAY}", 1440, True),
    ("map_latest", "web/?page=map", 1440, True),
    ("map_replay_2019", f"web/?page=map{REPLAY}", 1440, True),
    ("unit_latest", "web/?page=unit&region=R_NCR&area=QC", 1440, True),
    ("unit_replay_2019", f"web/?page=unit{REPLAY}", 1440, True),
    ("budget_replay_2019", f"web/?page=budget{REPLAY}", 1440, True),
    ("public", f"web/?page=public{REPLAY}", 1440, True),
    ("qc", "web/?page=qc&region=R_NCR&area=QC", 1440, True),
    ("proof", "web/?page=proof", 1440, True),
    ("about", "web/?page=about", 1440, True),
    ("app_phone", "web/?page=home", 390, False),
    ("methodology", "methodology.html", 1440, False),
]
DRILL = ["drill_title", "drill_receipt", "drill_round2", "drill_report"]


class _Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):  # the site is published under /epilag/
        return super().translate_path(path.removeprefix("/epilag"))

    def log_message(self, *args):
        pass


def shoot(browser, base, name, path, width, full):
    ctx = browser.new_context(viewport={"width": width, "height": 900 if width > 500 else 844}, device_scale_factor=1,
                              is_mobile=width < 500, has_touch=width < 500)
    ctx.add_init_script("try { sessionStorage.setItem('el-intro', '1') } catch (e) {}")  # skip the landing intro
    page = ctx.new_page()
    page.goto(base + path, wait_until="networkidle")
    page.wait_for_timeout(2500)
    if full:
        height = page.evaluate("document.documentElement.scrollHeight")
        page.set_viewport_size({"width": width, "height": min(height, 4200)})
        page.wait_for_timeout(1500)
    page.screenshot(path=OUT / f"{name}.png")
    ctx.close()
    print("saved", name)


def drill(browser, base, only):
    """Play into the drill (its first mission, Quezon City): title, the case receipt, round 2 with a few teams out, and the round report."""
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(base + "drill/", wait_until="networkidle")
    page.wait_for_timeout(4000)
    save = lambda n: (not only or n in only) and (page.screenshot(path=OUT / f"{n}.png"), print("saved", n))
    save("drill_title")
    page.click("#start"); page.wait_for_timeout(2800)
    save("drill_receipt")
    page.click("#go-r1"); page.wait_for_timeout(2500)
    for _ in range(8):
        page.click("#end"); page.wait_for_timeout(1300)
    page.wait_for_timeout(2500)
    page.click("#next-r"); page.wait_for_timeout(3000)  # round 2: EpiLag-PH intel
    for t in range(2):
        page.click(f".prow[data-k='{t + 1}']"); page.wait_for_timeout(300)
        page.click("#deploy"); page.wait_for_timeout(500)
        if page.is_enabled("#deploy"):  # a second team, unless the area is at its coverage cap
            page.click("#deploy")
        page.wait_for_timeout(900)
        page.click("#end"); page.wait_for_timeout(1600)
    page.click(".prow[data-k='1']"); page.wait_for_timeout(1500)
    page.evaluate("scrollTo(0, 0)")
    save("drill_round2")
    for _ in range(6):
        page.click("#end"); page.wait_for_timeout(1300)
    page.wait_for_timeout(3000)
    save("drill_report")
    page.close()


def main(only: set) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Handler, directory=str(DOCS)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/epilag/"
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", args=["--enable-unsafe-swiftshader"])
        except Exception:  # noqa: BLE001 (no Chrome installed: use Playwright's own Chromium)
            browser = p.chromium.launch(args=["--enable-unsafe-swiftshader"])
        for name, path, width, full in SHOTS:
            if not only or name in only:
                shoot(browser, base, name, path, width, full)
        if not only or only & set(DRILL):
            drill(browser, base, only)
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    main(set(sys.argv[1:]))
