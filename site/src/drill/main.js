// Dengue Drill: command the 2019 dengue response in one region, twice (round 1: case reports only; round 2: with
// EpiLag-PH's 4-week forecasts), on a 3D pixel board. The real 2019 cases keep score (rules.js, the same rules as
// scripts/drill_data.py). Flow: title -> rain receipt -> round 1 -> report -> round 2 -> report -> debrief.
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

const D = await fetch(`${import.meta.env.BASE_URL}drill/data.json`).then((r) => r.json());
const R = rules(D), { K, WEEKS, TURNS, FIRST, idx } = R;
const boards = await loadGrids("voxel_regions");
const LEVEL = { warning: "Outbreak warning", watch: "Watch", above: "Above usual", normal: "Normal" };
const GRADE_COL = { S: "#6FD6FF", A: "#34D27B", B: "#F7C928", C: "#F58220", D: "#F04B2A" };
const PRESS = { low: ["Low", "#34D27B"], rising: ["Rising", "#F7C928"], high: ["High", "#F58220"], critical: ["Critical", "#F04B2A"] };
const $ = (id) => document.getElementById(id);
const fmt = (n) => Math.round(n).toLocaleString("en");
const day = (s) => new Date(`${s}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const short = (name) => name.replace(/ \(.+\)/, "");
// for tests/test_drill_rules.py (parity with scripts/drill_data.py through Playwright)
window.drill = { D, R };

let regionIdx = Math.max(0, D.regions.findIndex((r) => r.name.includes("Western Visayas")));
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

function show(id) { document.querySelectorAll(".screen").forEach((s) => s.classList.toggle("on", s.id === id)); scrollTo({ top: 0 }); }

// ------------------------------------------------------------------ title: region rail and a turning 3D preview
const totals = D.regions.map((r) => r.provinces.reduce((s, p) => s + p.cases.slice(FIRST).reduce((a, c) => a + (c || 0), 0), 0));
const tmax = Math.max(...totals);
let preview = null, previewId = 0;
async function renderMissions() {
  $("missions").innerHTML = D.regions.map((r, k) => {
    const stars = Math.max(1, Math.ceil((totals[k] / tmax) * 5)), m = r.name.match(/^(.*?)(?: \((.+)\))?$/);
    return `<button type="button" class="mission${k === regionIdx ? " sel" : ""}" role="option" aria-selected="${k === regionIdx}" data-k="${k}">
      <b>${m[1]}${m[2] ? `<span>${m[2]}</span>` : ""}</b><small>${r.provinces.length} provinces · ${fmt(totals[k])} cases</small>
      <span class="threat" aria-label="Threat ${stars} of 5">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= stars ? "on" : ""}"></i>`).join("")}</span></button>`;
  }).join("");
  const r = D.regions[regionIdx], n = D.regions.length, pad = (v) => String(v).padStart(2, "0");
  $("m-count").innerHTML = `<b>${pad(regionIdx + 1)}</b> / ${pad(n)}`;
  $("m-prev").disabled = regionIdx === 0; $("m-next").disabled = regionIdx === n - 1;
  $("missions").querySelector(".sel").scrollIntoView({ inline: "center", block: "nearest", behavior: reduce ? "auto" : "smooth" });
  $("t-region").textContent = r.name;
  $("t-stats").textContent = `${r.provinces.length} provinces · ${fmt(totals[regionIdx])} cases in 2019`;
  // the preview: the region's columns at the season's busiest week, slowly turning
  const id = ++previewId;
  preview?.dispose(); preview = null;
  const grid = boards[r.id];
  $("t-map").innerHTML = "";
  const w = await createWorld($("t-map"), { grid, pixel: 2 });
  if (id !== previewId) { w.dispose(); return; } // the reader picked another region meanwhile
  preview = w;
  const busiest = r.provinces.map((p) => R.peak(p) ?? FIRST);
  preview.setValues(Object.fromEntries(r.provinces.map((p, k) => [p.id, columnOf(p, busiest[k])])), { duration: 1200 });
  preview.setWeather({ rain: 0.25 });
  preview.spin();
}
function pickRegion(k) { if (k < 0 || k >= D.regions.length || k === regionIdx) return; regionIdx = k; sfx.click(); renderMissions(); }
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
  region = D.regions[regionIdx]; results = {}; sfx.deploy();
  previewId++; preview?.dispose(); preview = null;
  const i0 = FIRST, i1 = Math.min(WEEKS.length - 1, FIRST + 20);
  const rain = region.provinces.map((p) => p.rain.slice(i0, i1 + 1).reduce((s, r) => s + (r || 0), 0));
  const items = region.provinces.map((p) => ({ name: p.name, cases: p.cases.slice(i0, i1 + 1).reduce((s, c) => s + (c || 0), 0), hit: R.peak(p) != null }));
  $("brief-chip").textContent = `Intel briefing · ${region.name}`;
  $("receipt").innerHTML = `<h3>RAIN RECEIPT</h3><p class="c">${region.name}</p><p class="c">${day(WEEKS[i0])} 2019 – ${day(WEEKS[i1])} 2019</p><hr>`
    + `<div class="ln"><span>Rain (avg per province)</span><span>${fmt(rain.reduce((a, b) => a + b, 0) / rain.length)} mm</span></div><div class="ln"><span>Price of rain</span><span>₱0.00</span></div><hr>`
    + items.map((x) => `<div class="ln"><span>${x.name}${x.hit ? " *" : ""}</span><span>${fmt(x.cases)}</span></div>`).join("")
    + `<hr><div class="ln tot"><span>TOTAL DUE</span><span>${fmt(items.reduce((s, x) => s + x.cases, 0))} cases</span></div><p class="c">* outbreak: peaked above its epidemic line</p>`
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

