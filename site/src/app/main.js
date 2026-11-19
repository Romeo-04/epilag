// EpiLag-PH dashboard shell: URL state, responsive navigation, forecast controls, and lazy views.
// Keep this file deliberately thin so the data and logic modules remain usable from window.epilag.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./app.css";
import "../lib/pixel.js";
import i18n from "./i18n.json";
import LABELS from "./labels.js";
import { hydrateIcons, icon } from "../lib/icons.js";
import * as data from "./data.js";
import * as logic from "./logic.js";
import { forecastFor, meta, origins } from "./data.js";
import { dayOf, fmtDay, isoOf } from "./logic.js";
import { esc, hydrateCounts, segmented } from "./ui.js";

const PAGES = ["home", "map", "unit", "budget", "public", "qc", "proof", "about"];
const PAGE_ICON = { home: "menu", map: "forecastMap", unit: "areaDetail", budget: "actionPlan", public: "residents", qc: "barangay", proof: "didItWork", about: "info" };
const GROUPS = [
  ["monitor", ["home", "map", "unit"]],
  ["act", ["budget", "public", "qc"]],
  ["evidence", ["proof", "about"]],
];
const VIEWS = {
  home: () => import("./views/home.js"), map: () => import("./views/map.js"), unit: () => import("./views/unit.js"),
  budget: () => import("./views/budget.js"), public: () => import("./views/public.js"), qc: () => import("./views/qc.js"),
  proof: () => import("./views/proof.js"), about: () => import("./views/about.js"),
};
const NEEDS_FORECAST = new Set(["home", "map", "unit", "budget", "public", "qc"]);
const $ = (id) => document.getElementById(id);

// ------------------------------------------------------------------ state <-> URL
function readUrl() {
  const q = new URLSearchParams(location.search);
  const page = PAGES.includes(q.get("page")) ? q.get("page") : "home";
  const hs = [2, 4, 6, 8];
  const h = Number(q.get("h"));
  return {
    page,
    panel: q.get("panel") === "province" ? "province" : "region_qc",
    mode: q.get("mode") === "replay" ? "replay" : "latest",
    origin: /^\d{4}-\d{2}-\d{2}$/.test(q.get("origin") || "") ? q.get("origin") : null,
    h: hs.includes(h) ? h : 4,
    lang: q.get("lang") === "fil" ? "fil" : "en",
    region: q.get("region") || null,
    area: q.get("area") || null,
    focus: /^[\w-]{1,40}$/.test(q.get("focus") || "") ? q.get("focus") : null, // the forecast map's drill-down level
  };
}

function writeUrl(s, push) {
  const q = new URLSearchParams({ page: s.page, panel: s.panel, mode: s.mode, h: s.h, lang: s.lang });
  if (s.mode === "replay" && s.origin) q.set("origin", s.origin);
  if (s.region) q.set("region", s.region);
  if (s.area) q.set("area", s.area);
  if (s.focus) q.set("focus", s.focus);
  history[push ? "pushState" : "replaceState"](null, "", `?${q}`);
}

let state = readUrl();

// Onboarding guide: opens by itself once per device, on the first visit to the Overview, and any time from "How to use"
// in the top bar. ?guide=1 forces it, ?guide=0 keeps it closed.
// writeUrl() drops the parameter, so read it once here.
const guideParam = new URLSearchParams(location.search).get("guide");
let guideAuto = guideParam === "1" ? "force" : guideParam === "0" ? "off" : "auto";
const guideSeen = () => { try { return localStorage.getItem("el-guide") === "done"; } catch { return true; } };

/** Show the Overview, then start the guide (its code loads only when needed). */
async function openGuide(returnTo) {
  closeMobileNav();
  if (state.page !== "home") await set({ page: "home" });
  const { startGuide } = await import("./guide.js");
  if (state.page !== "home") return; // the user moved on while it loaded
  const lang = state.lang;
  startGuide({ lang, t: i18n.T[lang], labels: LABELS[lang], levelName: (lv) => i18n.LEVEL_NAME[lang][lv], go: (page) => set({ page }), returnTo });
}

