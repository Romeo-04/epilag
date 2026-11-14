"""Site checks for the built pages in docs/, through Playwright.

For the landing page, every app view (both data panels, latest and replay, EN and FIL), the Dengue Drill and the
methodology and open-data pages:
  - loads with no console errors and no failed requests
  - no horizontal scroll at 390 px and 1440 px
  - with reduced motion, nothing is left hidden by an entrance animation
  - keyboard: Tab reaches the main controls and the focus is visible
  - axe-core: no serious or critical issues (skipped when the CDN cannot be reached)
  - without WebGL the maps fall back to 2D
  - the onboarding guide opens once per device, steps through the Overview on desktop and phone, and can be replayed
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


def open_page(browser, url, width=1440, guide=False, **ctx):
    c = browser.new_context(viewport={"width": width, "height": 900 if width > 500 else 844}, is_mobile=width < 500,
                            has_touch=width < 500, **ctx)
    c.add_init_script("try { sessionStorage.setItem('el-intro', '1') } catch (e) {}")  # skip the landing intro
    if not guide:  # a returning visitor: the onboarding guide stays closed
        c.add_init_script("try { localStorage.setItem('el-guide', 'done') } catch (e) {}")
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


# ------------------------------------------------------------------ onboarding guide
GUIDE_TARGETS = ["#ctx", "[data-guide=status]", "[data-guide=trend]", "[data-guide=rising]", "[data-guide=do]",
                 "[data-guide=map]", "[data-guide=priority]"]
GUIDE_FITS = """([sel, phone]) => {
  const c = document.querySelector('.guide__card').getBoundingClientRect();
  const onScreen = c.left >= 0 && c.top >= 0 && c.right <= innerWidth + 0.5 && c.bottom <= innerHeight + 0.5;
  if (!sel) return onScreen;
  const t = document.querySelector(sel).getBoundingClientRect(), s = document.querySelector('.guide__spot').getBoundingClientRect();
  const ringed = s.left <= t.left + 1 && s.top <= t.top + 1 && s.right >= t.right - 1 && s.bottom >= t.bottom - 1;
  const shown = t.top >= -1 && t.top < (phone ? c.top : innerHeight);
  const apart = phone || c.bottom <= t.top || c.top >= t.bottom || c.right <= t.left || c.left >= t.right;
  return onScreen && ringed && shown && apart;
}"""


def guide_step(pg, i, n):
    pg.wait_for_function("([i, n]) => document.querySelector('.guide__step')?.textContent === `Step ${i} of ${n}`", arg=[i, n])


def walk_guide(pg, phone):
    """Start the tour and step to the end, checking each card fits and rings its part of the page."""
    pg.click(".guide [data-act=next]")
    targets = GUIDE_TARGETS + ["#mobile-menu" if phone else "#tabs", "#guide-top", None]
    n = len(targets)
    for i, sel in enumerate(targets, 1):
        guide_step(pg, i, n)
        pg.wait_for_function(GUIDE_FITS, arg=[sel, phone], timeout=6000)
        assert pg.evaluate("!!document.activeElement.closest('.guide')"), f"focus left the guide at step {i}"
        if i < n:
            pg.click(".guide [data-act=next]")


@pytest.mark.parametrize("width", [1440, 390])
def test_guide_walks_through_the_overview(base, browser, width):
    c, pg, errors = open_page(browser, base + "web/?page=home", width=width, guide=True)
    try:
        pg.wait_for_selector(".guide #guide-title")
        assert pg.text_content("#guide-title") == "Welcome to EpiLag-PH"
        assert pg.evaluate("document.querySelector('.app-shell').inert"), "the page behind the guide is still usable"
        walk_guide(pg, phone=width < 500)
        assert pg.text_content("#guide-title") == "How to read a forecast"
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
        pg.click(".guide [data-act=close]")
        assert pg.evaluate("!document.querySelector('.guide') && !document.querySelector('.app-shell').inert")
        assert pg.evaluate("localStorage.getItem('el-guide')") == "done"
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(600)
        assert pg.query_selector(".guide") is None, "the guide opened again for a returning visitor"
        pg.click("#guide-top")  # but it can be replayed, on a phone too
        pg.wait_for_selector(".guide #guide-title")
        assert errors == []
    finally:
        c.close()


def test_guide_opens_only_once_per_device(base, browser):
    c, pg, errors = open_page(browser, base + "web/?page=home", guide=True)
    try:
        pg.wait_for_selector(".guide #guide-title")
        pg.reload(wait_until="networkidle")  # left half-way through: it still counts as seen
        pg.wait_for_timeout(600)
        assert pg.query_selector(".guide") is None
        pg.goto(base + "web/?page=home&lang=fil", wait_until="networkidle")
        pg.wait_for_timeout(600)
        assert pg.query_selector(".guide") is None
        assert errors == []
    finally:
        c.close()


def test_guide_keyboard_and_reopen(base, browser):
    c, pg, errors = open_page(browser, base + "web/?page=home&guide=0", guide=True)
    try:
        assert pg.query_selector(".guide") is None, "?guide=0 should keep the guide closed"
        pg.click("[data-page=map]")
        pg.wait_for_selector("#view:not([aria-busy])")
        pg.click("#guide-top")  # from another page: back to the Overview, then the tour
        pg.wait_for_selector(".guide #guide-title")
        assert "page=home" in pg.url
        pg.keyboard.press("ArrowRight")
        guide_step(pg, 1, 10)
        pg.keyboard.press("ArrowLeft")
        pg.wait_for_function("document.querySelector('#guide-title')?.textContent === 'Welcome to EpiLag-PH'")
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".guide", state="detached")
        assert pg.evaluate("document.activeElement.id") == "guide-top", "focus did not return to the button"
        assert pg.evaluate("localStorage.getItem('el-guide')") == "done"
        assert errors == []
    finally:
        c.close()


def test_guide_in_filipino(base, browser):
    c, pg, errors = open_page(browser, base + "web/?page=home&lang=fil", guide=True)
    try:
        pg.wait_for_selector(".guide #guide-title")
        assert pg.text_content("#guide-title") == "Maligayang pagdating sa EpiLag-PH"
        assert pg.text_content(".guide [data-act=next]") == "Simulan ang tour"
        assert pg.text_content("#guide-top").strip() == "Paano gamitin"
        assert errors == []
    finally:
        c.close()


def test_guide_axe_no_serious_issues(base, browser):
    c, pg, _ = open_page(browser, base + "web/?page=home&guide=1")
    try:
        pg.wait_for_selector(".guide #guide-title")
        try:
            pg.add_script_tag(url=AXE)
        except Exception:  # noqa: BLE001
            pytest.skip("axe-core CDN not reachable")
        found = []
        for i in [0, 2, 10]:  # welcome, the alert levels, how to read a forecast
            while i and pg.text_content(".guide__step") != f"Step {i} of 10":
                pg.click(".guide [data-act=next]")
                pg.wait_for_timeout(150)
            pg.wait_for_timeout(400)
            found += pg.evaluate("async () => (await axe.run('.guide', { resultTypes: ['violations'] })).violations"
                                 ".filter(v => ['serious', 'critical'].includes(v.impact)).map(v => v.id + ': ' + v.nodes.length)")
        assert found == []
    finally:
        c.close()