function roster() {
  const sent = region.provinces.map((p, k) => [p.name, (plan[k] || {})[turn] || 0]).filter((x) => x[1]);
  return `<div class="roster"><span class="k">This turn</span> ${sent.length ? sent.map(([n, c]) => `<b>${c}×</b> ${n}`).join(" · ") : "No teams deployed yet."}</div>`;
}
function renderList() {
  const i = idx(TURNS[turn]), tw = TURNS[turn];
  $("plist").innerHTML = region.provinces.map((p, k) => {
    const f = round === 2 ? p.fc[tw] : null, n = teamsIn(k);
    return `<button type="button" class="prow${sel === k ? " on" : ""}" role="option" aria-selected="${sel === k}" data-k="${k}">
      <span class="prow__heat" style="background:${R.heat(p, i)}"></span><span class="prow__nm">${p.name}</span>
      ${f && f[0] !== "normal" ? `<span class="prow__fc" data-lv="${f[0]}">▲${fmt(f[2])}</span>` : ""}
      <span class="prow__n nums">${p.cases[i] == null ? "–" : fmt(p.cases[i])}</span>${n ? `<span class="prow__team">${n}</span>` : ""}</button>`;
  }).join("");
}
function renderDetail() {
  const tw = TURNS[turn], i = idx(tw);
  if (sel == null) {
    $("detail").innerHTML = `<div class="empty">Pick a province on the board or in the list to see its reports${round === 2 ? " and EpiLag intel" : ""}, then deploy teams.</div>${roster()}`;
    return;
  }
  const p = region.provinces[sel], c = p.cases[i], prev = p.cases[i - 2], f = p.fc[tw], now = (plan[sel] || {})[turn] || 0;
  const trend = c != null && prev ? Math.round((c / prev - 1) * 100) : null;
  $("detail").innerHTML = `<h3>${p.name}</h3><div class="sub">${fmt(p.pop)} people · ${teamsIn(sel)} team${teamsIn(sel) === 1 ? "" : "s"} deployed</div>
    <div class="chart-surface">${spark(p, i, { fc: round === 2 ? f : null })}</div>
    <div class="kv"><div class="panel"><div class="k">Reported this week</div><div class="v nums">${c == null ? "–" : fmt(c)}</div><div class="d">${trend == null ? "" : `${trend >= 0 ? "▲ " : "▼ "}${Math.abs(trend)}% in 2 weeks`}</div></div>
      <div class="panel"><div class="k">Epidemic line</div><div class="v nums">${p.epi[i] == null ? "–" : fmt(p.epi[i])}</div><div class="sub">rain ${p.rain[i] == null ? "–" : `${fmt(p.rain[i])} mm`}</div></div></div>
    ${round === 2 && f ? `<div class="intel-box"><div class="k">EpiLag intel · week of ${day(WEEKS[i + 4])}</div><div class="v">~${fmt(f[2])} cases</div><div class="sub">likely ${fmt(f[1])}–${fmt(f[3])}</div><span class="lv" data-lv="${f[0]}">${LEVEL[f[0]]}</span></div>` : ""}
    <div class="take"><span class="k">Take action</span>
      <div class="action"><span class="tick"></span><div><b>Response team</b><small>Clean-up drives · container covers · household info, for ~${fmt(R.PEOPLE)} people</small></div><b>₱500K</b></div>
      <div class="deploy"><button type="button" class="btn btn--go btn--sm" id="deploy" ${kits && !capped(sel) ? "" : "disabled"}>Deploy team</button>
        <button type="button" class="btn btn--dark-ghost btn--sm" id="recall" ${now ? "" : "disabled"}>Recall</button></div>
      <div class="sub">${capped(sel) ? "Max coverage reached (30% of the population)." : kits ? `${kits} team${kits === 1 ? "" : "s"} left.` : "No teams left: end the turn."}</div></div>
    ${roster()}`;
  $("deploy").onclick = () => {
    if (!kits || capped(sel)) return;
    (plan[sel] ||= {})[turn] = now + 1; kits--; sfx.deploy(); tick(`Team deployed to ${p.name}.`); refresh({ drop: p.id });
  };
  $("recall").onclick = () => { if (!now) return; plan[sel][turn] = now - 1; kits++; sfx.recall(); refresh(); };
}
function pick(k) {
  if (k == null || k === sel) return;
  sel = k; sfx.click();
  board?.select(region.provinces[k].id);
  renderList(); renderDetail();
}
$("plist").addEventListener("click", (e) => { const b = e.target.closest(".prow"); if (b) pick(+b.dataset.k); });
$("plist").addEventListener("keydown", (e) => {
  const step = { ArrowDown: 1, ArrowUp: -1 }[e.key];
  if (!step) return;
  e.preventDefault();
  const n = region.provinces.length, k = sel == null ? 0 : (sel + step + n) % n;
  pick(k); $("plist").querySelector(`[data-k="${k}"]`)?.focus();
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
  $("h-rain").textContent = `${fmt(mm)} mm`;
  const sky = mm < 10 ? ["clear", "Mostly dry"] : mm < 30 ? ["rain", "Showers"] : mm < 56 ? ["rain", "Heavy rain"] : ["storm", "Storm"];
  $("h-sky").textContent = sky[1];
  $("board-wrap").dataset.weather = sky[0];
  const pr = R.pressure(region, i), [lab, col] = PRESS[pr.level];
  $("h-press").textContent = lab; $("h-press").style.color = col;
  $("h-meter").style.transform = `scaleX(${Math.min(1, pr.value / 2)})`; $("h-meter").style.background = col;
  $("end").innerHTML = `${turn === TURNS.length - 1 ? "End season" : "End turn"} ${icon("play", { size: 24 })}`;
  $("side-sub").textContent = `${kits} of ${K.kits} teams left`;
  $("legend-intel").innerHTML = round === 2 ? `<span class="intel">◯ EpiLag intel: forecast 4 weeks ahead</span>` : "";
  // the board
  board.setWeek(Object.fromEntries(region.provinces.map((p) => [p.id, columnOf(p, i)])), { duration });
  const counts = Object.fromEntries(region.provinces.map((p, k) => [p.id, teamsIn(k)]));
  board.setTeams(counts, { drop });
  board.setRain(mm);
  rainLevel = Math.min(1, mm / 70);
  rainSound(rainLevel);
  board.setGlow(region.provinces.filter((p) => p.cases[i] != null && p.epi[i] != null && p.cases[i] > p.epi[i]).map((p) => p.id));
  if (round === 2) {
    board.setIntel(Object.fromEntries(region.provinces.map((p) => [p.id, p.fc[tw]?.[0] ?? null])),
      Object.fromEntries(region.provinces.filter((p) => p.fc[tw] && p.fc[tw][0] !== "normal").map((p) => [p.id, `▲${fmt(p.fc[tw][2])}`])));
  } else board.setIntel(null);
  // mosquitoes: more after rain; more over provinces with more cases (same formula as before)
  const anchors = [];
  region.provinces.forEach((p) => { const r = Math.min(4, (p.cases[i] || 0) / (p.epi[i] || 1)); for (let j = 0; j < 1 + Math.round(r * 3); j++) anchors.push(p.id); });
  const rain = region.provinces.reduce((s, p) => s + (p.rain[i] || 0) + (p.rain[i - 1] || 0), 0) / region.provinces.length;
  // the old 2D board drew up to 220 specks; in 3D each is a sprite, so draw half as many
  board.setBugs(Math.round(Math.max(12, Math.min(220, Math.round(rain * 1.6))) / 2), anchors);
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
  return `Week ending ${day(tw)}: ${fmt(region.provinces.reduce((s, p) => s + (p.rain[i] || 0), 0) / region.provinces.length)} mm of rain on average across the region.`;
}
function warp(text, sub, then) {
  $("warp-text").textContent = text; $("warp-sub").textContent = sub; $("warp").classList.add("on");
  setTimeout(() => { $("warp").classList.remove("on"); then?.(); }, reduce ? 50 : 1300);
}
async function startRound(r) {
  round = r; turn = 0; kits = K.kits; plan = {}; sel = null;
  $("mode").textContent = r === 1 ? "Round 1 · No intel" : "Round 2 · EpiLag intel";
  $("mode").classList.toggle("chip--intel", r === 2);
  show("s-game"); sfx.turn();
  if (!board || board.regionId !== region.id) {
    board?.dispose();
    $("board").innerHTML = "";
    board = await createBoard($("board"), { grid: boards[region.id], region, onFlash: lightning,
      onPick: (u) => { const k = region.provinces.findIndex((p) => p.id === u); if (k >= 0) pick(k); } });
    board.regionId = region.id;
  }
  board.select(null);
  board.resetView();
  warp(r === 1 ? "Round 1" : "Round 2", r === 1 ? "Case reports only" : "EpiLag-PH intel online", () => { refresh({ duration: 0 }); tick(headline()); });
}
$("end").addEventListener("click", () => {
  sfx.turn(); board.burst();
  if (turn < TURNS.length - 1) {
    turn++;
    $("end").disabled = true;
    toast("2 weeks later", `${day(TURNS[turn])} 2019`);
    setTimeout(() => {
      $("end").disabled = false;
      refresh({ duration: 1400 });
      const i = idx(TURNS[turn]);
      board.floaters(region.provinces.map((p) => [p.id, (p.cases[i - 1] || 0) + (p.cases[i] || 0)]));
      tick(headline());
    }, reduce ? 0 : 900);
  } else warp("Season over", "Counting the real 2019 cases", endRound);
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
  $("r-lead").textContent = `Your grade compares you with the better of two fixed strategies for ${region.name}. Range: ${fmt(s.lo)}–${fmt(s.hi)} cases averted.`;
  $("r-scores").innerHTML = `<div class="panel"><div class="big nums">${fmt(s.mid)}</div><p>cases averted (central estimate)</p></div>
    <div class="panel"><div class="big nums">${s.onTime}<small>/ ${s.used}</small></div><p>teams in 4+ weeks before a peak</p></div>
    <div class="panel"><div class="big nums">${s.late}<small>/ ${s.used}</small></div><p>teams too close to the peak, or after</p></div>
    <div class="panel"><div class="big nums">${s.noOutbreak}<small>/ ${s.used}</small></div><p>teams where no outbreak came</p></div>`;
  const badges = [
    ["early", "Early bird", "3+ teams 4 weeks before a peak", s.onTime >= 3], ["waste", "No waste", "No team where no outbreak came", s.used > 0 && s.noOutbreak === 0],
    ["full", "All in", "Deployed all 10 teams", s.used === K.kits], ["bot", "Beat the bot", "More than EpiLag's autopilot", s.mid > auto.mid],
    ["saved", "Life saver", "Averted 100+ cases", s.mid >= 100],
  ];
  $("r-badges").innerHTML = badges.map(([ic, n, d, got], j) => `<div class="badge${got ? " got" : ""}" style="animation-delay:${0.5 + j * 0.15}s">${icon(BADGE_ICON[ic], { size: ic === "early" || ic === "waste" ? 36 : 48 })}<b>${n}</b><span>${got ? d : `Locked · ${d}`}</span></div>`).join("");
  $("r-replay").innerHTML = region.provinces.map((p, k) => {
    const pk = R.peak(p), ts = [];
    Object.entries(plan[k] || {}).forEach(([t, n]) => { for (let j = 0; j < n; j++) ts.push(+t); });
    return `<div class="panel"><b>${p.name}</b><small>${pk == null ? "No outbreak" : `Peaked ${day(WEEKS[pk])}`} · ${ts.length} team${ts.length === 1 ? "" : "s"}</small>${spark(p, WEEKS.length - 1, { teams: ts, peak: pk, cls: "" })}</div>`;
  }).join("");
  $("r-actions").innerHTML = `<button type="button" class="btn btn--go" id="next-r">${round === 1 ? "Round 2 · with EpiLag intel" : "Debrief"} ${icon("play", { size: 24 })}</button>`;
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
  const h = R.honest();
  $("vs-honest").textContent = `Across all ${D.regions.length} regions, the bot that follows EpiLag's alerts averted more cases than the bot that reacts to reports in ${h.better}, about the same in ${h.tie}, and fewer in ${h.worse}. `
    + "How scoring works: a team covers about 33,000 people (up to 30% of a province) and prevents a share of the cases reported 2 to 9 weeks later, since people already infected still fall sick. "
    + "The share uses cautious effects for clean-ups with container covers (10–50%, central 30%; Bowman et al. 2016), so treat the numbers as estimates.";
  show("s-vs"); sfx.grade();
}
$("again").addEventListener("click", () => { show("s-title"); renderMissions(); });

hydrateIcons();
$("mute").innerHTML = icon("sound", { size: 24 });
renderMissions();
