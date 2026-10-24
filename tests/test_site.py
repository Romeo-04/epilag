"""Site checks for the built pages in docs/, through Playwright.

For the landing page, every app view (both data panels, latest and replay, EN and FIL), the Dengue Drill and the
methodology and open-data pages:
  - loads with no console errors and no failed requests
  - no horizontal scroll at 390 px and 1440 px
  - with reduced motion, nothing is left hidden by an entrance animation
  - keyboard: Tab reaches the main controls and the focus is visible
  - axe-core: no serious or critical issues (skipped when the CDN cannot be reached)
  - without WebGL the maps fall back to 2D
Build first: `cd site && npm run build`. Skipped when Playwright or the build is missing.
"""
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
playwright = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not (DOCS / "web" / "index.html").exists(), reason="build the site first (cd site && npm run build)")

AXE = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
VIEWS = ["home", "map", "unit", "budget", "public", "qc", "proof", "about"]
APP = [f"web/?page={v}&panel={p}&mode={m}&lang={l}" for v in VIEWS for p in ("region_qc", "province")
       for m in ("latest", "replay") for l in ("en", "fil")]
PAGES = ["", "drill/", "methodology.html", "data/"]


class _Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):  # the site is published under /epilag/
        return super().translate_path(path.removeprefix("/epilag"))

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def base():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Handler, directory=str(DOCS)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/epilag/"
    server.shutdown()


@pytest.fixture(scope="module")
def pw():
    with playwright.sync_playwright() as p:
        yield p


def launch(pw, *args):
    try:
        return pw.chromium.launch(channel="chrome", args=list(args))
    except Exception:  # noqa: BLE001 (no Chrome installed: use Playwright's own Chromium)
        return pw.chromium.launch(args=list(args))


@pytest.fixture(scope="module")
def browser(pw):
    b = launch(pw, "--enable-unsafe-swiftshader")
    yield b
    b.close()


def open_page(browser, url, width=1440, **ctx):
    c = browser.new_context(viewport={"width": width, "height": 900 if width > 500 else 844}, is_mobile=width < 500,
                            has_touch=width < 500, **ctx)
    c.add_init_script("try { sessionStorage.setItem('el-intro', '1') } catch (e) {}")  # skip the landing intro
    pg = c.new_page()
    errors = []
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(f"page error: {e}"))
    pg.on("requestfailed", lambda r: errors.append(f"failed: {r.url}") if "fonts.g" not in r.url else None)
    pg.on("response", lambda r: errors.append(f"{r.status}: {r.url}") if r.status >= 400 else None)
    pg.goto(url, wait_until="networkidle")
    pg.wait_for_timeout(600)
    return c, pg, errors


@pytest.mark.parametrize("path", PAGES + APP)
def test_loads_clean_on_desktop(base, browser, path):
    c, pg, errors = open_page(browser, base + path)
    try:
        assert errors == []
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        c.close()


@pytest.mark.parametrize("path", PAGES + [f"web/?page={v}" for v in VIEWS] + ["web/?page=map&panel=province&mode=replay"])
def test_phone_has_no_horizontal_scroll(base, browser, path):
    c, pg, errors = open_page(browser, base + path, width=390)
    try:
        assert errors == []
        wide = pg.evaluate("""() => [...document.querySelectorAll('body *')].filter(e => {
            const r = e.getBoundingClientRect(), s = getComputedStyle(e);
            return r.width && r.right > innerWidth + 1 && s.position !== 'fixed' && !e.closest('[style*=overflow], .app-tabs, .missions, .tbl-wrap, .plist');
          }).length""")
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"{wide} elements stick out"
    finally:
        c.close()


@pytest.mark.parametrize("path", PAGES + ["web/?page=home", "web/?page=map"])
def test_reduced_motion_shows_everything(base, browser, path):
    c, pg, errors = open_page(browser, base + path, reduced_motion="reduce")
    try:
        assert errors == []
        hidden = pg.evaluate("""() => [...document.querySelectorAll('main h1, main h2, main p, main .card, main .btn')].filter(e => {
            const s = getComputedStyle(e); return e.offsetWidth && (s.visibility === 'hidden' || +s.opacity === 0);
          }).map(e => e.textContent.trim().slice(0, 40))""")
        assert hidden == []
    finally:
        c.close()


@pytest.mark.parametrize("path", ["", "web/?page=home", "web/?page=map", "web/?page=budget", "drill/"])
def test_keyboard_reaches_controls(base, browser, path):
    c, pg, _ = open_page(browser, base + path)
    try:
        seen, outlined = set(), 0
        for _ in range(40):
            pg.keyboard.press("Tab")
            info = pg.evaluate("""() => { const e = document.activeElement, s = getComputedStyle(e);
                return [e.tagName, e.id || e.textContent.trim().slice(0, 30), s.outlineStyle !== 'none' || s.boxShadow !== 'none'] }""")
            seen.add(info[0])
            outlined += info[2]
        assert {"A", "BUTTON"} & seen, "Tab reached no links or buttons"
        assert outlined > 0, "no visible focus indicator"
    finally:
        c.close()


@pytest.mark.parametrize("path", ["", "web/?page=home", "web/?page=map", "web/?page=unit", "drill/", "methodology.html", "data/"])
def test_axe_no_serious_issues(base, browser, path):
    c, pg, _ = open_page(browser, base + path)
    try:
        try:
            pg.add_script_tag(url=AXE)
        except Exception:  # noqa: BLE001
            pytest.skip("axe-core CDN not reachable")
        res = pg.evaluate("async () => (await axe.run(document, { resultTypes: ['violations'] })).violations"
                          ".filter(v => ['serious', 'critical'].includes(v.impact)).map(v => v.id + ': ' + v.nodes.length)")
        assert res == []
    finally:
        c.close()


def test_maps_fall_back_to_2d_without_webgl(base, pw):
    b = launch(pw, "--disable-webgl", "--disable-webgl2", "--disable-3d-apis")
    try:
        pg = b.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(base + "web/?page=map", wait_until="networkidle")
        pg.wait_for_timeout(800)
        assert errors == []
        assert pg.evaluate("!!document.querySelector('canvas')"), "no 2D map drawn"
    finally:
        b.close()
