// Landing page: fills the live parts (3D maps, priority list, drill console) from the 2 Jun 2019 replay data,
// places the scroll-following mosquito, and runs the scroll animations.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./landing.css";
import { hydrateIcons, icon } from "../lib/icons.js";
import { TOOLS } from "../lib/content.js";
import "../lib/pixel.js";
import { Mascot } from "../lib/mascot.js";
import { gsap, ScrollTrigger, countUp, curtain, reduced, reveal } from "../lib/motion.js";
import { createVoxelMap, loadGrids } from "../lib/voxel.js";
import { playIntro } from "./intro.js";
import { playFinale } from "./finale.js";
import { rules } from "../drill/rules.js";

const $ = (id) => document.getElementById(id);
const BASE = import.meta.env.BASE_URL;
const LV = { warning: ["#F04B2A", 4, "Outbreak warning"], watch: ["#F58220", 3, "Watch"], above: ["#F7C928", 2, "Above usual"], normal: ["#0C7A55", 1, "Normal"] };
const NODATA = { color: "#C9CFC9", height: 1 };
const day = (s) => new Date(`${s}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
const fmt = (n) => Math.round(n).toLocaleString("en");
const phone = matchMedia("(max-width: 680px)").matches;

// ------------------------------------------------------------------ static parts
// six tools as a getcko-style step band: icon tile, number, highlighted name, one line; dotted links between
const toolStep = (t, i) => `<li class="ts-step"><a href="web/?page=${t.page}">
  <span class="ts-icon">${icon(t.icon, { size: 48 })}</span>
  <span class="ts-head"><span class="ts-n nums">0${i + 1}</span><span class="ts-label"><span class="ts-mark" aria-hidden="true"></span>${t.name}</span></span>
  <span class="ts-line">${t.short}</span></a></li>`;
const toolLink = (i) => `<li class="ts-link" data-after="${i}" aria-hidden="true">${"<span><i></i></span>".repeat(6)}</li>`;
$("tools").innerHTML = TOOLS.map((t, i) => (i ? toolLink(i - 1) : "") + toolStep(t, i)).join("");

const INSIDE = [["menu", 24, "home", "Overview", "A quick view of the situation."], ["forecastMap", 32, "map", "Forecast Map", "See areas at higher risk in the next weeks."],
  ["areaDetail", 32, "unit", "Area Detail", "Explore local forecasts and trends."], ["actionPlan", 32, "budget", "Action Plan", "Find where resources have the greatest impact."],
  ["didItWork", 32, "proof", "Did It Work?", "Check how well forecasts match actual cases."], ["residents", 32, "public", "For Residents", "Simple guidance for safer communities."]];
$("inside").innerHTML = INSIDE.map(([ic, s, page, name, text]) => `<li><a href="web/?page=${page}">${icon(ic, { size: s })}<div><b>${name}</b><span>${text}</span></div>${icon("chevronRight", { size: 24 })}</a></li>`).join("");
hydrateIcons();

// first visit: pixel intro, then the hero window's pixel curtain lifts
let introDone;
const introFinished = new Promise((r) => { introDone = r; });
const heroIn = () => {
  introDone();
  if (reduced()) return;
  gsap.from("[data-hero-copy] > *", { autoAlpha: 0, y: 24, duration: 0.8, stagger: 0.08, ease: "expo.out" });
  gsap.from("[data-hero-window]", { y: 60, scale: 0.94, duration: 0.9, ease: "back.out(1.6)" });
  curtain($("hero-map"), { cell: 16 }).play(0.15);
};
if (document.documentElement.classList.contains("intro-pending")) playIntro(heroIn); else heroIn();

// ------------------------------------------------------------------ data-driven parts
// hero: the latest forecast from the open data, 4 weeks ahead, for the 17 regions and Quezon City
const LEVEL = { "outbreak warning": "warning", warning: "warning", watch: "watch", "above usual": "above", above: "above", normal: "normal" };
const dayY = (s) => new Date(`${s}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
const areaName = (n) => n.replace(/^REGION /, "Region ");
const latest = (await fetch(`${BASE}data/epilag_forecast_region_qc.json`).then((r) => r.json()).catch(() => []))
  .filter((r) => r.weeks_ahead === 4).map((r) => ({ ...r, lv: LEVEL[r.alert_level] || "normal" }))
  .sort((a, b) => b.cases_middle_per_100k - a.cases_middle_per_100k);
const bars = (lv) => `<span class="bar" aria-hidden="true">${[1, 2, 3, 4].map((k) => `<i class="${k <= LV[lv][1] ? "on" : ""}"></i>`).join("")}</span>`;
if (latest.length) {
  $("hero-sub").textContent = `Forecast made from the week ending ${dayY(latest[0].forecast_made_week_ending)} · for the week ending ${dayY(latest[0].target_week_ending)}`;
  $("hero-counts").innerHTML = ["warning", "watch", "above", "normal"]
    .map((lv) => `<li data-lv="${lv}"><span class="sq"></span><b class="nums">${latest.filter((r) => r.lv === lv).length}</b>${LV[lv][2]}</li>`).join("");
  $("hero-prio").innerHTML = latest.slice(0, 3).map((r, i) => `<div class="prio" data-lv="${r.lv}" ${i === 0 ? 'id="prio-first"' : ""}><span class="rank">${i + 1}</span>
    <div><div class="name">${areaName(r.area_name)}</div><div class="fc nums">${fmt(r.cases_middle)} (${fmt(r.cases_low)}–${fmt(r.cases_high)})</div></div>${bars(r.lv)}</div>`).join("");
  $("hero-table").innerHTML = `<table><thead><tr><th>Area</th><th>Level</th><th>Cases (range)</th><th>/100k</th></tr></thead><tbody>${latest.map((r) =>
    `<tr><td>${areaName(r.area_name)}</td><td><span class="lv" data-lv="${r.lv}">${LV[r.lv][2]}</span></td><td class="nums">${fmt(r.cases_middle)} (${fmt(r.cases_low)}–${fmt(r.cases_high)})</td><td class="nums">${r.cases_middle_per_100k.toFixed(1)}</td></tr>`).join("")}</tbody></table>`;
}
document.querySelectorAll(".hero__views [data-view]").forEach((b) => b.addEventListener("click", () => {
  const table = b.dataset.view === "table";
  document.querySelectorAll(".hero__views [data-view]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  $("hero-table").hidden = !table;
}));

// 2019 replay: the proof numbers, the Guimaras story and the drill console
const data = await fetch(`${BASE}data/replay_2019-06-02.json`).then((r) => r.json());
const H = data.horizons;
const claim4 = data.claim[4];
$("proof-claim").querySelectorAll("[data-count]").forEach((el, i) => { el.dataset.count = String(i ? claim4.crossed : claim4.flagged); el.textContent = el.dataset.count; });

// Guimaras card (the case the README tells)
const gid = Object.keys(data.names).find((u) => data.names[u] === "Guimaras");
const g = H[4].units[gid];
$("g-q50").textContent = fmt(g[2]); $("g-range").textContent = `${fmt(g[1])}–${fmt(g[3])}`; $("g-actual").textContent = fmt(g[4]);
$("brief-meta").innerHTML = `Forecast: ${fmt(g[2])} cases · likely range ${fmt(g[1])}–${fmt(g[3])}<br>Week ending ${day(H[4].target)} 2019`;

// drill console: a still of the game screen for Western Visayas on the turn of 2 Jun 2019, from the game's own data
// and rules (heat ramp, epidemic lines, outbreak pressure) so it reads like the real thing
const GAME = await fetch(`${BASE}drill/data.json`).then((r) => r.json());
const RG = rules(GAME), DW = RG.idx("2019-06-02"), DT = GAME.turns.indexOf("2019-06-02"), KITS = GAME.kit.kits;
const WV = GAME.regions.find((r) => r.id === "PH06"), regionName = WV.name.replace(/^Region VI \((.+)\)$/, "$1");
const PRESS = { low: ["Low", "#34D27B"], rising: ["Rising", "#F7C928"], high: ["High", "#F58220"], critical: ["Critical", "#F04B2A"] };
const casesAt = (j) => WV.provinces.reduce((s, p) => s + (p.cases[j] || 0), 0), now = casesAt(DW), before = casesAt(DW - 2);
const fcOf = (p) => p.fc?.[GAME.turns[DT]];
const pr = RG.pressure(WV, DW), [prLab, prCol] = PRESS[pr.level];
$("dc-region").textContent = regionName;
$("dc-cases").textContent = fmt(now);
$("dc-change").textContent = `${now >= before ? "▲" : "▼"} ${Math.abs(Math.round((now / before - 1) * 100))}% in 2 weeks`;
$("dc-press").textContent = prLab; $("dc-press").style.color = prCol;
$("dc-meter").style.transform = `scaleX(${Math.min(1, pr.value / 2)})`; $("dc-meter").style.background = prCol;
$("dc-timeline").innerHTML = GAME.turns.map((w, t) => `<li class="${t < DT ? "done" : t === DT ? "now" : ""}"><i></i><span>${day(w)}</span></li>`).join("");
// round 1 colours the board by cases against each epidemic line (the game's heat ramp); round 2 by EpiLag-PH's forecast
const heatValues = Object.fromEntries(WV.provinces.map((p) => [p.id, { color: RG.heat(p, DW), height: Math.max(1, Math.min(4, Math.round((p.cases[DW] / p.epi[DW]) * 1.6))) }]));
const intelValues = Object.fromEntries(WV.provinces.map((p) => { const f = fcOf(p); return [p.id, f ? { color: LV[f[0]][0], height: LV[f[0]][1] } : NODATA]; }));
const busiest = WV.provinces.reduce((a, b) => (b.cases[DW] > a.cases[DW] ? b : a));
const warned = WV.provinces.filter((p) => fcOf(p)?.[0] === "warning");
// pick, deploy, replay: who holds teams, which row is selected, what the ticker says
const STEPS = [
  { teams: {}, on: null, ticker: `Mission: ${regionName}, 2019 rainy season. Select an area.` },
  { teams: { [busiest.id]: 2 }, on: busiest.id,
    ticker: `2 teams to ${busiest.name}: ${fmt(busiest.cases[DW])} cases, ${(busiest.cases[DW] / busiest.epi[DW]).toFixed(1)}× its epidemic line.` },
  { teams: Object.fromEntries(warned.map((p) => [p.id, 1])), on: null,
    ticker: `Intel: ${warned.map((p) => p.name).join(", ")} hit outbreak warning in 4 weeks.` },
];
let drillMap = null, drillOn = -1;
function drillStep(i) {
  if (i === drillOn) return;
  drillOn = i;
  const st = STEPS[i], intel = i === 2, used = Object.values(st.teams).reduce((a, b) => a + b, 0);
  $("dc-round").textContent = intel ? "Round 2 · EpiLag intel" : "Round 1 · No intel";
  $("dc-round").classList.toggle("chip--intel", intel);
  $("dc-budget").textContent = `₱${((KITS - used) * GAME.kit.pesos / 1e6).toFixed(1)}M`;
  $("dc-tokens").innerHTML = Array.from({ length: KITS }, (_, t) => `<i class="${t >= KITS - used ? "spent" : ""}"></i>`).join("");
  $("dc-left").textContent = `${KITS - used} of ${KITS} teams left`;
  $("dc-ticker").textContent = st.ticker;
  $("dc-legend").innerHTML = intel
    ? `<span class="intel">◯ EpiLag intel: forecast 4 weeks ahead</span>${["warning", "watch", "above", "normal"].map((l) => `<span class="dgame__lv" style="--c:${LV[l][0]}">${LV[l][2]}</span>`).join("")}`
    : `<span>Cases vs epidemic line</span><span class="grad"></span>`;
  $("dc-plist").innerHTML = WV.provinces.map((p) => {
    const f = fcOf(p), n = st.teams[p.id];
    return `<div class="dgame__row${st.on === p.id ? " on" : ""}"><span class="dgame__heat" style="background:${RG.heat(p, DW)}"></span><span class="dgame__nm">${p.name}</span>`
      + (intel && f && f[0] !== "normal" ? `<span class="dgame__fc" data-lv="${f[0]}">▲${fmt(f[2])}</span>` : "<span></span>")
      + `<span class="dgame__n nums">${fmt(p.cases[DW])}</span>${n ? `<span class="dgame__team">${n}</span>` : "<span></span>"}</div>`;
  }).join("");
  $("drill-map").setAttribute("aria-label", `3D map of the ${regionName} provinces coloured by ${intel ? "the EpiLag-PH forecast 4 weeks ahead" : "cases against each epidemic line"}, week ending ${day(GAME.turns[DT])} 2019`);
  drillMap?.setValues(intel ? intelValues : heatValues, { duration: 600 });
  drillMap?.highlight(st.on);
}
drillStep(2); // without motion the still shows round 2; the scroll timeline starts it at pick

// ------------------------------------------------------------------ 3D maps (created when near the viewport)
const grids = loadGrids("voxel_ph"), boards = loadGrids("voxel_regions");
function whenNear(el, fn) {
  const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); fn(); } }, { rootMargin: "300px" });
  io.observe(el);
}
// island names over the hero map, placed at a region's projected centre
const ISLANDS = [["Luzon", "R_REGION_III", 34, -6], ["Visayas", "R_REGION_VII", 30, 0], ["Mindanao", "R_REGION_X", 34, 4]];
whenNear($("hero-map"), async () => {
  const gr = await grids, grid = phone ? gr.region_coarse : gr.region;
  const map = await createVoxelMap($("hero-map"), { grid, pixel: phone ? 2 : 3, markers: true });
  const byArea = Object.fromEntries(latest.map((r) => [r.area_code, { color: LV[r.lv][0], height: LV[r.lv][1] }]));
  map.setValues({ ...Object.fromEntries(map.units.map((u) => [u, NODATA])), ...byArea }, { duration: 900 });
  const place = () => {
    $("hero-labels").innerHTML = ISLANDS.map(([name, u, dx, dy]) => {
      const p = map.project(u);
      return p ? `<span style="left:${Math.round(p.x + dx)}px;top:${Math.round(p.y + dy)}px">${name}</span>` : "";
    }).join("");
  };
  setTimeout(place, 950);
  new ResizeObserver(place).observe($("hero-map"));
});

