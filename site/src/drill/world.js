// The Dengue Drill's 3D world: the region as a floating pixel diorama. Land cells get relief (higher inland, gentle
// hills) and each province swells into a mound whose height shows cases against the epidemic line; borders between
// provinces are darker, coasts sandier. Around it: animated pixel water with foam, a layered soil base, drifting voxel
// clouds that cast shadows, rain with splashes and lightning. The camera orbits (drag), pans (right-drag, shift-drag
// or two fingers) and zooms (wheel, pinch or the buttons) within bounds. Rendered at low resolution, scaled up
// with image-rendering: pixelated, like the other voxel maps (src/lib/voxel.js, whose grid decoder it reuses).
import { decode } from "../lib/voxel.js";

const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const hash = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
function vnoise(x, y) { // smooth value noise
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
const PAD = 7; // water around the land, in cells

export async function createWorld(el, { grid, pixel = 2, lift = 1.35, onPick, onHover, onFlash }) {
  const THREE = await import("three");
  const { cells, centre, units } = decode(grid);
  const W = grid.w, H = grid.h, index = new Map(units.map((u, i) => [u, i]));
  const at = new Map(cells.map((c, i) => [`${c.x},${c.y}`, i]));
  const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];

  // ------------------------------------------------------------------ terrain: distances to the coast and to borders
  const bfs = (isEdge) => {
    const d = new Array(cells.length).fill(Infinity), q = [];
    cells.forEach((c, i) => { if (isEdge(c)) { d[i] = 0; q.push(i); } });
    for (let h = 0; h < q.length; h++) {
      const c = cells[q[h]];
      for (const [dx, dy] of N4) {
        const j = at.get(`${c.x + dx},${c.y + dy}`);
        if (j != null && d[j] > d[q[h]] + 1) { d[j] = d[q[h]] + 1; q.push(j); }
      }
    }
    return d;
  };
  const coast = bfs((c) => N4.some(([dx, dy]) => !at.has(`${c.x + dx},${c.y + dy}`)));
  const inner = bfs((c) => N4.some(([dx, dy]) => { const j = at.get(`${c.x + dx},${c.y + dy}`); return j == null || cells[j].u !== c.u; }));
  const border = cells.map((c) => N4.some(([dx, dy]) => { const j = at.get(`${c.x + dx},${c.y + dy}`); return j != null && cells[j].u !== c.u; }));
  const ground = cells.map((c, i) => 0.3 + Math.min(coast[i], 12) * 0.045 + vnoise(c.x / 7, c.y / 7) * 0.45); // in levels
  const swell = cells.map((c, i) => 0.35 + 0.65 * Math.min(1, (inner[i] + 1) / 5)); // a province is a mound, not a block
  const jitter = cells.map((c) => (hash(c.x * 3.1, c.y * 1.7) - 0.5) * 0.07);

  // ------------------------------------------------------------------ renderer, scene, lights
  const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: "high-performance" });
  renderer.setClearColor(0x000000, 0);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.BasicShadowMap; // hard pixel shadows
  const canvas = renderer.domElement;
  Object.assign(canvas.style, { width: "100%", height: "100%", display: "block", imageRendering: "pixelated", touchAction: "none" });
  canvas.setAttribute("aria-hidden", "true");
  el.append(canvas);
  const scene = new THREE.Scene();
  const hemi = new THREE.HemisphereLight(0xEAF6FF, 0x3B4A3A, 1.1);
  const sun = new THREE.DirectionalLight(0xFFF1D6, 2.4);
  const bx0 = -PAD, bx1 = W + PAD, bz0 = -PAD, bz1 = H + PAD, cx = W / 2, cz = H / 2;
  sun.position.set(cx - 40, 70, cz + 50);
  sun.target.position.set(cx, 0, cz);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -(W + 2 * PAD), right: W + 2 * PAD, top: H + 2 * PAD, bottom: -(H + 2 * PAD), near: 1, far: 260 });
  sun.shadow.bias = -0.002;
  scene.add(hemi, sun, sun.target);

  const box = new THREE.BoxGeometry(1, 1, 1);
  box.translate(0.5, 0.5, 0.5);
  const m4 = new THREE.Matrix4(), col = new THREE.Color(), tmp = new THREE.Color();

  // ------------------------------------------------------------------ the base: soil and rock under the island
  const soil = new THREE.Mesh(new THREE.BoxGeometry(bx1 - bx0, 2, bz1 - bz0), new THREE.MeshLambertMaterial({ color: 0x6B4A2E }));
  soil.position.set(cx, -1.6, cz);
  const rock = new THREE.Mesh(new THREE.BoxGeometry(bx1 - bx0, 5, bz1 - bz0), new THREE.MeshLambertMaterial({ color: 0x3A3631 }));
  rock.position.set(cx, -5.1, cz);
  soil.receiveShadow = true;
  scene.add(soil, rock);

  // ------------------------------------------------------------------ water: pixel cells that bob, foam at the coast
  const water = [];
  const nearLand = (x, y, r) => { for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) if (at.has(`${x + dx},${y + dy}`)) return true; return false; };
  for (let y = bz0; y < bz1; y++) for (let x = bx0; x < bx1; x++) {
    if (at.has(`${x},${y}`)) continue;
    water.push({ x, y, foam: nearLand(x, y, 1), shallow: nearLand(x, y, 3), ph: hash(x, y) * 6.28 });
  }
  const waterMesh = new THREE.InstancedMesh(box, new THREE.MeshLambertMaterial({ color: 0xffffff }), water.length);
  waterMesh.receiveShadow = true;
  scene.add(waterMesh);
  function writeWater(t) {
    const k = Math.floor(t / 140); // stepped, so the water moves like pixel art
    water.forEach((w, i) => {
      const y = Math.round((Math.sin(k * 0.35 + w.x * 0.45 + w.y * 0.3 + w.ph * 0.2) * 0.18) * 4) / 4;
      m4.makeScale(1, 0.6, 1).setPosition(w.x, -0.75 + y, w.y);
      waterMesh.setMatrixAt(i, m4);
      const foam = w.foam && (Math.sin(k * 0.6 + w.ph) > 0.1);
      col.set(foam ? 0xCFEFEA : w.shallow ? 0x2B8C92 : 0x16566A);
      if (!foam) col.offsetHSL(0, 0, (hash(w.x + k % 5, w.y) - 0.5) * 0.03);
      waterMesh.setColorAt(i, col);
    });
    waterMesh.instanceMatrix.needsUpdate = true;
    waterMesh.instanceColor.needsUpdate = true;
  }

  // ------------------------------------------------------------------ land
  const land = new THREE.InstancedMesh(box, new THREE.MeshLambertMaterial({ color: 0xffffff }), cells.length);
  land.castShadow = true; land.receiveShadow = true;
  scene.add(land);
  const value = units.map(() => ({ color: "#2E6B3F", height: 1 }));
  const shown = units.map(() => ({ h: 1 }));
  let hot = -1, glow = new Set(), glowK = 0;
  const topOf = (i) => (ground[i] + shown[cells[i].u].h * swell[i] + (cells[i].u === hot ? 0.5 : 0)) * lift;
  const tops = units.map(() => 0); // highest cell of each area, refreshed with every frame
  function writeLand() {
    tops.fill(0);
    cells.forEach((c, i) => {
      const top = topOf(i);
      if (top > tops[c.u]) tops[c.u] = top;
      m4.makeScale(1, top + 0.75, 1).setPosition(c.x, -0.75, c.y);
      land.setMatrixAt(i, m4);
      col.set(value[c.u].color);
      if (coast[i] === 0) col.lerp(tmp.set(0xD9C48A), 0.35); // sandy coast
      col.offsetHSL(0, 0, jitter[i] + (border[i] ? -0.12 : 0) + (c.u === hot ? 0.1 : 0) + (glow.has(c.u) ? glowK : 0));
      land.setColorAt(i, col);
    });
    land.instanceMatrix.needsUpdate = true;
    land.instanceColor.needsUpdate = true;
  }

  // ------------------------------------------------------------------ clouds
  const CLOUDS = 6, puffs = [];
  const clouds = Array.from({ length: CLOUDS }, (_, k) => {
    const n = 14 + Math.floor(hash(k, 9) * 16), parts = [];
    for (let j = 0; j < n; j++) parts.push([Math.round((hash(k, j) - 0.5) * 9), Math.round(hash(j, k) * 2), Math.round((hash(k + 3, j) - 0.5) * 5)]);
    return { x: bx0 + hash(k, 1) * (bx1 - bx0), z: bz0 + hash(k, 2) * (bz1 - bz0), y: 34 + hash(k, 3) * 6, parts };
  });
  clouds.forEach((c) => c.parts.forEach(() => puffs.push(c)));
  const cloudMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1.8, 1.3, 1.8), new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.55, depthWrite: false }), puffs.length);
  cloudMesh.castShadow = true;
  scene.add(cloudMesh);
  let cloudTint = 0; // 0 white .. 1 storm grey
  function writeClouds(dt) {
    let k = 0;
    clouds.forEach((c) => {
      c.x += dt * (1.2 + cloudTint * 1.4);
      if (c.x > bx1 + 10) c.x = bx0 - 10;
      c.parts.forEach(([px, py, pz]) => {
        m4.makeTranslation(c.x + px * 1.6, c.y + py * 1.2, c.z + pz * 1.6);
        cloudMesh.setMatrixAt(k, m4);
        col.set(0xF4F7F2).lerp(tmp.set(0x6E7C78), cloudTint * (0.7 + py * 0.1));
        cloudMesh.setColorAt(k++, col);
      });
    });
    cloudMesh.instanceMatrix.needsUpdate = true;
    cloudMesh.instanceColor.needsUpdate = true;
  }

  // ------------------------------------------------------------------ rain and splashes
  const DROPS = 650, SPL = 150;
  const rainMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.28, 2.6, 0.28), new THREE.MeshBasicMaterial({ color: 0xCFE9F0, transparent: true, opacity: 0.55, depthWrite: false }), DROPS);
  const splashMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.3, 0.2, 0.3), new THREE.MeshBasicMaterial({ color: 0x9FD3E0, transparent: true, opacity: 0.7, depthWrite: false }), SPL);
  rainMesh.visible = splashMesh.visible = false; // until the first rain frame places the drops
  scene.add(rainMesh, splashMesh);
  const drops = Array.from({ length: DROPS }, () => ({ x: 0, y: -99, z: 0, v: 0, on: false }));
  const splashes = Array.from({ length: SPL }, () => ({ x: 0, y: -99, z: 0, age: 9 }));
  let splashAt = 0, rain = 0, storm = false, nextBolt = 0, flash = 0;
  const surface = (x, z) => { const i = at.get(`${Math.floor(x)},${Math.floor(z)}`); return i == null ? -0.2 : topOf(i) - 0.75 + 0.75; };
  const tilt = new THREE.Matrix4().makeRotationZ(0.18);
  function writeRain(dt, t) {
    const active = Math.round(DROPS * rain);
    drops.forEach((d, i) => {
      if (d.y < -50 && i < active) { // respawn under a cloud-ish height
        Object.assign(d, { x: bx0 + Math.random() * (bx1 - bx0), z: bz0 + Math.random() * (bz1 - bz0), y: 18 + Math.random() * 16, v: 34 + Math.random() * 18, on: true });
      }
      if (d.y > -50) {
        d.y -= d.v * dt; d.x += d.v * dt * 0.18;
        const s = surface(d.x, d.z);
        if (d.y <= s) {
          if (i % 3 === 0) { const sp = splashes[splashAt++ % SPL]; Object.assign(sp, { x: d.x, y: s + 0.1, z: d.z, age: 0 }); }
          d.y = i < active ? 22 + Math.random() * 14 : -99;
          if (i < active) { d.x = bx0 + Math.random() * (bx1 - bx0); d.z = bz0 + Math.random() * (bz1 - bz0); }
        }
      }
      m4.makeTranslation(d.x, d.y, d.z).multiply(tilt);
      if (d.y < -50) m4.makeScale(0, 0, 0);
      rainMesh.setMatrixAt(i, m4);
    });
    splashes.forEach((sp, i) => {
      sp.age += dt;
      const k = sp.age / 0.22;
      if (k >= 1) m4.makeScale(0, 0, 0);
      else m4.makeScale(1 + k * 1.6, 1 - k, 1 + k * 1.6).setPosition(sp.x, sp.y + k * 0.4, sp.z);
      splashMesh.setMatrixAt(i, m4);
    });
    rainMesh.instanceMatrix.needsUpdate = true;
    splashMesh.instanceMatrix.needsUpdate = true;
    rainMesh.visible = splashMesh.visible = rain > 0 || drops.some((d) => d.y > -50);
    // lightning in a storm: two quick flashes, then thunder (the page plays it via onFlash)
    if (storm && t > nextBolt) { nextBolt = t + 4000 + Math.random() * 6000; flash = 1; onFlash?.(); }
    flash = Math.max(0, flash - dt * 4);
    const pulse = flash > 0.5 || (flash > 0.1 && flash < 0.3) ? 1 : 0;
    hemi.intensity = (1.1 - rain * 0.45) + pulse * 2.2;
    sun.intensity = 2.4 - rain * 1.5;
  }

  // ------------------------------------------------------------------ camera: orbit, pan, zoom
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -2000, 2000);
  const home = { yaw: -16, pitch: 48, zoom: 1.12, tx: cx, tz: cz };
  const cam = { ...home };
  function place() {
    const p = THREE.MathUtils.degToRad(cam.pitch), y = THREE.MathUtils.degToRad(cam.yaw);
    const target = new THREE.Vector3(cam.tx, 0, cam.tz);
    camera.position.copy(target).addScaledVector(new THREE.Vector3(Math.sin(y) * Math.cos(p), Math.sin(p), Math.cos(y) * Math.cos(p)), 600);
    camera.lookAt(target);
    camera.updateMatrixWorld();
    const w = el.clientWidth || 1, h = el.clientHeight || 1;
    const corners = [[bx0, bz0], [bx1, bz0], [bx0, bz1], [bx1, bz1]].flatMap(([x, z]) => [-6, 14].map((yy) => new THREE.Vector3(x, yy, z).applyMatrix4(camera.matrixWorldInverse)));
    const xs = corners.map((v) => v.x), ys = corners.map((v) => v.y);
    const s = Math.max((Math.max(...xs) - Math.min(...xs)) / w, (Math.max(...ys) - Math.min(...ys)) / h) * 1.04;
    const mx = (Math.max(...xs) + Math.min(...xs)) / 2, my = (Math.max(...ys) + Math.min(...ys)) / 2;
    Object.assign(camera, { left: mx - (w / 2) * s, right: mx + (w / 2) * s, top: my + (h / 2) * s, bottom: my - (h / 2) * s, zoom: cam.zoom });
    camera.updateProjectionMatrix();
  }
  function size() {
    renderer.setPixelRatio(1 / pixel);
    renderer.setSize(el.clientWidth || 1, el.clientHeight || 1, false);
    place();
  }
  size();

  // ------------------------------------------------------------------ the frame loop (paused off screen)
  let raf = 0, last = 0, onScreen = true, tween = null, view = null, spin = 0;
  const tickers = new Set();
  const render = () => { if (!raf) raf = requestAnimationFrame(frame); };
  function frame(t) {
    raf = 0;
    const dt = Math.min(0.1, last ? (t - last) / 1000 : 0);
    last = t;
    if (tween) {
      const k = Math.min(1, (t - tween.start) / tween.dur), e = 1 - (1 - k) ** 3;
      shown.forEach((s, i) => { s.h = tween.from[i] + (tween.to[i] - tween.from[i]) * e; });
      if (k >= 1) tween = null;
    }
    if (view) {
      const k = Math.min(1, (t - view.start) / view.dur), e = 1 - (1 - k) ** 3;
      for (const key of Object.keys(view.to)) cam[key] = view.from[key] + (view.to[key] - view.from[key]) * e;
      place();
      if (k >= 1) view = null;
    }
    const still = reduced();
    if (spin && !still && !view && !drag) { // the title screen's slow turn, back and forth
      cam.yaw += spin * dt * 7;
      if (cam.yaw > 30 || cam.yaw < -60) spin = -spin;
      place();
    }
    glowK = glow.size && !still ? Math.round((Math.sin(t / 260) * 0.5 + 0.5) * 3) * 0.04 : 0;
    writeLand();
    if (!still) { writeWater(t); writeClouds(dt); writeRain(dt, t); }
    tickers.forEach((fn) => fn(t, dt));
    renderer.render(scene, camera);
    if (onScreen && (!still || tween || view)) render();
  }
  if (reduced()) { writeWater(0); writeClouds(0); }
  render();
  const ro = new ResizeObserver(() => { size(); render(); });
  ro.observe(el);
  const io = new IntersectionObserver(([e]) => { onScreen = e.isIntersecting; if (onScreen) { last = 0; render(); } });
  io.observe(el);

  // ------------------------------------------------------------------ input: picking, orbit, pan, zoom
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  function pickAt(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    ndc.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObject(land, false)[0];
    return hit ? units[cells[hit.instanceId].u] : null;
  }
  /** World point on the ground plane under a screen point. */
  function groundAt(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    ndc.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const o = ray.ray.origin, d = ray.ray.direction, k = -o.y / d.y;
    return { x: o.x + d.x * k, z: o.z + d.z * k };
  }
  const bound = () => { cam.tx = clamp(cam.tx, 0, W); cam.tz = clamp(cam.tz, 0, H); };
  function zoomAt(factor, clientX, clientY) {
    const before = clientX == null ? null : groundAt(clientX, clientY);
    cam.zoom = clamp(cam.zoom * factor, 1, 5);
    view = null;
    place();
    if (before) { const after = groundAt(clientX, clientY); cam.tx += before.x - after.x; cam.tz += before.z - after.z; bound(); place(); }
    render();
  }
  const pointers = new Map();
  let drag = null, dragged = false;
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  canvas.addEventListener("pointerdown", (e) => {
    canvas.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    dragged = false;
    drag = { x: e.clientX, y: e.clientY, mode: e.button === 2 || e.shiftKey ? "pan" : "orbit", cam: { ...cam }, g: groundAt(e.clientX, e.clientY) };
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      drag = { mode: "pinch", dist: Math.hypot(a.x - b.x, a.y - b.y), mid: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }, cam: { ...cam } };
    }
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag) {
      const u = pickAt(e.clientX, e.clientY);
      canvas.style.cursor = u ? "pointer" : "grab";
      onHover?.(u, e);
      return;
    }
    if (pointers.has(e.pointerId)) pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const dx = e.clientX - (drag.x ?? 0), dy = e.clientY - (drag.y ?? 0);
    if (drag.mode !== "pinch" && Math.abs(dx) + Math.abs(dy) < 5 && !dragged) return;
    dragged = true;
    view = null;
    if (drag.mode === "orbit") {
      cam.yaw = clamp(drag.cam.yaw - dx * 0.3, -70, 40); cam.pitch = clamp(drag.cam.pitch + dy * 0.22, 24, 80);
    } else if (drag.mode === "pan") {
      Object.assign(cam, { tx: drag.cam.tx, tz: drag.cam.tz }); place();
      const g = groundAt(e.clientX, e.clientY);
      cam.tx += drag.g.x - g.x; cam.tz += drag.g.z - g.z; bound();
    } else if (pointers.size === 2) {
      const [a, b] = [...pointers.values()], dist = Math.hypot(a.x - b.x, a.y - b.y);
      cam.zoom = clamp(drag.cam.zoom * (dist / drag.dist), 1, 5);
    }
    place(); render();
  });
  const up = (e) => { pointers.delete(e.pointerId); if (!pointers.size) drag = null; };
  canvas.addEventListener("pointerup", up);
  canvas.addEventListener("pointercancel", up);
  canvas.addEventListener("click", (e) => { if (dragged) { dragged = false; return; } onPick?.(pickAt(e.clientX, e.clientY), e); });
  canvas.addEventListener("wheel", (e) => { e.preventDefault(); zoomAt(Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY); }, { passive: false });

  return {
    three: THREE, scene, camera, units, lift, size: [W, H],
    toScreen(v) { const p = v.clone().project(camera); return { x: ((p.x + 1) / 2) * el.clientWidth, y: ((1 - p.y) / 2) * el.clientHeight }; },
    centreOf(u) { const i = index.get(u); return i == null || !centre[i] ? null : { x: centre[i][0], z: centre[i][1] }; },
    /** The top of an area's mound (world y), at its highest cell. */
    heightOf(u) { const i = index.get(u); return i == null ? 0 : tops[i]; },
    cellsOf(u) { const i = index.get(u); return cells.filter((c) => c.u === i); },
    /** values: {unitId: {color, height (levels)}}; animated over `duration` ms. */
    setValues(values, { duration = 900 } = {}) {
      const from = shown.map((s) => s.h);
      for (const [u, v] of Object.entries(values)) { const i = index.get(u); if (i != null) value[i] = { ...value[i], ...v }; }
      const to = value.map((v) => v.height ?? 1);
      if (duration && !reduced()) tween = { start: performance.now(), dur: duration, from, to };
      else shown.forEach((s, i) => { s.h = to[i]; });
      render();
    },
    highlight(u) { hot = u == null ? -1 : index.get(u) ?? -1; render(); },
    /** Areas whose tops pulse (outbreaks). */
    setGlow(list) { glow = new Set(list.map((u) => index.get(u)).filter((i) => i != null)); render(); },
    /** rain 0..1 (share of the drops falling), storm adds lightning; clouds darken with rain. */
    setWeather({ rain: r = 0, storm: s = false } = {}) { rain = clamp(r, 0, 1); storm = s; cloudTint = clamp(r * 1.3, 0, 1); if (!reduced()) nextBolt = performance.now() + 1500; render(); },
    zoomBy(f) { zoomAt(f); },
    /** Turn slowly on its own (the title screen), until the reader drags. */
    spin(on = true) { spin = on ? 1 : 0; render(); },
    rotateBy(deg) { view = { start: performance.now(), dur: 400, from: { ...cam }, to: { yaw: clamp(cam.yaw + deg, -70, 40) } }; render(); },
    resetView() { view = { start: performance.now(), dur: reduced() ? 1 : 700, from: { ...cam }, to: { ...home } }; render(); },
    addTicker(fn) { tickers.add(fn); render(); return () => tickers.delete(fn); },
    render,
    dispose() {
      cancelAnimationFrame(raf); ro.disconnect(); io.disconnect(); tickers.clear();
      scene.traverse((o) => { o.geometry?.dispose(); o.material?.dispose?.(); });
      box.dispose(); renderer.dispose(); canvas.remove();
    },
  };
}
