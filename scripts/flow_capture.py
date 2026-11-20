"""Capture the live app and game for the system-flow video (docs/reel/flow/index.html).

The same recorder as scripts/reel_capture.py and scripts/trailer_capture.py (Chrome's screencast, resampled to 30 fps,
a pixel cursor drawn in), filming the current app: the Overview, the 3D forecast map drilling from the country to
NCR, Quezon City and Batasan Hills, Quezon City's page down to its report card, the action plan, the barangay
shortlist, the switch to Filipino, the residents' text message and Dengue Drill. Clips go to
docs/reel/flow/clips/<name>/ and are listed in docs/reel/flow/clips.js, with the boxes the film's camera flies to
and "marks" (the frame of each click or scroll), so the film can land them on the spoken words.

FLOW_SITE names the built site to film (a docs/ folder); the default is this checkout's docs/.

Usage: [FLOW_SITE=~/other-checkout/docs] python scripts/flow_capture.py [clip ...]
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel_capture as rc  # noqa: E402
import trailer_capture as tc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
tc.DOCS = Path(os.environ.get("FLOW_SITE", ROOT / "docs")).expanduser()
tc.OUT = rc.OUT = ROOT / "docs" / "reel" / "flow" / "clips"
glide, hover_path, boxes = rc.glide, rc.hover_path, rc.boxes
REPLAY = "panel=region_qc&mode=replay&h=4&lang=en&origin=2024-09-15"


class Marks:
    """Times of the clicks during a recording, turned into frame numbers of the finished clip."""

    def __init__(self):
        self.t = {}

    def __call__(self, name):
        self.t[name] = time.time()

    def stop(self, rec, name):
        t1 = time.time()
        out = rec.stop(name)
        out["marks"] = {k: max(0, round(out["n"] - 1 - (t1 - 0.05 - v) * rc.FPS)) for k, v in self.t.items()}
        return out


def overview(ctx, base, rec_page):
    """Overview, replaying 2024: drag the forecast week from August to 15 Sep 2024, then read the cards."""
    page, rec = rec_page
    page.goto(base + "web/?page=home&panel=region_qc&mode=replay&h=4&lang=en&origin=2024-08-04", wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.mouse.move(1200, 600)
    sel = {"strip": ".status-strip", "trend": "[data-guide='trend']", "rising": "[data-guide='rising']", "do": "[data-guide='do']",
           "map": ".overview-map", "prio": ".overview-priority", "slider": "#c-origin"}
    m = Marks()
    rec.start()
    page.wait_for_timeout(400)
    glide(page, "#c-origin", steps=26, click=False)
    slider = page.locator("#c-origin")
    box = slider.bounding_box()
    lo, hi = int(slider.get_attribute("min")), int(slider.get_attribute("max"))
    v = int(slider.input_value())
    knob = lambda v: (box["x"] + 8 + (box["width"] - 16) * (v - lo) / max(1, hi - lo), box["y"] + box["height"] / 2)
    page.mouse.move(*knob(v), steps=8)
    page.mouse.down()
    for _ in range(6):  # one week per step, released each time so the page redraws
        v += 1
        page.mouse.move(*knob(v), steps=5)
        page.mouse.up()
        page.wait_for_timeout(380)
        page.mouse.down()
    page.mouse.up()
    page.wait_for_timeout(700)
    bx = boxes(page, sel)
    m("strip")
    hover_path(page, [(420, 225), (700, 225), (1150, 225)], steps=22, pause=380)
    for k in ("trend", "rising", "do"):
        b = bx[k]
        m(k)
        hover_path(page, [(b[0] + b[2] * .4, b[1] + b[3] * .45), (b[0] + b[2] * .6, b[1] + b[3] * .55)], steps=20, pause=450)
    page.wait_for_timeout(600)
    out = m.stop(rec, "overview")
    out["boxes"] = bx
    return out


TIP = "(() => { const t = document.querySelector('.dmap__tip'); return t && !t.hidden ? t.innerText.split('\\n')[0] : '' })()"
LABELS = "() => Object.fromEntries([...document.querySelectorAll('.dmap svg text')].map(e => { const r = e.getBoundingClientRect(); return [e.textContent.trim(), [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]] }))"
STEPS = [("ncr", "NCR", ("NCR", "Metro Manila", "National Capital")), ("qc", "Quezon City", ("Quezon City",)), ("bgy", "Batasan Hills", ("Batasan Hills",))]


def open_map(page, base):
    page.goto(base + f"web/?page=map&{REPLAY}", wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.evaluate("document.querySelector('#dmap').scrollIntoView({block: 'end'})")
    page.wait_for_timeout(1500)


def find(page, names, cx, cy, r=72):
    """Hover outward from a label until the tooltip names the area: a point on its block."""
    for d in range(0, r, 6):
        for dx in range(-d, d + 1, 6):
            for dy in ((-d, d) if abs(dx) != d else range(-d, d + 1, 6)):
                page.mouse.move(cx + dx, cy + dy)
                page.wait_for_timeout(20)
                if any(n in page.evaluate(TIP) for n in names):
                    return cx + dx, cy + dy
    raise SystemExit(f"no block for {names[0]} near {cx}, {cy}")


def drillmap(ctx, base, rec_page):
    """The forecast map drilling down: the country, then NCR, Quezon City and Batasan Hills, with the panel beside it."""
    page, rec = rec_page
    open_map(page, base)  # a first pass finds where each block sits once the camera has settled
    pts = {}
    for key, label, names in STEPS:
        lab = page.evaluate(LABELS)
        pts[key] = find(page, names, *lab[label])
        page.mouse.click(*pts[key])
        page.mouse.move(1300, 200)
        page.wait_for_timeout(4200)
    open_map(page, base)
    page.mouse.move(1250, 420)
    page.wait_for_timeout(600)
    bx = boxes(page, {"map": "#dmap", "panel": "#dpanel", "crumbs": ".dmap__crumbs"})
    m = Marks()
    rec.start()
    page.wait_for_timeout(1300)
    for key, _, _ in STEPS:
        x, y = pts[key]
        page.mouse.move(x, y, steps=26)
        page.wait_for_timeout(260)
        m(key)
        page.mouse.click(x, y)
        page.wait_for_timeout(500)
        page.mouse.move(1120, 400, steps=30)  # off the map, to the panel, while the camera flies
        page.wait_for_timeout(1300)
        hover_path(page, [(1080, 385), (1250, 390)], steps=18, pause=700)
    page.wait_for_timeout(1200)
    out = m.stop(rec, "drillmap")
    out["boxes"] = bx | {"panel_top": [1012, 233, 388, 220]}
    return out


def area(ctx, base, rec_page):
    """Quezon City's page on 15 Sep 2024: the Watch call, the forecast, the checklist, then the report card."""
    page, rec = rec_page
    page.goto(base + f"web/?page=unit{rc.QC}&origin=2024-09-15", wait_until="networkidle")
    page.wait_for_timeout(2500)
    bx = boxes(page, {"hero": ".status-hero", "kpi": ".kpi", "playbook": ".playbook", "rows": ".todo__row"})
    y = page.evaluate("Math.round(document.getElementById('card').getBoundingClientRect().top + scrollY - 120)")
    page.mouse.move(1100, 300)
    m = Marks()
    rec.start()
    page.wait_for_timeout(400)
    hover_path(page, [(480, 320), (560, 340)], steps=22, pause=500)
    hover_path(page, [(860, 320), (900, 330)], steps=20, pause=400)
    m("todo")
    for r in bx["rows"]:
        hover_path(page, [(r[0] + 160, r[1] + r[3] / 2), (r[0] + 520, r[1] + r[3] / 2)], steps=18, pause=380)
    m("scroll")
    rc.smooth_scroll(page, y, 1200)
    page.wait_for_timeout(200)
    c = page.evaluate("(() => { const r = document.getElementById('card').getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round) })()")
    m("card")
    hover_path(page, [(c[0] + 120, c[1] + 100), (c[0] + 330, c[1] + 105), (c[0] + 420, c[1] + 190)], steps=20, pause=600)
    page.wait_for_timeout(900)
    out = m.stop(rec, "area")
    out["boxes"] = bx | {"card": c, "track": page.evaluate("(() => { const r = document.getElementById('track').getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round) })()"), "scroll_y": y}
    return out


