"""Red hand-drawn annotations, in slide coordinates (1920 x 1080).

Each item: t = text, x/y = top-left of the text, w = text width,
a = optional arrow (x1, y1, x2, y2), or arrows = list of them, drawn as curves ending in arrowheads,
box = optional (x, y, w, h) rough rectangle drawn around something.
"""

ANN = {
    2: [dict(t="in a single year", x=690, y=560, w=260)],
    5: [dict(t="humidity acts fastest", x=800, y=402, w=300),
        dict(t="temperature acts slowest:<br>up to 4 months", x=1010, y=652, w=320, a=(1060, 650, 1120, 618)),
        dict(t="too hot is bad for mosquitoes too", x=1390, y=660, w=430)],
    6: [dict(t="EpiLag-PH fills the gap", x=1460, y=925, w=360, box=(86, 800, 1750, 110))],
    8: [dict(t="rain looks back the furthest: 12 weeks", x=560, y=960, w=520, a=(1080, 970, 1225, 470)),
        dict(t="from 6 groups", x=1560, y=380, w=220)],
    9: [dict(t="3 models: low, middle, high", x=100, y=750, w=420),
        dict(t="set once, the same<br>for every test year", x=1010, y=880, w=280, a=(1000, 890, 960, 870)),
        dict(t="filled = raw range, dashed = calibrated", x=1320, y=605, w=520)],
    10: [dict(t="the model never sees the year it is tested on", x=330, y=760, w=620, a=(900, 770, 1030, 648))],
    11: [dict(t="falls further behind<br>the further ahead", x=548, y=798, w=260)],
    12: [dict(t="called the outbreak,<br>not its full height", x=740, y=880, w=300, a=(1000, 895, 1140, 760))],
    13: [dict(t="the 2 we missed", x=110, y=960, w=240, arrows=[(170, 960, 150, 760), (260, 960, 400, 830)]),
         dict(t="2023: the only year we lost<br>to “same as this week”", x=1560, y=585, w=340, a=(1555, 640, 1190, 662))],
    14: [dict(t="green = helped the forecast", x=1540, y=900, w=320)],
    16: [dict(t="same outbreak data, now playable", x=1380, y=880, w=420)],
    17: [dict(t="each step must prove itself first", x=1380, y=940, w=460)],
}


def overlay(n, dark=False):
    items = ANN.get(n, [])
    if not items:
        return ""
    col = "#FF6B5E" if dark else "#D23B30"
    svg, html = "", ""
    for it in items:
        for x1, y1, x2, y2 in ([it["a"]] if "a" in it else []) + it.get("arrows", []):
            cx, cy = (x1 + x2) / 2 + (y2 - y1) * 0.25, (y1 + y2) / 2 - (x2 - x1) * 0.25
            svg += f'<path d="M{x1} {y1} Q {cx:.0f} {cy:.0f} {x2} {y2}" fill="none" stroke="{col}" stroke-width="3.5" stroke-linecap="round" marker-end="url(#ah{n})"/>'
        if "box" in it:
            bx, by, bw, bh = it["box"]
            svg += f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="18" fill="none" stroke="{col}" stroke-width="4" transform="rotate(-0.4 {bx} {by})"/>'
        html += f'<div class="ann" style="left:{it["x"]}px;top:{it["y"]}px;width:{it.get("w", 320)}px;color:{col}">{it["t"]}</div>'
    marker = f'<defs><marker id="ah{n}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10" fill="none" stroke="{col}" stroke-width="2"/></marker></defs>'
    return f'<svg class="annsvg" viewBox="0 0 1920 1080" width="1920" height="1080">{marker}{svg}</svg>{html}'
