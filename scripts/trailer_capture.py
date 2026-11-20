"""Capture live clips of the built site for the trailer (docs/reel/trailer/index.html).

The same recorder as scripts/reel_capture.py (Chrome's screencast, resampled to 30 fps, a pixel cursor drawn in),
with the trailer's own shot list: the dashboard, the first-visit tour, the Filipino labels, the Research page and
the Dengue Drill's model choice, a round with forecasts and the debrief.

The clips are saved to docs/reel/trailer/clips/<name>/ and listed in docs/reel/trailer/clips.js.
TRAILER_SITE names the built site to film (a docs/ folder); the default is this checkout's docs/.

Usage: [TRAILER_SITE=~/other-checkout/docs] python scripts/trailer_capture.py [clip ...]
"""
import json
import os
import sys
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel_capture as rc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOCS = Path(os.environ.get("TRAILER_SITE", ROOT / "docs")).expanduser()
OUT = ROOT / "docs" / "reel" / "trailer" / "clips"
rc.OUT = OUT  # the shared Recorder writes here
QC = rc.QC
glide, hover_path, boxes = rc.glide, rc.hover_path, rc.boxes


def with_boxes(fn, rename=None):
    def run(ctx, base, rec_page):
        out = fn(ctx, base, rec_page)
        for a, b in (rename or {}).items():
            out["boxes"][b] = out["boxes"].pop(a)
        return out
    return run