whenNear($("drill-map"), async () => {
  const b = await boards;
  const m = await createVoxelMap($("drill-map"), { grid: b.PH06, pixel: 3, pitch: 46, sea: "#1C4F6E" });
  m.setValues(drillOn === 2 ? intelValues : heatValues, { duration: 1200 });
  m.highlight(STEPS[drillOn]?.on ?? null);
  drillMap = m;
});
whenNear($("action-map"), async () => {
  const b = await boards;
  const m = await createVoxelMap($("action-map"), { grid: b.PH06, pixel: 3, pitch: 44, yaw: -8 });
  const faint = Object.fromEntries(b.PH06.units.map((u) => [u, { color: "#D3DECF", height: 1 }]));
  m.setValues({ ...faint, [gid]: { color: LV[g[0]][0], height: 4 } }, { duration: 1200 });
});

// ------------------------------------------------------------------ mascot (the mosquito follows the reader)
// It flies from section to section, standing on alternate sides of the page and facing the content, then
// ends in the frog's mouth at the bottom of the page.
let mascot = null;
// a slot that hops between items (the lit chain step, the lit tool): `place(item, box)` gives its left/top in
// px inside the slot's offset parent, whose box is passed in; the slot's CSS transition makes the hop
function hopper(slotEl, items, place) {
  const h = { on: 0, items, move(i) {
    h.on = i;
    const box = slotEl.offsetParent.getBoundingClientRect(), [left, top] = place(items[i], box, slotEl);
    Object.assign(slotEl.style, { left: `${left}px`, top: `${top}px` });
  } };
  h.move(0);
  addEventListener("resize", () => h.move(h.on));
  return h;
}
const lit = (els) => { let i = 0; els.forEach((e, k) => { if (Number(gsap.getProperty(e, "--on")) > 0.5) i = k; }); return i; };
// problem: stand on top of the lit step's prop
const chainHop = hopper($("slot-problem"), [...document.querySelectorAll(".chain__step pixel-sprite")], (el, box, sl) => {
  const r = el.getBoundingClientRect();
  return [r.left + r.width / 2 - box.left - sl.offsetWidth / 2, r.top - box.top - sl.offsetHeight + 4];
});
// six tools: beside the lit tool's icon (desktop), or above the right end of its row (one column)
const toolSteps = [...document.querySelectorAll(".ts-step")];
const toolHop = hopper($("slot-features"), toolSteps, (el, box, sl) => {
  const st = el.getBoundingClientRect(), ic = el.querySelector(".ts-icon").getBoundingClientRect();
  if (matchMedia("(max-width: 1099px)").matches) return [st.right - box.left - sl.offsetWidth, st.top - box.top - sl.offsetHeight + 20];
  return [ic.right - box.left + 4, ic.bottom - box.top - sl.offsetHeight];
});

