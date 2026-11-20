"""Capture live clips of the built site for the showreel (docs/reel/index.html).

Serves docs/ the way GitHub Pages does (under /epilag/), drives Chrome with Playwright and records Chrome's
screencast while a scripted visitor uses the real interfaces: the landing intro, the dashboard replaying
Quezon City's 2024-25 season, the QC barangay shortlist and a Dengue Drill round. Each clip is resampled to a
constant 30 fps and saved as a JPEG sequence in docs/reel/clips/<name>/, listed in docs/reel/clips.js.
A pixel cursor is drawn into the pages, so the clicks read on screen.

Build the site first (cd site && npm run build). Usage: python scripts/reel_capture.py [clip ...]
"""
import base64
import json
import shutil
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "reel" / "clips"
FPS = 30
W, H, SCALE = 1440, 900, 2  # frames come out at 2880 x 1800, sharp enough for the camera to push in 2x
QC = "&panel=region_qc&mode=replay&region=R_NCR&area=QC&h=4&lang=en"

# A pixel arrow that follows the mouse, with a ring on every click.
CURSOR = r"""
addEventListener("DOMContentLoaded", () => {
  const c = document.createElement("div");
  c.id = "reel-cursor";
  c.innerHTML = '<svg width="30" height="42" viewBox="0 0 10 14" shape-rendering="crispEdges"><path fill="#071711" d="M0 0h1v1h1v1h1v1h1v1h1v1h1v1h1v1h1v1h1v1h-4v1h1v2h1v2h-2v-2h-1v-2h-1v1h-1v1h-1z"/><path fill="#FBFAF4" d="M1 2h1v1h1v1h1v1h1v1h1v1h1v1h-3v1h1v2h1v1h-1v-2h-1v-2h-2v1h-1z"/></svg>';
  Object.assign(c.style, { position: "fixed", left: "-60px", top: "-60px", zIndex: 2147483647, pointerEvents: "none", filter: "drop-shadow(3px 3px 0 rgba(7,23,17,.25))" });
  document.documentElement.append(c);
  addEventListener("mousemove", (e) => { c.style.left = e.clientX + "px"; c.style.top = e.clientY + "px"; }, true);
  addEventListener("mousedown", (e) => {
    const r = document.createElement("div");
    Object.assign(r.style, { position: "fixed", left: e.clientX - 22 + "px", top: e.clientY - 22 + "px", width: "44px", height: "44px", zIndex: 2147483646,
      pointerEvents: "none", border: "4px solid #F5A51C", boxSizing: "border-box" });
    document.documentElement.append(r);
    r.animate([{ transform: "scale(.3)", opacity: 1 }, { transform: "scale(1.4)", opacity: 0 }], { duration: 520, easing: "steps(6)" }).onfinish = () => r.remove();
  }, true);
});
"""


class _Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):  # the site is published under /epilag/
        return super().translate_path(path.removeprefix("/epilag"))

    def log_message(self, *args):
        pass


class Recorder:
    """Chrome's screencast for one page: start(), act, stop(name) writes the constant-rate JPEG sequence."""

    def __init__(self, page):
        self.page, self.cdp, self.frames = page, page.context.new_cdp_session(page), []
        self.cdp.on("Page.screencastFrame", self._frame)
        self.t0 = None

    def _frame(self, ev):
        if self.t0 is not None:
            self.frames.append((ev["metadata"]["timestamp"], base64.b64decode(ev["data"])))
        try:
            self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:  # the page navigated while a frame was in flight
            pass

    def start(self):
        self.frames = []
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "maxWidth": round(W * SCALE), "maxHeight": round(H * SCALE)})
        self.page.wait_for_timeout(300)
        self.t0 = time.time()

    def stop(self, name):
        t1 = time.time()
        self.cdp.send("Page.stopScreencast")
        frames, self.t0 = self.frames, None
        ts = np.array([t for t, _ in frames])
        ticks = (t1 - 0.05) - np.arange(int((t1 - 0.05 - (ts[0])) * FPS))[::-1] / FPS
        idx = np.clip(np.searchsorted(ts, ticks, side="right") - 1, 0, len(frames) - 1)
        out = OUT / name
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True)
        for k, i in enumerate(idx):
            (out / f"{k:04d}.jpg").write_bytes(frames[i][1])
        print(f"{name}: {len(idx)} frames ({len(idx) / FPS:.1f} s, {len(frames) / max(ts[-1] - ts[0], 1e-3):.0f} fps captured)")
        return {"n": len(idx), "w": round(W * SCALE), "h": round(H * SCALE)}


