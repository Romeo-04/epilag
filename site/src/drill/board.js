// The Dengue Drill's board: the region's diorama (world.js) plus the game's pieces in the same scene:
//   intel rings that pulse by forecast level and a scan line sweeping the island (round 2),
//   shield tokens that drop with a bounce and a puff of dust when teams deploy,
//   pixel mosquitoes swarming over the provinces (count from rain, as before), outbreaks glowing,
//   the week's weather (rain from the data; a heavier burst when two weeks pass),
// plus HTML labels, forecast tags and "+N cases" floaters projected from 3D.
import { createWorld } from "./world.js";
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
  "..KKKKKKKK..", ".KLLGGGGGGK.", "KLGGGGGGGGGK", "KLGGGGGGGGGK", "KGGGGGGGGGGK", "KGGGGGGGGGGK", "KGGGGGGGGGGK",
  ".KGGGGGGGGK.", ".KGGGGGGGGK.", "..KGGGGGGK..", "...KGGGGK...", "....KGGK....", ".....KK.....",
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

export async function createBoard(el, { grid, region, onPick, onFlash }) {
  const overlay = Object.assign(document.createElement("div"), { className: "board__overlay" });
  let selected = null, world = null;
  world = await createWorld(el, { grid, pixel: 2, onPick, onFlash, onHover: (u) => world?.highlight(u ?? selected) });
  el.append(overlay);
  const T = world.three, scene = world.scene, ids = region.provinces.map((p) => p.id);
  const mosquito = await loadSprite("mosquito");
  const disposables = [];
  const keep = (x) => { disposables.push(x); return x; };
  const [W, H] = world.size;

  // ------------------------------------------------------------------ HTML labels projected from 3D
  const labels = new Map(ids.map((u, k) => {
    const el2 = document.createElement("div");
    el2.className = "board__label";
    el2.innerHTML = `<span class="board__name">${region.provinces[k].name.replace(/ \(.+\)/, "")}</span><span class="board__tag"></span>`;
    overlay.append(el2);
    return [u, el2];
  }));
  function placeLabels() {
    for (const [u, el2] of labels) {
      const c = world.centreOf(u);
      if (!c) { el2.hidden = true; continue; }
      const p = world.toScreen(new T.Vector3(c.x, world.heightOf(u) + 1, c.z));
      el2.style.transform = `translate(${Math.round(p.x)}px, ${Math.round(p.y)}px)`;
    }
  }

  // ------------------------------------------------------------------ intel rings and the scan line (round 2)
  const ringGeo = keep(new T.RingGeometry(0.82, 1, 40));
  const rings = new Map();
  for (const u of ids) {
    const c = world.centreOf(u);
    if (!c) continue;
    const m = new T.Mesh(ringGeo, keep(new T.MeshBasicMaterial({ color: "#6FD6FF", transparent: true, opacity: 0.9, side: T.DoubleSide, depthWrite: false })));
    m.rotation.x = -Math.PI / 2;
    m.position.set(c.x, 0, c.z);
    m.visible = false;
    m.userData = { r: Math.max(2.5, Math.sqrt(world.cellsOf(u).length / Math.PI) * 0.9), level: null };
    scene.add(m);
    rings.set(u, m);
  }
  const sweep = new T.Mesh(keep(new T.BoxGeometry(0.8, 14, H + 14)), keep(new T.MeshBasicMaterial({ color: "#6FD6FF", transparent: true, opacity: 0.16, depthWrite: false })));
  sweep.position.set(0, 7, H / 2);
  sweep.visible = false;
  scene.add(sweep);

  // ------------------------------------------------------------------ team tokens and dust
  const tokens = new Map();
  const dust = [];
  const dustGeo = keep(new T.BoxGeometry(0.5, 0.5, 0.5)), dustMat = keep(new T.MeshLambertMaterial({ color: "#D9C48A" }));
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
    world.render();
  }
  function puff(u) {
    const c = world.centreOf(u), y = world.heightOf(u);
    for (let i = 0; i < 18; i++) {
      const m = new T.Mesh(dustGeo, dustMat);
      m.position.set(c.x, y + 0.5, c.z);
      m.userData = { vx: (Math.random() - 0.5) * 10, vy: 3 + Math.random() * 6, vz: (Math.random() - 0.5) * 10, life: 0.6 + Math.random() * 0.4, age: -0.4 };
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
      const s = new T.Sprite(bugMat[i % 2]);
      s.scale.set(1.5, 1.5, 1);
      scene.add(s);
      return { s, a: anchors[Math.floor(Math.random() * anchors.length)], p: Math.random() * 6.28, sp: 0.6 + Math.random() * 0.8, r: 1.5 + Math.random() * 4, h: 3 + Math.random() * 5 };
    });
    world.render();
  }

  // ------------------------------------------------------------------ the frame loop
  let intelOn = false, weekRain = 0, burstUntil = 0;
  world.addTicker((t, dt) => {
    for (const [u, k] of tokens) {
      const c = world.centreOf(u), top = world.heightOf(u) + 3.2;
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
    if (intelOn) {
      for (const [u, m] of rings) {
        if (!m.visible) continue;
        const speed = m.userData.level === "warning" ? 1.6 : 2.6, k = ((t / 1000) / speed + m.userData.r) % 1;
        m.position.y = world.heightOf(u) + 0.3;
        m.scale.setScalar(m.userData.r * (reduced() ? 1.2 : 0.9 + k * 0.7));
        m.material.opacity = reduced() ? 0.9 : 0.95 * (1 - k);
      }
      sweep.position.x = reduced() ? -20 : (((t / 3600) % 1) * (W + 30)) - 15;
    }
    const fr = Math.floor(t / 90) % 2;
    for (const b of bugs) {
      b.p += dt * 3 * b.sp;
      const c = world.centreOf(b.a);
      b.s.material = bugMat[fr];
      b.s.position.set(c.x + Math.cos(b.p * 1.3) * b.r, world.heightOf(b.a) + b.h + Math.sin(b.p * 2.1), c.z + Math.sin(b.p) * b.r);
    }
    if (burstUntil && t > burstUntil) { burstUntil = 0; world.setWeather({ rain: weekRain, storm: weekRain > 0.8 }); }
    placeLabels();
  });

  return {
    world,
    setWeek(values, { duration = 900 } = {}) { world.setValues(values, { duration }); },
    /** Outbreak provinces (cases above the epidemic line) glow. */
    setGlow(list) { world.setGlow(list); },
    /** The week's rain in mm (region average) sets the weather, from drizzle to a storm. */
    setRain(mm) { weekRain = Math.min(1, Math.max(0.04, mm / 70)); if (!burstUntil) world.setWeather({ rain: weekRain, storm: weekRain > 0.8 }); },
    /** A heavier downpour for a few seconds (two weeks passing), then back to the week's rain. */
    burst(ms = 2600) { if (reduced()) return; burstUntil = performance.now() + ms; world.setWeather({ rain: 1, storm: true }); },
    setIntel(levels, tags = {}) {
      intelOn = !!levels;
      sweep.visible = intelOn && !reduced();
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
      world.render();
    },
    setTeams,
    setBugs,
    select(u) { selected = u; world.highlight(u); for (const [k, el2] of labels) el2.classList.toggle("on", k === u); },
    floaters(adds) {
      adds.forEach(([u, n], i) => {
        if (!n) return;
        const c = world.centreOf(u);
        if (!c) return;
        const p = world.toScreen(new T.Vector3(c.x, world.heightOf(u) + 2, c.z));
        const f = Object.assign(document.createElement("div"), { className: "board__floater", textContent: `+${Math.round(n).toLocaleString("en")} cases` });
        f.style.left = `${p.x}px`; f.style.top = `${p.y}px`; f.style.animationDelay = `${i * 90}ms`;
        overlay.append(f);
        setTimeout(() => f.remove(), 2600);
      });
    },
    zoomBy: (f) => world.zoomBy(f),
    rotateBy: (d) => world.rotateBy(d),
    resetView: () => world.resetView(),
    dispose() {
      bugs.forEach((b) => scene.remove(b.s));
      for (const k of tokens.values()) { k.sprite.material.map.dispose(); k.sprite.material.dispose(); }
      disposables.forEach((d) => d.dispose?.());
      world.dispose();
      overlay.remove();
    },
  };
}
