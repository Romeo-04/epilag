// Pixel sprites from text grids (site/public/sprites/*.json, made by scripts/sprites.py).
// A sprite is { palette: {letter: hex}, size: [w, h], anchor: [x, y], blink: {from: to}, poses: {name: [rows]} }.
// Poses are drawn once to a 1x canvas and scaled with smoothing off, so every art pixel stays square.

const sheets = new Map();
const baked = new Map();

/** Load a sprite sheet by name ("mosquito", "frog"). Cached. */
export function loadSprite(name) {
  if (!sheets.has(name)) {
    sheets.set(name, fetch(`${import.meta.env.BASE_URL}sprites/${name}.json`).then((r) => {
      if (!r.ok) throw new Error(`sprite ${name}: ${r.status}`);
      return r.json();
    }));
  }
  return sheets.get(name);
}

/** Rows for a pose, optionally mirrored and with the eyes closed. Cached per sheet. */
export function rows(sheet, pose, { flip = false, blink = false } = {}) {
  const key = `${pose}|${+flip}|${+blink}`;
  sheet._rows ||= new Map();
  let r = sheet._rows.get(key);
  if (r) return r;
  r = sheet.poses[pose] ?? Object.values(sheet.poses)[0];
  if (blink && sheet.blink) r = r.map((row) => [...row].map((c) => sheet.blink[c] ?? c).join(""));
  if (flip) r = r.map((row) => [...row].reverse().join(""));
  r = Object.freeze(r);
  sheet._rows.set(key, r);
  return r;
}

/** A 1x canvas of the rows (one canvas pixel per art pixel). */
export function bake(rowsIn, palette) {
  const key = rowsIn.join("|");
  let c = baked.get(key);
  if (c) return c;
  c = document.createElement("canvas");
  c.width = rowsIn[0].length;
  c.height = rowsIn.length;
  const g = c.getContext("2d");
  rowsIn.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      const col = palette[row[x]];
      if (!col) continue;
      g.fillStyle = col;
      g.fillRect(x, y, 1, 1);
    }
  });
  baked.set(key, c);
  return c;
}

/** Every opaque art pixel as {x, y, color}, for particle effects. */
export function cells(rowsIn, palette) {
  const out = [];
  rowsIn.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) if (palette[row[x]]) out.push({ x, y, color: palette[row[x]] });
  });
  return out;
}

/** Draw rows at (x, y) with `cell` screen pixels per art pixel, snapped to device pixels. */
export function draw(ctx, rowsIn, palette, x, y, cell, dpr = 1) {
  const src = bake(rowsIn, palette);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(src, Math.round(x * dpr), Math.round(y * dpr), Math.round(src.width * cell * dpr), Math.round(src.height * cell * dpr));
}

const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * <pixel-sprite sprite="mosquito" pose="fly1" scale="4" flip frames="fly1,fly2" fps="8" label="...">
 * Draws one pose, or loops `frames` at `fps` (a still frame under reduced motion). Blinks every few seconds.
 */
class PixelSprite extends HTMLElement {
  static observedAttributes = ["pose", "scale", "flip", "frames", "fps"];

  connectedCallback() {
    if (!this.canvas) {
      this.canvas = document.createElement("canvas");
      this.canvas.style.imageRendering = "pixelated";
      this.canvas.style.display = "block";
      this.append(this.canvas);
      const label = this.getAttribute("label");
      if (label) { this.setAttribute("role", "img"); this.setAttribute("aria-label", label); } else this.setAttribute("aria-hidden", "true");
    }
    loadSprite(this.getAttribute("sprite") || "mosquito").then((s) => { this.sheet = s; this.render(); this.play(); })
      .catch(() => this.setAttribute("data-missing", ""));
  }

  disconnectedCallback() { cancelAnimationFrame(this.raf); }
  attributeChangedCallback() { if (this.sheet) { this.render(); this.play(); } }

  render(pose = this.getAttribute("pose"), blink = false) {
    const s = this.sheet;
    const scale = Math.max(1, Number(this.getAttribute("scale") || 4));
    const dpr = Math.min(devicePixelRatio || 1, 3);
    const r = rows(s, pose || Object.keys(s.poses)[0], { flip: this.hasAttribute("flip"), blink });
    const [w, h] = [r[0].length, r.length];
    if (this.canvas.width !== Math.round(w * scale * dpr)) {
      this.canvas.width = Math.round(w * scale * dpr);
      this.canvas.height = Math.round(h * scale * dpr);
      this.canvas.style.width = `${w * scale}px`;
      this.canvas.style.height = `${h * scale}px`;
    }
    const g = this.canvas.getContext("2d");
    g.clearRect(0, 0, this.canvas.width, this.canvas.height);
    draw(g, r, s.palette, 0, 0, scale, dpr);
  }

  play() {
    cancelAnimationFrame(this.raf);
    const frames = (this.getAttribute("frames") || "").split(",").map((f) => f.trim()).filter(Boolean);
    if (reduced()) return;
    const fps = Number(this.getAttribute("fps") || 8);
    let nextBlink = performance.now() + 2000 + Math.random() * 3000, last = "";
    const tick = (t) => {
      const pose = frames.length ? frames[Math.floor((t / 1000) * fps) % frames.length] : this.getAttribute("pose");
      const blink = t > nextBlink && t < nextBlink + 140;
      if (t > nextBlink + 140) nextBlink = t + 3000 + Math.random() * 3000;
      const key = `${pose}|${blink}`;
      if (key !== last) { this.render(pose, blink); last = key; }
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }
}

if (!customElements.get("pixel-sprite")) customElements.define("pixel-sprite", PixelSprite);
