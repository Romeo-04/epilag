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
    area: q.get("area") || null,
    map: q.get("map") === "maplibre" ? "maplibre" : null,
  };
}

function writeUrl(s, push) {
  const q = new URLSearchParams({ page: s.page, panel: s.panel, mode: s.mode, h: s.h, lang: s.lang });
  if (s.mode === "replay" && s.origin) q.set("origin", s.origin);
  if (s.area) q.set("area", s.area);
  if (s.map) q.set("map", s.map);
  history[push ? "pushState" : "replaceState"](null, "", `?${q}`);
}

let state = readUrl();

/** Change URL state and re-render. A new page returns focus to the content heading. */
function set(patch, { push = true } = {}) {
  const next = { ...state, ...patch };
  if (patch.panel && patch.panel !== state.panel) next.area = null;
  if (patch.mode === "latest") next.origin = null;
  const pageChanged = next.page !== state.page;
  state = next;
  writeUrl(state, push);
  closeMobileNav();
  render();
  if (pageChanged) { scrollTo({ top: 0 }); $("view").focus({ preventScroll: true }); }
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
  $("sidebar-toggle")?.addEventListener("click", () => {
    const collapsed = document.body.classList.toggle("sidebar-collapsed");
    $("sidebar-toggle").setAttribute("aria-expanded", String(!collapsed));
    $("sidebar-toggle").setAttribute("aria-label", collapsed ? LABELS[state.lang].expand_navigation : LABELS[state.lang].collapse_navigation);
  });
  addEventListener("keydown", (e) => { if (e.key === "Escape") closeMobileNav(); });
}

let topDownloadCleanup = null;
function clearTopAction() {
  topDownloadCleanup?.();
  topDownloadCleanup = null;
  const host = $("top-actions");
  if (host) host.innerHTML = "";
}
function setTopDownload(label, handler) {
  const host = $("top-actions");
  if (!host) return;
  topDownloadCleanup?.();
  host.innerHTML = `<details class="download-menu"><summary class="btn btn--ghost btn--sm top-download"><i data-icon="download" data-size="20"></i><span>${esc(LABELS[state.lang].download)}</span><i data-icon="chevronRight" data-size="16" class="download-menu__chev"></i></summary><div class="download-menu__pop"><button type="button" id="top-download">${icon("download", { size: 18 })}<span>${esc(label)}</span></button></div></details>`;
  const button = $("top-download");
  const onClick = () => handler();
  button.addEventListener("click", onClick);
  topDownloadCleanup = () => button.removeEventListener("click", onClick);
  hydrateIcons(host);
}

// ------------------------------------------------------------------ chrome
function groupFor(page) {
  return GROUPS.find(([, pages]) => pages.includes(page))?.[0] || "monitor";
}

