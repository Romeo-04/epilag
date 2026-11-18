"""Build docs/deck/final/EpiLag-PH_final_deck.pptx from the rendered deck.

Layer 1: one picture per slide (visuals only, from extract_layers.py).
Layer 2: editable text boxes at the same positions, fonts and colours.
Layer 3: editable red annotation arrows and boxes (annotations.py), plus the hook arrow on slide 1.
Fonts used: Plus Jakarta Sans, Caveat, IBM Plex Mono (free Google Fonts; install them for an exact match).
"""
import json
import re
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from annotations import ANN  # noqa: E402

ROOT = HERE.parent
PX = 6350  # EMU per CSS pixel on a 13.333 x 7.5 in slide (1920 x 1080)
DARK = {1, 2, 3, 4, 19}
data = json.loads((HERE / "pptx/text.json").read_text(encoding="utf8"))


def rgb(css):
    m = re.findall(r"[\d.]+", css)
    r, g, b = (int(float(v)) for v in m[:3])
    a = float(m[3]) if len(m) > 3 else 1.0
    return RGBColor(r, g, b), a


def px(v):
    return Emu(int(round(v * PX)))


prs = Presentation()
prs.slide_width, prs.slide_height = px(1920), px(1080)
blank = prs.slide_layouts[6]


FACES = {
    "Plus Jakarta Sans": {400: ("Plus Jakarta Sans", False), 500: ("Plus Jakarta Sans Medium", False), 600: ("Plus Jakarta Sans SemiBold", False),
                          700: ("Plus Jakarta Sans", True), 800: ("Plus Jakarta Sans ExtraBold", False)},
    "Caveat": {400: ("Caveat", False), 600: ("Caveat SemiBold", False), 700: ("Caveat", True)},
    "IBM Plex Mono": {400: ("IBM Plex Mono", False), 500: ("IBM Plex Mono Medium", False), 600: ("IBM Plex Mono SemiBold", False)},
}


def face_for(fam, weight):
    table = FACES.get(fam)
    if not table:
        return fam, weight >= 600
    w = min(table, key=lambda k: abs(k - weight))
    return table[w]


def add_text(slide, blk, styles):
    lines = blk["lines"]
    x0, x1, y0, y1 = blk["x0"], blk["x1"], blk["y0"], blk["y1"]
    slack = 14
    left = x0 - (slack if blk["align"] == "right" else 0) - (slack / 2 if blk["align"] == "center" else 0)
    tb = slide.shapes.add_textbox(px(left), px(y0), px(x1 - x0 + slack), px(y1 - y0))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.auto_size = None
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    lh = blk["lh"]
    for i, ln in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = {"right": PP_ALIGN.RIGHT, "center": PP_ALIGN.CENTER}.get(blk["align"], PP_ALIGN.LEFT)
        para.line_spacing = Pt((lh if lh else ln["h"]) * 0.5)
        for run in ln["runs"]:
            st = styles[run["s"]]
            r = para.add_run()
            r.text = run["t"]
            f = r.font
            face, bold = face_for(st["fam"], st["weight"])
            f.name = face
            f.size = Pt(st["size"] * 0.5)
            f.bold = bold
            f.italic = st["italic"]
            col, a = rgb(st["color"])
            f.color.rgb = col
            rPr = r._r.get_or_add_rPr()
            if a < 0.99:
                fill = rPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
                clr = fill[0]
                etree.SubElement(clr, "{http://schemas.openxmlformats.org/drawingml/2006/main}alpha").set("val", str(int(a * 100000)))
            ls = st.get("ls", "normal")
            if ls not in ("normal", "0px"):
                rPr.set("spc", str(int(float(ls.replace("px", "")) * 0.5 * 100)))
            for tag in ("latin", "ea", "cs"):
                el = rPr.find(f"{{http://schemas.openxmlformats.org/drawingml/2006/main}}{tag}")
                if el is None:
                    el = etree.SubElement(rPr, f"{{http://schemas.openxmlformats.org/drawingml/2006/main}}{tag}")
                el.set("typeface", face)
    return tb


