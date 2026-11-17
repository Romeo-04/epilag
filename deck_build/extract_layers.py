"""Split each rendered slide into (1) a visuals-only image, with all HTML text, annotations and
hand-drawn arrows hidden, and (2) a JSON list of text blocks: lines, runs, fonts, colours, positions.
Chart labels drawn inside SVG stay in the image (they are part of the visual).

Output: deck_build/pptx/bg_XX.jpg and deck_build/pptx/text.json
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/deck/final/index.html"
OUT = Path(__file__).parent / "pptx"
OUT.mkdir(exist_ok=True)

JS = r"""
(idx) => {
  const sec = document.querySelectorAll('section.slide')[idx];
  const sr = sec.getBoundingClientRect();
  const walker = document.createTreeWalker(sec, NodeFilter.SHOW_TEXT);
  const blocks = new Map(); const order = [];
  let n;
  while ((n = walker.nextNode())) {
    if (!n.textContent.trim()) continue;
    const pe = n.parentElement;
    if (pe.closest('svg')) continue;
    if (getComputedStyle(pe).visibility === 'hidden') continue;
    let b = pe;
    while (b !== sec && getComputedStyle(b).display === 'inline') b = b.parentElement;
    if (!blocks.has(b)) { blocks.set(b, []); order.push(b); }
    blocks.get(b).push(n);
  }
  const styles = []; const styleKey = new Map();
  const sid = (el) => {
    const st = getComputedStyle(el);
    const fam = st.fontFamily.split(',')[0].replace(/["']/g, '').trim();
    const s = {fam, size: parseFloat(st.fontSize), weight: parseInt(st.fontWeight), italic: st.fontStyle === 'italic',
               color: st.color, ls: st.letterSpacing};
    const k = JSON.stringify(s);
    if (!styleKey.has(k)) { styleKey.set(k, styles.length); styles.push(s); }
    return styleKey.get(k);
  };
  const out = [];
  for (const b of order) {
    const bst = getComputedStyle(b);
    const chars = [];
    for (const t of blocks.get(b)) {
      const st = getComputedStyle(t.parentElement);
      const id = sid(t.parentElement);
      const up = st.textTransform === 'uppercase';
      const s = t.textContent;
      for (let i = 0; i < s.length; i++) {
        const r = document.createRange(); r.setStart(t, i); r.setEnd(t, i + 1);
        const rects = r.getClientRects(); if (!rects.length) continue;
        const rc = rects[0];
        if (rc.width === 0) continue;
        let ch = s[i]; if (/\s/.test(ch)) ch = ' '; if (up) ch = ch.toUpperCase();
        chars.push({ch, x: rc.left - sr.left, y: rc.top - sr.top, w: rc.width, h: rc.height, s: id});
      }
    }
    if (!chars.length) continue;
    // group into lines by vertical position
    const lines = [];
    for (const c of chars) {
      const mid = c.y + c.h / 2;
      let L = lines.find(l => Math.abs(l.mid - mid) < Math.max(4, c.h * 0.35));
      if (!L) { L = {mid, top: c.y, h: c.h, chars: []}; lines.push(L); }
      L.chars.push(c); L.top = Math.min(L.top, c.y); L.h = Math.max(L.h, c.h);
    }
    lines.sort((a, b) => a.top - b.top);
    const outLines = lines.map(l => {
      l.chars.sort((a, b) => a.x - b.x);
      // collapse double spaces, trim
      const runs = [];
      let prevSpace = true;
      for (const c of l.chars) {
        if (c.ch === ' ' && prevSpace) continue;
        prevSpace = c.ch === ' ';
        if (runs.length && runs[runs.length - 1].s === c.s) runs[runs.length - 1].t += c.ch;
        else runs.push({s: c.s, t: c.ch});
      }
      if (runs.length) runs[runs.length - 1].t = runs[runs.length - 1].t.replace(/\s+$/, '');
      const x0 = Math.min(...l.chars.map(c => c.x)), x1 = Math.max(...l.chars.map(c => c.x + c.w));
      // split the line where glyphs are far apart (flex gaps, margins): separate text boxes
      const segs = []; let cur = null;
      for (const c of l.chars) {
        if (!cur || c.x - (cur.x1) > Math.max(10, c.h * 0.45)) { cur = {x0: c.x, x1: c.x + c.w, chars: []}; segs.push(cur); }
        cur.chars.push(c); cur.x1 = Math.max(cur.x1, c.x + c.w);
      }
      const segOut = segs.map(sg => {
        const rr = []; let ps = true;
        for (const c of sg.chars) {
          if (c.ch === ' ' && ps) continue; ps = c.ch === ' ';
          if (rr.length && rr[rr.length - 1].s === c.s) rr[rr.length - 1].t += c.ch; else rr.push({s: c.s, t: c.ch});
        }
        if (rr.length) rr[rr.length - 1].t = rr[rr.length - 1].t.replace(/\s+$/, '');
        return {x0: sg.x0, x1: sg.x1, runs: rr};
      }).filter(sg => sg.runs.length && sg.runs.some(r => r.t.trim()));
      return {top: l.top, h: l.h, x0, x1, runs, segs: segOut};
    });
    const x0 = Math.min(...outLines.map(l => l.x0)), x1 = Math.max(...outLines.map(l => l.x1));
    const y0 = outLines[0].top, y1 = Math.max(...outLines.map(l => l.top + l.h));
    let align = bst.textAlign;
    if (align === 'start') align = 'left'; if (align === 'end') align = 'right';
    const lh = outLines.length > 1 ? (outLines[outLines.length - 1].top - outLines[0].top) / (outLines.length - 1) : null;
    out.push({x0, x1, y0, y1, align, lh, lines: outLines});
  }
  return {blocks: out, styles};
}
"""

HIDE = """
section.slide *:not(svg):not(svg *) { color: transparent !important; text-shadow: none !important; }
.ann, .annsvg, .hookarrow { display: none !important; }
"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
    pg.goto(SRC.as_uri(), wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(800)
    n = pg.evaluate("document.querySelectorAll('section.slide').length")
    data = [pg.evaluate(JS, i) for i in range(n)]
    pg.add_style_tag(content=HIDE)
    pg.wait_for_timeout(300)
    for i, el in enumerate(pg.query_selector_all("section.slide")):
        el.screenshot(path=str(OUT / f"bg_{i+1:02d}.jpg"), type="jpeg", quality=90)
    b.close()
(OUT / "text.json").write_text(json.dumps(data), encoding="utf8")
print("slides", n, "blocks", sum(len(d["blocks"]) for d in data))