def sms(ctx, base, rec_page):
    """For residents, Quezon City: the outlook as one text message, for phones without data."""
    page, rec = rec_page
    page.goto(base + f"web/?page=public{rc.QC}&origin=2024-09-15", wait_until="networkidle")
    page.wait_for_timeout(2500)
    y = page.evaluate("Math.round(document.getElementById('sms-card').getBoundingClientRect().bottom + scrollY - innerHeight + 40)")
    page.evaluate(f"scrollTo(0, {y})")
    page.wait_for_timeout(900)
    bx = boxes(page, {"sms": "#sms-card", "hero": ".hero-card", "msg": "#msg"})
    page.mouse.move(1150, 420)
    m = Marks()
    rec.start()
    page.wait_for_timeout(500)
    s = bx["sms"]
    m("sms")
    hover_path(page, [(s[0] + 260, s[1] + 85), (s[0] + 700, s[1] + 88)], steps=24, pause=500)
    glide(page, "#copy-sms", steps=22)
    page.wait_for_timeout(1600)
    out = m.stop(rec, "sms")
    out["boxes"] = bx
    return out


def lang(ctx, base, rec_page):
    """The same Overview, switched from English to Filipino (the mark is the click on FIL)."""
    page, rec = rec_page
    page.goto(base + f"web/?page=home&{REPLAY}", wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.mouse.move(700, 500)
    bx = boxes(page, {"strip": ".status-strip", "trend": "[data-guide='trend']", "map": ".overview-map", "prio": ".overview-priority"})
    fil = page.get_by_text("FIL", exact=True).first
    b = fil.bounding_box()
    bx["switch"] = [round(b["x"]) - 40, round(b["y"]) - 30, 110, round(b["height"]) + 40]
    m = Marks()
    rec.start()
    page.wait_for_timeout(700)
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=26)
    page.wait_for_timeout(250)
    m("flip")
    page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    page.wait_for_timeout(1000)
    hover_path(page, [(500, 225), (900, 330), (1200, 330)], steps=24, pause=600)
    out = m.stop(rec, "lang")
    out["boxes"] = bx
    return out


CLIPS = {"overview": overview, "drillmap": drillmap, "area": area, "budget": rc.budget, "barangays": rc.barangays,
         "lang": lang, "sms": sms, "drill": tc.drill}

if __name__ == "__main__":
    tc.CLIPS = CLIPS
    tc.main(set(sys.argv[1:]))