def curve_points(pts, n=24):
    if len(pts) == 3:  # quadratic
        (x1, y1), (cx, cy), (x2, y2) = pts
        return [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2, (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2)
                for t in (k / n for k in range(n + 1))]
    (x1, y1), (c1x, c1y), (c2x, c2y), (x2, y2) = pts  # cubic
    out = []
    for k in range(n + 1):
        t = k / n
        mt = 1 - t
        out.append((mt**3 * x1 + 3 * mt * mt * t * c1x + 3 * mt * t * t * c2x + t**3 * x2,
                    mt**3 * y1 + 3 * mt * mt * t * c1y + 3 * mt * t * t * c2y + t**3 * y2))
    return out


def add_arrow(slide, pts, color, width_px, name="Annotation arrow"):
    p = curve_points(pts)
    fb = slide.shapes.build_freeform(px(p[0][0]), px(p[0][1]), scale=1.0)
    fb.add_line_segments([(px(x), px(y)) for x, y in p[1:]], close=False)
    shp = fb.convert_to_shape()
    shp.name = name
    shp.fill.background()
    shp.line.color.rgb = color
    shp.line.width = Pt(width_px * 0.5)
    ln = shp.line._get_or_add_ln()
    tail = etree.SubElement(ln, "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd")
    tail.set("type", "arrow")
    tail.set("w", "med")
    tail.set("len", "med")
    return shp


for i, d in enumerate(data):
    n = i + 1
    slide = prs.slides.add_slide(blank)
    pic = slide.shapes.add_picture(str(HERE / f"pptx/bg_{n:02d}.jpg"), 0, 0, prs.slide_width, prs.slide_height)
    pic.name = "Slide visuals"
    for blk in d["blocks"]:
        if any(len(ln.get("segs", [])) > 1 for ln in blk["lines"]):
            # one text box per line segment, so flex gaps and column spacing survive
            for ln in blk["lines"]:
                for sg in ln["segs"]:
                    add_text(slide, {"x0": sg["x0"], "x1": sg["x1"], "y0": ln["top"], "y1": ln["top"] + ln["h"], "align": "left", "lh": None,
                                     "lines": [{"top": ln["top"], "h": ln["h"], "runs": sg["runs"]}]}, d["styles"])
        else:
            add_text(slide, blk, d["styles"])
    red = RGBColor(0xFF, 0x6B, 0x5E) if n in DARK else RGBColor(0xD2, 0x3B, 0x30)
    for it in ANN.get(n, []):
        for x1, y1, x2, y2 in ([it["a"]] if "a" in it else []) + it.get("arrows", []):
            cx, cy = (x1 + x2) / 2 + (y2 - y1) * 0.25, (y1 + y2) / 2 - (x2 - x1) * 0.25
            add_arrow(slide, [(x1, y1), (cx, cy), (x2, y2)], red, 3.5)
        if "box" in it:
            bx, by, bw, bh = it["box"]
            box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(bx), px(by), px(bw), px(bh))
            box.name = "Annotation box"
            box.adjustments[0] = 18 / min(bw, bh)
            box.fill.background()
            box.line.color.rgb = red
            box.line.width = Pt(2)
            box.shadow.inherit = False
    if n == 1:  # hook arrow: svg at (700, 470), path M40 340 C 70 250, 150 150, 300 60
        ox, oy = 700, 470
        add_arrow(slide, [(ox + 40, oy + 340), (ox + 70, oy + 250), (ox + 150, oy + 150), (ox + 300, oy + 60)],
                  RGBColor(0xFF, 0x5A, 0x4E), 6, "Hook arrow")

out = ROOT / "docs/deck/final/EpiLag-PH_final_deck.pptx"
prs.save(out)
print("saved", out, out.stat().st_size // 1024, "KB")