/** Change URL state and re-render (resolves when the page has rendered). A new page returns focus to the content heading. */
function set(patch, { push = true } = {}) {
  const next = { ...state, ...patch };
  if (patch.panel && patch.panel !== state.panel && !Object.prototype.hasOwnProperty.call(patch, "area")) next.area = null;
  if (patch.mode === "latest") next.origin = null;
  // a new region or area from the settings starts the map's drill-down from there
  if (("region" in patch || "area" in patch || "panel" in patch) && !("focus" in patch)) next.focus = null;
  const pageChanged = next.page !== state.page;
  if (pageChanged) ctxOpen = false;
  state = next;
  writeUrl(state, push);
  closeMobileNav();
  const done = render();
  if (pageChanged) { scrollTo({ top: 0 }); $("view").focus({ preventScroll: true }); }
  return done;
}

/**
 * Update URL state without re-rendering the view (the forecast map drills down in place and keeps its animation).
 * The settings bar is redrawn so it shows the new region; the page note and the top Download menu are kept.
 */
let chromeArgs = null, topArgs = null;
function setQuiet(patch) {
  state = { ...state, ...patch };
  writeUrl(state, false);
  if (!chromeArgs) return;
  const note = $("app-page-note").textContent, keep = topArgs;
  renderChrome(...chromeArgs);
  $("app-page-note").textContent = note;
  if (keep) setTopDownload(...keep);
}

addEventListener("popstate", () => { state = readUrl(); closeMobileNav(); render(); });

// ------------------------------------------------------------------ shell interactions
function closeMobileNav() {
  document.body.classList.remove("nav-open");
  $("mobile-menu")?.setAttribute("aria-expanded", "false");
  $("mobile-close")?.setAttribute("aria-expanded", "false");
}

function bindShell() {
  $("mobile-menu")?.addEventListener("click", () => {
    const open = document.body.classList.toggle("nav-open");
    $("mobile-menu").setAttribute("aria-expanded", String(open));
    $("mobile-close")?.setAttribute("aria-expanded", String(open));
    if (open) $("mobile-close")?.focus();
  });
  $("mobile-close")?.addEventListener("click", closeMobileNav);
  $("guide-top")?.addEventListener("click", () => openGuide($("guide-top")));
  $("sidebar-toggle")?.addEventListener("click", () => {
    const collapsed = document.body.classList.toggle("sidebar-collapsed");
    $("sidebar-toggle").setAttribute("aria-expanded", String(!collapsed));
    $("sidebar-toggle").setAttribute("aria-label", collapsed ? LABELS[state.lang].expand_navigation : LABELS[state.lang].collapse_navigation);
  });
  addEventListener("keydown", (e) => { if (e.key === "Escape") closeMobileNav(); });
}

let topDownloadCleanup = null;
function clearTopAction() {
  topArgs = null;
  topDownloadCleanup?.();
  topDownloadCleanup = null;
  const host = $("top-actions");
  if (host) host.innerHTML = "";
}
/** The top-bar Download menu: the main download, plus optional [label, handler, icon] items (e.g. print). */
function setTopDownload(label, handler, more = []) {
  const host = $("top-actions");
  if (!host) return;
  topDownloadCleanup?.();
  topArgs = [label, handler, more];
  const items = [[label, handler, "download"], ...more];
  host.innerHTML = `<details class="download-menu"><summary class="btn btn--ghost btn--sm top-download"><i data-icon="download" data-size="20"></i><span>${esc(LABELS[state.lang].download)}</span><i data-icon="chevronRight" data-size="16" class="download-menu__chev"></i></summary><div class="download-menu__pop">${
    items.map(([l, , ic], i) => `<button type="button" id="${i ? `top-download-${i}` : "top-download"}" data-i="${i}">${icon(ic || "download", { size: 18 })}<span>${esc(l)}</span></button>`).join("")}</div></details>`;
  const menu = host.querySelector(".download-menu");
  const onClick = (e) => {
    const b = e.target.closest("button[data-i]");
    if (!b) return;
    menu.open = false;
    items[Number(b.dataset.i)][1]();
  };
  menu.addEventListener("click", onClick);
  topDownloadCleanup = () => menu.removeEventListener("click", onClick);
  hydrateIcons(host);
}

