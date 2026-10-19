// The Dengue Drill's 3D board: a region's provinces as voxel columns (height = cases against the epidemic line this
// week, colour = the heat ramp), with the game's pieces in the same scene:
//   intel rings that pulse by forecast level and a scan line sweeping the board (round 2),
//   shield tokens that drop with a bounce and a puff of dust when teams deploy,
//   pixel mosquitoes swarming over the provinces (count from rain, as before), and voxel rain on turn change,
// plus HTML labels, forecast tags and "+N cases" floaters projected from 3D. Built on src/lib/voxel.js.
import { createVoxelMap } from "../lib/voxel.js";
import { bake, loadSprite, rows } from "../lib/pixel.js";

const LCOL = { warning: "#F04B2A", watch: "#F58220", above: "#F7C928", normal: "#0C7A55" };
const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/** A crisp texture from a canvas (nearest-neighbour, so pixel art stays square). */
function texture(T, canvas) {
  const t = new T.CanvasTexture(canvas);
  t.magFilter = T.NearestFilter; t.minFilter = T.NearestFilter; t.colorSpace = T.SRGBColorSpace; t.generateMipmaps = false;
  return t;
}

// a pixel shield, 12 x 13 art pixels: K outline, G body, L highlight
const SHIELD = [
  "..KKKKKKKK..",
  ".KLLGGGGGGK.",
  "KLGGGGGGGGGK",
  "KLGGGGGGGGGK",
  "KGGGGGGGGGGK",
  "KGGGGGGGGGGK",
  "KGGGGGGGGGGK",
  ".KGGGGGGGGK.",
  ".KGGGGGGGGK.",
  "..KGGGGGGK..",
  "...KGGGGK...",
  "....KGGK....",
  ".....KK.....",
];
function shieldCanvas(n) {
  const s = 6, c = document.createElement("canvas");
  c.width = 12 * s; c.height = 13 * s;
  const g = c.getContext("2d"), pal = { K: "#071711", G: "#2BB673", L: "#9FE8BF" };
  SHIELD.forEach((row, y) => [...row].forEach((ch, x) => { if (pal[ch]) { g.fillStyle = pal[ch]; g.fillRect(x * s, y * s, s, s); } }));
  g.fillStyle = "#071711"; g.font = `800 ${5 * s}px "Inter Tight", system-ui, sans-serif`; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(String(n), 6 * s, 5.6 * s);
  return c;
}

