// Drill-down forecast map: Philippines -> region -> province or Quezon City -> barangay.
// Areas are 3D blocks (Three.js ExtrudeGeometry) whose height and colour come from the view. A click flies the
// camera to the area along a smooth zoom-out/pan/zoom-in path (van Wijk & Nuij, as in d3.interpolateZoom), the
// areas around it sink and turn grey, and the next level rises out of the ground. Labels, outlines, the pulse and
// the minimap are drawn in screen space on an SVG overlay. Without WebGL the same camera draws a flat 2D canvas.
// Like the voxel maps (voxel.js) it renders at low resolution and scales up with image-rendering: pixelated, and the
// outlines, labels and pulse snap to the same art-pixel grid, so it matches the site's pixel look.
// Boundaries: site/public/geo/drill.json from scripts/drill_map/build.py (PSA PSGC shapefiles, faeldon/philippines-json-maps, MIT).

const SVGNS = "http://www.w3.org/2000/svg";
const PITCH = { country: 36, region: 44, province: 44, city: 48, barangay: 46 };
const LVH = { normal: 1, above: 2, watch: 3, warning: 4, none: 0.45 };
const files = new Map();

/** Load the drill boundaries once. */
export function loadDrillGeo() {
  if (!files.has("drill")) files.set("drill", fetch(`${import.meta.env.BASE_URL}geo/drill.json`).then((r) => { if (!r.ok) throw new Error(`drill.json: ${r.status}`); return r.json(); }));
  return files.get("drill");
}

/* ---------- small maths (no d3 in the app) ---------- */
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const cubicInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const cubicOut = (t) => 1 - Math.pow(1 - t, 3);
const backOut = (t) => { const s = 1.25; t -= 1; return t * t * ((s + 1) * t + s) + 1; };
const diag = (bb) => Math.hypot(bb[2] - bb[0], bb[3] - bb[1]);
/** d3.interpolateZoom: points are [centreX, centreY, viewWidth]. */
function interpolateZoom(p0, p1) {
  const rho = Math.SQRT2, rho2 = 2, rho4 = 4;
  const [ux0, uy0, w0] = p0, [ux1, uy1, w1] = p1, dx = ux1 - ux0, dy = uy1 - uy0, d2 = dx * dx + dy * dy;
  let i, S;
  if (d2 < 1e-12) {
    S = Math.log(w1 / w0) / rho;
    i = (t) => [ux0 + t * dx, uy0 + t * dy, w0 * Math.exp(rho * t * S)];
  } else {
    const d1 = Math.sqrt(d2);
    const b0 = (w1 * w1 - w0 * w0 + rho4 * d2) / (2 * w0 * rho2 * d1), b1 = (w1 * w1 - w0 * w0 - rho4 * d2) / (2 * w1 * rho2 * d1);
    const r0 = Math.log(Math.sqrt(b0 * b0 + 1) - b0), r1 = Math.log(Math.sqrt(b1 * b1 + 1) - b1);
    S = (r1 - r0) / rho;
    i = (t) => {
      const s = t * S, c0 = Math.cosh(r0), u = (w0 / (rho2 * d1)) * (c0 * Math.tanh(rho * s + r0) - Math.sinh(r0));
      return [ux0 + u * dx, uy0 + u * dy, (w0 * c0) / Math.cosh(rho * s + r0)];
    };
  }
  i.duration = Math.abs(S) * 1000;
  return i;
}
function inRings(P, x, y) {
  let c = false;
  for (const r of P) for (let i = 0, j = r.length - 2; i < r.length; j = i, i += 2) {
    const xi = r[i], yi = r[i + 1], xj = r[j], yj = r[j + 1];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}
function webgl() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch { return false; }
}

/**
 * Mount the drill map in `el`.
 *   geo         loadDrillGeo() result
 *   names       { region: {id: {name, short, tag}}, province: {id: name}, city: "Quezon City" }
 *   level(node) the alert level key of a region, province or city ("normal" | "above" | "watch" | "warning" | "none")
 *   expected(b) a barangay's expected cases (bars at city level); maxExpected the largest
 *   tip(node)   tooltip HTML; legend(levelKind) legend HTML; text: interface strings (see map.js)
 *   onFocus(node, chain, api) after every change of level (also once on mount, before this returns); initial: node id to fly to after mounting
 *   pixel       art-pixel size in screen pixels (render scale is 1 / pixel), default 3 as in voxel.js
 * Returns { go(idOrNode), up(), get(id), nodes, current(), dispose() }.
 */