// ------------------------------------------------------------------ chrome
function panelLabel(labels, panel) {
  return panel === "province" ? labels.provinces : labels.regions;
}

/** Keep old URLs usable while making the new region/area relationship explicit. */
function normalizeState(m) {
  const regions = Array.isArray(m.regions) ? m.regions : [];
  let region = regions.find((r) => r.id === state.region) || null;
  let changed = false;

  if (state.region && !region) {
    state.region = null;
    changed = true;
  }

  // Old latest links may contain area=R_* or area=QC without the new region param.
  if (!state.region && state.panel === "region_qc" && state.area) {
    region = regions.find((r) => r.id === state.area || (r.cities || []).includes(state.area)) || null;
    if (region) {
      state.region = region.id;
      changed = true;
    } else {
      state.area = null;
      changed = true;
    }
  } else {
    region = regions.find((r) => r.id === state.region) || null;
  }

  if (region) {
    const isProvince = (region.provinces || []).includes(state.area);
    const isLatest = state.area === region.id || (region.cities || []).includes(state.area);
    if (!isProvince && !isLatest) {
      state.panel = "region_qc";
      state.area = region.id;
      changed = true;
    } else {
      const panel = isProvince ? "province" : "region_qc";
      if (state.panel !== panel) { state.panel = panel; changed = true; }
      if (isProvince && state.mode === "latest") { state.mode = "replay"; state.origin = null; changed = true; }
    }
  } else if (state.panel === "region_qc" && state.area) {
    state.area = null;
    changed = true;
  }

  if (changed) writeUrl(state, false);
  return region;
}

let ctxOpen = false, ctxOpenedAt = 0; // phone settings panel, open or folded (kept while settings change)
function setCtxOpen(open) {
  ctxOpen = open;
  ctxOpenedAt = scrollY;
  $("ctx").dataset.open = String(open);
  $("ctx-summary")?.setAttribute("aria-expanded", String(open));
}
// the header is sticky, so an open panel would ride along over the page: fold it once the page scrolls on
addEventListener("scroll", () => { if (ctxOpen && Math.abs(scrollY - ctxOpenedAt) > 120) setCtxOpen(false); }, { passive: true });

