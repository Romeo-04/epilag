// Dengue Drill: command a dengue response twice (round 1: case reports only; round 2: with EpiLag-PH's 4-week
// forecasts) on a 3D pixel board, scored on the real cases (rules.js, the same rules as scripts/drill_data.py).
// Missions: Quezon City in 2024-25 (the latest data, barangay by barangay, estimated from the city's weekly cases;
// scripts/qc_drill_data.py) and the 17 regions in 2019, province by province (scripts/drill_data.py).
// Flow: title -> receipt -> round 1 -> report -> round 2 -> report -> debrief.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./drill.css";
import "../lib/pixel.js";
import { hydrateIcons, icon } from "../lib/icons.js";
import { loadGrids } from "../lib/voxel.js";
import { createWorld } from "./world.js";
import { rules } from "./rules.js";
import { createBoard } from "./board.js";

const json = (f) => fetch(`${import.meta.env.BASE_URL}drill/${f}`).then((r) => r.json());
const [D2019, DQ, boards2019, boardsQC] = await Promise.all([json("data.json"), json("qc.json"), loadGrids("voxel_regions"), loadGrids("voxel_qc")]);
const R2019 = rules(D2019);
const byTotal = (reg, R) => [...reg.provinces].sort((a, b) => R.total(b) - R.total(a));
// Quezon City first (the latest data), then the 17 regions of 2019
const MISSIONS = [
  { id: "QC", D: DQ, R: rules(DQ), region: DQ.regions[0], board: boardsQC.QC, year: "2024–25", place: "Quezon City", unit: ["barangay", "barangays"], estimated: true },
  ...D2019.regions.map((r) => ({ id: r.id, D: D2019, R: R2019, region: r, board: boards2019[r.id], year: "2019", place: "Philippines", unit: ["province", "provinces"] })),
];
let M, R, K, WEEKS, TURNS, FIRST, idx;
function useMission(m) { M = m; R = m.R; ({ K, WEEKS, TURNS, FIRST, idx } = R); }
const LEVEL = { warning: "Outbreak warning", watch: "Watch", above: "Above usual", normal: "Normal" };
const GRADE_COL = { S: "#6FD6FF", A: "#34D27B", B: "#F7C928", C: "#F58220", D: "#F04B2A" };
const $ = (id) => document.getElementById(id);
const fmt = (n) => Math.round(n).toLocaleString("en");
const day = (s) => new Date(`${s}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
const dayY = (s) => `${day(s)} ${s.slice(0, 4)}`;
const cap = (s) => s[0].toUpperCase() + s.slice(1);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const short = (name) => name.replace(/ \(.+\)/, "");
// for tests/test_drill_rules.py (parity with scripts/drill_data.py through Playwright)
window.drill = { D: D2019, R: R2019, missions: MISSIONS };

let regionIdx = 0;
useMission(MISSIONS[0]);
let region, round, turn, kits, plan, sel = null, results = {}, board = null;

// ------------------------------------------------------------------ sound (synthesised, no audio files)
let ac = null, muted = false;
function tone(freq, dur, type = "sine", vol = 0.06, when = 0, slide = 0) {
  if (muted) return;
  try {
    ac ||= new (window.AudioContext || window.webkitAudioContext)();
    const t0 = ac.currentTime + when, o = ac.createOscillator(), g = ac.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t0); if (slide) o.frequency.exponentialRampToValueAtTime(slide, t0 + dur);
    g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g).connect(ac.destination); o.start(t0); o.stop(t0 + dur);
  } catch { /* no audio available */ }
}
const sfx = {
  click: () => tone(880, 0.06, "square", 0.025),
  deploy: () => { tone(330, 0.09, "square", 0.04); tone(660, 0.14, "square", 0.04, 0.08); },
  recall: () => tone(440, 0.12, "square", 0.035, 0, 220),
  turn: () => { tone(120, 0.5, "sawtooth", 0.035, 0, 60); tone(300, 0.35, "sine", 0.03, 0.1, 900); },
  alarm: () => { tone(740, 0.12, "square", 0.04); tone(740, 0.12, "square", 0.04, 0.18); },
  grade: () => [523, 659, 784, 1047].forEach((f, i) => tone(f, 0.18, "triangle", 0.06, i * 0.11)),
  thunder: () => { tone(60, 1.2, "sawtooth", 0.05, 0.15, 30); tone(90, 0.8, "triangle", 0.04, 0.1, 40); },
};
// rain on the roof: filtered noise whose volume follows the week's rain (and the mute button)
let rainGain = null;
function rainSound(level) {
  try {
    if (!rainGain) {
      if (muted || !level) return;
      ac ||= new (window.AudioContext || window.webkitAudioContext)();
      const buf = ac.createBuffer(1, ac.sampleRate * 2, ac.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      const src = ac.createBufferSource(), lp = ac.createBiquadFilter();
      src.buffer = buf; src.loop = true; lp.type = "lowpass"; lp.frequency.value = 1400;
      rainGain = ac.createGain(); rainGain.gain.value = 0;
      src.connect(lp).connect(rainGain).connect(ac.destination); src.start();
    }
    rainGain.gain.setTargetAtTime(muted ? 0 : level * 0.05, ac.currentTime, 0.6);
  } catch { /* no audio available */ }
}
let rainLevel = 0;
$("mute").addEventListener("click", () => {
  muted = !muted;
  rainSound(muted ? 0 : rainLevel);
  $("mute").setAttribute("aria-pressed", String(muted));
  $("mute").setAttribute("aria-label", muted ? "Sound off" : "Sound on");
  $("mute").innerHTML = icon(muted ? "soundOff" : "sound", { size: 24 });
});

function show(id) { document.querySelectorAll(".screen").forEach((s) => s.classList.toggle("on", s.id === id)); scrollTo({ top: 0 }); if (id !== "s-game") coach.hide(); }

// ------------------------------------------------------------------ walkthrough (first play) and the how-to-play guide
const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage blocked */ } } };
// each step points at one control; steps with `wait` move on when the player does the action
const TOUR = [
  { at: "#board", text: () => `Each block is a ${M.unit[0]}. Taller and redder means more cases than usual.` },
  { at: "#plist", wait: "pick", text: () => `Pick a ${M.unit[0]} on the map or in this list.` },
  { at: "#deploy", wait: "deploy", text: () => `Send a team. One team protects about ${fmt(Math.round(R.PEOPLE / 1000) * 1000)} people.` },
  { at: "#end", wait: "end", text: () => "End the turn. Two weeks pass and new reports come in." },
  { at: "#h-timeline", text: () => `Teams take 2 weeks to show, so send them before cases peak. You have ${TURNS.length} turns.` },
];
const TIP2 = [{ at: "#board", text: () => "Blue rings are forecasts for 4 weeks ahead. Use them to get in early." }];
const coach = (() => {
  const el = $("coach"), ring = $("coach-ring");
  let steps = TOUR, step = -1, key = null, timer = 0;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function place() {
    const t = document.querySelector(steps[step]?.at);
    if (!t) { ring.hidden = true; return; }
    const r = t.getBoundingClientRect(), b = el.getBoundingClientRect(), vw = innerWidth, vh = innerHeight, gap = 18;
    ring.hidden = false;
    Object.assign(ring.style, { left: `${r.left - 5}px`, top: `${r.top - 5}px`, width: `${r.width + 10}px`, height: `${r.height + 10}px` });
    let x = r.left + (r.width - b.width) / 2, y;
    if (r.width > vw * 0.45 && r.height > vh * 0.35) y = r.top + r.height * 0.6;            // a large target (the board): sit inside it
    else if (t.closest(".side") && r.left - b.width - gap > 0) { x = r.left - b.width - gap; y = r.top + (r.height - b.height) / 2; } // the side panel: sit beside it
    else if (r.top - b.height - gap > 0) y = r.top - b.height - gap;
    else y = r.bottom + gap;
    el.style.transform = `translate(${Math.round(clamp(x, 8, vw - b.width - 8))}px, ${Math.round(clamp(y, 8, vh - b.height - 8))}px)`;
  }
  function go(n) {
    step = n;
    // a step whose action is already done (an area is picked) is skipped
    while (steps[step]?.wait === "pick" && sel != null) step++;
    if (step >= steps.length) return finish();
    const s = steps[step];
    $("coach-n").textContent = steps.length > 1 ? `${step + 1} / ${steps.length}` : "Round 2";
    $("coach-text").textContent = s.text();
    $("coach-next").hidden = !!s.wait;
    $("coach-next").textContent = step === steps.length - 1 ? "Got it" : "Next";
    $("coach-skip").hidden = steps.length === 1;
    el.hidden = false;
    const t = document.querySelector(s.at), r = t?.getBoundingClientRect();
    if (r && (r.top < 0 || r.bottom > innerHeight)) t.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
    place();
    clearInterval(timer); timer = setInterval(place, 150); // the target moves as panels re-render and the page scrolls
  }
  function hide() { clearInterval(timer); step = -1; el.hidden = true; ring.hidden = true; }
  function finish() { if (key) store.set(key, "1"); hide(); }
  $("coach-next").addEventListener("click", () => { sfx.click(); go(step + 1); });
  $("coach-skip").addEventListener("click", finish);
  return {
    hide,
    /** The first-play walkthrough; `force` replays it from the guide. */
    start(force = false) { if (!force && store.get("drill-tour")) return; setTab("areas"); steps = TOUR; key = "drill-tour"; go(0); },
    /** One pointer the first time round 2 starts. */
    tip2() { if (store.get("drill-tip2")) return; steps = TIP2; key = "drill-tip2"; go(0); },
    /** The player did `what` (pick, deploy, end): move on if the current step was waiting for it. */
    did(what) { if (step >= 0 && steps[step]?.wait === what) go(step + 1); },
  };
})();
function openGuide() { sfx.click(); $("guide-tour").hidden = !$("s-game").classList.contains("on"); $("guide").showModal(); }
["how", "help"].forEach((id) => $(id).addEventListener("click", openGuide));
["guide-close", "guide-ok"].forEach((id) => $(id).addEventListener("click", () => $("guide").close()));
$("guide").addEventListener("click", (e) => { if (e.target === $("guide")) $("guide").close(); }); // a click on the backdrop
$("guide-tour").addEventListener("click", () => { $("guide").close(); coach.start(true); });

// ------------------------------------------------------------------ title: region rail and a turning 3D preview
const totals = MISSIONS.map((m) => m.region.provinces.reduce((s, p) => s + m.R.total(p), 0));
const tmax = Math.max(...totals.slice(1));
let preview = null, previewId = 0;
async function renderMissions() {
  $("missions").innerHTML = MISSIONS.map((mi, k) => {
    const r = mi.region, stars = Math.max(1, Math.min(5, Math.ceil((totals[k] / tmax) * 5))), m = r.name.match(/^(.*?)(?: \((.+)\))?$/);
    const sub = mi.estimated ? `${mi.year} · latest data` : m[2];
    return `<button type="button" class="mission${mi.estimated ? " mission--latest" : ""}${k === regionIdx ? " sel" : ""}" role="option" aria-selected="${k === regionIdx}" data-k="${k}">
      <b>${m[1]}${sub ? `<span>${sub}</span>` : ""}</b><small>${r.provinces.length} ${mi.unit[1]} · ${fmt(totals[k])} cases</small>
      <span class="threat" aria-label="Threat ${stars} of 5">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= stars ? "on" : ""}"></i>`).join("")}</span></button>`;
  }).join("");
  useMission(MISSIONS[regionIdx]);
  const r = M.region, n = MISSIONS.length, pad = (v) => String(v).padStart(2, "0");
  document.querySelector(".title__copy .chip").textContent = `Mission ${M.year} · ${M.place}`;
  $("m-count").innerHTML = `<b>${pad(regionIdx + 1)}</b> / ${pad(n)}`;
  $("m-prev").disabled = regionIdx === 0; $("m-next").disabled = regionIdx === n - 1;
  $("missions").querySelector(".sel").scrollIntoView({ inline: "center", block: "nearest", behavior: reduce ? "auto" : "smooth" });
  $("t-region").textContent = r.name;
  $("t-stats").textContent = `${r.provinces.length} ${M.unit[1]} · ${fmt(totals[regionIdx])} cases in ${M.year}`;
  // the preview: the region's columns at the season's busiest week, slowly turning
  const id = ++previewId;
  preview?.dispose(); preview = null;
  const grid = M.board;
  $("t-map").innerHTML = "";
  const w = await createWorld($("t-map"), { grid, pixel: 2, water: false });
  if (id !== previewId) { w.dispose(); return; } // the reader picked another region meanwhile
  preview = w;
  const busiest = r.provinces.map((p) => R.peak(p) ?? FIRST);
  preview.setValues(Object.fromEntries(r.provinces.map((p, k) => [p.id, columnOf(p, busiest[k])])), { duration: 1200 });
  preview.setWeather({ rain: 0.25 });
  preview.spin();
}
function pickRegion(k) { if (k < 0 || k >= MISSIONS.length || k === regionIdx) return; regionIdx = k; sfx.click(); renderMissions(); }
$("missions").addEventListener("click", (e) => { const b = e.target.closest(".mission"); if (b) pickRegion(+b.dataset.k); });
$("missions").addEventListener("keydown", (e) => { const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key]; if (step) { e.preventDefault(); pickRegion(regionIdx + step); } });
$("m-prev").addEventListener("click", () => pickRegion(regionIdx - 1));
$("m-next").addEventListener("click", () => pickRegion(regionIdx + 1));

