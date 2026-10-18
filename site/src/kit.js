// Component kit: every token, icon, texture and component on one page, to check against the UI mockups.
import "./css/tokens.css";
import "./css/base.css";
import "./css/surfaces.css";
import "./css/components.css";
import { ICONS, hydrateIcons, icon } from "./lib/icons.js";
import { TOOLS } from "./lib/content.js";
import { loadSprite } from "./lib/pixel.js";
import { Mascot } from "./lib/mascot.js";
import { createVoxelMap, loadGrids } from "./lib/voxel.js";

const $ = (id) => document.getElementById(id);

const CORE = [["Ink", "--ink", "#071711", true], ["Forest", "--forest", "#08754F", true], ["Sage", "--sage", "#789373", true],
  ["Warm white", "--paper", "#FBFAF4"], ["Amber", "--amber", "#F5A51C"], ["Weather blue", "--sky", "#BFE2EC"]];
const LEVELS = [["Warning", "warning", "#F04B2A"], ["Watch", "watch", "#F58220"], ["Above usual", "above", "#F7C928"], ["Normal", "normal", "#0C7A55"], ["No data", "nodata", "#C9CFC9"]];

$("sw-core").innerHTML = CORE.map(([n, v, hex, dark]) =>
  `<div class="sw" style="background:var(${v});color:${dark ? "#fff" : "var(--ink)"}"><b>${n}</b>${hex}</div>`).join("");
$("sw-level").innerHTML = LEVELS.map(([n, lv, hex]) =>
  `<div class="sw" data-lv="${lv}" style="background:var(--c);color:var(--c-ink)"><b>${n}</b>${hex}</div>`).join("");

const fig = (name, size) => `<figure>${icon(name, { size })}<figcaption>${name}</figcaption></figure>`;
const ui = Object.entries(ICONS).filter(([, [g]]) => g === 12).map(([n]) => n);
const art = Object.entries(ICONS).filter(([, [g]]) => g === 16).map(([n]) => n);
$("ic-ui").innerHTML = ui.map((n) => fig(n, 24)).join("") + ui.slice(0, 3).map((n) => fig(n, 36)).join("");
$("ic-art").innerHTML = art.map((n) => fig(n, 48)).join("") + fig("logo", 64);

$("tools").innerHTML = TOOLS.map((t, i) => `<a class="card tool" href="#">
  <span class="ic">${icon(t.icon, { size: 48 })}</span>
  <div><h3>${i + 1}. ${t.name}</h3><p>${t.short}</p></div>
  <span class="go">${icon("arrowRight", { size: 24 })}</span></a>`).join("");

hydrateIcons();

// voxel maps: national provinces + Western Visayas board, coloured by the 2 Jun 2019 forecast (4 weeks ahead)
const LV = { warning: ["#F04B2A", 4], watch: ["#F58220", 3], above: ["#F7C928", 2], normal: ["#0C7A55", 1] };
const voxelDemo = (async () => {
  const [grids, boards, drill] = await Promise.all([loadGrids("voxel_ph"), loadGrids("voxel_regions"),
    fetch(`${import.meta.env.BASE_URL}drill/data.js`).then((r) => r.text())
      .then((t) => JSON.parse(t.replace(/^window\.DRILL = /, "").trim().replace(/;$/, "")))]);
  const values = {}, names = {};
  drill.regions.forEach((r) => r.provinces.forEach((p) => {
    names[p.id] = p.name;
    const f = p.fc["2019-06-02"];
    if (f) values[p.id] = { color: LV[f[0]][0], height: LV[f[0]][1] };
  }));
  const pick = (u) => { $("voxel-pick").textContent = u ? `${names[u] ?? u}: ${values[u] ? "forecast level shown" : "no forecast"}` : "Click a province."; };
  const ph = await createVoxelMap($("voxel-ph"), { grid: grids.province, onPick: (u) => { ph.highlight(u); pick(u); } });
  ph.setValues(values);
  const wv = await createVoxelMap($("voxel-wv"), { grid: boards.PH06, pixel: 4, pitch: 48, onPick: (u) => { wv.highlight(u); pick(u); } });
  wv.setValues(values);
})().catch((e) => { $("voxel-pick").textContent = `Voxel demo failed: ${e.message}`; });

// sprites: gallery of every pose, then the scroll demo
const sheets = ["mosquito", "frog"];
Promise.allSettled(sheets.map(loadSprite)).then(async (res) => {
  const ok = res.map((r, i) => r.status === "fulfilled" && [sheets[i], r.value]).filter(Boolean);
  if (!ok.length) { $("sprite-missing").hidden = false; return; }
  $("sprite-gallery").innerHTML = ok.flatMap(([name, s]) => Object.keys(s.poses).map((pose) =>
    `<figure>${[2, 4, 8].map((k) => `<pixel-sprite sprite="${name}" pose="${pose}" scale="${k}"></pixel-sprite>`).join("")}<figcaption>${name} · ${pose}</figcaption></figure>`)).join("");
  if (!ok.some(([n]) => n === "mosquito")) return;
  const m = await Mascot.create("mosquito");
  m.register({ id: "a", section: $("demo-a"), slot: $("slot-a"), frames: ["fly1", "fly2"], target: $("target-a") });
  m.register({ id: "b", section: $("demo-b"), slot: $("slot-b"), pose: "pin", target: $("target-b") });
  m.register({ id: "c", section: $("demo-c"), slot: $("slot-c"), pose: "clipboard", flip: true, target: $("target-c") });
}).finally(() => voxelDemo.finally(() => { $("kit").dataset.ready = "1"; }));