function renderChrome(t, originList, m) {
  const labels = LABELS[state.lang];
  const regions = [...(m.regions || [])].sort((a, b) => String(a.psgc).localeCompare(String(b.psgc)));
  const region = regions.find((r) => r.id === state.region) || null;
  const latestNames = m.panels.region_qc.names || {};
  const provinceNames = m.panels.province.names || {};
  const areaRows = region ? [
    { value: region.id, kind: "latest", label: `${labels.whole_region} ${labels.latest_suffix}` },
    ...(region.cities || []).map((id) => ({ value: id, kind: "latest", label: `${latestNames[id] || id} ${labels.latest_suffix}` })),
    ...(region.provinces || []).map((id) => ({ value: id, kind: "province", label: `${provinceNames[id] || id} ${labels.province_suffix}` })),
  ] : [];
  const selectedArea = areaRows.some((r) => r.value === state.area) ? state.area : region?.id || "";
  const provinceScope = state.panel === "province";
  const panelNote = i18n.PANELS[state.panel].note[state.lang];
  document.documentElement.lang = state.lang === "fil" ? "fil" : "en";
  $("app-page-title").textContent = t[`nav_${state.page}`];
  $("app-page-note").textContent = panelNote;
  $("sidebar-title").textContent = labels.dashboard;
  $("sidebar").querySelector(".sidebar__language .ctx__label")?.replaceChildren(document.createTextNode(t.lang));
  $("sidebar").querySelector("a.sidebar__link .nav-item__text")?.replaceChildren(document.createTextNode(labels.drill));
  $("install-app")?.querySelector(".nav-item__text")?.replaceChildren(document.createTextNode(labels.install));
  $("guide-top")?.querySelector("span")?.replaceChildren(document.createTextNode(labels.guide));
  $("guide-top")?.setAttribute("aria-label", labels.guide);
  $("sidebar").setAttribute("aria-label", labels.navigation);
  $("mobile-menu")?.setAttribute("aria-label", labels.open_navigation);
  $("mobile-close")?.setAttribute("aria-label", labels.close_navigation);
  $("sidebar-toggle")?.setAttribute("aria-label", document.body.classList.contains("sidebar-collapsed") ? labels.expand_navigation : labels.collapse_navigation);

  $("tabs").innerHTML = GROUPS.map(([name, pages]) => `<section class="nav-group" aria-labelledby="nav-group-${name}">
    <h2 class="nav-group__label" id="nav-group-${name}">${esc(labels[name])}</h2>
    <div class="nav-group__items">${pages.map((p) => `<a href="?page=${p}" data-page="${p}"${p === state.page ? ' aria-current="page"' : ""}>
      <span class="nav-item__icon">${icon(PAGE_ICON[p], { size: 24 })}</span><span class="nav-item__text">${esc(t[`nav_${p}`])}</span>
    </a>`).join("")}</div></section>`).join("");
  $("tabs").onclick = (e) => {
    const a = e.target.closest("a[data-page]");
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    set({ page: a.dataset.page });
  };

  segmented($("lang"), t.lang, [["en", "EN"], ["fil", "FIL"]], state.lang, (v) => set({ lang: v }, { push: false }));

  const replay = state.mode === "replay";
  const hs = replay ? [4, 8] : [2, 4, 6, 8];
  // On phones the four settings fold into one summary line (see .ctx-summary in app.css); desktop shows them all.
  const where = region ? (areaRows.find((r) => r.value === selectedArea)?.label.replace(/ ·.*$/, "") || region.name) : labels.all_philippines;
  const when = replay ? `${t.mode_replay} ${fmtDay(dayOf(state.origin))}` : t.mode_latest;
  const summary = [region && selectedArea !== region.id ? `${region.name} › ${where}` : region ? region.name : where, when, labels.wk_short.replace("{h}", state.h)];
  $("ctx").dataset.open = String(ctxOpen);
  $("ctx").innerHTML = `
    <button type="button" class="ctx-summary" id="ctx-summary" aria-expanded="${ctxOpen}" aria-controls="ctx-fields">
      <span class="ctx-summary__label">${esc(labels.forecast_settings)}</span>
      <span class="ctx-summary__value">${summary.map((x) => `<span>${esc(x)}</span>`).join("")}</span>
      <i data-icon="chevronRight" data-size="18" class="ctx-summary__chev"></i>
    </button>
    <div class="ctx__fields" id="ctx-fields">
    <label class="ctx__item ctx__item--region" for="c-region"><span class="ctx__label">${esc(labels.region)}</span>
      <select class="ctx__select" id="c-region" aria-label="${esc(labels.region)}">
        <option value=""${state.region ? "" : " selected"}>${esc(labels.all_philippines)}</option>
        ${regions.map((r) => `<option value="${esc(r.id)}"${r.id === state.region ? " selected" : ""}>${esc(r.name)}</option>`).join("")}
      </select></label>
    <label class="ctx__item ctx__item--area" for="c-area"><span class="ctx__label">${esc(labels.province_city)}</span>
      <select class="ctx__select" id="c-area"${region ? "" : " disabled"}${provinceScope ? ' aria-describedby="c-scope-note"' : ""}>
        ${region ? areaRows.map((r) => `<option value="${esc(r.value)}"${r.value === selectedArea ? " selected" : ""}>${esc(r.label)}</option>`).join("") : `<option value="">${esc(labels.choose_region_first)}</option>`}
      </select>${provinceScope ? `<span class="ctx__note ctx__note--old" id="c-scope-note">${esc(labels.province_note)}</span>` : ""}
    </label>
    <label class="ctx__item ctx__item--mode" for="c-mode"><span class="ctx__label">${esc(t.mode)}</span>
      <select class="ctx__select" id="c-mode"><option value="latest"${state.mode === "latest" ? " selected" : ""}>${esc(t.mode_latest)}</option><option value="replay"${state.mode === "replay" ? " selected" : ""}>${esc(t.mode_replay)}</option></select>
    </label>
    ${replay ? `<label class="ctx__item ctx__item--origin" for="c-origin"><span class="ctx__label">${esc(t.origin)} <b id="c-origin-v">${esc(fmtDay(dayOf(state.origin)))}</b></span>
      <input class="ctx__range" type="range" id="c-origin" min="0" max="${Math.max(0, originList.length - 1)}" step="1" value="${Math.max(0, originList.indexOf(dayOf(state.origin)))}" aria-label="${esc(t.origin)}" aria-valuetext="${esc(fmtDay(dayOf(state.origin)))}"></label>` : ""}
    <label class="ctx__item ctx__item--horizon" for="c-h"><span class="ctx__label">${esc(t.horizon)}</span>
      <select class="ctx__select" id="c-h">${hs.map((h) => `<option value="${h}"${h === state.h ? " selected" : ""}>${h}</option>`).join("")}</select>
    </label>
    </div>`;
  $("ctx-summary").addEventListener("click", () => setCtxOpen(!ctxOpen));
  $("c-region").addEventListener("change", (e) => {
    const id = e.target.value || null;
    set({ region: id, panel: "region_qc", area: id }, { push: true });
  });
  $("c-area").addEventListener("change", (e) => {
    const choice = areaRows.find((r) => r.value === e.target.value);
    if (!choice || !region) return;
    const isProvince = choice.kind === "province";
    set({ region: region.id, panel: isProvince ? "province" : "region_qc", area: choice.value, mode: isProvince && state.mode === "latest" ? "replay" : state.mode }, { push: true });
  });
  $("c-mode").addEventListener("change", (e) => set({ mode: e.target.value }));
  $("c-h").addEventListener("change", (e) => set({ h: Number(e.target.value) }, { push: false }));
  const slider = $("c-origin");
  if (slider) {
    const day = () => originList[Number(slider.value)];
    slider.oninput = () => {
      const selected = day();
      $("c-origin-v").textContent = fmtDay(selected);
      slider.setAttribute("aria-valuetext", fmtDay(selected));
    };
    slider.onchange = () => set({ origin: isoOf(day()) }, { push: false });
  }
  clearTopAction();
  hydrateIcons($("sidebar"));
  hydrateIcons($("ctx"));
}