/** A province's column for week i: height from cases against the epidemic line, colour from the heat ramp. */
function columnOf(p, i) {
  const c = p.cases[i], e = p.epi[i];
  return { color: R.heat(p, i), height: c == null || !e ? 0.3 : 0.3 + Math.min(5.5, (c / e) * 2.4) };
}

// ------------------------------------------------------------------ briefing: the rain receipt
$("start").addEventListener("click", () => {
  useMission(MISSIONS[regionIdx]);
  region = M.region; results = {}; sfx.deploy();
  previewId++; preview?.dispose(); preview = null;
  const i0 = FIRST, i1 = Math.min(WEEKS.length - 1, FIRST + 20);
  const rain = region.provinces.map((p) => p.rain.slice(i0, i1 + 1).reduce((s, r) => s + (r || 0), 0));
  const items = byTotal(region, R).map((p) => ({ name: p.name, cases: p.cases.slice(i0, i1 + 1).reduce((s, c) => s + (c || 0), 0), hit: R.peak(p) != null }));
  const shown = M.estimated ? items.slice(0, 12) : region.provinces.map((p) => items.find((x) => x.name === p.name));
  $("brief-chip").textContent = `Intel briefing · ${region.name} · ${M.year}`;
  document.querySelector(".briefing__copy p").textContent = M.estimated
    ? "Teams cut the bill only if they arrive before the cases do. Barangay counts here are estimates from the city's weekly cases."
    : "Teams cut the bill only if they arrive before the cases do.";
  $("receipt").innerHTML = `<h3>${M.estimated ? "CASE RECEIPT" : "RAIN RECEIPT"}</h3><p class="c">${region.name}</p><p class="c">${dayY(WEEKS[i0])} – ${dayY(WEEKS[i1])}</p><hr>`
    + (M.estimated ? "" : `<div class="ln"><span>Rain (avg per province)</span><span>${fmt(rain.reduce((a, b) => a + b, 0) / rain.length)} mm</span></div><div class="ln"><span>Price of rain</span><span>₱0.00</span></div><hr>`)
    + shown.map((x) => `<div class="ln"><span>${x.name}${x.hit ? " *" : ""}</span><span>${fmt(x.cases)}</span></div>`).join("")
    + (items.length > shown.length ? `<div class="ln"><span>+ ${items.length - shown.length} more ${M.unit[1]}</span><span>${fmt(items.slice(shown.length).reduce((s, x) => s + x.cases, 0))}</span></div>` : "")
    + `<hr><div class="ln tot"><span>TOTAL DUE</span><span>${fmt(items.reduce((s, x) => s + x.cases, 0))} cases</span></div><p class="c">* outbreak: peaked above its epidemic line${M.estimated ? "<br>barangay counts: city cases × 2025 share" : ""}</p>`
    + `<div class="stamp">UNPAID · ACT EARLIER</div>`;
  show("s-brief");
});
$("go-r1").addEventListener("click", () => startRound(1));

