"""Generated artwork for the deck: pixel icons, voxel maps of the Philippines, device frames."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- pixel icons (12 x 12)
ICONS = {
    "rain": ["....XXXX....", "..XXXXXXXX..", ".XXXXXXXXXX.", "XXXXXXXXXXXX", ".XXXXXXXXXX.", "............",
             "..B...B...B.", ".B...B...B..", "............", "...B...B....", "..B...B.....", "............"],
    "container": ["............", "............", ".XXXXXXXXXX.", ".XBBBBBBBBX.", ".XBBBBBBBBX.", "..XBBBBBBX..",
                  "..XBBBBBBX..", "..XBBBBBBX..", "...XBBBBX...", "...XXXXXX...", "............", "............"],
    "mosquito": ["............", "....W..W....", "...WW..WW...", "....WXXW....", ".....XX.....", "...XXXXXX...",
                 "..X.XXXX.X..", ".X..XXXX..X.", "....X..X....", "...X....X...", "..X......X..", "............"],
    "sick": ["....XXXX....", "...XXXXXX...", "...XXXXXX...", "....XXXX..R.", "..XXXXXXXXR.", ".XXXXXXXXXR.",
             ".XXXXXXXXXR.", ".XX.XXXX.XR.", "....XXXX..RR", "....XX.XX.RR", "....XX.XX...", "....XX.XX..."],
    "counted": ["....XXXX....", "..XXXXXXXX..", "..XPPPPPPX..", "..XPLLLLPX..", "..XPPPPPPX..", "..XPLLLLPX..",
                "..XPPPPPPX..", "..XPLLLPPX..", "..XPPPPPPX..", "..XXXXXXXX..", "............", "............"],
}
ICON_COLORS = {"X": "currentColor", "B": "#5AA9E6", "W": "#BFD9E8", "R": "#E5483C", "P": "#F4F1E8", "L": "#9AA59F"}


def icon(name, size=96, color=None):
    rows = ICONS[name]
    cell = size / 12
    rects = "".join(
        f'<rect x="{x*cell:.2f}" y="{y*cell:.2f}" width="{cell+.4:.2f}" height="{cell+.4:.2f}" fill="{ICON_COLORS[ch]}"/>'
        for y, row in enumerate(rows) for x, ch in enumerate(row) if ch != ".")
    style = f' style="color:{color}"' if color else ""
    return f'<svg class="px" viewBox="0 0 {size} {size}" width="{size}" height="{size}"{style} shape-rendering="crispEdges">{rects}</svg>'


# ---------------------------------------------------------------- voxel map of the Philippines
_V = json.load(open(ROOT / "site/public/geo/voxel_ph.json"))["province"]


def voxel_map(color_of, px=2.0, extra="", sea=None):
    """color_of(unit_id) -> fill. One square per grid cell, run-length rows from voxel_ph.json."""
    units = _V["units"]
    out = []
    for y, row in enumerate(_V["rows"]):
        x = 0
        for k in range(0, len(row), 2):
            idx, run = row[k], row[k + 1]
            if idx >= 0:
                c = color_of(units[idx])
                out.append(f'<rect x="{x*px:.1f}" y="{y*px:.1f}" width="{run*px+.3:.1f}" height="{px+.3:.1f}" fill="{c}"/>')
            x += run
    W, H = _V["w"] * px, _V["h"] * px
    bg = f'<rect width="{W}" height="{H}" fill="{sea}"/>' if sea else ""
    return f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges">{bg}{"".join(out)}{extra}</svg>'


def lonlat_to_px(lon, lat, px=2.0):
    x = (lon - _V["origin"][0]) / _V["cellx"]
    y = (_V["origin"][1] - lat) / _V["cell"]
    return x * px, y * px


# ---------------------------------------------------------------- device frames
def laptop(src, width=1100):
    return f'''<div class="laptop" style="width:{width}px"><div class="lid"><div class="cam"></div><img src="{src}"></div><div class="base"></div></div>'''


def phone(src, height=760):
    return f'''<div class="phone" style="height:{height}px"><div class="notch"></div><img src="{src}"></div>'''