export async function createBoard(el, { grid, region, onPick }) {
  const overlay = Object.assign(document.createElement("div"), { className: "board__overlay" });
  let selected = null;
  const map = await createVoxelMap(el, { grid, pixel: 3, pitch: 50, yaw: -12, lift: 2.2, top: 7, sea: "#0B2A1F",
    orbit: { yaw: [-50, 26], pitch: [28, 70] }, onPick, onHover: (u) => map?.highlight(u ?? selected) });
  if (!map.three) return flatBoard(map); // no WebGL: the 2D map, without the 3D pieces
  el.append(overlay);
  const T = map.three, scene = map.scene, ids = region.provinces.map((p) => p.id);
  const mosquito = await loadSprite("mosquito");
  const disposables = [];
  const keep = (x) => { disposables.push(x); return x; };

  // ------------------------------------------------------------------ HTML labels projected from 3D
  const labels = new Map(ids.map((u, k) => {
    const el2 = document.createElement("div");
    el2.className = "board__label";
    el2.innerHTML = `<span class="board__name">${region.provinces[k].name.replace(/ \(.+\)/, "")}</span><span class="board__tag"></span><span class="board__team"></span>`;
    overlay.append(el2);
    return [u, el2];
  }));
  function placeLabels() {
    for (const [u, el2] of labels) {
      const c = map.centreOf(u);
      if (!c) { el2.hidden = true; continue; }
      const p = map.toScreen(new T.Vector3(c.x, map.heightOf(u) + 1, c.z));
      el2.style.transform = `translate(${Math.round(p.x)}px, ${Math.round(p.y)}px)`;
    }
  }

  // ------------------------------------------------------------------ intel rings and the scan line (round 2)
  const ringGeo = keep(new T.RingGeometry(0.82, 1, 48));
  const rings = new Map();
  for (const u of ids) {
    const c = map.centreOf(u);
    if (!c) continue;
    const r = Math.max(2.5, Math.sqrt(map.cellsOf(u).length / Math.PI) * 0.9);
    const m = new T.Mesh(ringGeo, keep(new T.MeshBasicMaterial({ color: "#6FD6FF", transparent: true, opacity: 0.9, side: T.DoubleSide, depthWrite: false })));
    m.rotation.x = -Math.PI / 2;
    m.position.set(c.x, 0, c.z);
    m.scale.setScalar(r);
    m.visible = false;
    m.userData = { r, level: null };
    scene.add(m);
    rings.set(u, m);
  }
  const [W, H] = map.size;
  // the scan line: a thin glowing bar on the ground, crossing the board
  const sweepBox = new T.Mesh(keep(new T.BoxGeometry(0.8, 2.5, H)), keep(new T.MeshBasicMaterial({ color: "#6FD6FF", transparent: true, opacity: 0.35, depthWrite: false })));
  sweepBox.position.set(0, 1.25, H / 2);
  sweepBox.visible = false;
  scene.add(sweepBox);

  // ------------------------------------------------------------------ team tokens
  const tokens = new Map(); // u -> { sprite, n, drop: {t0} }
  const dust = [];
  const dustGeo = keep(new T.BoxGeometry(0.5, 0.5, 0.5)), dustMat = keep(new T.MeshBasicMaterial({ color: "#D5E3DA", transparent: true }));
  function setTeams(counts, { drop = null } = {}) {
    for (const u of ids) {
      const n = counts[u] || 0, cur = tokens.get(u);
      if (!n) { if (cur) { scene.remove(cur.sprite); cur.sprite.material.map.dispose(); cur.sprite.material.dispose(); tokens.delete(u); } continue; }
      if (cur && cur.n === n) continue;
      const tex = texture(T, shieldCanvas(n));
      const sprite = cur?.sprite ?? new T.Sprite(new T.SpriteMaterial({ map: tex, depthTest: false }));
      if (cur) { cur.sprite.material.map.dispose(); cur.sprite.material.map = tex; cur.sprite.material.needsUpdate = true; }
      sprite.scale.set(4.4, 4.8, 1);
      sprite.renderOrder = 5;
      if (!cur) scene.add(sprite);
      tokens.set(u, { sprite, n, t0: u === drop && !reduced() ? performance.now() : 0 });
      if (u === drop && !reduced()) puff(u);
    }
    map.render();
  }
  function puff(u) {
    const c = map.centreOf(u), y = map.heightOf(u);
    for (let i = 0; i < 14; i++) {
      const m = new T.Mesh(dustGeo, dustMat);
      m.position.set(c.x, y + 0.5, c.z);
      m.userData = { vx: (Math.random() - 0.5) * 9, vy: 3 + Math.random() * 5, vz: (Math.random() - 0.5) * 9, life: 0.6 + Math.random() * 0.4, age: -0.35 };
      scene.add(m); dust.push(m);
    }
  }

  // ------------------------------------------------------------------ mosquitoes
  const frames = ["fly1", "fly2"].map((pose) => keep(texture(T, bake(rows(mosquito, pose), mosquito.palette))));
  const bugMat = [keep(new T.SpriteMaterial({ map: frames[0], depthWrite: false })), keep(new T.SpriteMaterial({ map: frames[1], depthWrite: false }))];
  let bugs = [];
  function setBugs(n, anchors) {
    bugs.forEach((b) => scene.remove(b.s));
    bugs = reduced() || !anchors.length ? [] : Array.from({ length: n }, (_, i) => {
      const a = anchors[Math.floor(Math.random() * anchors.length)];
      const s = new T.Sprite(bugMat[i % 2]);
      s.scale.set(1.5, 1.5, 1);
      scene.add(s);
      return { s, a, p: Math.random() * 6.28, sp: 0.6 + Math.random() * 0.8, r: 1.5 + Math.random() * 4, h: 4 + Math.random() * 6 };
    });
    map.render();
  }

  // ------------------------------------------------------------------ rain
  const RAIN = 260;
  const rainMesh = new T.InstancedMesh(keep(new T.BoxGeometry(0.15, 2.2, 0.15)), keep(new T.MeshBasicMaterial({ color: "#A0DCC8", transparent: true, opacity: 0.55 })), RAIN);
  const drops = Array.from({ length: RAIN }, () => ({ x: Math.random() * W, y: Math.random() * 60, z: Math.random() * H, v: 30 + Math.random() * 20 }));
  rainMesh.visible = false;
  scene.add(rainMesh);
  let rainUntil = 0;
  const m4 = new T.Matrix4();

  // ------------------------------------------------------------------ the frame loop
  let intelOn = false;
  map.addTicker((t, dt) => {
    // tokens: drop from above with a bounce, then sit on top of the column
    for (const [u, k] of tokens) {
      const c = map.centreOf(u), top = map.heightOf(u) + 3.2;
      let y = top;
      if (k.t0) {
        const a = Math.min(1, (t - k.t0) / 650);
        const b = a < 0.6 ? 1 - (a / 0.6) ** 2 : Math.abs(Math.sin(((a - 0.6) / 0.4) * Math.PI)) * 0.25 * (1 - a);
        y = top + b * 22;
        if (a >= 1) k.t0 = 0;
      }
      k.sprite.position.set(c.x, y, c.z);
    }
    for (let i = dust.length - 1; i >= 0; i--) {
      const m = dust[i], d = m.userData;
      d.age += dt;
      if (d.age < 0) continue;
      d.vy -= 18 * dt; m.position.x += d.vx * dt; m.position.y = Math.max(0.2, m.position.y + d.vy * dt); m.position.z += d.vz * dt;
      if (d.age > d.life) { scene.remove(m); dust.splice(i, 1); }
    }
    // rings pulse by level; the scan line crosses the board every 3.2 s
    if (intelOn) {
      for (const [u, m] of rings) {
        if (!m.visible) continue;
        const lv = m.userData.level, speed = lv === "warning" ? 1.6 : 2.6;
        const k = ((t / 1000) / speed + m.userData.r) % 1;
        m.position.y = map.heightOf(u) + 0.3;
        m.scale.setScalar(m.userData.r * (reduced() ? 1.2 : 0.9 + k * 0.7));
        m.material.opacity = reduced() ? 0.9 : 0.95 * (1 - k);
      }
      sweepBox.position.x = reduced() ? -10 : (((t / 3200) % 1) * (W + 20)) - 10;
    }
    // mosquitoes wander around their province
    const fr = Math.floor(t / 100) % 2;
    for (const b of bugs) {
      b.p += dt * 3 * b.sp;
      const c = map.centreOf(b.a);
      b.s.material = bugMat[fr];
      b.s.position.set(c.x + Math.cos(b.p * 1.3) * b.r, map.heightOf(b.a) + b.h + Math.sin(b.p * 2.1), c.z + Math.sin(b.p) * b.r);
    }
    // rain
    if (rainMesh.visible) {
      const on = t < rainUntil;
      let alive = 0;
      drops.forEach((d, i) => {
        d.y -= d.v * dt;
        if (d.y < 0) { if (on) { d.y = 50 + Math.random() * 12; d.x = Math.random() * W; d.z = Math.random() * H; } else d.y = -100; }
        if (d.y > -50) alive++;
        m4.makeTranslation(d.x, d.y, d.z);
        rainMesh.setMatrixAt(i, m4);
      });
      rainMesh.instanceMatrix.needsUpdate = true;
      if (!on && !alive) rainMesh.visible = false;
    }
    placeLabels();
  });

  return {
    map,
    /** Columns for week index i: height from cases / epidemic line, colour from the heat ramp. */
    setWeek(values, { duration = 900 } = {}) { map.setValues(values, { duration }); },
    /** Round 2 intel: { unitId: level } for watch/warning/above (rings + tags); null hides it. */
    setIntel(levels, tags = {}) {
      intelOn = !!levels;
      sweepBox.visible = intelOn && !reduced();
      for (const [u, m] of rings) {
        const lv = levels?.[u];
        m.visible = !!lv && lv !== "normal";
        m.userData.level = lv;
        if (m.visible) m.material.color.set(LCOL[lv]);
      }
      for (const [u, el2] of labels) {
        const tag = el2.querySelector(".board__tag");
        tag.textContent = tags[u] ?? "";
        tag.style.color = LCOL[levels?.[u]] || "";
      }
      map.render();
    },
    setTeams(counts, opts) {
      setTeams(counts, opts);
      for (const [u, el2] of labels) el2.querySelector(".board__team").textContent = "";
    },
    setBugs,
    rain(ms = 2600) { if (reduced()) return; rainUntil = performance.now() + ms; drops.forEach((d) => { d.y = 20 + Math.random() * 45; }); rainMesh.visible = true; map.render(); },
    select(u) { selected = u; map.highlight(u); for (const [k, el2] of labels) el2.classList.toggle("on", k === u); },
    /** "+N cases" floaters over provinces. */
    floaters(adds) {
      adds.forEach(([u, n], i) => {
        if (!n) return;
        const c = map.centreOf(u);
        if (!c) return;
        const p = map.toScreen(new T.Vector3(c.x, map.heightOf(u) + 2, c.z));
        const f = Object.assign(document.createElement("div"), { className: "board__floater", textContent: `+${Math.round(n).toLocaleString("en")} cases` });
        f.style.left = `${p.x}px`; f.style.top = `${p.y}px`; f.style.animationDelay = `${i * 90}ms`;
        overlay.append(f);
        setTimeout(() => f.remove(), 2600);
      });
    },
    resetView() { map.setView(); },
    dispose() {
      bugs.forEach((b) => scene.remove(b.s));
      for (const k of tokens.values()) { k.sprite.material.map.dispose(); k.sprite.material.dispose(); }
      disposables.forEach((d) => d.dispose?.());
      rainMesh.dispose();
      map.dispose();
      overlay.remove();
    },
  };
}

// without WebGL the voxel engine falls back to a flat 2D map; the game still works, just without the 3D pieces
function flatBoard(map) {
  const none = () => {};
  return { map, setWeek: (v) => map.setValues(v), setIntel: none, setTeams: none, setBugs: none, rain: none,
    select: (u) => map.highlight(u), floaters: none, resetView: none, dispose: () => map.dispose() };
}
