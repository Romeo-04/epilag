// 3D pixel ("voxel") maps: one cube per grid cell (site/public/geo/*.json from scripts/voxel_data.py), drawn with a
// single Three.js InstancedMesh, rendered at low resolution and scaled up with image-rendering: pixelated.
// Colour and height come per area (province or region). Renders only when something changes.
// Patterns adapted from Room TBA's Building3DViewer (github.com/uplbtools/room-tba, MIT): lazy-loaded three,
// raycast only when the pointer or camera moved, full disposal. See REDESIGN_PLAN.md section 9.

const SEA = "#BFE2EC";
const LAND = "#C9CFC9";

/** Load a grid file once. `file` is "voxel_ph" or "voxel_regions". */
const files = new Map();
export function loadGrids(file) {
  if (!files.has(file)) files.set(file, fetch(`${import.meta.env.BASE_URL}geo/${file}.json`).then((r) => r.json()));
  return files.get(file);
}

/**
 * Decode a run-length grid into land cells [{x, y, u}], per-area centroids (in cell units) and the unit list.
 * With `markers`, each point area in grid.markers (e.g. Quezon City inside the NCR region) becomes a unit of its
 * own: it takes over its marker cell and the land cells around it (a 3x3 block), so it can be coloured and picked.
 */
export function decode(grid, { markers = false } = {}) {
  const units = [...grid.units];
  const cells = [], at = new Map();
  grid.rows.forEach((row, y) => {
    let x = 0;
    for (let i = 0; i < row.length; i += 2) {
      const u = row[i], n = row[i + 1];
      if (u >= 0) for (let k = 0; k < n; k++) { const c = { x: x + k, y, u }; cells.push(c); at.set(`${x + k},${y}`, c); }
      x += n;
    }
  });
  if (markers) {
    for (const [id, [mx, my]] of Object.entries(grid.markers || {})) {
      const u = units.push(id) - 1;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const c = at.get(`${mx + dx},${my + dy}`); if (c) c.u = u; }
    }
  }
  const sum = units.map(() => [0, 0, 0]);
  for (const c of cells) { sum[c.u][0] += c.x; sum[c.u][1] += c.y; sum[c.u][2]++; }
  const centre = sum.map(([sx, sy, n]) => (n ? [sx / n + 0.5, sy / n + 0.5] : null));
  return { cells, centre, units };
}

const clamp = (v, [lo, hi]) => Math.min(hi, Math.max(lo, v));

function webgl() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch { return false; }
}

/**
 * Mount a voxel map in `el`. Options:
 *   grid        a grid object from loadGrids()
 *   pixel       art-pixel size in screen pixels (render scale is 1 / pixel), default 3
 *   pitch, yaw  camera angles in degrees (default 40, -14)
 *   lift        screen height of one level step, in cells (default 2.5)
 *   markers     also make grid.markers point areas (Quezon City) their own units (see decode)
 *   sea         sea colour (default light blue); top: tallest height to frame, in levels (default 5)
 *   orbit       { yaw: [min, max], pitch: [min, max] }: drag to turn the camera within these bounds
 *   onPick      called with (unitId | null) on click; enables hover too (onHover)
 * Returns { setValues, highlight, project, pickAt, render, dispose, units } plus, for scenes built on top (the Dengue
 * Drill board): three, scene, camera, toScreen(vec3), centreOf(u), heightOf(u), lift, addTicker(fn), setView().
 */