def guide(ctx, base, rec_page):
    """A first visit: the tour opens by itself and walks through the dashboard."""
    page, rec = rec_page
    page.goto(base + "web/?page=home&panel=region_qc&mode=replay&h=4&lang=en&origin=2024-09-15&tour=1", wait_until="networkidle")
    page.evaluate("localStorage.removeItem('el-guide')")
    page.goto("about:blank")
    page.goto(base + "web/?page=home&panel=region_qc&mode=replay&h=4&lang=en&origin=2024-09-15&tour=1", wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.mouse.move(1100, 650)
    bx = boxes(page, {"card": ".guide__card"})
    rec.start()
    page.wait_for_timeout(1300)
    for k in range(4):
        glide(page, ".guide__card [data-act='next']", steps=22 if k == 0 else 10, pause=300)
        page.wait_for_timeout(1500)
    out = rec.stop("guide")
    out["boxes"] = bx
    return out


def lang(ctx, base, rec_page):
    """The same Overview, switched from English to Filipino."""
    page, rec = rec_page
    page.goto(base + "web/?page=home&panel=region_qc&mode=replay&h=4&lang=en&origin=2024-09-15", wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.mouse.move(700, 500)
    bx = boxes(page, {"strip": ".status-strip", "map": ".overview-map", "prio": ".overview-priority"})
    rec.start()
    page.wait_for_timeout(900)
    fil = page.get_by_text("FIL", exact=True).first
    b = fil.bounding_box()
    bx["switch"] = [round(b["x"]) - 40, round(b["y"]) - 30, 110, round(b["height"]) + 40]
    glide(page, (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2), steps=30)
    page.wait_for_timeout(1200)
    hover_path(page, [(500, 150), (900, 330), (1200, 330)], steps=26, pause=700)
    out = rec.stop("lang")
    out["boxes"] = bx
    return out


def research(ctx, base, rec_page):
    """The Research page: the headline numbers, the four-method test, and the losses with their causes."""
    page, rec = rec_page
    page.goto(base + "research.html", wait_until="networkidle")
    page.wait_for_timeout(2000)
    tops = page.evaluate("Object.fromEntries(['methods','losses'].map(id => [id, Math.round(document.getElementById(id).getBoundingClientRect().top + scrollY)]))")
    for y in range(0, page.evaluate("document.documentElement.scrollHeight"), 500):  # let every scroll reveal run once
        page.evaluate(f"scrollTo(0, {y})")
        page.wait_for_timeout(120)
    page.evaluate("scrollTo(0, 0)")
    page.wait_for_timeout(800)
    page.mouse.move(1150, 300)
    clips = {}
    rec.start()
    page.wait_for_timeout(600)
    hover_path(page, [(250, 780), (480, 780), (720, 780), (960, 780)], steps=22, pause=650)
    clips["research_top"] = rec.stop("research_top")
    page.evaluate(f"scrollTo(0, {tops['methods'] - 20})")
    page.wait_for_timeout(700)
    rec.start()
    page.wait_for_timeout(500)
    rc.smooth_scroll(page, tops["methods"] + 430, 2600)
    hover_path(page, [(520, 420), (760, 520)], steps=24, pause=700)
    clips["research_methods"] = rec.stop("research_methods")
    page.evaluate(f"scrollTo(0, {tops['losses'] - 20})")
    page.wait_for_timeout(700)
    rec.start()
    page.wait_for_timeout(500)
    rc.smooth_scroll(page, tops["losses"] + 330, 2400)
    hover_path(page, [(360, 520), (720, 520), (1080, 520)], steps=24, pause=650)
    clips["research_losses"] = rec.stop("research_losses")
    return clips


def play_out(page):
    """End turns until the round's report is up."""
    for _ in range(40):
        if page.locator("#s-report.on").count():
            return
        if page.locator("#s-game.on").count() and not page.locator("#warp.on").count() and page.is_enabled("#end"):
            try:
                page.click("#end", timeout=1500)
            except Exception:  # the season-over card came up first
                pass
        page.wait_for_timeout(900)
    raise SystemExit("the round did not finish")


def drill(ctx, base, rec_page):
    """Dengue Drill, Quezon City: the title and briefing, the choice of forecaster, a round 2 turn, the debrief."""
    page, rec = rec_page
    page.goto(base + "drill/", wait_until="networkidle")
    page.evaluate("localStorage.setItem('drill-tour', '1'); localStorage.setItem('drill-tip2', '1'); localStorage.removeItem('drill-model')")
    page.goto(base + "drill/", wait_until="networkidle")
    page.wait_for_timeout(3500)
    page.mouse.move(1100, 500)
    clips = {}
    rec.start()
    page.wait_for_timeout(1500)
    for _ in range(2):
        glide(page, "#m-next", steps=20, pause=200)
        page.wait_for_timeout(900)
    for _ in range(2):
        glide(page, "#m-prev", steps=6, pause=150)
        page.wait_for_timeout(600)
    glide(page, "#start", steps=28)
    page.wait_for_timeout(3200)
    clips["drill_intro"] = rec.stop("drill_intro")

    page.click("#go-r1")
    page.wait_for_timeout(900)
    cards = page.locator("#models > *")
    n = cards.count()
    bx = boxes(page, {"models": "#models", "title": "#mo-title"})
    rec.start()
    page.wait_for_timeout(900)
    for k in list(range(1, n)) + [0]:
        b = cards.nth(k).bounding_box()
        glide(page, (b["x"] + b["width"] / 2, b["y"] + b["height"] * .45), steps=16, pause=250)
        page.wait_for_timeout(650)
    glide(page, "#cmp-open", steps=22)
    page.wait_for_timeout(2600)
    clips["drill_models"] = rec.stop("drill_models")
    clips["drill_models"]["boxes"] = bx
    page.click("#cmp-ok")
    page.wait_for_timeout(500)
    page.click("#go-r2")
    page.wait_for_timeout(4500)

    play_out(page)  # round 1, off camera
    page.wait_for_timeout(2500)
    page.click("#next-r")
    page.wait_for_timeout(600)
    if page.locator("#s-models.on").count():  # the model can be changed before round 2
        page.click("#go-r2")
    page.wait_for_timeout(1200)
    rec.start()  # the warp into round 2, then two turns with forecasts
    page.wait_for_timeout(3600)
    page.mouse.move(900, 450)
    for turn in range(2):
        for k in (0, 1, 2):
            add = page.locator(f"#plist .prow[data-k='{k}'] .prow__add")
            if add.count() and add.is_enabled():
                b = add.bounding_box()
                glide(page, (b["x"] + b["width"] / 2, b["y"] + b["height"] / 2), steps=16, pause=200)
                page.wait_for_timeout(450)
        glide(page, "#end", steps=22)
        page.wait_for_timeout(2400)
    clips["drill_play"] = rec.stop("drill_play")

    play_out(page)
    page.wait_for_timeout(1500)
    rec.start()
    page.wait_for_timeout(3600)
    clips["drill_report"] = rec.stop("drill_report")
    page.click("#next-r")
    page.wait_for_timeout(400)
    rec.start()
    page.wait_for_timeout(5200)
    clips["drill_vs"] = rec.stop("drill_vs")
    return clips


CLIPS = {
    "overview": rc.overview, "map": rc.forecast_map, "area": rc.area, "why": rc.why, "budget": rc.budget, "barangays": rc.barangays,
    "guide": guide, "lang": lang, "research": research, "drill": drill,
}


def main(only: set) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    listing = OUT.parent / "clips.js"
    known = json.loads(listing.read_text(encoding="utf-8").removeprefix("window.CLIPS = ").rstrip(";\n")) if listing.exists() else {}
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(rc._Handler, directory=str(DOCS)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/epilag/"
    print("filming", DOCS)
    with sync_playwright() as p:
        headed = os.environ.get("HEADED") == "1"  # a visible window renders WebGL on the GPU, so the 3D clips capture at full rate
        gpu = ["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"] if sys.platform == "darwin" else ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"]
        try:  # installed Chrome in new headless mode draws WebGL on the GPU, without opening a window
            browser = p.chromium.launch(channel="chrome", headless=not headed, args=[] if headed else gpu)
        except Exception:
            browser = p.chromium.launch(headless=not headed, args=[] if headed else ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"])
        for name, fn in CLIPS.items():
            if only and name not in only:
                continue
            ctx = browser.new_context(viewport={"width": rc.W, "height": rc.H}, device_scale_factor=rc.SCALE)
            ctx.add_init_script(rc.CURSOR)
            ctx.add_init_script("try { sessionStorage.setItem('el-intro', '1'); if (!location.search.includes('tour')) localStorage.setItem('el-guide', 'done') } catch (e) {}")
            page = ctx.new_page()
            got = fn(ctx, base, (page, rc.Recorder(page)))
            known.update(got if "n" not in got else {name: got})
            listing.write_text("window.CLIPS = " + json.dumps(known) + ";\n", encoding="utf-8")
            ctx.close()
        browser.close()
    server.shutdown()
    listing.write_text("window.CLIPS = " + json.dumps(known) + ";\n", encoding="utf-8")
    print("saved", listing.relative_to(ROOT))


if __name__ == "__main__":
    main(set(sys.argv[1:]))