introFinished.then(() => Mascot.create("mosquito")).then((m) => {
  mascot = m;
  const slot = (id, section, pose, target, extra = {}) => m.register({ id, section: document.querySelector(section), slot: $(`slot-${id}`), target, ...pose, ...extra });
  slot("hero", ".hero", { frames: ["fly1", "fly2"], fps: 12 }, () => $("prio-first"), { flip: false });
  slot("problem", ".problem", { pose: "alert" }, $("problem-callout"), { flip: false });
  slot("drill", ".drill", { pose: "dash" }, document.querySelector(".dgame__end"));
  slot("features", ".features", { pose: "search" }, () => toolSteps[toolHop.on].querySelector(".ts-icon"), { flip: true });
  slot("action", ".alert-action", { pose: "clipboard" }, $("brief"), { flip: true });
  slot("film", ".film", { pose: "front" }, null);
  slot("proof", ".proof", { pose: "check" }, $("proof-claim"));
  // final call to action: the mosquito flies down to the frog, which eats it
  playFinale($("finale"), m);
}).catch(() => playFinale($("finale"), null));

// ------------------------------------------------------------------ scroll animations
reveal(".sec-head, .problem__head, .opendata, .action__card, .action__map, .step, .inside, .film__player, .evidence, .drill__copy > *, .console, .cta__grid > div:first-child");
document.querySelectorAll("[data-count]").forEach((el) => countUp(el));