export async function createVoxelMap(el, { grid, pixel = 3, pitch = 40, yaw = -14, zoom = 1, lift = 2.5, markers = false, sea: seaColor = SEA,
  top: topLevel = 5, orbit = null, onPick, onHover } = {}) {
  const { cells, centre, units } = decode(grid, { markers });
  const yaw0 = yaw, pitch0 = pitch;
  const index = new Map(units.map((u, i) => [u, i]));
  const value = units.map(() => ({ color: LAND, height: 1 }));
  if (!webgl()) return flat(el, grid, cells, centre, units, index, value);

  const THREE = await import("three");
  const W = grid.w, H = grid.h;
  const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: "low-power" });
  renderer.setClearColor(0x000000, 0);
  const canvas = renderer.domElement;
  Object.assign(canvas.style, { width: "100%", height: "100%", display: "block", imageRendering: "pixelated" });
  canvas.setAttribute("aria-hidden", "true");
  el.append(canvas);

  const scene = new THREE.Scene();
  // low side light so column walls read darker than tops (the pixel-art 'lit top, shaded side' look)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x51665a, 1.15));
  const sun = new THREE.DirectionalLight(0xffffff, 2.2);
  sun.position.set(-0.55, 0.8, 0.9);
  scene.add(sun);

  // sea: one flat plane under the land
  const sea = new THREE.Mesh( // much larger than the map, so its edges never show
    new THREE.PlaneGeometry(W * 8, H * 8), new THREE.MeshBasicMaterial({ color: seaColor }));
  sea.rotation.x = -Math.PI / 2;
  sea.position.set(W / 2, -0.01, H / 2);
  scene.add(sea);

  // land: one instance per cell; y-scale is the area's height (whole cubes)
  const geo = new THREE.BoxGeometry(1, 1, 1);
  geo.translate(0.5, 0.5, 0.5);
  const mat = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const mesh = new THREE.InstancedMesh(geo, mat, cells.length);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  scene.add(mesh);
  const m4 = new THREE.Matrix4(), col = new THREE.Color();
  const shown = units.map(() => ({ h: 1 })); // current animated heights
  let hot = -1;

  function writeInstances() {
    cells.forEach((c, i) => {
      const h = (shown[c.u].h + (c.u === hot ? 1 : 0)) * lift;
      m4.makeScale(1, Math.max(0.3, h), 1).setPosition(c.x, 0, c.y);
      mesh.setMatrixAt(i, m4);
      col.set(value[c.u].color);
      if (c.u === hot) col.offsetHSL(0, 0, 0.08);
      mesh.setColorAt(i, col);
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.instanceColor.needsUpdate = true;
  }

  // camera: orthographic, looking at the map centre from the south, tilted by `pitch`, turned by `yaw`
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -2000, 2000);
  const target = new THREE.Vector3(W / 2, 0, H / 2);
  function place() {
    const p = THREE.MathUtils.degToRad(pitch), y = THREE.MathUtils.degToRad(yaw);
    const dir = new THREE.Vector3(Math.sin(y) * Math.cos(p), Math.sin(p), Math.cos(y) * Math.cos(p));
    camera.position.copy(target).addScaledVector(dir, 600);
    camera.lookAt(target);
  }
  function fit() {
    const w = el.clientWidth || 1, h = el.clientHeight || 1;
    renderer.setPixelRatio(1 / pixel);
    renderer.setSize(w, h, false);
    // frame the projected footprint of the grid
    const top = lift * topLevel; // tallest column (by default level 4 plus the highlight step)
    const corners = [[0, 0], [W, 0], [0, H], [W, H]].flatMap(([x, z]) => [0, top].map((y) => new THREE.Vector3(x, y, z).applyMatrix4(camera.matrixWorldInverse)));
    const xs = corners.map((v) => v.x), ys = corners.map((v) => v.y);
    const cw = Math.max(...xs) - Math.min(...xs), ch = Math.max(...ys) - Math.min(...ys);
    // centre the frustum on that box (the camera looks at ground level, so tall columns would drift off-centre)
    const midY = (Math.max(...ys) + Math.min(...ys)) / 2, midX = (Math.max(...xs) + Math.min(...xs)) / 2;
    const s = Math.max(cw / w, ch / h) / zoom;
    camera.left = midX - (w / 2) * s; camera.right = midX + (w / 2) * s; camera.top = midY + (h / 2) * s; camera.bottom = midY - (h / 2) * s;
    camera.updateProjectionMatrix();
  }
  place();
  camera.updateMatrixWorld();
  fit();
  writeInstances();

  // render on demand; tweens, camera moves and tickers (scene animations) keep the loop alive until they finish.
  // Tickers pause while the map is off screen.
  let raf = 0, tween = null, view = null, last = 0, onScreen = true;
  const tickers = new Set();
  const render = () => { if (!raf) raf = requestAnimationFrame(frame); };
  function frame(t) {
    raf = 0;
    const dt = Math.min(0.1, last ? (t - last) / 1000 : 0);
    last = t;
    if (tween) {
      const k = Math.min(1, (t - tween.start) / tween.dur), e = 1 - (1 - k) ** 3;
      shown.forEach((s, i) => { s.h = tween.from[i] + (tween.to[i] - tween.from[i]) * e; });
      writeInstances();
      if (k < 1) render(); else tween = null;
    }
    if (view) {
      const k = Math.min(1, (t - view.start) / view.dur), e = 1 - (1 - k) ** 3;
      yaw = view.yaw[0] + (view.yaw[1] - view.yaw[0]) * e; pitch = view.pitch[0] + (view.pitch[1] - view.pitch[0]) * e;
      place(); camera.updateMatrixWorld(); fit();
      if (k < 1) render(); else view = null;
    }
    if (tickers.size && onScreen) { tickers.forEach((fn) => fn(t, dt)); render(); } else if (tickers.size) last = 0;
    renderer.render(scene, camera);
  }
  render();

  const ro = new ResizeObserver(() => { fit(); render(); });
  ro.observe(el);
  const io = new IntersectionObserver(([e]) => { onScreen = e.isIntersecting; if (onScreen) render(); });
  io.observe(el);

  // drag to orbit, within bounds; a drag does not count as a click
  let drag = null, dragged = false;
  const onDown = (e) => { if (!orbit) return; drag = { x: e.clientX, y: e.clientY, yaw, pitch }; dragged = false; canvas.setPointerCapture?.(e.pointerId); };
  const onDrag = (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) dragged = true;
    if (!dragged) return;
    yaw = clamp(drag.yaw - dx * 0.25, orbit.yaw); pitch = clamp(drag.pitch + dy * 0.2, orbit.pitch);
    view = null; place(); camera.updateMatrixWorld(); fit(); render();
  };
  const onUp = () => { drag = null; };
  if (orbit) {
    canvas.style.touchAction = "none";
    canvas.addEventListener("pointerdown", onDown); canvas.addEventListener("pointermove", onDrag); addEventListener("pointerup", onUp);
  }

  // picking: only when the pointer actually moved (Room TBA pattern)
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  function pickAt(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    ndc.set(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObject(mesh, false)[0];
    return hit ? units[cells[hit.instanceId].u] : null;
  }
  const onMove = (e) => { const u = pickAt(e.clientX, e.clientY); canvas.style.cursor = u ? "pointer" : ""; onHover?.(u, e); };
  const onClick = (e) => { if (dragged) { dragged = false; return; } onPick?.(pickAt(e.clientX, e.clientY), e); };
  if (onPick || onHover) { canvas.addEventListener("pointermove", onMove); canvas.addEventListener("click", onClick); }

  return {
    units,
    /** values: {unitId: {color, height}}; heights in whole cubes. Animates over `duration` ms (0 = instant). */
    setValues(values, { duration = 700 } = {}) {
      const from = shown.map((s) => s.h);
      for (const [u, v] of Object.entries(values)) {
        const i = index.get(u);
        if (i == null) continue;
        value[i] = { ...value[i], ...v };
      }
      const to = value.map((v) => v.height ?? 1);
      if (duration && !matchMedia("(prefers-reduced-motion: reduce)").matches) tween = { start: performance.now(), dur: duration, from, to };
      else { shown.forEach((s, i) => { s.h = to[i]; }); }
      writeInstances();
      render();
    },
    /** Raise and brighten one area (null clears). */
    highlight(u) { hot = u == null ? -1 : index.get(u) ?? -1; writeInstances(); render(); },
    /** Screen position (px, relative to el) of an area's centre top, for HTML labels. */
    project(u) {
      const i = index.get(u);
      if (i == null || !centre[i]) return null;
      const v = new THREE.Vector3(centre[i][0], shown[i].h * lift + 0.5, centre[i][1]).project(camera);
      return { x: (v.x + 1) / 2 * el.clientWidth, y: (1 - v.y) / 2 * el.clientHeight };
    },
    pickAt,
    render,
    three: THREE, scene, camera, lift, size: [W, H],
    /** Screen position (px, relative to el) of a world point. */
    toScreen(v) { const p = v.clone().project(camera); return { x: (p.x + 1) / 2 * el.clientWidth, y: (1 - p.y) / 2 * el.clientHeight }; },
    /** An area's centre on the ground (world x, z), and its current column height (world y). */
    centreOf(u) { const i = index.get(u); return i == null || !centre[i] ? null : { x: centre[i][0], z: centre[i][1] }; },
    heightOf(u) { const i = index.get(u); return i == null ? 0 : shown[i].h * lift; },
    /** Cells of an area (grid x, y), e.g. to place things on it. */
    cellsOf(u) { const i = index.get(u); return cells.filter((c) => c.u === i); },
    /** fn(time, dt) runs every frame until the returned function removes it. */
    addTicker(fn) { tickers.add(fn); render(); return () => tickers.delete(fn); },
    /** Animate the camera to { yaw, pitch } (defaults: the starting view). */
    setView({ yaw: y1 = yaw0, pitch: p1 = pitch0 } = {}, { duration = 600 } = {}) {
      view = { start: performance.now(), dur: Math.max(1, matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : duration), yaw: [yaw, y1], pitch: [pitch, p1] };
      render();
    },
    dispose() {
      cancelAnimationFrame(raf); ro.disconnect(); io.disconnect(); tickers.clear();
      canvas.removeEventListener("pointermove", onMove); canvas.removeEventListener("click", onClick);
      canvas.removeEventListener("pointerdown", onDown); canvas.removeEventListener("pointermove", onDrag); removeEventListener("pointerup", onUp);
      geo.dispose(); mat.dispose(); sea.geometry.dispose(); sea.material.dispose(); mesh.dispose();
      renderer.dispose(); canvas.remove();
    },
  };
}