export async function createDrillMap(el, { geo, names, level, expected, maxExpected, tip, legend, text, onFocus, initial = null, keyRoot = null, pixel = 3 }) {
  const THREE = await import("three");
  const W = geo.W, H = geo.H;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const css = (n) => getComputedStyle(el).getPropertyValue(n).trim();

  /* ---------- nodes ---------- */
  const regions = new Map(geo.regions.map((r) => [r.id, { ...r, kind: "region", ...(names.region[r.id] || { name: r.id, short: r.id, tag: r.id }) }]));
  const provs = new Map(geo.provinces.map((p) => [p.id, { ...p, kind: "province", name: names.province[p.id] || names.special || p.id }]));
  const bgys = new Map(geo.barangays.map((b) => [b.id, { ...b, kind: "barangay" }]));
  const drawnB = [...bgys.values()].filter((b) => b.polys);
  const qbb = drawnB.reduce((a, b) => [Math.min(a[0], b.bb[0]), Math.min(a[1], b.bb[1]), Math.max(a[2], b.bb[2]), Math.max(a[3], b.bb[3])], [1e9, 1e9, -1e9, -1e9]);
  const QC = { id: "QC", kind: "city", name: names.city, bb: qbb, c: [(qbb[0] + qbb[2]) / 2, (qbb[1] + qbb[3]) / 2], h: 0, outline: geo.qcOutline, region: "R_NCR" };
  const get = (id) => (typeof id === "object" ? id : id === "QC" ? QC : regions.get(id) || provs.get(id) || bgys.get(id) || null);
  const chain = (n) => (!n ? [] : n.kind === "region" ? [n] : n.kind === "province" ? [regions.get(n.region), n] : n.kind === "city" ? [regions.get("R_NCR"), QC] : [regions.get("R_NCR"), QC, n]);
  const levelOf = (n) => (!n ? "country" : n.kind);
  const lvColor = (lv) => css(lv === "none" ? "--dm-nodata" : `--lv-${lv}`);
  const rampLo = new THREE.Color(), rampHi = new THREE.Color();
  const ramp = (v) => rampLo.clone().lerp(rampHi, Math.sqrt(clamp(v / (maxExpected || 1), 0, 1)));

  /* ---------- DOM ---------- */
  el.classList.add("dmap");
  el.style.setProperty("--dm-px", `${Math.max(1, pixel)}px`);
  el.innerHTML = `
    <svg class="dmap__ov" aria-hidden="true"><path class="dmap__halo"></path><path class="dmap__focus"></path><path class="dmap__hover"></path><g class="dmap__labels"></g>
      <g class="dmap__pulse" hidden><rect class="r1" x="-6" y="-6" width="12" height="12"></rect><rect class="r2" x="-6" y="-6" width="12" height="12"></rect><rect class="dot" x="-4" y="-4" width="8" height="8"></rect></g></svg>
    <nav class="dmap__crumbs" aria-label="${text.where}"></nav>
    <div class="dmap__ctls">
      <button type="button" class="dmap__ctl" data-act="up" aria-label="${text.up}" title="${text.up} (Esc)"><svg viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M11 4 6 9l5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
      <button type="button" class="dmap__ctl" data-act="in" aria-label="${text.zoom_in}" title="${text.zoom_in}"><svg viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M9 4v10M4 9h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button>
      <button type="button" class="dmap__ctl" data-act="out" aria-label="${text.zoom_out}" title="${text.zoom_out}"><svg viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M4 9h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button>
      <button type="button" class="dmap__ctl" data-act="home" aria-label="${text.home}" title="${text.home}"><svg viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M3 8.2 9 3l6 5.2V15H3V8.2Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg></button>
      <button type="button" class="dmap__ctl dmap__ctl--txt" data-act="tilt" aria-label="${text.tilt}" title="${text.tilt}" aria-pressed="true">3D</button>
      <button type="button" class="dmap__ctl" data-act="north" aria-label="${text.north}" title="${text.north}"><svg viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M9 2.5 11.6 9H6.4L9 2.5Z" fill="var(--lv-warning)"/><path d="M9 15.5 6.4 9h5.2L9 15.5Z" fill="currentColor" opacity=".55"/></svg></button>
    </div>
    <div class="dmap__legend"></div>
    <div class="dmap__mini" data-off="true" aria-hidden="true"><svg></svg></div>
    <div class="dmap__hint" data-off="true"></div>
    <div class="dmap__tip" hidden></div>
    <p class="dmap__live" aria-live="polite"></p>`;
  const q = (s) => el.querySelector(s);
  const ov = q(".dmap__ov"), lblG = q(".dmap__labels"), focusP = q(".dmap__focus"), haloP = q(".dmap__halo"), hovP = q(".dmap__hover");
  const pulseG = q(".dmap__pulse"), tipEl = q(".dmap__tip"), hintEl = q(".dmap__hint");
  let vw = el.clientWidth || 600, vh = el.clientHeight || 400;

  /* ---------- renderer: WebGL, or a flat 2D canvas ---------- */
  const gl = webgl();
  let renderer = null, scene, camera, hemi, sun, shadowMat, ctx2 = null, canvas;
  const px = Math.max(1, pixel), dpr = 1 / px; // render scale: one art pixel = px screen pixels
  if (gl) {
    try {
      renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: "high-performance" });
      renderer.setPixelRatio(dpr); renderer.setSize(vw, vh, false);
      renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
      canvas = renderer.domElement;
    } catch { renderer = null; }
  }
  if (!renderer) { canvas = document.createElement("canvas"); ctx2 = canvas.getContext("2d"); }
  canvas.className = "dmap__gl"; canvas.setAttribute("aria-hidden", "true");
  Object.assign(canvas.style, { imageRendering: "pixelated" });
  el.prepend(canvas);
  if (renderer) {
    scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0xffffff, 100, 1000);
    camera = new THREE.PerspectiveCamera(34, vw / vh, 1, 10000);
    hemi = new THREE.HemisphereLight(0xffffff, 0x8a9590, 1.9);
    sun = new THREE.DirectionalLight(0xffffff, 1.75);
    sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
    scene.add(hemi, sun, sun.target);
    shadowMat = new THREE.ShadowMaterial({ opacity: 0.2, polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 2 });
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(40000, 40000), shadowMat);
    ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
  }
  let flat = !renderer;
  if (flat) q('[data-act="tilt"]').hidden = q('[data-act="north"]').hidden = true;
  function setColours() {
    rampLo.set(css("--dm-ramp-lo")); rampHi.set(css("--dm-ramp-hi"));
    if (renderer) { const sea = new THREE.Color(css("--dm-sea")); renderer.setClearColor(sea, 1); scene.fog.color.copy(sea); }
  }
  setColours();

  /* ---------- geometry, per node (built when first needed) ---------- */
  const v2 = (x, y) => new THREE.Vector2(x - W / 2, -(y - H / 2));
  const ringPts = (f) => { const o = []; for (let i = 0; i < f.length; i += 2) o.push(v2(f[i], f[i + 1])); return o; };
  function ensure(n) {
    if (n.col || !n.polys) return !!n.polys;
    n.h = 0; n.col = new THREE.Color(css("--dm-ghost"));
    if (renderer) {
      const shapes = n.polys.map((P) => { const sh = new THREE.Shape(ringPts(P[0])); for (let i = 1; i < P.length; i++) sh.holes.push(new THREE.Path(ringPts(P[i]))); return sh; });
      const g = new THREE.ExtrudeGeometry(shapes, { depth: 1, bevelEnabled: false, curveSegments: 1 });
      g.rotateX(-Math.PI / 2);
      n.top = new THREE.MeshLambertMaterial(); n.side = new THREE.MeshLambertMaterial();
      n.mesh = new THREE.Mesh(g, [n.top, n.side]);
      n.mesh.castShadow = n.mesh.receiveShadow = true; n.mesh.scale.y = 1e-4; n.mesh.visible = false; n.mesh.userData.node = n;
      scene.add(n.mesh);
    } else {
      n.path = new Path2D();
      for (const P of n.polys) for (const r of P) { n.path.moveTo(r[0], r[1]); for (let i = 2; i < r.length; i += 2) n.path.lineTo(r[i], r[i + 1]); n.path.closePath(); }
    }
    return true;
  }
  for (const r of regions.values()) ensure(r);

  /* ---------- tweens ---------- */
  const tw = new Map();
  let instant = false;
  const tmp = new THREE.Color();
  function applyNode(n, h, col) {
    n.h = h; n.col.copy(col);
    if (n.mesh) {
      n.mesh.scale.y = Math.max(h, 1e-4); n.mesh.visible = h > 1e-4;
      n.top.color.copy(col); n.side.color.copy(col).multiplyScalar(0.74);
    }
  }
  function setTarget(n, h, colour, delay = 0, dur = 750) {
    if (!ensure(n)) return;
    const col = colour instanceof THREE.Color ? colour : new THREE.Color(colour);
    if (reduce || instant) { tw.delete(n); applyNode(n, h, col); return; }
    if (Math.abs(n.h - h) < 1e-6 && n.col.equals(col)) { tw.delete(n); return; }
    tw.set(n, { h0: n.h, h1: h, c0: n.col.clone(), c1: col, t0: performance.now() + delay, dur, up: h > n.h * 1.05 });
    kick();
  }
  function runTweens(now) {
    for (const [n, t] of tw) {
      const k = (now - t.t0) / t.dur;
      if (k < 0) continue;
      const e = Math.min(1, k);
      tmp.copy(t.c0).lerp(t.c1, cubicOut(e));
      applyNode(n, t.h0 + (t.h1 - t.h0) * (t.up ? backOut(e) : cubicInOut(e)), tmp);
      if (k >= 1) { applyNode(n, t.h1, t.c1); tw.delete(n); }
    }
  }

  /* ---------- camera ---------- */
  const C = { x: 0, z: 0, w: 1400, pitch: PITCH.country, bearing: 0 };
  let flight = null;
  function camApply() {
    if (!renderer) return;
    const asp = vw / vh, vf = (camera.fov * Math.PI) / 180, hf = 2 * Math.atan(Math.tan(vf / 2) * asp);
    const d = C.w / 2 / Math.tan(hf / 2), p = (C.pitch * Math.PI) / 180, b = (C.bearing * Math.PI) / 180;
    camera.aspect = asp;
    camera.position.set(C.x + d * Math.sin(p) * Math.sin(b), d * Math.cos(p), C.z + d * Math.sin(p) * Math.cos(b));
    camera.near = d * 0.03; camera.far = d * 14;
    camera.lookAt(C.x, 0, C.z); camera.updateProjectionMatrix(); camera.updateMatrixWorld();
    scene.fog.near = d * 1.05; scene.fog.far = d * 3.6;
    sun.position.set(C.x - C.w * 0.55, C.w * 1.25, C.z - C.w * 0.4); sun.target.position.set(C.x, 0, C.z);
    const s = sun.shadow.camera, e = C.w * 0.95;
    s.left = -e; s.right = e; s.top = e; s.bottom = -e; s.near = C.w * 0.05; s.far = C.w * 4; s.updateProjectionMatrix();
    sun.shadow.bias = -0.0005; sun.shadow.normalBias = C.w * 0.0008;
  }
  function pads(kind) {
    const narrow = vw < 560, top = narrow ? 64 : 70, side = narrow ? 14 : 46, bot = narrow ? 70 : 64;
    if (kind === "barangay") return [Math.max(top, vh * 0.24), Math.max(side, vw * 0.26), Math.max(bot, vh * 0.2), Math.max(side, vw * 0.26)];
    if (kind === "country") return [top - 30, side - 6, bot - 34, side - 6];
    return [top, side + 16, bot, side + 16];
  }
  function fitCam(bb, kind) {
    const pitch = flat ? 0 : PITCH[kind], [t, r, b, l] = pads(kind);
    const fx = (vw - l - r) / vw, fy = (vh - t - b) / vh, asp = vw / vh;
    const bw = Math.max(bb[2] - bb[0], 0.05), bh = Math.max(bb[3] - bb[1], 0.05);
    const w = Math.max(bw / fx, (bh * asp * Math.cos(((pitch * Math.PI) / 180) * 0.75)) / fy) * 1.04, s = w / vw;
    const cx = (bb[0] + bb[2]) / 2 - W / 2, cz = (bb[1] + bb[3]) / 2 - H / 2;
    return { x: cx - ((l - r) / 2) * s, z: cz - (((t - b) / 2) * s) / Math.max(0.5, Math.cos((pitch * Math.PI) / 180)), w, pitch, bearing: 0 };
  }
  const flightMs = (to) => clamp(interpolateZoom([C.x, C.z, C.w], [to.x, to.z, to.w]).duration * 0.85, 750, 1900);
  function flyTo(to, ms) {
    if (flight) { flight.res(); flight = null; }
    if (reduce || !ms) { Object.assign(C, to); kick(); return Promise.resolve(); }
    let b1 = to.bearing; while (b1 - C.bearing > 180) b1 -= 360; while (b1 - C.bearing < -180) b1 += 360;
    return new Promise((res) => { flight = { t0: performance.now(), ms, iz: interpolateZoom([C.x, C.z, C.w], [to.x, to.z, to.w]), p0: C.pitch, p1: to.pitch, b0: C.bearing, b1, res }; kick(); });
  }
  function runFlight(now) {
    const f = flight, t = Math.min(1, (now - f.t0) / f.ms), e = cubicInOut(t), [x, z, w] = f.iz(e);
    Object.assign(C, { x, z, w, pitch: f.p0 + (f.p1 - f.p0) * e - Math.sin(Math.PI * e) * (flat ? 0 : 10), bearing: f.b0 + (f.b1 - f.b0) * e });
    if (t >= 1) { flight = null; f.res(); }
  }

  /* ---------- drawing ---------- */
  let raf = 0, alive = true;
  const kick = () => { if (!raf && alive) raf = requestAnimationFrame(frame); };
  const LAYERS = () => [regions.values(), provs.values(), drawnB];
  function draw2d() {
    const k = vw / C.w;
    ctx2.imageSmoothingEnabled = false;
    ctx2.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx2.fillStyle = css("--dm-sea"); ctx2.fillRect(0, 0, vw, vh);
    ctx2.setTransform(dpr * k, 0, 0, dpr * k, dpr * (vw / 2 - (W / 2 + C.x) * k), dpr * (vh / 2 - (H / 2 + C.z) * k));
    ctx2.lineWidth = 1 / k; ctx2.strokeStyle = css("--dm-edge");
    for (const layer of LAYERS()) for (const n of layer) {
      if (!n.path || n.h <= 1e-4) continue;
      ctx2.fillStyle = `#${n.col.getHexString()}`; ctx2.fill(n.path, "evenodd"); ctx2.stroke(n.path);
    }
  }
  function frame(now) {
    raf = 0;
    if (flight) runFlight(now);
    if (tw.size) runTweens(now);
    if (renderer) { camApply(); renderer.render(scene, camera); } else draw2d();
    overlay();
    if (flight || tw.size) kick();
  }

  /* ---------- screen-space overlay ---------- */
  const pv = new THREE.Vector3();
  const snap = (v) => Math.round(v / px) * px + px / 2; // centre of an art pixel
  function scr(x, y, h) {
    if (!renderer) { const k = vw / C.w; return [(x - W / 2 - C.x) * k + vw / 2, (y - H / 2 - C.z) * k + vh / 2, 0]; }
    pv.set(x - W / 2, h, y - H / 2).project(camera);
    return [((pv.x + 1) / 2) * vw, ((1 - pv.y) / 2) * vh, pv.z];
  }
  function outlineD(n, h) {
    const rings = n.kind === "city" ? n.outline.map((r) => [r]) : n.polys;
    if (!rings) return "";
    let d = "";
    for (const P of rings) for (const r of P) {
      let s = "";
      let lx = NaN, ly = NaN;
      for (let i = 0; i < r.length; i += 2) {
        const p = scr(r[i], r[i + 1], h); if (p[2] > 1) return "";
        const x = snap(p[0]), y = snap(p[1]);
        if (x === lx && y === ly) continue; // drop points inside the same art pixel
        s += (s ? "L" : "M") + x + " " + y; lx = x; ly = y;
      }
      d += s + "Z";
    }
    return d;
  }
  const qcState = { on: false, split: false };
  const top = (n) => (n.kind === "city" ? (qcState.split ? 0 : QC.h) : n.h || 0);
  // a region's outline follows the tops of its raised provinces, so the lines sit on the blocks, not on the ground
  function focusD(n) {
    if (n.kind !== "region") return outlineD(n, top(n) * 1.002);
    let d = "";
    for (const p of provs.values()) if (p.region === n.id && p.h > 1e-4) d += outlineD(p, p.h * 1.002);
    if (qcState.on && !qcState.split) d += outlineD(QC, QC.h * 1.002);
    return d;
  }
  let focusNode = null, hoverNode = null, pulseNode = null;
  function overlay() {
    const d = focusNode ? focusD(focusNode) : "";
    focusP.setAttribute("d", d); haloP.setAttribute("d", d);
    hovP.setAttribute("d", hoverNode && hoverNode !== focusNode ? outlineD(hoverNode, top(hoverNode) * 1.002) : "");
    placeLabels(); placeMini(); placePulse();
    q('[data-act="north"] svg').style.transform = `rotate(${C.bearing}deg)`;
  }
  let labels = [], chrome = null;
  const meas = document.createElement("canvas").getContext("2d");
  const font = getComputedStyle(el).fontFamily || "sans-serif";
  const textW = (s, big) => { meas.font = `${big ? 800 : 650} ${big ? 13 : 11}px ${font}`; return meas.measureText(s).width; };
  function buildLabels(n) {
    const lvl = levelOf(n), ch = chain(n), L = [];
    const add = (node, s, cls, pri, minPx = 0) => L.push({ node, s, cls, pri, w: textW(s, cls === "big"), minPx });
    if (lvl === "country") for (const r of regions.values()) add(r, r.tag, "tag", 10 + r.a / 1000);
    else {
      const region = ch[0];
      for (const r of regions.values()) if (r !== region) add(r, r.tag, "tag sub", 1 + r.a / 1e4);
      if (lvl === "region" || lvl === "province") {
        for (const p of provs.values()) if (p.region === region.id) add(p, p.name, p === ch[1] ? "big" : "", p === ch[1] ? 100 : 5 + p.a / 100, 18);
        if (region.id === "R_NCR") add(QC, QC.name, "big", 120);
      } else {
        const sel = ch[2];
        for (const b of drawnB) add(b, b.name, b === sel ? "big" : "", b === sel ? 200 : sel && sel.nb.includes(b.id) ? 60 + (expected(b) || 0) : 10 + (expected(b) || 0), b === sel ? 0 : 14);
      }
    }
    labels = L.sort((a, b) => b.pri - a.pri);
    lblG.textContent = "";
    for (const l of labels) {
      const t = document.createElementNS(SVGNS, "text");
      t.setAttribute("class", `dmap__lbl ${l.cls}`); t.setAttribute("text-anchor", "middle"); t.setAttribute("dominant-baseline", "central");
      t.textContent = l.s; lblG.appendChild(t); l.el = t;
    }
  }
  function placeLabels() {
    const ppu = vw / C.w;
    if (!chrome) { // labels never sit under the crumbs, controls, legend or minimap (measured once per level and resize)
      const er = el.getBoundingClientRect();
      chrome = [...el.querySelectorAll(".dmap__crumbs, .dmap__ctls, .dmap__legend, .dmap__mini:not([data-off='true'])")].map((c) => {
        const r = c.getBoundingClientRect(); return [r.left - er.left, r.top - er.top, r.right - er.left, r.bottom - er.top];
      }).filter((b) => b[2] > b[0]);
    }
    const boxes = chrome.slice();
    for (const l of labels) {
      const n = l.node, [sx, sy0, sz] = scr(n.c[0], n.c[1], top(n)), big = l.cls === "big", sy = sy0 - (big ? 12 : 8);
      let ok = sz < 1 && sx > 10 && sx < vw - 10 && sy > 10 && sy < vh - 10 && (n.bb[2] - n.bb[0]) * ppu >= l.minPx;
      const w = l.w + 6, h = big ? 18 : 15, box = [sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2];
      if (ok) for (const b of boxes) if (box[0] < b[2] && box[2] > b[0] && box[1] < b[3] && box[3] > b[1]) { ok = false; break; }
      if (ok) boxes.push(box);
      l.el.setAttribute("x", snap(sx)); l.el.setAttribute("y", snap(sy));
      l.el.classList.toggle("is-hidden", !ok);
    }
  }
  function placePulse() {
    if (!pulseNode) { pulseG.hidden = true; return; }
    const [x, y, z] = scr(pulseNode.c[0], pulseNode.c[1], pulseNode.h);
    pulseG.hidden = z > 1;
    pulseG.setAttribute("transform", `translate(${snap(x)},${snap(y + 14)})`);
  }
  // minimap: the regions, and the ground the camera sees
  const mini = q(".dmap__mini svg");
  mini.setAttribute("viewBox", `0 0 ${W} ${H}`); mini.setAttribute("preserveAspectRatio", "xMidYMid meet");
  for (const r of regions.values()) { const p = document.createElementNS(SVGNS, "path"); p.setAttribute("d", geo.mini[r.id] || ""); mini.appendChild(p); r.miniEl = p; }
  const miniPoly = document.createElementNS(SVGNS, "polygon"); mini.appendChild(miniPoly);
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), hit = new THREE.Vector3();
  function groundAt(x, y) {
    if (!renderer) { const k = vw / C.w; return new THREE.Vector3((x - vw / 2) / k + C.x, 0, (y - vh / 2) / k + C.z); }
    ndc.set((x / vw) * 2 - 1, -(y / vh) * 2 + 1); ray.setFromCamera(ndc, camera);
    return ray.ray.intersectPlane(plane, hit) ? hit.clone() : null;
  }
  function placeMini() {
    miniPoly.setAttribute("points", [[0, 0], [vw, 0], [vw, vh], [0, vh]].map(([x, y]) => {
      const g = groundAt(x, y) || groundAt(x, vh * 0.45) || new THREE.Vector3(C.x, 0, C.z);
      const dx = g.x - C.x, dz = g.z - C.z, m = Math.hypot(dx, dz), cap = C.w * 2.2;
      if (m > cap) { g.x = C.x + (dx / m) * cap; g.z = C.z + (dz / m) * cap; }
      return `${(g.x + W / 2).toFixed(1)},${(g.z + H / 2).toFixed(1)}`;
    }).join(" "));
    miniPoly.classList.toggle("is-tiny", C.w < W * 0.05);
  }

  /* ---------- navigation ---------- */
  let cur = null, navId = 0, hintT = 0;
  const wait = (ms) => new Promise((r) => setTimeout(r, reduce ? 0 : ms));
  const bbOf = (n) => (n ? n.bb : [0, 0, W, H]);
  async function go(target, { direct = false } = {}) {
    target = target ? get(target) : null;
    const id = ++navId, from = chain(cur), to = chain(target);
    let k = 0; while (k < from.length && k < to.length && from[k] === to[k]) k++;
    const steps = to.slice(k);
    if (direct || steps.length <= 1) return step(target, id, 1);
    for (let i = 0; i < steps.length; i++) {
      if (id !== navId) return;
      await step(steps[i], id, i === steps.length - 1 ? 1 : 0.75);
      if (i < steps.length - 1) await wait(300);
    }
  }
  async function step(n, id, speed) {
    if (id !== navId) return;
    const prev = cur; cur = n;
    const to = fitCam(bbOf(n), levelOf(n)), ms = reduce ? 0 : flightMs(to) * speed;
    apply(prev, n, chain(n).length > chain(prev).length ? ms * 0.5 : 0);
    await flyTo(to, ms);
    if (id === navId) arrive(n);
  }
  function arrive(n) {
    focusNode = n && n.kind === "city" ? null : n;
    focusP.classList.remove("is-drawn"); void focusP.getBoundingClientRect(); focusP.classList.add("is-drawn");
    haloP.classList.toggle("is-on", !!focusNode);
    pulseNode = n && n.kind === "barangay" && n.polys ? n : null;
    kick();
  }

  /** What every area does at each level: height, colour, delay. */
  function apply(prev, n, reveal) {
    const lvl = levelOf(n), ch = chain(n), region = ch[0] || null, second = ch[1] || null, bgy = ch[2] || null;
    el.dataset.level = lvl;
    focusNode = null; pulseNode = null; focusP.classList.remove("is-drawn"); haloP.classList.remove("is-on");
    const floor = Math.max(diag(bbOf(n)) * 0.006, 0.004);
    const ghost = new THREE.Color(css("--dm-ghost")), land = new THREE.Color(css("--dm-land"));
    const dim = (c, k = 0.58) => new THREE.Color(c).lerp(ghost, k);
    for (const r of regions.values()) {
      const sel = region === r;
      if (!region) setTarget(r, 12 + 24 * LVH[level(r)], lvColor(level(r)), prev ? 120 + Math.random() * 200 : 0, 800);
      else if (sel) setTarget(r, 0, land, 0, 450);
      else setTarget(r, floor, ghost, 0, 650);
      r.miniEl.classList.toggle("is-sel", sel);
    }
    const rd = region ? diag(region.bb) : 0;
    const cx = region ? (region.bb[0] + region.bb[2]) / 2 : 0, cy = region ? (region.bb[1] + region.bb[3]) / 2 : 0;
    const provH = (p) => rd * (0.014 + 0.02 * LVH[level(p)]) * (second && second.kind === "province" ? 0.6 : 1);
    for (const p of provs.values()) {
      if (!region || p.region !== region.id) { if (p.col) setTarget(p, 0, p.col, 0, 380); continue; }
      ensure(p);
      let h = provH(p), col = new THREE.Color(lvColor(level(p)));
      if (second && second.kind === "city") { h = floor; col = dim(col, 0.7); }
      else if (second && second !== p) col = dim(col);
      else if (second === p) h *= 1.12;
      const appear = p.h < 1e-4;
      if (appear) p.col.copy(col);
      setTarget(p, h, col, appear ? reveal + (Math.hypot(p.c[0] - cx, p.c[1] - cy) / (rd / 2)) * 380 : 0, 820);
    }
    // Quezon City: one plateau inside NCR, bars by expected cases once it is chosen
    const qcOn = !!region && region.id === "R_NCR", split = qcOn && second === QC, wasSplit = qcState.split;
    qcState.on = qcOn; qcState.split = split;
    const plateau = qcOn ? Math.max(provH(provs.get("PH13074") || { region: "R_NCR" }), provH(QC)) * 1.22 : 0;
    QC.h = plateau;
    const qd = diag(QC.bb), qcCol = new THREE.Color(lvColor(level(QC)));
    for (const b of drawnB) {
      if (!qcOn) { if (b.col) setTarget(b, 0, b.col, 0, 380); continue; }
      ensure(b);
      let h, col, delay = 0;
      if (!split) {
        h = plateau; col = second && second.kind === "province" ? dim(qcCol) : qcCol.clone();
        if (b.h < 1e-4) { delay = reveal + 260; b.col.copy(col); }
      } else {
        const hs = bgy ? Math.max(diag(bgy.bb) * 1.6, qd * 0.12) : qd;
        h = hs * (0.02 + 0.16 * Math.sqrt((expected(b) || 0) / (maxExpected || 1))); col = ramp(expected(b) || 0);
        if (bgy && b !== bgy && !bgy.nb.includes(b.id)) col = dim(col, 0.62);
        if (b === bgy) h *= 1.15;
        if (!wasSplit) delay = reveal + (Math.hypot(b.c[0] - QC.c[0], b.c[1] - QC.c[1]) / (qd / 2)) * 420;
      }
      setTarget(b, h, col, delay, split && !wasSplit ? 900 : 650);
    }
    picks = [...[...regions.values()].filter((r) => r !== region), ...(region ? [...provs.values()].filter((p) => p.region === region.id && p.col) : []), ...(qcOn ? drawnB : [])];
    buildLabels(n);
    crumbs(n);
    q(".dmap__legend").innerHTML = legend(lvl === "city" || lvl === "barangay" ? "expected" : "level");
    q(".dmap__mini").dataset.off = String(!n);
    q('[data-act="up"]').disabled = !n;
    chrome = null;
    hintEl.textContent = !n ? text.hint_country : n.kind === "region" ? (n.id === "R_NCR" ? text.hint_ncr : text.hint_region) : n.kind === "city" ? text.hint_city : text.hint_deep;
    hintEl.dataset.off = "false"; clearTimeout(hintT); hintT = setTimeout(() => { hintEl.dataset.off = "true"; }, 4200);
    q(".dmap__live").textContent = n ? `${text.zoomed_to} ${n.name}` : text.whole_country;
    onFocus?.(n, ch, api);
    kick();
  }
  function crumbs(n) {
    const items = [{ n: null, label: text.philippines, kind: text.k_country }, ...chain(n).map((x) => ({ n: x, label: x.kind === "region" ? x.short : x.name, kind: text[`k_${x.kind}`] }))];
    const nav = q(".dmap__crumbs");
    nav.innerHTML = items.map((it, i) => `${i ? '<span class="dmap__sep" aria-hidden="true">›</span>' : ""}<button type="button" class="dmap__crumb" data-i="${i}"${i === items.length - 1 ? ' aria-current="location"' : ""} style="animation-delay:${i * 50}ms"><small>${it.kind}</small><span>${it.label}</span></button>`).join("");
    nav.onclick = (e) => { const b = e.target.closest("[data-i]"); if (!b) return; const it = items[+b.dataset.i]; if (it.n !== cur) go(it.n); };
  }

  /* ---------- picking and input ---------- */
  let picks = [];
  function pickAt(x, y) {
    let n = null;
    if (renderer) {
      ndc.set((x / vw) * 2 - 1, -(y / vh) * 2 + 1); ray.setFromCamera(ndc, camera);
      const hits = ray.intersectObjects(picks.filter((p) => p.mesh && p.mesh.visible).map((p) => p.mesh), false);
      n = hits[0]?.object.userData.node || null;
    } else {
      const g = groundAt(x, y), px = g.x + W / 2, py = g.z + H / 2;
      for (let i = picks.length - 1; i >= 0 && !n; i--) { const p = picks[i]; if (p.h > 1e-4 && px >= p.bb[0] && px <= p.bb[2] && py >= p.bb[1] && py <= p.bb[3] && p.polys.some((P) => inRings(P, px, py))) n = p; }
    }
    return n && n.kind === "barangay" && !qcState.split ? QC : n;
  }
  function hideTip() { tipEl.hidden = true; if (hoverNode) { hoverNode = null; kick(); } }
  const local = (e) => { const r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
  let hoverRaf = 0, lastMove = null, drag = null, pinch = null;
  const ptrs = new Map();
  function doHover() {
    hoverRaf = 0;
    if (!lastMove || drag || !alive) return;
    const n = pickAt(lastMove.x, lastMove.y);
    if (!n || n === cur) { hideTip(); canvas.style.cursor = ""; return; }
    canvas.style.cursor = "pointer";
    if (hoverNode !== n) { hoverNode = n; tipEl.innerHTML = tip(n); kick(); }
    tipEl.hidden = false;
    tipEl.style.left = `${Math.min(lastMove.x + 14, vw - 215)}px`; tipEl.style.top = `${Math.min(lastMove.y + 14, vh - 110)}px`;
  }
  function stopFlight() { if (flight) { flight.res(); flight = null; navId++; arrive(cur); } }
  const on = (t, ev, fn, o) => { t.addEventListener(ev, fn, o); offs.push(() => t.removeEventListener(ev, fn, o)); };
  const offs = [];
  on(canvas, "contextmenu", (e) => e.preventDefault());
  on(canvas, "pointerdown", (e) => {
    const p = local(e); canvas.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, p);
    if (ptrs.size === 1) drag = { mode: !flat && (e.button === 2 || e.shiftKey || e.ctrlKey || e.altKey) ? "rotate" : "pan", sx: p.x, sy: p.y, lx: p.x, ly: p.y, moved: false, g: groundAt(p.x, p.y) };
    else if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), w: C.w }; if (drag) drag.moved = true; }
  });
  on(canvas, "pointermove", (e) => {
    const p = local(e);
    if (ptrs.has(e.pointerId)) ptrs.set(e.pointerId, p);
    if (pinch && ptrs.size === 2) { const [a, b] = [...ptrs.values()]; C.w = clamp((pinch.w * pinch.d) / Math.max(Math.hypot(a.x - b.x, a.y - b.y), 1), 0.3, 4000); stopFlight(); kick(); return; }
    if (drag) {
      if (!drag.moved && Math.hypot(p.x - drag.sx, p.y - drag.sy) > 5) { drag.moved = true; stopFlight(); hideTip(); }
      if (!drag.moved) return;
      if (drag.mode === "pan" && drag.g) { camApply(); const g1 = groundAt(p.x, p.y); if (g1) { C.x += drag.g.x - g1.x; C.z += drag.g.z - g1.z; } }
      else if (drag.mode === "rotate") { C.bearing -= (p.x - drag.lx) * 0.3; C.pitch = clamp(C.pitch + (p.y - drag.ly) * 0.25, 0, 68); }
      drag.lx = p.x; drag.ly = p.y; kick(); return;
    }
    if (e.pointerType === "touch") return;
    lastMove = p; if (!hoverRaf) hoverRaf = requestAnimationFrame(doHover);
  });
  const endPtr = (e) => {
    const was = drag, p = local(e);
    ptrs.delete(e.pointerId);
    if (ptrs.size < 2) pinch = null;
    if (ptrs.size === 0) { drag = null; if (was && !was.moved && e.type === "pointerup" && e.button !== 2) click(p.x, p.y); }
  };
  on(canvas, "pointerup", endPtr); on(canvas, "pointercancel", endPtr);
  on(canvas, "pointerleave", () => { if (!drag) hideTip(); });
  on(canvas, "wheel", (e) => {
    e.preventDefault(); stopFlight(); camApply();
    const p = local(e), g0 = groundAt(p.x, p.y);
    C.w = clamp(C.w * Math.exp(e.deltaY * (e.ctrlKey ? 0.01 : 0.0013)), 0.3, 4000);
    camApply();
    const g1 = groundAt(p.x, p.y);
    if (g0 && g1) { C.x += g0.x - g1.x; C.z += g0.z - g1.z; }
    kick();
  }, { passive: false });
  function click(x, y) {
    const n = pickAt(x, y);
    hideTip();
    if (!n) { if (cur) up(); return; }
    if (n !== cur) go(n);
  }
  const up = () => { const ch = chain(cur); return go(ch.length > 1 ? ch[ch.length - 2] : null); };
  const zoomBy = (k) => { stopFlight(); flyTo({ ...C, w: clamp(C.w * k, 0.3, 4000) }, reduce ? 0 : 420); };
  on(q(".dmap__ctls"), "click", (e) => {
    const a = e.target.closest("[data-act]")?.dataset.act;
    if (a === "up") up();
    else if (a === "home") go(null);
    else if (a === "in") zoomBy(1 / 1.6);
    else if (a === "out") zoomBy(1.6);
    else if (a === "north") { stopFlight(); flyTo({ ...C, bearing: 0, pitch: flat ? 0 : PITCH[levelOf(cur)] }, reduce ? 0 : 600); }
    else if (a === "tilt") {
      flat = !flat; const b = q('[data-act="tilt"]'); b.setAttribute("aria-pressed", String(!flat)); b.textContent = flat ? "2D" : "3D";
      stopFlight(); flyTo(fitCam(bbOf(cur), levelOf(cur)), reduce ? 0 : 900);
    }
  });
  // Esc goes up a level while the map, or anything inside keyRoot (the side panel too), has focus
  on(document, "keydown", (e) => {
    if (e.key !== "Escape" || !cur || e.defaultPrevented) return;
    const t = e.target, root = keyRoot || el;
    if (t !== document.body && !root.contains(t)) return;
    if (t.closest?.("input, textarea, select, [contenteditable]")) return;
    e.preventDefault(); up();
  });
  const ro = new ResizeObserver(() => {
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h || (w === vw && h === vh)) return;
    vw = w; vh = h;
    if (renderer) renderer.setSize(vw, vh, false); else { canvas.width = Math.ceil(vw * dpr); canvas.height = Math.ceil(vh * dpr); canvas.style.width = `${vw}px`; canvas.style.height = `${vh}px`; }
    ov.setAttribute("viewBox", `0 0 ${vw} ${vh}`); chrome = null;
    if (!flight) Object.assign(C, fitCam(bbOf(cur), levelOf(cur)));
    kick();
  });
  ro.observe(el);

  const api = {
    go, up, get, current: () => cur, nodes: { regions, provinces: provs, barangays: bgys, city: QC }, chain,
    hover(id) { hoverNode = id ? get(id) : null; kick(); },
    dispose() {
      alive = false; cancelAnimationFrame(raf); cancelAnimationFrame(hoverRaf); clearTimeout(startT); clearTimeout(hintT); ro.disconnect(); offs.forEach((f) => f());
      if (renderer) {
        scene.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => m.dispose()); } });
        renderer.dispose(); renderer.forceContextLoss?.();
      }
      el.innerHTML = ""; el.classList.remove("dmap");
    },
  };

  let startT = 0;
  /* ---------- start ---------- */
  if (!renderer) { canvas.width = Math.ceil(vw * dpr); canvas.height = Math.ceil(vh * dpr); canvas.style.width = `${vw}px`; canvas.style.height = `${vh}px`; }
  ov.setAttribute("viewBox", `0 0 ${vw} ${vh}`);
  Object.assign(C, fitCam([0, 0, W, H], "country"));
  apply(null, null, 0);
  // first rise: regions grow north to south
  if (!reduce) for (const r of regions.values()) { const t = tw.get(r); if (t) t.t0 = performance.now() + 120 + (r.c[1] / H) * 650; }
  if (initial && get(initial)) startT = setTimeout(() => go(get(initial)), reduce ? 0 : 650);

  return api;
}