// ------------------------------------------------------------------ the game
const teamsIn = (k) => R.teamsIn(plan, k);
const capped = (k) => R.capped(plan, k, region);

function spark(p, upto, opts = {}) {
  const W = 340, H = 110, n = WEEKS.length, f = opts.fc, seen = p.cases.slice(0, upto + 1).map((c) => c || 0);
  const maxv = Math.max(1, ...seen, ...p.epi.map((e) => e || 0), f ? f[3] : 0) * 1.12; // never scaled to the unseen future
  const X = (j) => 6 + (j / (n - 1)) * (W - 12), Y = (v) => H - 10 - (v / maxv) * (H - 20);
  const line = (arr, end) => arr.slice(0, end + 1).map((v, j) => (v == null ? null : `${X(j).toFixed(1)},${Y(v).toFixed(1)}`)).filter(Boolean).join(" ");
  let s = `<svg class="${opts.cls ?? "spark"}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Weekly cases in ${p.name}">`;
  if (upto < n - 1) s += `<rect x="${X(upto)}" y="0" width="${W - X(upto)}" height="${H}" fill="rgba(255,255,255,.03)"/><line x1="${X(upto)}" x2="${X(upto)}" y1="0" y2="${H}" stroke="#1E5A40" stroke-dasharray="3 3"/>`;
  s += `<polyline points="${line(p.epi, n - 1)}" fill="none" stroke="#F04B2A" stroke-width="1.3" stroke-dasharray="5 4" vector-effect="non-scaling-stroke"/>`;
  s += `<polyline points="${line(p.cases, upto)}" fill="none" stroke="#E9F3EC" stroke-width="2.2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>`;
  if (f) { const j = upto + 4; s += `<line x1="${X(j)}" x2="${X(j)}" y1="${Y(f[1])}" y2="${Y(f[3])}" stroke="#6FD6FF" stroke-width="3" vector-effect="non-scaling-stroke"/><rect x="${X(j) - 4}" y="${Y(f[2]) - 4}" width="8" height="8" fill="#6FD6FF"/>`; }
  (opts.teams || []).forEach((t) => { const x = X(idx(TURNS[t])); s += `<path d="M${x - 5} ${H}L${x} ${H - 9}L${x + 5} ${H}Z" fill="#34D27B"/>`; });
  if (opts.peak != null) s += `<line x1="${X(opts.peak)}" x2="${X(opts.peak)}" y1="0" y2="${H}" stroke="#F04B2A" stroke-width="1.5" vector-effect="non-scaling-stroke"/>`;
  return `${s}</svg>`;
}
/** A tiny region-wide sparkline for the HUD: total cases up to this week. */
function hudSpark(i) {
  const tot = WEEKS.map((_, j) => region.provinces.reduce((s, p) => s + (p.cases[j] || 0), 0)).slice(0, i + 1);
  const W = 96, H = 26, max = Math.max(1, ...tot), X = (j) => (j / Math.max(1, WEEKS.length - 1)) * W, Y = (v) => H - 2 - (v / max) * (H - 4);
  return `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" aria-hidden="true"><polyline points="${tot.map((v, j) => `${X(j)},${Y(v)}`).join(" ")}" fill="none" stroke="#E9F3EC" stroke-width="1.6"/></svg>`;
}