def glide(page, target, steps=28, click=True, pause=250):
    """Move the mouse to a selector (or an (x, y) point) like a hand would, then click."""
    if isinstance(target, str):
        box = page.locator(target).first.bounding_box()
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    else:
        x, y = target
    page.mouse.move(x, y, steps=steps)
    page.wait_for_timeout(pause)
    if click:
        page.mouse.click(x, y)


def smooth_scroll(page, to, ms):
    page.evaluate("""([to, ms]) => new Promise(done => {
      const from = scrollY, t0 = performance.now();
      const step = (now) => { const k = Math.min(1, (now - t0) / ms), e = k < .5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2;
        scrollTo(0, from + (to - from) * e); k < 1 ? requestAnimationFrame(step) : done(); };
      requestAnimationFrame(step); })""", [to, ms])


# ------------------------------------------------------------------ the clips

def landing(ctx, base, rec_page):
    page, rec = rec_page
    page.goto("about:blank")
    rec.start()
    page.goto(base + "?intro", wait_until="domcontentloaded")
    page.wait_for_timeout(5200)
    page.mouse.move(700, 500)
    glide(page, (330, 690), steps=40, click=False)
    page.wait_for_timeout(900)
    return rec.stop("landing")


BOXES_JS = """(sels) => Object.fromEntries(Object.entries(sels).map(([k, s]) => {
  const all = [...document.querySelectorAll(s)].map((e) => { const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); });
  return [k, all.length === 1 ? all[0] : all.length ? all : null];
}))"""


def boxes(page, sels):
    """Where the key elements sit, in page pixels (1440 x 900), so the film's camera can fly to them."""
    return page.evaluate(BOXES_JS, sels)


def hover_path(page, pts, steps=24, pause=500):
    for x, y in pts:
        page.mouse.move(x, y, steps=steps)
        page.wait_for_timeout(pause)


def center(box):
    return box[0] + box[2] / 2, box[1] + box[3] / 2


