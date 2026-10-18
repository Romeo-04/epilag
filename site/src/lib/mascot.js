// The mascot that follows the reader: one fixed full-screen canvas, and sections register a slot to stand in.
// When the section at the middle of the viewport changes, the sprite breaks into its own pixels, which fly along
// curved paths and re-form in the new slot and pose. After landing, the slot's target gets a pulsing halo.
// Same idea as getcko.vercel.app's mascot controller (REDESIGN_PLAN.md 3.1), written for plain JS.
import { cells, draw, loadSprite, rows } from "./pixel.js";

const reducedQuery = matchMedia("(prefers-reduced-motion: reduce)");
const easeOut = (t) => 1 - (1 - t) ** 3;
const clamp01 = (t) => Math.min(1, Math.max(0, t));
const bezier = (a, c, b, t) => (1 - t) * (1 - t) * a + 2 * (1 - t) * t * c + t * t * b;

export class Mascot {
  /** Create the overlay canvas for a sprite sheet ("mosquito" or "frog"). */
  static async create(name, { zIndex = 30 } = {}) {
    const m = new Mascot(await loadSprite(name), zIndex);
    m.start();
    return m;
  }

  constructor(sheet, zIndex) {
    this.sheet = sheet;
    this.slots = new Map();
    this.active = null;
    this.particles = [];
    this.sparks = [];
    this.morphing = false;
    this.last = null; // { x, y, cell, rows } of the last drawn sprite
    this.sceneKey = "";
    this.nextBlink = 0;
    this.landedAt = 0;
    this.halo = null;
    this.canvas = Object.assign(document.createElement("canvas"), { ariaHidden: "true" });
    this.canvas.setAttribute("aria-hidden", "true");
    Object.assign(this.canvas.style, { position: "fixed", inset: "0", pointerEvents: "none", zIndex: String(zIndex) });
    document.body.append(this.canvas);
    this.ctx = this.canvas.getContext("2d");
    this.resize = this.resize.bind(this);
    this.frame = this.frame.bind(this);
  }

  /**
   * Register a slot. `section`: the element whose position decides when this slot is active. `slot`: where the
   * sprite stands (centred, feet on the slot's bottom edge; art-pixel size from the slot's --cell, default 4).
   * `pose` or `frames` (+ `fps`): what it shows. `target`: element to halo after landing. Returns an unregister function.
   */
  register({ id, section, slot, pose, frames, fps = 8, flip = false, target = null }) {
    this.slots.set(id, { id, section, slot, pose, frames, fps, flip, target, cell: 0 });
    this.sceneKey = "";
    return () => { this.slots.delete(id); if (this.active?.id === id) this.active = null; };
  }

  setPose(id, pose, frames) {
    const s = this.slots.get(id);
    if (!s) return;
    s.pose = pose;
    s.frames = frames;
    this.sceneKey = "";
  }

  start() {
    this.resize();
    addEventListener("resize", this.resize);
    this.raf = requestAnimationFrame(this.frame);
  }

  destroy() {
    cancelAnimationFrame(this.raf);
    removeEventListener("resize", this.resize);
    this.setHalo(null);
    this.canvas.remove();
  }

  resize() {
    this.dpr = Math.min(devicePixelRatio || 1, 3);
    this.canvas.width = Math.round(innerWidth * this.dpr);
    this.canvas.height = Math.round(innerHeight * this.dpr);
    this.canvas.style.width = `${innerWidth}px`;
    this.canvas.style.height = `${innerHeight}px`;
    this.slots.forEach((s) => { s.cell = 0; });
    this.sceneKey = "";
  }

  pickActive() {
    const mid = innerHeight / 2;
    let best = null, dist = Infinity;
    for (const s of this.slots.values()) {
      const r = s.section.getBoundingClientRect();
      if (!r.height) continue;
      const d = r.top <= mid && r.bottom >= mid ? 0 : Math.min(Math.abs(r.top - mid), Math.abs(r.bottom - mid));
      if (d < dist) { dist = d; best = s; }
    }
    // only show a mascot while its section is at least near the viewport
    return dist < innerHeight * 0.6 ? best : null;
  }

  geom(s) {
    if (!s.cell) s.cell = parseInt(getComputedStyle(s.slot).getPropertyValue("--cell"), 10) || 4;
    const r = s.slot.getBoundingClientRect();
    const [w, h] = this.sheet.size;
    return { x: Math.round(r.left + (r.width - w * s.cell) / 2), y: Math.round(r.bottom - h * s.cell), cell: s.cell };
  }

  poseOf(s, t) {
    if (s.frames?.length && !reducedQuery.matches) return s.frames[Math.floor((t / 1000) * s.fps) % s.frames.length];
    return s.pose || s.frames?.[0] || Object.keys(this.sheet.poses)[0];
  }

  setHalo(el) {
    if (this.halo === el) return;
    this.halo?.removeAttribute("data-halo");
    this.halo = el;
    el?.setAttribute("data-halo", "");
  }