function renderChrome(t, originList) {
  const labels = LABELS[state.lang];
  document.documentElement.lang = state.lang === "fil" ? "fil" : "en";
  const group = groupFor(state.page);
  $("app-page-title").textContent = t[`nav_${state.page}`];
  $("app-page-group").textContent = labels[group];
  $("app-page-note").textContent = i18n.PANELS[state.panel].note[state.lang];
  $("sidebar-title").textContent = labels.dashboard;
  $("sidebar").querySelector(".sidebar__language .ctx__label")?.replaceChildren(document.createTextNode(t.lang));
  $("sidebar").querySelector(".sidebar__link .nav-item__text")?.replaceChildren(document.createTextNode(labels.drill));
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

  const P = i18n.PANELS, replay = state.mode === "replay";
  const hs = replay ? [4, 8] : [2, 4, 6, 8];
  $("ctx").innerHTML = `
    <div class="ctx__item"><span class="ctx__label">${esc(t.dataset)}</span><div class="seg" id="c-panel"></div>
      <span class="ctx__note">${esc(P[state.panel].note[state.lang])}</span></div>
    <div class="ctx__item"><span class="ctx__label">${esc(t.mode)}</span><div class="seg" id="c-mode"></div></div>
    ${replay ? `<div class="ctx__item ctx__item--origin"><label class="ctx__label" for="c-origin">${esc(t.origin)} <b id="c-origin-v">${esc(fmtDay(dayOf(state.origin)))}</b></label>
      <input type="range" id="c-origin" min="0" max="${Math.max(0, originList.length - 1)}" step="1" value="${Math.max(0, originList.indexOf(dayOf(state.origin)))}" aria-label="${esc(t.origin)}"></div>` : ""}
    <div class="ctx__item"><span class="ctx__label">${esc(t.horizon)}</span><div class="seg" id="c-h"></div></div>`;
  segmented($("c-panel"), t.dataset, Object.keys(P).map((p) => [p, P[p].label[state.lang]]), state.panel, (v) => set({ panel: v }));
  segmented($("c-mode"), t.mode, [["latest", t.mode_latest], ["replay", t.mode_replay]], state.mode, (v) => set({ mode: v }));
  segmented($("c-h"), t.horizon, hs.map((h) => [h, String(h)]), state.h, (v) => set({ h: Number(v) }, { push: false }));
  const slider = $("c-origin");
  if (slider) {
    const day = () => originList[Number(slider.value)];
    slider.oninput = () => { $("c-origin-v").textContent = fmtDay(day()); };
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
    let list = [];
    if (state.mode === "replay") {
      const o = await origins(state.panel);
      list = o.list;
      if (!state.origin || !list.includes(dayOf(state.origin))) { state.origin = isoOf(o.fallback); writeUrl(state, false); }
    }
    const hs = state.mode === "replay" ? [4, 8] : [2, 4, 6, 8];
    if (!hs.includes(state.h)) { state.h = 4; writeUrl(state, false); }
    renderChrome(t, list);
    if (id !== renderId) return;

    cleanup?.(); cleanup = null;
    clearTopAction();
    view.setAttribute("aria-busy", "true");
    view.innerHTML = `<div class="skeleton" aria-label="Loading"><i></i><i></i><i></i></div>`;
    const origin = state.mode === "replay" ? dayOf(state.origin) : null;
    const [mod, fc] = await Promise.all([VIEWS[state.page](), NEEDS_FORECAST.has(state.page) ? forecastFor({ panel: state.panel, mode: state.mode, origin }) : null]);
    if (id !== renderId) return;
    if (fc?.length) {
      const current = fc.filter((r) => r.horizon === state.h);
      $("app-page-note").textContent = `${t.as_of} ${fmtDay(Math.max(...current.map((r) => r.week)))} · ${i18n.PANELS[state.panel].note[state.lang]}`;
    }
    const ctx = {
      ...state, horizon: state.h, origin, t, i18n, labels: LABELS[state.lang], lang: state.lang, meta: m.panels[state.panel],
      panelLabel: i18n.PANELS[state.panel].label[state.lang],
      levelName: (lv) => i18n.LEVEL_NAME[state.lang][lv],
      fc, fcH: fc ? fc.filter((r) => r.horizon === state.h) : null,
      set, go: (page, extra = {}) => set({ page, ...extra }),
      topDownload: setTopDownload,
    };
    view.innerHTML = "";
    cleanup = (await mod.render(view, ctx)) || null;
    hydrateIcons(view);
    hydrateCounts(view);
    view.removeAttribute("aria-busy");
  } catch (err) {
    if (id !== renderId) return;
    console.error(err);
    view.removeAttribute("aria-busy");
    view.innerHTML = `<section class="card empty-state callout-error"><span class="empty-state__icon">${icon("alert", { size: 24 })}</span><div><b>Could not load the data.</b><p>${esc(err.message)}</p><button type="button" class="btn btn--ghost btn--sm" id="retry">Try again</button></div></section>`;
    view.querySelector("#retry")?.addEventListener("click", () => location.reload());
  }
}

// Exposed for tests/test_web_logic.py; this is intentionally unchanged in shape.
window.epilag = { logic, data };

bindShell();
hydrateIcons(document);
writeUrl(state, false);
render();
