// EpiLag-PH web app shell: top bar (pages + language), the forecast settings bar, and a small router.
// All state lives in the URL (?page=map&panel=province&mode=replay&origin=2019-06-02&h=4&lang=fil&area=...), so
// every view can be linked and the old Streamlit ?page= links keep working. Views load lazily from ./views/.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./app.css";
import "../lib/pixel.js";
import i18n from "./i18n.json";
import { hydrateIcons, icon } from "../lib/icons.js";
import * as data from "./data.js";
import * as logic from "./logic.js";
import { forecastFor, meta, origins } from "./data.js";
import { dayOf, fmtDay, isoOf } from "./logic.js";
import { esc, hydrateCounts, segmented } from "./ui.js";

const PAGES = ["home", "map", "unit", "budget", "public", "qc", "proof", "about"];
const PAGE_ICON = { home: "menu", map: "forecastMap", unit: "areaDetail", budget: "actionPlan", public: "residents", qc: "barangay", proof: "didItWork", about: "info" };
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
  return { page, panel: q.get("panel") === "province" ? "province" : "region_qc", mode: q.get("mode") === "replay" ? "replay" : "latest",
    origin: /^\d{4}-\d{2}-\d{2}$/.test(q.get("origin") || "") ? q.get("origin") : null, h: Number(q.get("h")) || 4,
    lang: q.get("lang") === "fil" ? "fil" : "en", area: q.get("area") || null,
    map: q.get("map") === "maplibre" ? "maplibre" : null }; // hidden switch for the D9 MapLibre comparison
}
function writeUrl(s, push) {
  const q = new URLSearchParams({ page: s.page, panel: s.panel, mode: s.mode, h: s.h, lang: s.lang });
  if (s.mode === "replay" && s.origin) q.set("origin", s.origin);
  if (s.area) q.set("area", s.area);
  if (s.map) q.set("map", s.map);
  history[push ? "pushState" : "replaceState"](null, "", `?${q}`);
}
let state = readUrl();

/** Change the state (and the URL) and re-render. A new page scrolls to the top. */
function set(patch, { push = true } = {}) {
  const next = { ...state, ...patch };
  if (patch.panel && patch.panel !== state.panel) next.area = null;
  if (patch.mode === "latest") next.origin = null;
  const pageChanged = next.page !== state.page;
  state = next;
  writeUrl(state, push);
  render();
  if (pageChanged) { scrollTo({ top: 0 }); $("view").focus({ preventScroll: true }); }
}
addEventListener("popstate", () => { state = readUrl(); render(); });

// ------------------------------------------------------------------ chrome
function renderChrome(t, originList) {
  document.documentElement.lang = state.lang === "fil" ? "fil" : "en";
  $("tabs").innerHTML = PAGES.map((p) => `<a role="listitem" href="?page=${p}" data-page="${p}"${p === state.page ? ' aria-current="page"' : ""}>${icon(PAGE_ICON[p], { size: p === "home" || p === "about" ? 24 : 32 })}<span>${esc(t[`nav_${p}`])}</span></a>`).join("");
  $("tabs").onclick = (e) => { const a = e.target.closest("a[data-page]"); if (!a || e.ctrlKey || e.metaKey) return; e.preventDefault(); set({ page: a.dataset.page }); };
  $("tabs").querySelector("[aria-current]")?.scrollIntoView({ block: "nearest", inline: "nearest" });
  segmented($("lang"), t.lang, [["en", "EN"], ["fil", "FIL"]], state.lang, (v) => set({ lang: v }, { push: false }));

  const P = i18n.PANELS, replay = state.mode === "replay";
  const hs = replay ? [4, 8] : [2, 4, 6, 8];
  $("ctx").innerHTML = `
    <div class="ctx__item"><span class="ctx__label">${esc(t.dataset)}</span><div class="seg" id="c-panel"></div>
      <span class="ctx__note">${esc(P[state.panel].note[state.lang])}</span></div>
    <div class="ctx__item"><span class="ctx__label">${esc(t.mode)}</span><div class="seg" id="c-mode"></div></div>
    ${replay ? `<div class="ctx__item ctx__item--grow"><label class="ctx__label" for="c-origin">${esc(t.origin)} <b id="c-origin-v">${esc(fmtDay(dayOf(state.origin)))}</b></label>
      <input type="range" id="c-origin" min="0" max="${originList.length - 1}" step="1" value="${Math.max(0, originList.indexOf(dayOf(state.origin)))}"></div>` : ""}
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
}

// ------------------------------------------------------------------ render
let renderId = 0, cleanup = null;
async function render() {
  const id = ++renderId, t = i18n.T[state.lang];
  document.title = `${t[`nav_${state.page}`]} · EpiLag-PH`;
  const view = $("view");
  try {
    const m = await meta();
    // settle the replay week and the horizon for this panel and mode
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
    view.setAttribute("aria-busy", "true");
    view.innerHTML = `<div class="skeleton"><i></i><i></i><i></i></div>`;
    const origin = state.mode === "replay" ? dayOf(state.origin) : null;
    const [mod, fc] = await Promise.all([VIEWS[state.page](),
      NEEDS_FORECAST.has(state.page) ? forecastFor({ panel: state.panel, mode: state.mode, origin }) : null]);
    if (id !== renderId) return;
    const ctx = {
      ...state, horizon: state.h, origin, t, i18n, lang: state.lang, meta: m.panels[state.panel],
      panelLabel: i18n.PANELS[state.panel].label[state.lang],
      levelName: (lv) => i18n.LEVEL_NAME[state.lang][lv],
      fc, fcH: fc ? fc.filter((r) => r.horizon === state.h) : null,
      set, go: (page, extra = {}) => set({ page, ...extra }),
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
    view.innerHTML = `<div class="card callout-error"><b>Could not load the data.</b> ${esc(err.message)}<br><button type="button" class="btn btn--ghost btn--sm" onclick="location.reload()">Try again</button></div>`;
  }
}

// the logic and data modules, for tests/test_web_logic.py (parity with the Python app through Playwright)
window.epilag = { logic, data };

hydrateIcons(document);
writeUrl(state, false);
render();