  // the old sprite's pixels (or pixels falling from above, the first time) fly to the new slot
  beginMorph(s, t) {
    this.setHalo(null);
    const target = cells(rows(this.sheet, this.poseOf(s, t), { flip: s.flip }), this.sheet.palette);
    if (reducedQuery.matches) { this.morphing = false; this.landedAt = t; return; }
    const from = this.morphing ? this.particles.map((p) => ({ x: p.x, y: p.y, s: p.s, color: p.color }))
      : this.last ? cells(this.last.rows, this.sheet.palette).map((c) => ({
        x: this.last.x + c.x * this.last.cell, y: this.last.y + c.y * this.last.cell, s: this.last.cell, color: c.color }))
        : null;
    const [, h] = this.sheet.size;
    this.particles = target.map((c, i) => {
      const f = from?.length ? from[i % from.length] : { x: innerWidth * (0.3 + Math.random() * 0.4), y: -20 - Math.random() * 120, s: 3, color: c.color };
      return { fx: f.x, fy: f.y, fs: f.s, x: f.x, y: f.y, s: f.s, color: f.color, toColor: c.color, tx: c.x, ty: c.y,
        cx: (Math.random() - 0.5) * 160, cy: -60 - Math.random() * 90,
        delay: (c.y / h) * 380 + Math.random() * 240, dur: 700 + Math.random() * 380 };
    });
    this.morphStart = t;
    this.morphing = true;
  }

  // the sprite breaks into pixels that drift up and fade (when no slot is active)
  scatter(t) {
    if (!this.last || reducedQuery.matches) return;
    for (const c of cells(this.last.rows, this.sheet.palette)) {
      this.sparks.push({ x: this.last.x + c.x * this.last.cell, y: this.last.y + c.y * this.last.cell, s: this.last.cell,
        color: c.color, vx: (Math.random() - 0.5) * 0.6, vy: -0.2 - Math.random() * 0.5, born: t + Math.random() * 160, life: 520 + Math.random() * 380 });
    }
  }

  frame(t) {
    this.raf = requestAnimationFrame(this.frame);
    const next = this.pickActive();
    if (next !== this.active) {
      if (next) this.beginMorph(next, t);
      else { this.scatter(t); this.particles = []; this.morphing = false; this.setHalo(null); }
      this.active = next;
    }
    const s = this.active, g = s ? this.geom(s) : null;
    const pose = s && !this.morphing ? this.poseOf(s, t) : null;
    if (pose && t > this.nextBlink + 140) this.nextBlink = t + 3000 + Math.random() * 3000;
    const blink = !!pose && !reducedQuery.matches && t > this.nextBlink && t < this.nextBlink + 140;
    const busy = this.morphing || this.sparks.length > 0;
    const key = s ? `${s.id}|${g.x}|${g.y}|${g.cell}|${pose}|${blink}` : "none";
    if (!busy && key === this.sceneKey) {
      if (s && t - this.landedAt > 80) this.setHalo(s.target);
      return;
    }
    this.sceneKey = busy ? "" : key;

    const { ctx, dpr } = this;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (s && this.morphing) {
      let done = true;
      for (const p of this.particles) {
        const k = clamp01((t - this.morphStart - p.delay) / p.dur);
        if (k < 1) done = false;
        const e = easeOut(k), tx = g.x + p.tx * g.cell, ty = g.y + p.ty * g.cell;
        p.x = bezier(p.fx, (p.fx + tx) / 2 + p.cx, tx, e);
        p.y = bezier(p.fy, (p.fy + ty) / 2 + p.cy, ty, e);
        p.s = p.fs + (g.cell - p.fs) * e;
        ctx.fillStyle = k > 0.62 ? p.toColor : p.color;
        ctx.fillRect(Math.round(p.x * dpr), Math.round(p.y * dpr), Math.ceil(p.s * dpr), Math.ceil(p.s * dpr));
      }
      if (done) { this.morphing = false; this.landedAt = t; this.nextBlink = t + 1800; this.sceneKey = ""; }
    } else if (s) {
      const r = rows(this.sheet, pose, { flip: s.flip, blink });
      draw(ctx, r, this.sheet.palette, g.x, g.y, g.cell, dpr);
      this.last = { x: g.x, y: g.y, cell: g.cell, rows: r };
    }
    this.sparks = this.sparks.filter((p) => {
      const age = t - p.born;
      if (age < 0) return true;
      if (age > p.life) return false;
      p.x += p.vx * 2; p.y += p.vy * 2;
      ctx.globalAlpha = 1 - age / p.life;
      ctx.fillStyle = p.color;
      ctx.fillRect(Math.round(p.x * dpr), Math.round(p.y * dpr), Math.ceil(p.s * dpr), Math.ceil(p.s * dpr));
      ctx.globalAlpha = 1;
      return true;
    });
  }
}