function renderList() {
  const i = idx(TURNS[turn]), tw = TURNS[turn];
  $("plist").innerHTML = region.provinces.map((p, k) => {
    const f = round === 2 ? p.fc[tw] : null, n = teamsIn(k);
    return `<div class="prow${sel === k ? " on" : ""}" data-k="${k}"><button type="button" class="prow__pick" aria-pressed="${sel === k}">
      <span class="prow__heat" style="background:${R.heat(p, i)}"></span><span class="prow__nm">${p.name}</span>
      ${f && f[0] !== "normal" ? `<span class="prow__fc" data-lv="${f[0]}">▲${fmt(f[2])}</span>` : ""}
      <span class="prow__n nums">${p.cases[i] == null ? "–" : fmt(p.cases[i])}</span>${n ? `<span class="prow__team">${n}</span>` : ""}</button>
      <button type="button" class="prow__add" aria-label="Send a team to ${p.name}" ${kits && !capped(k) ? "" : "disabled"}>+</button></div>`;
  }).join("");
}
/** Send one team to area k this turn, or take one of this turn's teams back. */
function deploy(k) {
  if (!kits || capped(k)) return;
  const p = region.provinces[k], now = (plan[k] || {})[turn] || 0;
  (plan[k] ||= {})[turn] = now + 1; kits--; sfx.deploy(); tick(`Team sent to ${p.name}.`); refresh({ drop: p.id });
  coach.did("deploy");
}
function recall(k) {
  const now = (plan[k] || {})[turn] || 0;
  if (!now) return;
  plan[k][turn] = now - 1; kits++; sfx.recall(); refresh();
}
function renderDetail() {
  const tw = TURNS[turn], i = idx(tw);
  if (sel == null) { $("detail").innerHTML = `<div class="empty">Pick a ${M.unit[0]} on the map or in the list.</div>`; return; }
  const p = region.provinces[sel], c = p.cases[i], prev = p.cases[i - 2], f = round === 2 ? p.fc[tw] : null, now = (plan[sel] || {})[turn] || 0;
  const trend = c != null && prev ? Math.round((c / prev - 1) * 100) : null;
  $("detail").innerHTML = `<div class="detail__head"><h3>${p.name}</h3><span class="sub">${fmt(p.pop)} people</span></div>
    <div class="chart-surface">${spark(p, i, { fc: f })}</div>
    <div class="chart-key"><span class="ck ck--cases">Cases</span><span class="ck ck--line">Epidemic line</span>${f ? `<span class="ck ck--fc">Forecast</span>` : ""}</div>
    <div class="kv"><div class="panel"><div class="k">This week</div><div class="v nums">${c == null ? "–" : fmt(c)}</div><div class="d">${trend == null ? "" : `${trend >= 0 ? "▲ " : "▼ "}${Math.abs(trend)}% in 2 weeks`}</div></div>
      <div class="panel"><div class="k">Epidemic line</div><div class="v nums">${p.epi[i] == null ? "–" : fmt(p.epi[i])}</div><div class="sub">${M.estimated ? "city line × usual share" : `rain ${p.rain[i] == null ? "–" : `${fmt(p.rain[i])} mm`}`}</div></div></div>
    ${f ? `<div class="intel-box"><div class="k">Forecast · week of ${day(WEEKS[i + 4])}</div><div class="intel-box__row"><div class="v">~${fmt(f[2])} cases</div><span class="lv" data-lv="${f[0]}">${LEVEL[f[0]]}</span></div><div class="sub">likely ${fmt(f[1])}–${fmt(f[3])}</div></div>` : ""}
    <div class="send"><button type="button" class="send__back" id="recall" aria-label="Take a team back" ${now ? "" : "disabled"}>−</button>
      <div class="send__n"><b class="nums">${now}</b><span>sent this turn</span></div>
      <button type="button" class="btn btn--go btn--sm" id="deploy" ${kits && !capped(sel) ? "" : "disabled"}>Send team · ₱${K.pesos / 1000}K</button></div>
    <div class="sub">${capped(sel) ? "Max coverage reached here (30% of the population)." : kits ? `${teamsIn(sel)} here so far · ${kits} left` : "No teams left. End the turn."}</div>`;
  $("deploy").onclick = () => deploy(sel);
  $("recall").onclick = () => recall(sel);
}
// ------------------------------------------------------------------ the side panel's tabs and the turn report
let tab = "areas", logTurn = 0;
function setTab(t) {
  tab = t;
  for (const id of ["areas", "log"]) { $(`tab-${id}`).setAttribute("aria-selected", String(id === t)); $(`pane-${id}`).hidden = id !== t; }
  if (t === "log") { $("log-dot").hidden = true; renderLog(); }
}
$("tab-areas").addEventListener("click", () => { sfx.click(); setTab("areas"); });
$("tab-log").addEventListener("click", () => { sfx.click(); logTurn = turn; setTab("log"); });
const money = (n) => `₱${((n * K.pesos) / 1e6).toFixed(1)}M`;
/** What the reports said at turn `logTurn`: the two weeks before it, and the teams sent the turn before. Nothing from the future. */
function renderLog() {
  const t = logTurn, tw = TURNS[t], i = idx(tw), ps = region.provinces, live = t === turn;
  const sum = (j) => ps.reduce((s, p) => s + (p.cases[j] || 0), 0), now = sum(i), was = sum(i - 2);
  const over = (p, j) => p.cases[j] != null && p.epi[j] != null && p.cases[j] > p.epi[j];
  const crossed = ps.filter((p) => over(p, i) && !over(p, i - 2)), above = ps.filter((p) => over(p, i)).length;
  const pct = was ? Math.round((now / was - 1) * 100) : null;
  const names = (list) => `${list.slice(0, 3).map((p) => short(p.name)).join(", ")}${list.length > 3 ? ` and ${list.length - 3} more` : ""}`;
  // one sentence for the two weeks, one for where the outbreaks are
  const head = !t ? "The season begins." : pct == null ? "New reports are in." : pct >= 100 ? "Cases more than doubled." : pct >= 15 ? `Cases are up ${pct}%.` : pct <= -15 ? `Cases are down ${-pct}%.` : "Cases are holding steady.";
  const next = crossed.length ? `${names(crossed)} crossed the epidemic line.` : above ? `${above} of ${ps.length} ${M.unit[1]} ${above === 1 ? "is" : "are"} above the epidemic line.` : "No outbreaks yet.";
  const moves = ps.map((p, k) => ({ p, k, c: p.cases[i] || 0, d: (p.cases[i] || 0) - (p.cases[i - 2] || 0) })).sort((a, b) => b.d - a.d).slice(0, 10);
  const mm = ps.reduce((s, p) => s + (p.rain[i] || 0), 0) / ps.length;
  const sent = t ? ps.map((p, k) => [short(p.name), (plan[k] || {})[t - 1] || 0]).filter((x) => x[1]) : [];
  const nSent = sent.reduce((s, x) => s + x[1], 0);
  const spent = ps.reduce((s, _, k) => s + Object.entries(plan[k] || {}).reduce((a, [tt, n]) => a + (+tt < t ? n : 0), 0), 0);
  const tag = (p) => {
    const f = round === 2 ? p.fc[tw] : null;
    if (f && (f[0] === "warning" || f[0] === "watch")) return `<span class="log__tag" data-lv="${f[0]}">${f[0] === "warning" ? "Forecast: outbreak" : "Forecast: watch"}</span>`;
    return crossed.includes(p) ? `<span class="log__tag" data-lv="warning">New outbreak</span>` : over(p, i) ? `<span class="log__tag" data-lv="watch">Outbreak</span>` : "";
  };
  $("pane-log").innerHTML = `<div class="log__nav"><button type="button" class="log__step" id="log-prev" aria-label="Earlier turn" ${t ? "" : "disabled"}>${icon("chevronLeft", { size: 24 })}</button>
      <div class="log__when"><b>Turn ${t + 1} of ${TURNS.length}</b><span>${t ? `${day(TURNS[t - 1])} to ${day(tw)}` : day(tw)}${live ? "" : " · past turn"}</span></div>
      <button type="button" class="log__step" id="log-next" aria-label="Later turn" ${live ? "disabled" : ""}>${icon("chevronRight", { size: 24 })}</button></div>
    <div class="log__head"><h3>${head}</h3><p>${next}</p></div>
    <div class="log__stats"><div><b class="nums">${fmt(now)}</b><span>cases this week</span></div>
      <div><b class="nums">${above}<small>/${ps.length}</small></b><span>in outbreak</span></div>
      ${M.estimated ? "" : `<div><b class="nums">${fmt(mm)}<small> mm</small></b><span>rain</span></div>`}</div>
    <div class="log__sec"><div class="log__cols"><span class="k">${cap(M.unit[0])}</span><span class="k">Cases</span><span class="k">2 weeks</span></div>
      <div class="log__moves">${moves.map(({ p, k, c, d }) => `<div class="log__row" data-k="${k}"><button type="button" class="log__move" aria-label="Open ${p.name}">
          <span class="prow__heat" style="background:${R.heat(p, i)}"></span><span class="log__nm"><span class="prow__nm">${p.name}</span>${tag(p)}</span>
          <span class="nums">${fmt(c)}</span><b class="nums ${d > 0 ? "up" : d < 0 ? "down" : ""}">${d > 0 ? "▲ " : d < 0 ? "▼ " : ""}${fmt(Math.abs(d))}</b></button>
        ${live ? `<button type="button" class="prow__add" aria-label="Send a team to ${p.name}" ${kits && !capped(k) ? "" : "disabled"}>+</button>` : ""}</div>`).join("")}</div>
      ${ps.length > moves.length ? `<p class="sub">The ${moves.length} biggest rises of ${ps.length} ${M.unit[1]}.</p>` : ""}</div>
    <div class="log__teams"><span class="k">${t ? "Sent last turn" : "Your teams"}</span>
      <p>${nSent ? sent.map(([n, c]) => `<span class="log__sent"><i></i><b>${c}×</b> ${n}</span>`).join("") : t ? "No teams sent." : "None sent yet."}</p>
      <p class="sub">${nSent ? `${money(nSent)} that turn · ` : ""}${money(spent)} spent · ${money(K.kits - spent)} left</p></div>`;
}
$("pane-log").addEventListener("click", (e) => {
  const step = e.target.closest(".log__step"), row = e.target.closest(".log__row");
  if (step) { sfx.click(); logTurn += step.id === "log-prev" ? -1 : 1; renderLog(); ($(step.id).disabled ? $("pane-log").querySelector(".log__step:not(:disabled)") : $(step.id))?.focus(); return; }
  if (!row) return;
  const k = +row.dataset.k;
  if (e.target.closest(".prow__add")) { deploy(k); $("pane-log").querySelector(`[data-k="${k}"] .prow__add`)?.focus(); } // send from the report
  else if (e.target.closest(".log__move")) { setTab("areas"); pick(k); } // open that area
});
function pick(k) {
  if (k == null || k === sel) return;
  sel = k; sfx.click();
  board?.select(region.provinces[k].id);
  setTab("areas");
  renderList(); renderDetail();
  coach.did("pick");
}
$("plist").addEventListener("click", (e) => {
  const row = e.target.closest(".prow");
  if (!row) return;
  const k = +row.dataset.k;
  pick(k);
  if (e.target.closest(".prow__add")) { deploy(k); $("plist").querySelector(`[data-k="${k}"] .prow__add`)?.focus(); } // + on a row: pick and send in one press
});
$("plist").addEventListener("keydown", (e) => {
  const step = { ArrowDown: 1, ArrowUp: -1 }[e.key];
  if (!step) return;
  e.preventDefault();
  const n = region.provinces.length, k = sel == null ? 0 : (sel + step + n) % n;
  pick(k); $("plist").querySelector(`[data-k="${k}"] .prow__pick`)?.focus();
});
$("reset-view").addEventListener("click", () => board?.resetView());
$("v-in").addEventListener("click", () => board?.zoomBy(1.35));
$("v-out").addEventListener("click", () => board?.zoomBy(1 / 1.35));
$("v-left").addEventListener("click", () => board?.rotateBy(-25));
$("v-right").addEventListener("click", () => board?.rotateBy(25));
function lightning() {
  sfx.thunder();
  if (reduce) return;
  $("flash").classList.remove("on"); void $("flash").offsetWidth; $("flash").classList.add("on");
}
/** A short banner over the board (two weeks passing), instead of covering the whole screen. */
function toast(text, sub) {
  $("toast").innerHTML = `<b>${text}</b><span>${sub}</span>`;
  $("toast").classList.remove("on"); void $("toast").offsetWidth; $("toast").classList.add("on");
}