def overview(ctx, base, rec_page):
    """Overview, replaying 2024: drag the forecast week from August to 15 Sep 2024, then read the strip and the map."""
    page, rec = rec_page
    page.goto(base + "web/?page=home&panel=region_qc&mode=replay&h=4&lang=en&origin=2024-08-04", wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.mouse.move(1200, 600)
    bx = boxes(page, {"strip": ".status-strip", "map": ".overview-map", "prio": ".overview-priority", "slider": "#c-origin", "trend": "#home-trend"})
    rec.start()
    page.wait_for_timeout(500)
    glide(page, "#c-origin", steps=30, click=False)
    slider = page.locator("#c-origin")
    box = slider.bounding_box()
    lo, hi = int(slider.get_attribute("min")), int(slider.get_attribute("max"))
    v = int(slider.input_value())
    knob = lambda v: (box["x"] + 8 + (box["width"] - 16) * (v - lo) / max(1, hi - lo), box["y"] + box["height"] / 2)
    page.mouse.move(*knob(v), steps=10)
    page.mouse.down()
    for _ in range(6):  # one week per step, released each time so the page redraws
        v += 1
        page.mouse.move(*knob(v), steps=6)
        page.mouse.up()
        page.wait_for_timeout(480)
        page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(500)
    hover_path(page, [(420, 225), (640, 225), (900, 225)], steps=26, pause=450)
    hover_path(page, [(560, 760), (640, 820)], steps=26, pause=600)
    out = rec.stop("overview")
    out["boxes"] = bx
    return out


def forecast_map(ctx, base, rec_page):
    """The 3D forecast map on 15 Sep 2024: hover the columns, then Quezon City in the priority list."""
    page, rec = rec_page
    page.goto(base + f"web/?page=map{QC}&origin=2024-09-15", wait_until="networkidle")
    page.wait_for_timeout(3000)
    bx = boxes(page, {"map": "#vmap", "rank": "#rank", "banner": ".replay-banner"})
    qc = page.locator("#rank >> text=Quezon City").first.bounding_box()
    bx["qc"] = [round(qc["x"]) - 40, round(qc["y"]) - 8, 420, round(qc["height"]) + 16] if qc else None
    page.mouse.move(1100, 300)
    rec.start()
    page.wait_for_timeout(500)
    hover_path(page, [(470, 600), (520, 690), (600, 760), (690, 820), (760, 760), (560, 640)], steps=22, pause=700)
    if qc:
        page.mouse.move(qc["x"] + 60, qc["y"] + qc["height"] / 2, steps=30)
    page.wait_for_timeout(1600)
    out = rec.stop("map")
    out["boxes"] = bx
    return out


def area(ctx, base, rec_page):
    """Area detail for Quezon City, as it read on 15 Sep 2024: the Watch call, the forecast, then each checklist row."""
    page, rec = rec_page
    page.goto(base + f"web/?page=unit{QC}&origin=2024-09-15", wait_until="networkidle")
    page.wait_for_timeout(2500)
    bx = boxes(page, {"hero": ".status-hero", "kpi": ".kpi", "playbook": ".playbook", "rows": ".todo__row"})
    page.mouse.move(1100, 300)
    rec.start()
    page.wait_for_timeout(500)
    hover_path(page, [(480, 320), (560, 340)], steps=26, pause=700)
    hover_path(page, [(860, 320), (900, 330)], steps=22, pause=600)
    for r in bx["rows"]:
        hover_path(page, [(r[0] + 160, r[1] + r[3] / 2), (r[0] + 520, r[1] + r[3] / 2)], steps=26, pause=650)
    page.wait_for_timeout(800)
    out = rec.stop("area")
    out["boxes"] = bx
    return out


def why(ctx, base, rec_page):
    """Why Quezon City is flagged: the forecast's drivers (SHAP), shown for the latest forecast."""
    page, rec = rec_page
    page.goto(base + "web/?page=unit&panel=region_qc&mode=latest&region=R_NCR&area=QC&h=4&lang=en", wait_until="networkidle")
    page.wait_for_timeout(2000)
    y = page.evaluate("document.getElementById('why').getBoundingClientRect().top + scrollY - 60")
    page.evaluate(f"scrollTo(0, {y})")
    page.wait_for_timeout(1200)
    bx = boxes(page, {"why": "#why", "chart": "#why-chart"})
    c = bx["chart"]
    page.mouse.move(1200, 200)
    rec.start()
    page.wait_for_timeout(400)
    hover_path(page, [(c[0] + c[2] * .55, c[1] + c[3] * .2), (c[0] + c[2] * .5, c[1] + c[3] * .55), (c[0] + c[2] * .35, c[1] + c[3] * .9), (c[0] + c[2] * .75, c[1] + c[3] * .8)], steps=26, pause=700)
    page.wait_for_timeout(500)
    out = rec.stop("why")
    out["boxes"] = bx
    return out


def budget(ctx, base, rec_page):
    """The action plan: type a budget and watch the plan re-rank."""
    page, rec = rec_page
    page.goto(base + "web/?page=budget&panel=region_qc&mode=replay&h=4&lang=en&origin=2024-09-15", wait_until="networkidle")
    page.wait_for_timeout(2500)
    bx = boxes(page, {"input": "#budget", "out": "#out", "spend": "#spend"})
    page.mouse.move(1000, 600)
    rec.start()
    page.wait_for_timeout(400)
    glide(page, "#budget", steps=26)
    page.keyboard.press("Meta+A")
    page.wait_for_timeout(150)
    for ch in "20000000":
        page.keyboard.type(ch)
        page.wait_for_timeout(90)
    page.keyboard.press("Tab")
    page.wait_for_timeout(1200)
    hover_path(page, [(900, 270), (1100, 280)], steps=24, pause=500)
    hover_path(page, [(900, 470), (1300, 500)], steps=26, pause=700)
    out = rec.stop("budget")
    out["boxes"] = bx
    return out


def barangays(ctx, base, rec_page):
    """The QC barangay shortlist, read top to bottom."""
    page, rec = rec_page
    page.goto(base + f"web/?page=qc{QC}&origin=2024-09-15", wait_until="networkidle")
    page.wait_for_timeout(2500)
    bx = boxes(page, {"hero": ".hero-card", "chart": "#bchart"})
    c = bx["chart"]
    page.mouse.move(600, 600)
    rec.start()
    page.wait_for_timeout(300)
    hover_path(page, [(c[0] + c[2] * .5, c[1] + c[3] * .12), (c[0] + c[2] * .45, c[1] + c[3] * .2), (c[0] + c[2] * .35, c[1] + c[3] * .28), (c[0] + c[2] * .3, c[1] + c[3] * .5)], steps=24, pause=600)
    out = rec.stop("barangays")
    out["boxes"] = bx
    return out


def drill(ctx, base, rec_page):
    """The Dengue Drill, Quezon City mission: the title, the briefing, then a round 2 turn with EpiLag-PH intel."""
    page, rec = rec_page
    page.goto(base + "drill/", wait_until="networkidle")
    page.wait_for_timeout(3500)
    page.mouse.move(1100, 400)
    rec.start()
    page.wait_for_timeout(1800)
    glide(page, "#start", steps=34)
    page.wait_for_timeout(2600)
    glide(page, "#go-r1", steps=26)
    page.wait_for_timeout(2600)
    clips = {"drill_intro": rec.stop("drill_intro")}

    for _ in range(8):  # round 1, off camera
        page.click("#end"); page.wait_for_timeout(1100)
    page.wait_for_timeout(2500)
    page.click("#next-r"); page.wait_for_timeout(3200)
    page.mouse.move(900, 450)
    rec.start()
    page.wait_for_timeout(700)
    for k in (1, 2):
        glide(page, f".prow[data-k='{k}']", steps=24)
        page.wait_for_timeout(700)
        glide(page, "#deploy", steps=22)
        page.wait_for_timeout(500)
        if page.is_enabled("#deploy"):
            glide(page, "#deploy", steps=4)
        page.wait_for_timeout(700)
    glide(page, "#end", steps=26)
    page.wait_for_timeout(2600)
    clips["drill_play"] = rec.stop("drill_play")

    for _ in range(7):
        page.click("#end"); page.wait_for_timeout(1100)
    page.wait_for_timeout(1200)
    rec.start()
    page.wait_for_timeout(4200)
    clips["drill_report"] = rec.stop("drill_report")
    return clips


CLIPS = {"landing": landing, "overview": overview, "map": forecast_map, "area": area, "why": why, "budget": budget, "barangays": barangays, "drill": drill}


def main(only: set) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    listing = OUT.parent / "clips.js"
    known = {}
    if listing.exists():
        known = json.loads(listing.read_text(encoding="utf-8").removeprefix("window.CLIPS = ").rstrip(";\n"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_Handler, directory=str(DOCS)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/epilag/"
    with sync_playwright() as p:
        import os
        headed = os.environ.get("HEADED") == "1"  # a visible window renders WebGL on the GPU, so the 3D clips capture at full rate
        browser = p.chromium.launch(headless=not headed, args=[] if headed else ["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"])
        for name, fn in CLIPS.items():
            if only and name not in only:
                continue
            ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=SCALE)
            ctx.add_init_script(CURSOR)
            if name != "landing":
                ctx.add_init_script("try { sessionStorage.setItem('el-intro', '1') } catch (e) {}")
            page = ctx.new_page()
            got = fn(ctx, base, (page, Recorder(page)))
            known.update(got if "n" not in got else {name: got})
            ctx.close()
        browser.close()
    server.shutdown()
    listing.write_text("window.CLIPS = " + json.dumps(known) + ";\n", encoding="utf-8")
    print("saved", listing.relative_to(ROOT))


if __name__ == "__main__":
    main(set(sys.argv[1:]))
