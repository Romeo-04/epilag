"""Render the social card (site/public/og.png, 1200 x 630) in the site's pixel style, with Playwright.

Draws the brand, the headline, the province grid of site/public/geo/voxel_ph.json as a flat pixel map (coloured by
the 2 June 2019 replay levels, from site/public/data/replay_2019-06-02.json) and the mosquito and frog sprites.
Vite copies the image to docs/og.png. Usage: python scripts/og_image.py
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "site" / "public"
OUT = PUBLIC / "og.png"
LEVEL = {"warning": "#F04B2A", "watch": "#F58220", "above": "#F7C928", "normal": "#0C7A55"}

HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;700;800&display=swap" rel="stylesheet">
<style>
* { margin: 0; box-sizing: border-box; }
body { width: 1200px; height: 630px; overflow: hidden; font-family: "Inter Tight", Arial, sans-serif; color: #E9F3EC;
  background: linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px) 0 0 / 100% 4px, radial-gradient(120% 90% at 75% 10%, #13492F, #0A2A1D 60%); }
.card { position: absolute; inset: 0; display: grid; grid-template-columns: 1fr 470px; gap: 20px; padding: 64px 64px 56px; }
.brand { display: flex; align-items: center; gap: 14px; font-weight: 800; font-size: 30px; letter-spacing: -.02em; }
.lg { width: 56px; height: 56px; border-radius: 14px; background: #08754F; display: grid; place-items: center; }
h1 { margin-top: 40px; font-size: 64px; line-height: .98; letter-spacing: -.045em; font-weight: 800; }
h1 span { display: block; color: #34D27B; }
p { margin-top: 22px; font-size: 24px; line-height: 1.35; color: #9DBDAC; max-width: 23ch; }
.tag { position: absolute; left: 64px; bottom: 52px; display: flex; gap: 10px; }
.tag b { padding: 8px 14px; border: 2px solid #1E5A40; font-size: 18px; letter-spacing: .06em; text-transform: uppercase; color: #E9F3EC; }
.map { position: relative; align-self: center; }
canvas { image-rendering: pixelated; display: block; }
#mosq { position: absolute; left: -40px; top: 10px; }
#frog { position: absolute; right: -6px; bottom: -14px; }
</style></head><body>
<div class="card"><div>
  <div class="brand"><span class="lg"><canvas id="logo"></canvas></span>EpiLag-PH</div>
  <h1>Rain starts the clock.<span>We read what comes next.</span></h1>
  <p>Dengue forecasts 2–8 weeks ahead, for every province.</p>
</div>
<div class="map"><canvas id="map"></canvas><canvas id="mosq"></canvas><canvas id="frog"></canvas></div></div>
<div class="tag"><b>Early warning</b><b>3D pixel maps</b><b>Open data</b></div>
<script>
const DATA = __DATA__;
function sprite(id, sheet, pose, scale) {
  const rows = sheet.poses[pose], c = document.getElementById(id), g = c.getContext("2d");
  c.width = rows[0].length; c.height = rows.length; c.style.width = c.width * scale + "px"; c.style.height = c.height * scale + "px";
  rows.forEach((r, y) => [...r].forEach((ch, x) => { const col = sheet.palette[ch]; if (col) { g.fillStyle = col; g.fillRect(x, y, 1, 1); } }));
}
const grid = DATA.grid, c = document.getElementById("map"), g = c.getContext("2d");
c.width = grid.w; c.height = grid.h;
const s = Math.min(470 / grid.w, 520 / grid.h); c.style.width = grid.w * s + "px"; c.style.height = grid.h * s + "px";
grid.rows.forEach((row, y) => { let x = 0; for (let i = 0; i < row.length; i += 2) { const u = row[i], n = row[i + 1];
  if (u >= 0) { g.fillStyle = DATA.colors[grid.units[u]] || "#2E6B3F"; g.fillRect(x, y, n, 1); } x += n; } });
sprite("mosq", DATA.mosquito, "fly1", 5);
sprite("logo", DATA.frog, "peek", 1);
sprite("frog", DATA.frog, "watch", 4);
</script></body></html>"""


def main() -> None:
    grid = json.loads((PUBLIC / "geo" / "voxel_ph.json").read_text())["province"]
    replay = json.loads((PUBLIC / "data" / "replay_2019-06-02.json").read_text())
    colors = {u: LEVEL[f[0]] for u, f in replay["horizons"]["4"]["units"].items()}
    data = {"grid": grid, "colors": colors,
            "mosquito": json.loads((PUBLIC / "sprites" / "mosquito.json").read_text()),
            "frog": json.loads((PUBLIC / "sprites" / "frog.json").read_text())}
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception:  # noqa: BLE001
            b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        pg.set_content(HTML.replace("__DATA__", json.dumps(data)), wait_until="networkidle")
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT))
        b.close()
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
