"""EpiLag-PH research poster, pixel edition (A-series portrait, 1900 x 2688 px).
Layout follows a numbered research-poster template; art comes from the repo's pixel sprites, voxel map and textures.
Run: .venv/bin/python poster_build/claude/build_pixel.py && sh poster_build/claude/render_pixel.sh"""
import json
from datetime import date
from pathlib import Path

import segno

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
LV = {"normal": "#0C7A55", "above": "#F7C928", "watch": "#F58220", "warning": "#F04B2A"}


# ---------- pixel sprites (docs/sprites/*.json: rows of palette letters, "." = clear)
def sprite(sheet, pose, px=6, flip=False, cls=""):
    d = json.load(open(ROOT / "docs/sprites" / f"{sheet}.json"))
    rows = d["poses"][pose]
    w, h = d["size"]
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            c = row[x]
            if c == ".":
                x += 1
                continue
            run = 1
            while x + run < len(row) and row[x + run] == c:
                run += 1
            xx = (w - x - run) if flip else x
            out.append(f'<rect x="{xx}" y="{y}" width="{run}" height="1" fill="{d["palette"][c]}"/>')
            x += run
    return (f'<svg class="spr {cls}" viewBox="0 0 {w} {h}" width="{w*px}" height="{h*px}" '
            f'shape-rendering="crispEdges">{"".join(out)}</svg>')


# ---------- voxel map of the Philippines, coloured by the 4-week forecast issued 2 June 2019
def voxel_map():
    v = json.load(open(ROOT / "docs/geo/voxel_ph.json"))["province"]
    rp = json.load(open(ROOT / "site/public/data/replay_2019-06-02.json"))["horizons"]["4"]["units"]
    units = v["units"]
    top, side = [], []
    for y, row in enumerate(v["rows"]):
        x = 0
        for k in range(0, len(row), 2):
            u, n = row[k], row[k + 1]
            if u >= 0:
                lv = rp.get(units[u], ["normal"])[0]
                top.append(f'<rect x="{x}" y="{y}" width="{n}" height="1" fill="{LV[lv]}"/>')
                side.append(f'<rect x="{x}" y="{y+1.6}" width="{n}" height="1" fill="#06301F"/>')
            x += n
    w, h = v["w"], v["h"]
    return (f'<svg class="vox" viewBox="20 0 {w-30} {h+3}" shape-rendering="crispEdges">'
            f'<g opacity=".9">{"".join(side)}</g>{"".join(top)}</svg>')


# ---------- Quezon City 2024-25 chart, drawn on a pixel grid
def qc_chart():
    d = json.load(open(HERE / "qc.json"))
    weeks = [date.fromisoformat(w) for w in d["weeks"]]
    W, H, L, R, T, B = 1250, 318, 56, 10, 22, 40
    n = len(weeks)
    step = (W - L - R) / n
    X = lambda i: L + i * step  # noqa: E731
    Y = lambda v: T + (1 - v / 700) * (H - T - B)  # noqa: E731
    bw = round(step) - 4
    bars = "".join(
        f'<rect x="{X(i)+2:.0f}" y="{Y(c):.0f}" width="{bw}" height="{Y(0)-Y(c):.0f}" '
        f'fill="{"#F04B2A" if c > e else "#B9C4BC"}"/>'
        for i, (c, e) in enumerate(zip(d["cases"], d["epi"])))
    epi = "M" + " L".join(f"{X(i)+step/2:.1f},{Y(e):.1f}" for i, e in enumerate(d["epi"]))
    fc = "M" + " L".join(f"{X(i)+step/2:.1f},{Y(q):.1f}" for i, q in enumerate(d["q50"]) if q is not None)
    grid = "".join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.0f}" y2="{Y(v):.0f}" stroke="#E4E4D9" stroke-width="2"/>'
                   f'<text x="{L-10}" y="{Y(v)+6:.0f}" class="tk" text-anchor="end">{v}</text>' for v in (0, 200, 400, 600))
    months = "".join(
        f'<text x="{X(i)+step/2:.0f}" y="{H-12}" class="tk" text-anchor="middle">'
        f'{w.strftime("%b")}{" ’25" if w.month == 1 else (" ’24" if i == 0 else "")}</text>'
        for i, w in enumerate(weeks) if w.day <= 7)
    idx = {w.isoformat(): i for i, w in enumerate(weeks)}

    def mark(week, label, color, y):
        x = X(idx[week]) + step / 2
        return (f'<line x1="{x:.0f}" x2="{x:.0f}" y1="{y}" y2="{Y(0):.0f}" stroke="{color}" stroke-width="4" stroke-dasharray="4 6"/>'
                f'<rect x="{x-7:.0f}" y="{y-7}" width="14" height="14" fill="{color}"/>'
                f'<text x="{x+14:.0f}" y="{y+7}" class="mk" fill="{color}">{label}</text>')
    pk = max(range(n), key=lambda i: d["cases"][i])
    return (f'<svg viewBox="0 0 {W} {H}" class="chart" shape-rendering="crispEdges">{grid}{bars}'
            f'<path d="{epi}" fill="none" stroke="#071711" stroke-width="3" stroke-dasharray="9 6" opacity=".8" shape-rendering="auto"/>'
            f'<path d="{fc}" fill="none" stroke="#08754F" stroke-width="5" shape-rendering="auto"/>'
            f'{mark("2024-09-15", "First watch · 15 Sep", "#C25E00", 40)}'
            f'{mark("2024-10-20", "Crossed the line · 20 Oct", "#C6301A", 100)}'
            f'<text x="{X(pk)-8:.0f}" y="{Y(d["cases"][pk])+8:.0f}" class="mk" text-anchor="end">622 / wk peak</text>'
            f'{months}</svg>')


def main():
    qr = segno.make("https://romeo-04.github.io/epilag/", error="m").svg_inline(scale=8, border=0, dark="#071711")
    favicon = (ROOT / "docs/favicon.svg").read_text()
    subs = {
        "{{QR}}": qr,
        "{{CHART}}": qc_chart(),
        "{{MAP}}": voxel_map(),
        "{{FAVICON}}": favicon,
        "{{MOSQ}}": sprite("mosquito", "fly1", 7),
        "{{MOSQ_CLIP}}": sprite("mosquito", "clipboard", 5),
        "{{MOSQ_SLEEP}}": sprite("mosquito", "sleepy", 5, flip=True),
        "{{FROG}}": sprite("frog", "watch", 5),
        "{{FROG_HAPPY}}": sprite("frog", "happy", 7, flip=True),
        "{{FROG_PEEK}}": sprite("frog", "peek", 6),
    }
    for p in ["cloud", "sun", "house", "container", "residents", "hospital", "ambulance", "tree", "school",
              "broom", "clinicBag", "people"]:
        subs["{{P_" + p + "}}"] = sprite("props", p, 2, cls="ic")
    html = (HERE / "pixel_template.html").read_text()
    for k, v in subs.items():
        html = html.replace(k, v)
    assert "{{" not in html, html[html.index("{{"):html.index("{{") + 40]
    (HERE / "poster_pixel.html").write_text(html)
    print("wrote", HERE / "poster_pixel.html")


if __name__ == "__main__":
    main()