// ------------------------------------------------------------------ render
let renderId = 0, cleanup = null;
async function render() {
  const id = ++renderId, t = i18n.T[state.lang];
  document.title = `${t[`nav_${state.page}`]} · EpiLag-PH`;
  const view = $("view");
  try {
    const m = await meta();
    const region = normalizeState(m);
    let list = [];
    if (state.mode === "replay") {
      const o = await origins(state.panel);
      list = o.list;
      if (!state.origin || !list.includes(dayOf(state.origin))) { state.origin = isoOf(o.fallback); writeUrl(state, false); }
    }
    const hs = state.mode === "replay" ? [4, 8] : [2, 4, 6, 8];
    if (!hs.includes(state.h)) { state.h = 4; writeUrl(state, false); }
    renderChrome(t, list, m);
    chromeArgs = [t, list, m];
    if (id !== renderId) return;

    cleanup?.(); cleanup = null;
    clearTopAction();
    view.setAttribute("aria-busy", "true");
    view.innerHTML = `<div class="skeleton" aria-label="Loading"><i></i><i></i><i></i></div>`;
    const origin = state.mode === "replay" ? dayOf(state.origin) : null;
    const [mod, allFc] = await Promise.all([VIEWS[state.page](), NEEDS_FORECAST.has(state.page) ? forecastFor({ panel: state.panel, mode: state.mode, origin }) : null]);
    const allowed = state.panel === "province" && region ? new Set(region.provinces || []) : null;
    const fc = allFc && allowed ? allFc.filter((r) => allowed.has(r.unit_id)) : allFc;
    if (id !== renderId) return;
    if (fc?.length) {
      const current = fc.filter((r) => r.horizon === state.h);
      $("app-page-note").textContent = `${LABELS[state.lang].data_to} ${fmtDay(Math.max(...current.map((r) => r.week)))} → ${fmtDay(Math.max(...current.map((r) => r.target_week)))}`;
    }
    const ctx = {
      ...state, horizon: state.h, origin, t, i18n, labels: LABELS[state.lang], lang: state.lang, meta: m.panels[state.panel], regionMeta: region,
      panelLabel: panelLabel(LABELS[state.lang], state.panel),
      levelName: (lv) => i18n.LEVEL_NAME[state.lang][lv],
      fc, fcH: fc ? fc.filter((r) => r.horizon === state.h) : null,
      set, setQuiet, go: (page, extra = {}) => set({ page, ...extra }),
      topDownload: setTopDownload,
    };
    view.innerHTML = "";
    cleanup = (await mod.render(view, ctx)) || null;
    hydrateIcons(view);
    hydrateCounts(view);
    view.removeAttribute("aria-busy");
    if (state.page === "home" && (guideAuto === "force" || (guideAuto === "auto" && !guideSeen()))) { guideAuto = "off"; openGuide(); }
  } catch (err) {
    if (id !== renderId) return;
    console.error(err);
    view.removeAttribute("aria-busy");
    view.innerHTML = `<section class="card empty-state callout-error"><span class="empty-state__icon">${icon("alert", { size: 24 })}</span><div><b>Could not load the data.</b><p>${esc(err.message)}</p><button type="button" class="btn btn--ghost btn--sm" id="retry">Try again</button></div></section>`;
    view.querySelector("#retry")?.addEventListener("click", () => location.reload());
  }
}

