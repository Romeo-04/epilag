// The mascot that follows the reader: one fixed full-screen canvas, and sections register a slot to stand in.
// When the section at the middle of the viewport changes, the sprite flies (whole, wings beating, leaving a short
// pixel trail) from where it was to the new slot, then lands in that slot's pose and hovers. The first time, or
// after it has been eaten, it forms from pixels falling from above. After landing, the slot's target gets a halo.
// Same idea as getcko.vercel.app's mascot controller, written for plain JS.
import { cells, draw, loadSprite, rows } from "./pixel.js";

const reducedQuery = matchMedia("(prefers-reduced-motion: reduce)");
const easeOut = (t) => 1 - (1 - t) ** 3;
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const clamp01 = (t) => Math.min(1, Math.max(0, t));
const bezier = (a, c, b, t) => (1 - t) * (1 - t) * a + 2 * (1 - t) * t * c + t * t * b;
const TRAIL = ["#D5E3DA", "#A8BFB2", "#F5A51C"];

export class Mascot {
  /** Create the overlay canvas for a sprite sheet ("mosquito" or "frog"). */
  static async create(name, { zIndex = 30, travelFrames = ["fly1", "fly2"] } = {}) {
    const m = new Mascot(await loadSprite(name), zIndex, travelFrames);
    m.start();
    return m;
  }

