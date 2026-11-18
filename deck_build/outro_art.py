"""Pixel-art outro scene: the EpiLag frog catching a mosquito (sprites from site/public/sprites).
Output: deck_build/assets/frog_outro.png, 960 x 1080 logical px at 2x."""
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent / "assets" / "frog_outro.png"
CELL = 13
W, H = 74, 84  # cells -> 962 x 1092 css px, cropped to 960 x 1080
frog = json.load(open(ROOT / "site/public/sprites/frog.json"))
mosq = json.load(open(ROOT / "site/public/sprites/mosquito.json"))

BG = (15, 26, 21)
img = Image.new("RGB", (W, H), BG)
px = img.load()
rnd = random.Random(7)

# faint night-sky stipple and rain streaks
for _ in range(140):
    x, y = rnd.randrange(W), rnd.randrange(0, 56)
    px[x, y] = (24, 40, 33)
for _ in range(26):
    x, y = rnd.randrange(W), rnd.randrange(0, 52)
    for k in range(3):
        if y + k < H:
            px[x, y + k] = (46, 86, 112)

# water
for y in range(66, H):
    for x in range(W):
        px[x, y] = (12, 33, 38) if (x + y) % 6 else (16, 43, 48)
# lily pad under the frog
for x in range(24, 74):
    for y in range(66, 69):
        d = abs(x - 49) / 25
        if d < 1 - (y - 66) * 0.18:
            px[x, y] = (52, 107, 53) if y < 68 else (36, 78, 40)


def blit(sprite, pose, ox, oy, skip=None):
    pal = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in sprite["palette"].items()}
    for yy, row in enumerate(sprite["poses"][pose]):
        for xx, ch in enumerate(row):
            if ch == "." or (skip and ch in skip):
                continue
            X, Y = ox + xx, oy + yy
            if 0 <= X < W and 0 <= Y < H:
                px[X, Y] = pal.get(ch, (255, 255, 255))


FX, FY = 27, 27  # frog top-left (cells); frog 48 x 40 stands on the pad
rows = frog["poses"]["strike"]
trows = [i for i, r in enumerate(rows) if "T" in r]
ty = FY + trows[len(trows) // 2]
tongue_tip = 17
blit(frog, "strike", FX, FY)
# extend the tongue from the frog's mouth to the mosquito
red = (229, 96, 79)
for yy in range(FY + trows[0] + 0, FY + trows[-1] + 1):
    for xx in range(tongue_tip, FX):
        px[xx, yy] = red
# mosquito at the tongue tip
blit(mosq, "fly1", 1, ty - 17)
# tongue tip drawn over the mosquito's mouth
for yy in range(FY + trows[0], FY + trows[-1] + 1):
    for xx in range(26, FX):
        px[xx, yy] = red
# impact sparks
for dx, dy in [(-3, -6), (6, -8), (-5, 4), (8, 5)]:
    for k in range(2):
        px[tongue_tip + dx, ty + dy + k] = (245, 165, 28)

big = img.resize((W * CELL * 2, H * CELL * 2), Image.NEAREST).crop((0, 0, 1920, 2160))
big.save(OUT)
print("saved", OUT, big.size, "tongue row", ty)
