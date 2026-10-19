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
W, H, SCALE = 1440, 900, 4 / 3  # frames come out at 1920 x 1200
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


def overview(ctx, base, rec_page):
    """Overview, replaying Quezon City: step the forecast week from August to late October 2024."""
    page, rec = rec_page
    page.goto(base + f"web/?page=home{QC}&origin=2024-08-04", wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.mouse.move(1200, 600)
    rec.start()
    page.wait_for_timeout(600)
    glide(page, "#c-origin", steps=36, click=False)
    slider = page.locator("#c-origin")
    box = slider.bounding_box()
    lo, hi = int(slider.get_attribute("min")), int(slider.get_attribute("max"))
    v = int(slider.input_value())
    knob = lambda v: (box["x"] + 8 + (box["width"] - 16) * (v - lo) / max(1, hi - lo), box["y"] + box["height"] / 2)
    page.mouse.move(*knob(v), steps=10)
    page.mouse.down()
    for _ in range(12):  # one week per step, released each time so the page redraws
        v += 1
        page.mouse.move(*knob(v), steps=6)
        page.mouse.up()
        page.wait_for_timeout(520)
        page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(900)
    glide(page, (980, 620), steps=30, click=False)
    page.wait_for_timeout(700)
    return rec.stop("overview")


def area(ctx, base, rec_page):
    """Area detail for Quezon City, as it read on 22 Sep 2024: Watch, and the checklist."""
    page, rec = rec_page
    page.goto(base + f"web/?page=unit{QC}&origin=2024-09-22", wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.mouse.move(1100, 300)
    rec.start()
    page.wait_for_timeout(900)
    glide(page, (520, 320), steps=30, click=False)
    page.wait_for_timeout(700)
    glide(page, (640, 560), steps=24, click=False)
    page.wait_for_timeout(500)
    smooth_scroll(page, 520, 2200)
    page.wait_for_timeout(1600)
    return rec.stop("area")


def barangays(ctx, base, rec_page):
    """The QC barangay shortlist, loading in."""
    page, rec = rec_page
    page.goto(base + f"web/?page=unit{QC}&origin=2025-01-26", wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.mouse.move(700, 600)
    rec.start()
    page.wait_for_timeout(400)
    glide(page, 'a[data-page="qc"]', steps=26)
    page.wait_for_timeout(2600)
    glide(page, (1050, 262), steps=30, click=False)
    page.wait_for_timeout(900)
    glide(page, (1000, 305), steps=10, click=False)
    page.wait_for_timeout(1200)
    return rec.stop("barangays")


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


CLIPS = {"landing": landing, "overview": overview, "area": area, "barangays": barangays, "drill": drill}


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
        browser = p.chromium.launch(channel="chrome", args=["--enable-unsafe-swiftshader"])
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
