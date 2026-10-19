// Landing page: fills the live parts (3D maps, priority list, drill console) from the 2 Jun 2019 replay data,
// places the scroll-following mosquito, and runs the scroll animations. Structure: UI mockup/ final landing page.
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
const data = await fetch(`${BASE}data/replay_2019-06-02.json`).then((r) => r.json());
const H = data.horizons;
const valuesAt = (h) => Object.fromEntries(Object.entries(H[h].units).map(([u, f]) => [u, { color: LV[f[0]][0], height: LV[f[0]][1] }]));
$("t4").textContent = `week of ${day(H[4].target)}`;
$("t8").textContent = `week of ${day(H[8].target)}`;

function renderPrio(h) {
  $("hero-sub").textContent = `Forecast made 2 June 2019 · ${h} weeks ahead (week ending ${day(H[h].target)})`;
  const top = Object.entries(H[h].units).filter(([, f]) => f[0] === "warning" || f[0] === "watch")
    .map(([u, f]) => [u, f, f[2] / data.pop[u] * 1e5]).sort((a, b) => b[2] - a[2]).slice(0, 3);
  $("hero-prio").innerHTML = top.map(([u, f], i) => {
    const bars = LV[f[0]][1];
    return `<div class="prio" data-lv="${f[0]}" ${i === 0 ? 'id="prio-first"' : ""}><span class="rank">${i + 1}</span>
      <div><div class="name">${data.names[u]}</div><div class="fc nums">${fmt(f[2])} (${fmt(f[1])}–${fmt(f[3])}) · <span class="lv-text">${LV[f[0]][2]}</span></div></div>
      <span class="bar" aria-hidden="true">${[1, 2, 3, 4].map((k) => `<i class="${k <= bars ? "on" : ""}"></i>`).join("")}</span></div>`;
  }).join("");
  const c = data.claim[h];
  $("hero-claim").textContent = `${c.flagged} of the ${c.crossed} provinces that crossed the epidemic line ${h} weeks later were flagged watch or warning.`;
}
renderPrio(4);
const claim4 = data.claim[4];
$("proof-claim").querySelectorAll("[data-count]").forEach((el, i) => { el.dataset.count = String(i ? claim4.crossed : claim4.flagged); el.textContent = el.dataset.count; });

// Guimaras card (the case the README tells)
const gid = Object.keys(data.names).find((u) => data.names[u] === "Guimaras");
const g = H[4].units[gid];
$("g-q50").textContent = fmt(g[2]); $("g-range").textContent = `${fmt(g[1])}–${fmt(g[3])}`; $("g-actual").textContent = fmt(g[4]);
$("brief-meta").innerHTML = `Forecast: ${fmt(g[2])} cases · likely range ${fmt(g[1])}–${fmt(g[3])}<br>Week ending ${day(H[4].target)} 2019`;

// drill console (Western Visayas, turn of 2 Jun 2019)
const D = data.drill, provs = Object.entries(D.provinces);
const now = provs.reduce((s, [, p]) => s + (p.cases || 0), 0), before = provs.reduce((s, [, p]) => s + (p.before || 0), 0);
$("dc-title").textContent = `Dengue Drill · ${D.region.replace(/^Region VI \((.+)\)$/, "$1")} (2019)`;
$("dc-turn").textContent = `${D.turn} of ${D.turns}`;
$("dc-budget").textContent = `₱${D.budget / 1e6}M`;
$("dc-cases").textContent = fmt(now);
$("dc-change").textContent = `${now >= before ? "▲" : "▼"} ${Math.abs(Math.round((now / before - 1) * 100))}% in 2 weeks`;
const warned = provs.filter(([, p]) => p.fc?.[0] === "warning").map(([, p]) => p.name);
$("dc-status").lastElementChild.textContent = warned.length ? `${warned.join(", ")} · Outbreak warning` : "No outbreak warning";
const drillValues = Object.fromEntries(provs.map(([u, p]) => [u, p.fc ? { color: LV[p.fc[0]][0], height: LV[p.fc[0]][1] } : NODATA]));

// ------------------------------------------------------------------ 3D maps (created when near the viewport)
const grids = loadGrids("voxel_ph"), boards = loadGrids("voxel_regions");
function whenNear(el, fn) {
  const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); fn(); } }, { rootMargin: "300px" });
  io.observe(el);
}
let heroMap = null, heroH = 4, heroAuto = true;
whenNear($("hero-map"), async () => {
  const gr = await grids;
  heroMap = await createVoxelMap($("hero-map"), { grid: phone ? gr.province_coarse : gr.province, pixel: phone ? 2 : 3, zoom: 1.25 });
  heroMap.setValues({ ...Object.fromEntries(gr.province.units.map((u) => [u, NODATA])), ...valuesAt(4) }, { duration: 0 });
});
function setHorizon(h, { user = false } = {}) {
  if (user) heroAuto = false;
  heroH = h;
  document.querySelectorAll(".hero__step[data-h='4'], .hero__step[data-h='8']").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.h) === h)));
  renderPrio(h);
  heroMap?.setValues(valuesAt(h), { duration: 900 });
  mascot?.setPose("hero", null, ["fly1", "fly2"]);
}
document.querySelectorAll(".hero__step[data-h='4'], .hero__step[data-h='8']").forEach((b) => b.addEventListener("click", () => setHorizon(Number(b.dataset.h), { user: true })));
// hero loop: step between 4 and 8 weeks ahead while the hero is on screen and nobody has clicked
if (!reduced()) {
  let timer = 0;
  ScrollTrigger.create({ trigger: ".hero", start: "top bottom", end: "bottom top",
    onToggle: (st) => { clearInterval(timer); if (st.isActive) timer = setInterval(() => heroAuto && setHorizon(heroH === 4 ? 8 : 4), 3600); } });
}

whenNear($("drill-map"), async () => {
  const b = await boards;
  const m = await createVoxelMap($("drill-map"), { grid: b.PH06, pixel: 3, pitch: 46 });
  m.setValues(drillValues, { duration: 1200 });
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
  slot("hero", ".hero", { frames: ["fly1", "fly2"], fps: 12 }, () => $("prio-first"));
  slot("problem", ".problem", { pose: "alert" }, $("problem-callout"), { flip: false });
  slot("drill", ".drill", { pose: "dash" }, $("dc-status"));
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
  // action steps: the timeline line fills as the steps scroll past
  // six tools: getcko's "How it works" band. Pinned on desktop; each step lights up, its name gets the
  // highlighter, its icon pops in two steps, the dots to the next step pop, and the texture slides sideways
  const band = $("tools-band");
  const tt = gsap.timeline({ defaults: { ease: "none" },
    scrollTrigger: ctx.conditions.desk
      ? { trigger: band, start: "center center", end: "+=140%", scrub: 0.6, pin: true, anticipatePin: 1 }
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