function refresh({ drop = null, duration = 900 } = {}) {
  const tw = TURNS[turn], i = idx(tw);
  $("h-region").textContent = region.name;
  $("h-timeline").innerHTML = TURNS.map((w, t) => `<li class="${t < turn ? "done" : t === turn ? "now" : ""}"${t === turn ? ' aria-current="step"' : ""}><i></i><span>${day(w)}</span></li>`).join("");
  $("h-budget").textContent = `₱${((kits * K.pesos) / 1e6).toFixed(1)}M`;
  $("h-tokens").innerHTML = Array.from({ length: K.kits }, (_, t) => `<i class="${t >= kits ? "spent" : ""}"></i>`).join("");
  const now = region.provinces.reduce((s, p) => s + (p.cases[i] || 0), 0), before = region.provinces.reduce((s, p) => s + (p.cases[i - 2] || 0), 0);
  $("h-cases").textContent = fmt(now);
  $("h-change").textContent = before ? `${now >= before ? "▲" : "▼"} ${Math.abs(Math.round((now / before - 1) * 100))}% in 2 weeks` : "";
  $("h-spark").innerHTML = hudSpark(i);
  const mm = region.provinces.reduce((s, p) => s + (p.rain[i] || 0), 0) / region.provinces.length;
  $("h-rain").textContent = M.estimated ? "–" : `${fmt(mm)} mm`;
  const sky = M.estimated ? ["clear", "No rain data"] : mm < 10 ? ["clear", "Mostly dry"] : mm < 30 ? ["rain", "Showers"] : mm < 56 ? ["rain", "Heavy rain"] : ["storm", "Storm"];
  $("tab-areas").textContent = cap(M.unit[1]);
  $("h-spent").textContent = `${money(K.kits - kits)} spent of ${money(K.kits)}`;
  if (tab === "log") { logTurn = turn; renderLog(); }
  $("plist").setAttribute("aria-label", cap(M.unit[1]));
  $("h-sky").textContent = sky[1];
  $("board-wrap").dataset.weather = sky[0];
  const pr = R.pressure(region, i);
  confirmEnd = false;
  $("end").innerHTML = `${turn === TURNS.length - 1 ? "End season" : "End turn"} ${icon("play", { size: 24 })}`;
  $("end").classList.toggle("pulse", kits === 0); // nothing left to send: the next move is to end the turn
  $("side-sub").textContent = `${kits} of ${K.kits} teams left`;
  $("legend-intel").innerHTML = round === 2 ? `<span class="intel">◯ Forecast, 4 weeks ahead</span>` : "";
  // the board
  board.setWeek(Object.fromEntries(region.provinces.map((p) => [p.id, columnOf(p, i)])), { duration });
  const counts = Object.fromEntries(region.provinces.map((p, k) => [p.id, teamsIn(k)]));
  board.setTeams(counts, { drop });
  board.setRain(mm);
  rainLevel = Math.min(1, mm / 70);
  rainSound(rainLevel);
  board.setGlow(region.provinces.filter((p) => p.cases[i] != null && p.epi[i] != null && p.cases[i] > p.epi[i]).map((p) => p.id));
  if (round === 2) {
    // with 142 barangays, mark only the 12 with the highest forecast, so the board stays readable
    const flagged = region.provinces.filter((p) => p.fc[tw] && p.fc[tw][0] !== "normal").sort((a, b) => b.fc[tw][2] - a.fc[tw][2]).slice(0, M.estimated ? 12 : Infinity);
    board.setIntel(Object.fromEntries(flagged.map((p) => [p.id, p.fc[tw][0]])), Object.fromEntries(flagged.map((p) => [p.id, `▲${fmt(p.fc[tw][2])}`])));
  } else board.setIntel(null);
  // mosquitoes: more after rain; more over provinces with more cases (same formula as before)
  const anchors = [];
  region.provinces.forEach((p) => { const r = Math.min(4, (p.cases[i] || 0) / (p.epi[i] || 1)); for (let j = 0; j < 1 + Math.round(r * 3); j++) anchors.push(p.id); });
  const rain = region.provinces.reduce((s, p) => s + (p.rain[i] || 0) + (p.rain[i - 1] || 0), 0) / region.provinces.length;
  // the old 2D board drew up to 220 specks; in 3D each is a sprite, so draw half as many
  board.setBugs(M.estimated ? Math.round(24 + Math.min(60, pr.value * 25)) : Math.round(Math.max(12, Math.min(220, Math.round(rain * 1.6))) / 2), anchors);
  renderList(); renderDetail();
}
function tick(msg) { const t = $("ticker"); t.textContent = msg; t.style.animation = "none"; void t.offsetHeight; t.style.animation = ""; }
function headline() {
  const i = idx(TURNS[turn]), tw = TURNS[turn];
  if (round === 2) {
    const w = region.provinces.filter((p) => p.fc[tw] && p.fc[tw][0] === "warning");
    if (w.length) return `EpiLag intel: ${w.map((p) => p.name).join(", ")} flagged OUTBREAK WARNING for the week of ${day(WEEKS[i + 4])}.`;
  }
  const crossed = region.provinces.filter((p) => p.cases[i] > p.epi[i] && !(p.cases[i - 2] > p.epi[i - 2]));
  if (crossed.length) { sfx.alarm(); return `Alert: ${crossed.map((p) => p.name).join(", ")} crossed the epidemic line this week.`; }
  const up = region.provinces.map((p) => ({ p, r: p.cases[i - 2] ? p.cases[i] / p.cases[i - 2] : 0 })).sort((a, b) => b.r - a.r)[0];
  if (up && up.r > 1.3) return `${up.p.name}: reported cases up ${Math.round((up.r - 1) * 100)}% in two weeks.`;
  if (M.estimated) return `Week ending ${dayY(tw)}: ${fmt(region.provinces.reduce((s, p) => s + (p.cases[i] || 0), 0))} cases reported across the city.`;
  return `Week ending ${dayY(tw)}: ${fmt(region.provinces.reduce((s, p) => s + (p.rain[i] || 0), 0) / region.provinces.length)} mm of rain on average across the region.`;
}
function warp(text, sub, then) {
  $("warp-text").textContent = text; $("warp-sub").textContent = sub; $("warp").classList.add("on");
  setTimeout(() => { $("warp").classList.remove("on"); then?.(); }, reduce ? 50 : 1300);
}
async function startRound(r) {
  round = r; turn = 0; kits = K.kits; plan = {}; sel = null; logTurn = 0; setTab("areas"); $("log-dot").hidden = true;
  $("mode").textContent = r === 1 ? "Round 1 · No intel" : "Round 2 · EpiLag intel";
  $("mode").classList.toggle("chip--intel", r === 2);
  show("s-game"); sfx.turn();
  if (!board || board.regionId !== region.id) {
    board?.dispose();
    $("board").innerHTML = "";
    board = await createBoard($("board"), { grid: M.board, region, onFlash: lightning, labels: M.estimated ? byTotal(region, R).slice(0, 10).map((p) => p.id) : null,
      onPick: (u) => { const k = region.provinces.findIndex((p) => p.id === u); if (k >= 0) pick(k); } });
    board.regionId = region.id;
  }
  board.select(null);
  board.resetView();
  warp(r === 1 ? "Round 1" : "Round 2", r === 1 ? "Case reports only" : "EpiLag-PH intel online", () => { refresh({ duration: 0 }); tick(headline()); if (r === 1) coach.start(); else coach.tip2(); });
}
let confirmEnd = false;
$("end").addEventListener("click", () => {
  // the last turn with teams still unused: ask once before the season ends
  if (turn === TURNS.length - 1 && kits > 0 && !confirmEnd) {
    confirmEnd = true; sfx.alarm();
    $("end").innerHTML = `End with ${kits} unused? ${icon("play", { size: 24 })}`;
    tick(`${kits} team${kits === 1 ? " is" : "s are"} still unused. Press again to end the season.`);
    return;
  }
  coach.did("end");
  sfx.turn(); board.burst();
  if (turn < TURNS.length - 1) {
    turn++;
    $("end").disabled = true;
    toast("2 weeks later", dayY(TURNS[turn]));
    setTimeout(() => {
      $("end").disabled = false;
      refresh({ duration: 1400 });
      if (tab !== "log") $("log-dot").hidden = false; // a new turn report is waiting
      const i = idx(TURNS[turn]);
      board.floaters(region.provinces.map((p) => [p.id, (p.cases[i - 1] || 0) + (p.cases[i] || 0)]));
      tick(headline());
    }, reduce ? 0 : 900);
  } else warp("Season over", `Counting the real ${M.year} cases`, endRound);
});

