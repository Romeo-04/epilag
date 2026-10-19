"""Parity: the Dengue Drill's rules (site/src/drill/rules.js) score like scripts/drill_data.py, on the same data.

Serves the built docs/ (`cd site && npm run build`), opens the drill in Playwright and compares, for every region,
the two computer players (follow EpiLag alerts; react to reported outbreaks) with drill_data.play(), and the
"11 better, 1 about the same, 5 worse" summary the game shows. Skipped when Playwright or the build is missing.
"""
import importlib.util
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = DOCS / "drill" / "data.json"
playwright = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not (DOCS / "drill" / "index.html").exists() or not DATA.exists(),
                                reason="build the site first (cd site && npm run build)")

spec = importlib.util.spec_from_file_location("drill_data", ROOT / "scripts" / "drill_data.py")
drill_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drill_data)


class _Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):  # the site is published under /epilag/
        return super().translate_path(path.removeprefix("/epilag"))

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def page():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Handler, directory=str(DOCS)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:  # noqa: BLE001 (no Chrome installed: use Playwright's own Chromium)
            browser = p.chromium.launch()
        pg = browser.new_page()
        pg.goto(f"http://127.0.0.1:{server.server_address[1]}/epilag/drill/")
        pg.wait_for_function("window.drill && window.drill.R")
        yield pg
        browser.close()
    server.shutdown()


@pytest.fixture(scope="module")
def data():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    drill_data.WEEKS = d["weeks"]
    return d


def test_bots_match_python(page, data):
    js = page.evaluate("""() => { const { D, R } = window.drill;
        return D.regions.map(r => [R.autopilot("epilag", r).mid, R.autopilot("react", r).mid]); }""")
    for (epilag, react), region in zip(js, data["regions"]):
        assert epilag == pytest.approx(drill_data.play(region, data["weeks"], data["turns"], drill_data.epilag), rel=1e-12)
        assert react == pytest.approx(drill_data.play(region, data["weeks"], data["turns"], drill_data.reactive), rel=1e-12)


def test_honest_summary(page, data):
    """The note on the debrief and the landing page: EpiLag's bot did better in 11 regions, the same in 1, worse in 5."""
    assert page.evaluate("window.drill.R.honest()") == {"better": 11, "tie": 1, "worse": 5}


def test_one_team_scores_like_python(page, data):
    """A single team in each province on each turn: the game's score equals drill_data.averted()."""
    region = data["regions"][5]
    for k, prov in enumerate(region["provinces"]):
        for t, turn in enumerate(data["turns"]):
            js = page.evaluate("([r, k, t]) => { const { D, R } = window.drill; return R.score({ [k]: { [t]: 1 } }, D.regions[r]).mid; }", [5, k, t])
            assert js == pytest.approx(drill_data.averted(prov, data["weeks"], turn, 1), rel=1e-12, abs=1e-12)
