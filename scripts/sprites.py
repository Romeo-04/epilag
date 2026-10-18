"""Turn the pixel-art sprite sheets into text-grid JSON for the website (site/public/sprites/*.json).

Each sheet is one row of equal frames, 1 image pixel = 1 art pixel, drawn with the palette in site/briefs/sprites.md.
Every opaque pixel becomes one palette letter, so the site can redraw, blink, flip and scatter sprites pixel by pixel.
Pixels that are not an exact palette colour are snapped to the nearest one and counted, so a bad export shows up.

Usage: python scripts/sprites.py ["UI mockup/sprites"]   (needs Pillow)
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "UI mockup" / "sprites"
OUT = ROOT / "site" / "public" / "sprites"

PALETTE = {
    "K": "#071711", "D": "#1F3320", "G": "#3D6B35", "H": "#6E9A4A", "B": "#F2E3B3", "A": "#F5A51C",
    "W": "#FFFFFF", "L": "#D5E3DA", "M": "#A8BFB2", "T": "#E5604F", "R": "#F04B2A",
    # props only
    "S": "#BFE2EC", "s": "#7FB9CB", "O": "#C8553D", "F": "#F3EEE0",
}
# name, frame size, anchor (x, y), pose names in sheet order, how to close the eyes for a blink
SHEETS = {
    "mosquito": ((32, 32), (16, 18), ["fly1", "fly2", "turn", "dash", "pin", "alert", "clipboard", "search", "front",
                                      "happy", "check", "sleepy"], {"W": "D"}),
    "frog": ((48, 40), (24, 39), ["peek", "watch", "watchClose", "idle", "strike", "gulp", "chew", "happy"], {"W": "G"}),
    "props": ((48, 48), (24, 47), ["cloud", "sun", "house", "container", "residents", "hospital", "ambulance", "tree",
                                   "school", "broom", "clinicBag", "people"], {}),
}

RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PALETTE.items()}


def letter(rgb):
    """Exact palette letter, or the nearest one (second value False)."""
    for k, v in RGB.items():
        if v == rgb:
            return k, True
    return min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], rgb))), False


def frame_rows(img, x0, w, h):
    rows, off = [], 0
    for y in range(h):
        row = ""
        for x in range(x0, x0 + w):
            r, g, b, a = img.getpixel((x, y))
            if a < 128:
                row += "."
                continue
            k, exact = letter((r, g, b))
            off += not exact
            row += k
        rows.append(row)
    return rows, off


def convert(name, size, anchor, poses, blink):
    path = SRC / f"{name}.png"
    img = Image.open(path).convert("RGBA")
    w, h = size
    if img.height != h or img.width % w:
        raise SystemExit(f"{path}: expected frames of {w}x{h} in one row, got {img.size}")
    n = img.width // w
    if n < len(poses):
        print(f"  warning: {name} has {n} frames, brief lists {len(poses)}; extra names are dropped")
    out, off_total = {}, 0
    for i, pose in enumerate(poses[:n]):
        rows, off = frame_rows(img, i * w, w, h)
        out[pose] = rows
        off_total += off
    used = sorted({c for rows in out.values() for row in rows for c in row} - {"."})
    data = {"palette": {k: PALETTE[k] for k in used}, "size": [w, h], "anchor": list(anchor), "blink": blink,
            "poses": out}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(data, separators=(",", ":")))
    print(f"{name}: {len(out)} poses, colours {''.join(used)}, {off_total} off-palette pixels snapped")


def main():
    for name, spec in SHEETS.items():
        if (SRC / f"{name}.png").exists():
            convert(name, *spec)
        else:
            print(f"{name}: {SRC / (name + '.png')} not found, skipped")


if __name__ == "__main__":
    main()