// ------------------------------------------------------------------ round report and debrief
const BADGE_ICON = { early: "alert", waste: "check", full: "actionPlan", bot: "didItWork", saved: "residents" };
function endRound() {
  const s = R.score(plan, region), auto = R.autopilot("epilag", region), g = R.gradeOf(s.mid, region), gc = GRADE_COL[g];
  results[round] = { ...s, grade: g, color: gc };
  rainSound(0);
  board.setBugs(0, []);
  show("s-report"); sfx.grade();
  $("r-grade").textContent = g; $("r-grade").style.color = gc;
  frogReacts($("r-frog"), g);
  $("r-chip").textContent = `Mission report · Round ${round} · ${round === 1 ? "no intel" : "EpiLag intel"}`;
  $("r-title").innerHTML = `${fmt(s.mid)} cases averted. <span>${g === "S" || g === "A" ? "Outstanding command." : g === "B" ? "Solid response." : "The outbreak got ahead of you."}</span>`;
  $("r-lead").textContent = `Likely between ${fmt(s.lo)} and ${fmt(s.hi)}. Graded against two computer players.`;
  // one bar for all the teams: in time (4+ weeks before a peak), too late, sent where no outbreak came, never sent
  const seg = [["on", s.onTime, "in time"], ["late", s.late, "too late"], ["none", s.noOutbreak, "no outbreak there"], ["idle", K.kits - s.used, "unused"]];
  $("r-scores").innerHTML = `<div class="k">Where your ${K.kits} teams went</div>
    <div class="teambar" role="img" aria-label="${seg.map(([, n, l]) => `${n} ${l}`).join(", ")}">${seg.map(([c, n]) => (n ? `<i class="tb--${c}" style="flex:${n}"></i>` : "")).join("")}</div>
    <div class="teamkey">${seg.map(([c, n, l]) => `<span class="${n ? "" : "zero"}"><i class="tb--${c}"></i><b class="nums">${n}</b> ${l}</span>`).join("")}</div>
    <div class="sub">In time means 4 or more weeks before the peak.</div>`;
  const badges = [
    ["early", "Early bird", "3+ teams 4 weeks before a peak", s.onTime >= 3], ["waste", "No waste", "No team where no outbreak came", s.used > 0 && s.noOutbreak === 0],
    ["full", "All in", `Sent all ${K.kits} teams`, s.used === K.kits], ["bot", "Beat the bot", "More than EpiLag's autopilot", s.mid > auto.mid],
    ["saved", "Life saver", "Averted 100+ cases", s.mid >= 100],
  ];
  $("r-badges").innerHTML = badges.map(([ic, n, d, got], j) => `<div class="badge${got ? " got" : ""}" title="${d}" style="animation-delay:${0.5 + j * 0.12}s">${icon(BADGE_ICON[ic], { size: ic === "early" || ic === "waste" ? 36 : 48 })}<b>${n}</b><span class="sr-only">${got ? d : `Locked: ${d}`}</span></div>`).join("");
  // with many areas (Quezon City), replay the ones that got teams, then the busiest, 12 in all
  let shown = region.provinces.map((_, k) => k);
  if (shown.length > 12) {
    const busy = byTotal(region, R).map((p) => region.provinces.indexOf(p));
    shown = [...new Set([...shown.filter((k) => teamsIn(k)), ...busy])].slice(0, 12);
  }
  $("r-replay").innerHTML = shown.map((k) => {
    const p = region.provinces[k], pk = R.peak(p), ts = [];
    Object.entries(plan[k] || {}).forEach(([t, n]) => { for (let j = 0; j < n; j++) ts.push(+t); });
    return `<div class="panel"><b>${p.name}</b><small>${pk == null ? "No outbreak" : `Peaked ${day(WEEKS[pk])}`} · ${ts.length} team${ts.length === 1 ? "" : "s"}</small>${spark(p, WEEKS.length - 1, { teams: ts, peak: pk, cls: "" })}</div>`;
  }).join("");
  $("r-actions").innerHTML = `<button type="button" class="btn btn--go" id="next-r">${round === 1 ? "Round 2 · with forecasts" : "Debrief"} ${icon("play", { size: 24 })}</button>`;
  $("next-r").onclick = () => (round === 1 ? startRound(2) : versus());
}
/** The frog reacts to the grade: S/A strike then smile, B watches, C/D peeks. */
function frogReacts(el, g) {
  if (g === "S" || g === "A") { el.setAttribute("pose", "strike"); setTimeout(() => el.setAttribute("pose", "happy"), reduce ? 0 : 900); }
  else el.setAttribute("pose", g === "B" ? "watch" : "peek");
}
function versus() {
  const a = results[1], b = results[2], auto = R.autopilot("epilag", region), react = R.autopilot("react", region);
  $("vs-region").textContent = region.name;
  $("vs-title").textContent = b.mid > a.mid * 1.02 ? "Intel made the difference." : b.mid < a.mid * 0.98 ? "Your instincts won this time." : "Dead heat.";
  const card = (lab, r, win) => `<div class="panel vs__card${win ? " win" : ""}"><div class="k">${lab}</div><div class="g" style="color:${r.color}">${r.grade}</div><div class="v nums">${fmt(r.mid)} cases averted</div><div class="sub">${r.onTime} of ${r.used} teams in 4+ weeks before a peak</div></div>`;
  $("vs").innerHTML = card("Round 1 · no intel", a, a.mid > b.mid) + `<div class="vs__x">VS</div>` + card("Round 2 · EpiLag intel", b, b.mid >= a.mid);
  const rows = [["You · no intel", a.mid, "#9DBDAC"], ["You · EpiLag intel", b.mid, "#6FD6FF"], ["Bot · reacts to reported outbreaks", react.mid, "#1E5A40"], ["Bot · follows EpiLag alerts", auto.mid, "#34D27B"]];
  const max = Math.max(1, ...rows.map((r) => r[1]));
  $("vs-bars").innerHTML = rows.map(([n, v, c], j) => `<div class="bar"><span>${n}</span><div class="bar__track"><div class="bar__fill" style="width:${(v / max) * 100}%;background:${c};animation-delay:${j * 0.12}s"></div></div><b class="nums">${fmt(v)}</b></div>`).join("");
  const h = R2019.honest();
  $("vs-honest").textContent = (M.estimated
    ? "Quezon City's barangay numbers are estimates: weekly reports exist only for the whole city, so each barangay gets the city's weekly cases × its share of the city's 2025 cases, an epidemic line from its 2022–2025 share, and EpiLag-PH's real city forecast shared out the same way. "
    : "") + `In the 2019 missions, across all ${D2019.regions.length} regions, the bot that follows EpiLag's alerts averted more cases than the bot that reacts to reports in ${h.better}, about the same in ${h.tie}, and fewer in ${h.worse}. `
    + "How scoring works: a team covers about 33,000 people (up to 30% of a province) and prevents a share of the cases reported 2 to 9 weeks later, since people already infected still fall sick. "
    + "The share uses cautious effects for clean-ups with container covers (10–50%, central 30%; Bowman et al. 2016), so treat the numbers as estimates.";
  show("s-vs"); sfx.grade();
}
$("again").addEventListener("click", () => { show("s-title"); renderMissions(); });

hydrateIcons();
$("mute").innerHTML = icon("sound", { size: 24 });
renderMissions();