// ------------------------------------------------------------------ offline app
// The service worker (src/sw.js, built to docs/sw.js) saves the dashboard on the first visit. A banner says when
// the page is showing saved data; "Install app" appears where the browser offers installing.
function offlineBanner() {
  let el = null, timer = 0;
  const show = (online) => {
    const labels = LABELS[state.lang];
    clearTimeout(timer);
    if (!el) { el = Object.assign(document.createElement("div"), { className: "offline-banner", role: "status" }); document.body.append(el); }
    el.dataset.state = online ? "online" : "offline";
    el.innerHTML = `<span class="sq sq--round"></span><span>${esc(online ? labels.offline_back : labels.offline)}</span>`;
    if (online) timer = setTimeout(() => { el?.remove(); el = null; }, 2500);
  };
  addEventListener("offline", () => show(false));
  addEventListener("online", () => { if (el) show(true); });
  if (!navigator.onLine) show(false);
}

function installButton() {
  const btn = $("install-app");
  if (!btn) return;
  let prompt = null;
  addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    prompt = e;
    btn.querySelector(".nav-item__text").textContent = LABELS[state.lang].install;
    btn.hidden = false;
  });
  btn.addEventListener("click", async () => {
    if (!prompt) return;
    prompt.prompt();
    await prompt.userChoice.catch(() => null);
    prompt = null;
    btn.hidden = true;
  });
  addEventListener("appinstalled", () => { btn.hidden = true; });
}

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  addEventListener("load", () => navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`, { scope: import.meta.env.BASE_URL }).catch(() => {}));
}
offlineBanner();
installButton();

// Exposed for tests/test_web_logic.py (logic and data, plus the labels the SMS test reads).
window.epilag = { logic, data, labels: LABELS };

bindShell();
hydrateIcons(document);
writeUrl(state, false);
render();