  constructor(sheet, zIndex, travelFrames) {
    this.sheet = sheet;
    this.travelFrames = travelFrames.filter((p) => sheet.poses[p]);
    this.slots = new Map();
    this.active = null;
    this.particles = [];
    this.sparks = [];
    this.morphing = false;
    this.travel = null; // { fx, fy, fcell, start, dur, lift }
    this.last = null; // { x, y, cell, rows } of the last drawn sprite
    this.sceneKey = "";
    this.nextBlink = 0;
    this.landedAt = 0;
    this.halo = null;
    this.canvas = document.createElement("canvas");
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
   * `pose` or `frames` (+ `fps`): what it shows. `flip`: face left (the art faces right); left out, it faces the
   * middle of the screen. `target`: element (or function returning one) to halo after landing.
   * `when`: a function that, while it returns true, makes this slot win over the section test.
   * `onLand(slot)` / `onLeave(slot)`: called when the sprite arrives in / leaves this slot.
   * The returned slot object's `dx`, `dy` (px offset) and `hidden` can be changed (e.g. tweened) while it is active.
   */
  register({ id, section, slot, pose, frames, fps = 8, flip, target = null, when = null, onLand = null, onLeave = null }) {
    const s = { id, section, slot, pose, frames, fps, flip, target, when, onLand, onLeave, cell: 0, dx: 0, dy: 0, hidden: false };
    this.slots.set(id, s);
    this.sceneKey = "";
    return s;
  }

  unregister(id) {
    this.slots.delete(id);
    if (this.active?.id === id) this.active = null;
  }

  setPose(id, pose, frames) {
    const s = this.slots.get(id);
    if (!s) return;
    s.pose = pose;
    s.frames = frames;
    this.sceneKey = "";
  }

  /** Where the sprite of slot `id` is drawn now: top-left in viewport px, and the art-pixel size. */
  box(id) {
    const s = this.slots.get(id);
    return s ? this.geom(s) : null;
  }

  /** Bring a slot's sprite back (from pixels falling from above), e.g. to replay a scene. */
  relaunch(id) {
    const s = this.slots.get(id);
    if (!s) return;
    Object.assign(s, { hidden: false, dx: 0, dy: 0 });
    if (this.active !== s) return;
    this.last = null;
    this.travel = null;
    this.beginMorph(s, performance.now());
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
    for (const s of this.slots.values()) if (s.when?.()) return s;
    const mid = innerHeight / 2;
    let best = null, dist = Infinity;
    for (const s of this.slots.values()) {
      if (s.when) continue;
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
    return { x: Math.round(r.left + (r.width - w * s.cell) / 2 + s.dx), y: Math.round(r.bottom - h * s.cell + s.dy), cell: s.cell,
      flip: s.flip ?? r.left + r.width / 2 > innerWidth / 2 };
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

  switchTo(next, t) {
    const prev = this.active;
    this.setHalo(null);
    this.active = next;
    prev?.onLeave?.(prev);
    if (!next) { this.scatter(t); this.particles = []; this.morphing = false; this.travel = null; return; }
    if (reducedQuery.matches) { this.land(next, t); return; }
    const l = this.last, size = l ? this.sheet.size[1] * l.cell : 0;
    if (l && !this.morphing && l.y > -size && l.y < innerHeight) {
      const g = this.geom(next), d = Math.hypot(g.x - l.x, g.y - l.y);
      this.travel = { fx: l.x, fy: l.y, fcell: l.cell, start: t, dur: Math.min(820, Math.max(380, d * 0.75)), lift: Math.min(140, 30 + d * 0.25) };
    } else {
      this.travel = null;
      this.beginMorph(next, t);
    }
  }

  land(s, t) {
    this.morphing = false;
    this.travel = null;
    this.landedAt = t;
    this.nextBlink = t + 1800;
    this.sceneKey = "";
    s.onLand?.(s);
  }

  // pixels fall from above (or, mid-morph, from where they are) and form the sprite in the slot
  beginMorph(s, t) {
    this.setHalo(null);
    const g = this.geom(s);
    const target = cells(rows(this.sheet, this.poseOf(s, t), { flip: g.flip }), this.sheet.palette);
    if (reducedQuery.matches) { this.land(s, t); return; }
    const from = this.morphing ? this.particles.map((p) => ({ x: p.x, y: p.y, s: p.s, color: p.color })) : null;
    const [, h] = this.sheet.size;
    this.particles = target.map((c, i) => {
      const f = from?.length ? from[i % from.length] : { x: g.x + (Math.random() - 0.3) * 260, y: -20 - Math.random() * 140, s: 3, color: c.color };
      return { fx: f.x, fy: f.y, fs: f.s, x: f.x, y: f.y, s: f.s, color: f.color, toColor: c.color, tx: c.x, ty: c.y,
        cx: (Math.random() - 0.5) * 140, cy: -40 - Math.random() * 70,
        delay: (c.y / h) * 160 + Math.random() * 110, dur: 360 + Math.random() * 200 };
    });
    this.morphStart = t;
    this.morphing = true;
  }

  // the sprite breaks into pixels that drift up and fade (when no slot is active)
  scatter(t) {
    if (!this.last || reducedQuery.matches) return;
    for (const c of cells(this.last.rows, this.sheet.palette)) {
      this.sparks.push({ x: this.last.x + c.x * this.last.cell, y: this.last.y + c.y * this.last.cell, s: this.last.cell,
        color: c.color, vx: (Math.random() - 0.5) * 0.6, vy: -0.2 - Math.random() * 0.5, born: t + Math.random() * 120, life: 420 + Math.random() * 300 });
    }
  }

  frame(t) {
    this.raf = requestAnimationFrame(this.frame);
    const next = this.pickActive();
    if (next !== this.active) this.switchTo(next, t);
    const s = this.active, g = s ? this.geom(s) : null;
    const settled = s && !this.morphing && !this.travel;
    const pose = settled ? this.poseOf(s, t) : null;
    if (pose && t > this.nextBlink + 140) this.nextBlink = t + 3000 + Math.random() * 3000;
    const blink = !!pose && !reducedQuery.matches && t > this.nextBlink && t < this.nextBlink + 140;
    // hover: a one-art-pixel bob, in steps so it stays on the pixel grid
    const bob = settled && !reducedQuery.matches ? Math.round(Math.sin((t - this.landedAt) / 260)) * g.cell : 0;
    const busy = this.morphing || this.travel || this.sparks.length > 0;
    const key = s ? `${s.id}|${g.x}|${g.y + bob}|${g.cell}|${g.flip}|${pose}|${blink}|${s.hidden}` : "none";
    if (!busy && key === this.sceneKey) {
      if (s && !s.hidden && t - this.landedAt > 80) this.setHalo(typeof s.target === "function" ? s.target() : s.target);
      return;
    }
    this.sceneKey = busy ? "" : key;

    const { ctx, dpr } = this;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (s?.hidden) {
      this.last = null;
    } else if (s && this.morphing) {
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
      if (done) this.land(s, t);
    } else if (s && this.travel) {
      const tr = this.travel, k = clamp01((t - tr.start) / tr.dur), e = easeInOut(k);
      const cell = Math.max(1, Math.round(tr.fcell + (g.cell - tr.fcell) * e));
      // an arc above the straight line, plus a small buzz across it
      const x = bezier(tr.fx, (tr.fx + g.x) / 2, g.x, e);
      const y = bezier(tr.fy, Math.min(tr.fy, g.y) - tr.lift, g.y, e) + Math.round(Math.sin(k * Math.PI * 6) * 6 * (1 - k));
      const flip = g.x < tr.fx;
      const fr = this.travelFrames.length ? this.travelFrames[Math.floor(t / 70) % this.travelFrames.length] : this.poseOf(s, t);
      const r = rows(this.sheet, fr, { flip });
      draw(ctx, r, this.sheet.palette, x, y, cell, dpr);
      this.last = { x, y, cell, rows: r };
      // a short trail of pixels behind the tail
      const [w, h] = this.sheet.size;
      this.sparks.push({ x: x + (flip ? w * cell * 0.8 : w * cell * 0.15), y: y + h * cell * (0.4 + Math.random() * 0.3), s: Math.max(2, cell - 1),
        color: TRAIL[Math.floor(Math.random() * TRAIL.length)], vx: (Math.random() - 0.5) * 0.4, vy: 0.15 + Math.random() * 0.3, born: t, life: 260 + Math.random() * 160 });
      if (k >= 1) this.land(s, t);
    } else if (s) {
      const r = rows(this.sheet, pose, { flip: g.flip, blink });
      draw(ctx, r, this.sheet.palette, g.x, g.y + bob, g.cell, dpr);
      this.last = { x: g.x, y: g.y + bob, cell: g.cell, rows: r };
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