// 2D fallback without WebGL: the same grid drawn top-down as pixels, same API.
function flat(el, grid, cells, centre, units, index, value) {
  const canvas = document.createElement("canvas");
  canvas.width = grid.w; canvas.height = grid.h;
  Object.assign(canvas.style, { width: "100%", height: "100%", objectFit: "contain", imageRendering: "pixelated", background: SEA });
  canvas.setAttribute("aria-hidden", "true");
  el.append(canvas);
  const g = canvas.getContext("2d");
  let hot = -1;
  const draw = () => {
    g.clearRect(0, 0, grid.w, grid.h);
    for (const c of cells) { g.fillStyle = value[c.u].color; g.globalAlpha = hot < 0 || c.u === hot ? 1 : 0.75; g.fillRect(c.x, c.y, 1, 1); }
    g.globalAlpha = 1;
  };
  draw();
  const box = () => {
    const r = el.getBoundingClientRect(), s = Math.min(r.width / grid.w, r.height / grid.h);
    return { s, ox: (r.width - grid.w * s) / 2, oy: (r.height - grid.h * s) / 2, r };
  };
  return {
    units,
    setValues(values) { for (const [u, v] of Object.entries(values)) { const i = index.get(u); if (i != null) value[i] = { ...value[i], ...v }; } draw(); },
    highlight(u) { hot = u == null ? -1 : index.get(u) ?? -1; draw(); },
    project(u) { const i = index.get(u); if (i == null || !centre[i]) return null; const b = box(); return { x: b.ox + centre[i][0] * b.s, y: b.oy + centre[i][1] * b.s }; },
    pickAt(cx, cy) {
      const b = box(), x = Math.floor((cx - b.r.left - b.ox) / b.s), y = Math.floor((cy - b.r.top - b.oy) / b.s);
      const c = cells.find((k) => k.x === x && k.y === y);
      return c ? units[c.u] : null;
    },
    render: draw,
    dispose() { canvas.remove(); },
  };
}
