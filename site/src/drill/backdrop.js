// The backdrop behind every screen but the board: a situation-room display drawn as pixel art from the game's own data.
//   the Philippines, province by province, with the mission's region lit in the heat colours of its busiest week;
//   along the bottom, the season's weekly rain as bars and reported cases as a line against the epidemic line.
// Before a round the cases line stops at the first turn (the rest of the season is not known yet); on the report
// and the debrief it is drawn in full. The rain arrives first and the cases follow, which is the study's subject.
// Drawn small and scaled up without smoothing, like the rest of the game's art.

const INK = { land: "#1A2859", land2: "#1F3068", coast: "#2E3F7A", grid: "rgba(46, 63, 122, .22)", rain: "rgba(47, 214, 195, .30)", rainLit: "rgba(47, 214, 195, .62)",
  cases: "#F5A51C", over: "#F04B2A", epi: "rgba(240, 75, 42, .55)", unknown: "rgba(163, 176, 219, .28)", drop: "rgba(127, 228, 255, .30)" };
const still = () => document.documentElement.dataset.motion === "less" || matchMedia("(prefers-reduced-motion: reduce)").matches;

/** grid: the national province grid (run-length rows of unit indexes, -1 for sea). */
export function createBackdrop(canvas, grid) {
  const g = canvas.getContext("2d"), base = document.createElement("canvas"), b = base.getContext("2d");
  // land cells once: [x, y, unit index, on the coast?]
  const at = new Map(), cells = [];
  grid.rows.forEach((row, y) => {
    let x = 0;
    for (let i = 0; i < row.length; i += 2) { if (row[i] >= 0) for (let k = 0; k < row[i + 1]; k++) at.set(`${x + k},${y}`, row[i]); x += row[i + 1]; }
  });
  for (const [key, u] of at) {
    const [x, y] = key.split(",").map(Number);
    cells.push([x, y, u, !at.has(`${x - 1},${y}`) || !at.has(`${x + 1},${y}`) || !at.has(`${x},${y - 1}`) || !at.has(`${x},${y + 1}`)]);
  }
  let W = 0, H = 0, scene = null, on = true, raf = 0, last = 0, drops = [], map = null, chart = null;

  function size() {
    W = innerWidth >= 900 ? 480 : 240; H = Math.max(120, Math.round((W * innerHeight) / innerWidth));
    canvas.width = base.width = W; canvas.height = base.height = H;
    drops = Array.from({ length: Math.round((W * H) / 2600) }, () => ({ x: Math.random() * W, y: Math.random() * H, v: 60 + Math.random() * 70 }));
    paint();
  }

  /** Everything that does not move, drawn once into `base`. */
  function paint() {
    if (!scene || !W) return;
    const { lit, heat, pin, rain, cases, epi, known } = scene;
    for (let y = 0; y < H; y++) { const k = y / H; b.fillStyle = `rgb(${Math.round(9 + 8 * k)}, ${Math.round(17 + 11 * k)}, ${Math.round(40 + 28 * k)})`; b.fillRect(0, y, W, 1); }
    b.fillStyle = INK.grid;
    for (let x = 0; x < W; x += 24) b.fillRect(x, 0, 1, H);
    for (let y = 0; y < H; y += 24) b.fillRect(0, y, W, 1);
    // the map: on the right on a wide screen, centred on a phone; scaled down by whole cells if the screen is short
    const skip = grid.h > H * 0.94 ? 2 : 1, mw = Math.ceil(grid.w / skip), mh = Math.ceil(grid.h / skip);
    const mx = W >= 480 ? Math.round(W * 0.71 - mw / 2) : Math.round((W - mw) / 2), my = Math.round((H - mh) / 2);
    map = { x: mx, y: my, w: mw, h: mh };
    for (const [x, y, u, coast] of cells) {
      if (x % skip || y % skip) continue;
      const id = grid.units[u], hot = lit(id);
      b.fillStyle = hot ? heat(id) : coast ? INK.coast : (x + y) % 2 ? INK.land : INK.land2;
      b.globalAlpha = hot ? 1 : W >= 480 ? 0.9 : 0.6;
      b.fillRect(mx + x / skip, my + y / skip, 1, 1);
    }
    b.globalAlpha = 1;
    if (pin) map.pin = [mx + Math.round(pin[0] / skip), my + Math.round(pin[1] / skip)];
    // the season along the bottom: rain bars, the epidemic line, and cases as far as they are known
    const n = rain.length, x0 = 10, cw = W - 20, bh = Math.round(H * 0.16), y0 = H - 6, step = cw / n;
    const rmax = Math.max(1, ...rain), cmax = Math.max(1, ...cases.slice(0, known + 1), ...epi) * 1.1;
    const X = (i) => Math.round(x0 + i * step), Y = (v) => y0 - Math.round(Math.min(1, v / cmax) * bh);
    for (let i = 0; i < n; i++) { const h = Math.round((rain[i] / rmax) * bh * 0.85); b.fillStyle = INK.rain; b.fillRect(X(i), y0 - h, Math.max(1, Math.floor(step) - 1), h); }
    b.fillStyle = INK.epi;
    for (let i = 0; i < n; i++) for (let x = X(i); x < X(i + 1); x += 3) b.fillRect(x, Y(epi[i]), 2, 1);
    for (let i = 0; i < n; i++) {
      if (i > known) { b.fillStyle = INK.unknown; if (i % 2) b.fillRect(X(i), y0 - Math.round(bh * 0.5), 1, 1); continue; }
      b.fillStyle = cases[i] > epi[i] ? INK.over : INK.cases;
      b.fillRect(X(i), Y(cases[i]), X(i + 1) - X(i), 2);
      if (i < known) { const a = Y(cases[i]), c = Y(cases[i + 1]); b.fillRect(X(i + 1), Math.min(a, c), 1, Math.abs(a - c) + 2); } // the step up or down to the next week
    }
    chart = { X, y0, bh, n, rain, rmax, step };
    frame(performance.now(), true);
  }

  function frame(t, once = false) {
    if (!once) raf = 0;
    if (!on || !scene) return;
    if (!once && t - last < 66) { raf = requestAnimationFrame(frame); return; } // about 15 frames a second is plenty
    const dt = Math.min(0.2, (t - last) / 1000); last = t;
    g.drawImage(base, 0, 0);
    if (!still()) {
      // rain drifting down, a scan line passing over the map, and the week in view moving along the season
      g.fillStyle = INK.drop;
      for (const d of drops) { d.y += d.v * dt; d.x -= d.v * dt * 0.25; if (d.y > H) { d.y = -4; d.x = Math.random() * W; } g.fillRect(Math.round(d.x), Math.round(d.y), 1, 3); }
      const sy = map.y + ((t / 5200) % 1) * map.h;
      g.fillStyle = "rgba(47, 214, 195, .16)"; g.fillRect(map.x - 4, Math.round(sy), map.w + 8, 2);
      const i = Math.floor((t / 420) % chart.n), h = Math.round((chart.rain[i] / chart.rmax) * chart.bh * 0.85);
      g.fillStyle = INK.rainLit; g.fillRect(chart.X(i), chart.y0 - h, Math.max(1, Math.floor(chart.step) - 1), h);
    }
    if (map.pin && (still() || Math.floor(t / 500) % 2)) { g.fillStyle = "#7FE4FF"; g.fillRect(map.pin[0] - 1, map.pin[1] - 1, 3, 3); }
    if (!once && !still()) raf = requestAnimationFrame(frame);
  }
  const wake = () => { if (on && !raf && !document.hidden) { last = performance.now(); raf = requestAnimationFrame(frame); } };
  addEventListener("resize", size);
  document.addEventListener("visibilitychange", wake);
  size();

  return {
    /** scene: { lit(provinceId) -> bool, heat(provinceId) -> colour, pin: [x, y] | null, rain[], cases[], epi[], known: last week shown } */
    set(s) { scene = s; paint(); wake(); },
    /** Shown on every screen but the board. */
    show(v) { on = v; canvas.parentElement.hidden = !v; if (v) { frame(performance.now(), true); wake(); } else { cancelAnimationFrame(raf); raf = 0; } },
    /** The motion setting changed. */
    refresh() { if (on) { frame(performance.now(), true); wake(); } },
  };
}