const mm = gsap.matchMedia();
mm.add({ desk: "(min-width: 1100px) and (prefers-reduced-motion: no-preference)", mob: "(max-width: 1099px) and (prefers-reduced-motion: no-preference)" }, (ctx) => {
  // problem: steps light up in order as you scroll (pinned on desktop, like getcko's "How it works")
  const steps = gsap.utils.toArray(".chain__step");
  const tl = gsap.timeline({ defaults: { ease: "none" },
    scrollTrigger: ctx.conditions.desk
      ? { trigger: ".problem", start: "top top", end: "+=120%", scrub: 0.6, pin: ".problem__pin", anticipatePin: 1 }
      : { trigger: ".chain", start: "top 80%", end: "bottom 45%", scrub: 0.6 },
    onUpdate() { const i = lit(steps); if (i !== chainHop.on) chainHop.move(i); } });
  steps.forEach((s, i) => tl.fromTo(s, { "--on": 0 }, { "--on": 1, duration: 0.4, ease: "steps(2)" }, i * 0.5));
  tl.fromTo("#helps-rail", { "--fill": 0 }, { "--fill": 1, duration: steps.length * 0.5 }, 0);
  tl.to({}, { duration: 0.4 });
  // drill: pick, deploy, replay light up in turn (pinned on desktop) and the console plays each one.
  // Pins must be made in page order: each one's start counts the scroll space added by the pins above it.
  const how = gsap.utils.toArray(".dh-step");
  drillStep(0);
  const dt = gsap.timeline({ defaults: { ease: "none" },
    scrollTrigger: ctx.conditions.desk
      ? { trigger: ".drill__grid", start: "top 84px", end: "+=120%", scrub: 0.6, pin: true, anticipatePin: 1 }
      : { trigger: "#drill-how", start: "top 75%", end: "bottom 40%", scrub: 0.6 },
    onUpdate() { drillStep(lit(how)); } });
  dt.fromTo("#drill-how", { "--fill": 0 }, { "--fill": 1, duration: how.length - 1 }, 0);
  how.forEach((s, i) => dt.fromTo(s, { "--on": 0 }, { "--on": 1, duration: 0.3, ease: "steps(2)" }, i));
  dt.to({}, { duration: 0.6 });
  // action steps: the timeline line fills as the steps scroll past
  // six tools: getcko's "How it works" band. On desktop the heading and band lock under the nav while each
  // step lights up, its name gets the highlighter, its icon pops in two steps, the dots to the next step pop,
  // and the texture slides sideways
  const band = $("tools-band");
  const tt = gsap.timeline({ defaults: { ease: "none" },
    scrollTrigger: ctx.conditions.desk
      ? { trigger: ".features__pin", start: "top 84px", end: "+=140%", scrub: 0.6, pin: true, anticipatePin: 1 }
      : { trigger: band, start: "top 85%", end: "bottom 35%", scrub: 0.6 },
    onUpdate() { const i = lit(toolSteps); if (i !== toolHop.on) toolHop.move(i); } });
  tt.fromTo(band, { "--sf-x": "0px" }, { "--sf-x": "1280px", duration: toolSteps.length }, 0);
  toolSteps.forEach((s, i) => {
    tt.fromTo(s, { "--on": 0 }, { "--on": 1, duration: 0.35, ease: "power2.out" }, i)
      .fromTo(s.querySelector(".ts-mark"), { scaleX: 0 }, { scaleX: 1, duration: 0.3, ease: "power3.out" }, i + 0.05)
      .fromTo(s.querySelector(".ts-icon"), { scale: 0.5 }, { scale: 1, duration: 0.25, ease: "steps(2)" }, i);
    const dots = band.querySelectorAll(`.ts-link[data-after="${i}"] i`);
    if (dots.length) tt.fromTo(dots, { scale: 0 }, { scale: 1, duration: 0.12, ease: "steps(2)", stagger: 0.09 }, i + 0.4);
  });
  tt.to({}, { duration: 0.5 });
  gsap.fromTo(".steps", { "--fill": 0 }, { "--fill": 1, ease: "none", scrollTrigger: { trigger: ".steps", start: "top 80%", end: "bottom 55%", scrub: 0.5 } });
});


// ------------------------------------------------------------------ the film plays, muted, while it is on screen
// Browsers only autoplay muted video; the controls stay so a viewer can unmute. Once the viewer pauses it themselves,
// scrolling no longer starts it. Under reduced motion it waits for a click.
const film = document.querySelector(".film__player video");
if (film && !reduced()) {
  let auto = true, ours = false;
  new IntersectionObserver(([e]) => {
    if (!auto) return;
    if (e.intersectionRatio >= 0.5) film.play().catch(() => {});
    else if (!film.paused) { ours = true; film.pause(); }
  }, { threshold: [0, 0.5] }).observe(film);
  film.addEventListener("pause", () => { if (!ours && !film.ended) auto = false; ours = false; });
}
