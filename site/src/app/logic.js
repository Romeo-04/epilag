// Forecast logic of the web app, ported from app/streamlit_app.py, src/thresholds.py and src/allocate.py.
// Pure functions on plain row objects, so tests/test_web_logic.py can call them through Playwright and compare
// with the Python on the same data. Dates are whole days since 1970-01-01 (UTC).

export const LEVELS = ["normal", "above usual", "watch", "outbreak warning"];
const DAY = 86400000;
const isNum = (v) => typeof v === "number" && !Number.isNaN(v);
const gt = (a, b) => isNum(a) && isNum(b) && a > b; // pandas: comparisons with NaN are false

/** Columnar table from scripts/build_web.py -> row objects; `u` (unit index) becomes unit_id. */
export function rowsOf(table, units) {
  const { n, cols } = table, names = Object.keys(cols), out = new Array(n);
  for (let i = 0; i < n; i++) {
    const r = {};
    for (const c of names) r[c === "u" ? "unit_id" : c] = c === "u" ? units[cols.u[i]] : cols[c][i];
    out[i] = r;
  }
  return out;
}

/** ISO week number of a day (pandas .dt.isocalendar().week). */
export function isoWeek(day) {
  const d = new Date(day * DAY), dow = (d.getUTCDay() + 6) % 7; // Monday = 0
  const thursday = new Date(d.getTime() + (3 - dow) * DAY);
  const jan1 = Date.UTC(thursday.getUTCFullYear(), 0, 1);
  return Math.floor((thursday.getTime() - jan1) / DAY / 7) + 1;
}
/** Week of year as the app uses it: ISO week, with week 53 folded into 52. */
export const woy = (day) => Math.min(isoWeek(day), 52);
export const yearOf = (day) => new Date(day * DAY).getUTCFullYear();
export const dayOf = (iso) => Math.round(Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) / DAY);
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
/** strftime("%d %b %Y") / ("%d %b") */
export function fmtDay(day, year = true) {
  const d = new Date(day * DAY);
  return `${String(d.getUTCDate()).padStart(2, "0")} ${MONTHS[d.getUTCMonth()]}${year ? ` ${d.getUTCFullYear()}` : ""}`;
}
export const isoOf = (day) => new Date(day * DAY).toISOString().slice(0, 10);
/** f"{x:,.0f}" */
export const fmt = (x) => (isNum(x) ? Math.round(x).toLocaleString("en-US") : "–");

/** alert_level(): warning if q50 > epidemic; watch if q90 > epidemic; above usual if q50 > alert. */
export function alertLevel(q50, q90, alert, epidemic) {
  if (gt(q50, epidemic)) return LEVELS[3];
  if (gt(q90, epidemic)) return LEVELS[2];
  if (gt(q50, alert)) return LEVELS[1];
  return LEVELS[0];
}

/**
 * src/thresholds.py: per unit and week of year, from the history passed in (earlier years only):
 * alert = mean of the same weeks (+-2) in those years, epidemic = mean + 2 SD (sample SD; 0 if one value).
 * Returns Map "unit|woy" -> {alert, epidemic, count}.
 */
export function thresholds(history) {
  const acc = new Map();
  for (const r of history) {
    if (!isNum(r.cases)) continue;
    const w = woy(r.week);
    for (let shift = -2; shift <= 2; shift++) {
      const k = `${r.unit_id}|${((((w - 1 + shift) % 52) + 52) % 52) + 1}`;
      let a = acc.get(k);
      if (!a) acc.set(k, (a = []));
      a.push(r.cases);
    }
  }
  const out = new Map();
  for (const [k, v] of acc) {
    const n = v.length, mean = v.reduce((s, x) => s + x, 0) / n;
    const sd = n > 1 ? Math.sqrt(v.reduce((s, x) => s + (x - mean) ** 2, 0) / (n - 1)) : 0;
    out.set(k, { alert: mean, epidemic: mean + 2 * sd, count: n });
  }
  return out;
}

/** replay_origins(): weeks from which both the 4- and 8-week out-of-sample forecasts exist (sorted days). */
export function replayOrigins(backtest) {
  const hs = new Map();
  for (const r of backtest) {
    const o = r.target_week - r.horizon * 7;
    if (!hs.has(o)) hs.set(o, new Set());
    hs.get(o).add(r.horizon);
  }
  return [...hs].filter(([, s]) => s.size === 2).map(([o]) => o).sort((a, b) => a - b);
}

/** Default replay week: the first June origin, else the first one. */
export function defaultOrigin(origins) {
  return origins.find((o) => new Date(o * DAY).getUTCMonth() === 5) ?? origins[0];
}

/**
 * replay_forecast(): the out-of-sample forecasts made at `origin`, shaped like the latest forecast, plus what
 * happened. Thresholds come from the history before 1 January of the origin's year, as the backtest used.
 */
export function replayForecast({ backtest, history, forecast, meta }, origin) {
  const static_ = new Map();
  for (const r of forecast) if (!static_.has(r.unit_id)) static_.set(r.unit_id, r);
  const cutoff = Date.UTC(yearOf(origin), 0, 1) / DAY;
  const thr = thresholds(history.filter((r) => r.week < cutoff));
  const out = [];
  for (const b of backtest) {
    if (b.target_week - b.horizon * 7 !== origin || !static_.has(b.unit_id)) continue;
    const t = thr.get(`${b.unit_id}|${woy(b.target_week)}`) || {};
    const population = meta.population[b.unit_id];
    const alert = t.alert ?? NaN, epidemic = t.epidemic ?? NaN;
    out.push({ unit_id: b.unit_id, unit_name: meta.names[b.unit_id], week: origin, population, horizon: b.horizon,
      target_week: b.target_week, q10: b.q10, q50: b.q50, q90: b.q90, actual: b.actual, test_year: b.test_year, alert, epidemic,
      level: alertLevel(b.q50, b.q90, alert, epidemic), actual_level: alertLevel(b.actual, b.actual, alert, epidemic),
      q50_per100k: (b.q50 / population) * 1e5 });
  }
  return out;
}

/** The latest forecast rows with names and populations added. */
export function latestForecast({ forecast, meta }) {
  return forecast.map((r) => ({ ...r, unit_name: meta.names[r.unit_id], population: meta.population[r.unit_id] }));
}

/** Areas that crossed the epidemic threshold in the replayed week, and how many were flagged watch or warning. */
export function replayClaim(rowsAtHorizon) {
  const crossed = rowsAtHorizon.filter((r) => r.actual_level === LEVELS[3]);
  return { crossed: crossed.length, flagged: crossed.filter((r) => r.level === LEVELS[2] || r.level === LEVELS[3]).length };
}

const groupBy = (rows, key) => {
  const m = new Map();
  for (const r of rows) { const k = r[key]; if (!m.has(k)) m.set(k, []); m.get(k).push(r); }
  return m;
};

/** expected_cases_8wk(): weekly forecasts summed over weeks 1-8, interpolated from the available horizons. */
export function expectedCases8wk(forecast) {
  const out = [];
  for (const [unit_id, f] of groupBy(forecast, "unit_id")) {
    const pts = [...f].sort((a, b) => a.horizon - b.horizon);
    const at = (k, h) => { // pandas interpolate("index") + bfill: linear between horizons, flat outside
      if (h <= pts[0].horizon) return pts[0][k];
      for (let i = 1; i < pts.length; i++) {
        if (h <= pts[i].horizon) {
          const a = pts[i - 1], b = pts[i];
          return a[k] + ((b[k] - a[k]) * (h - a.horizon)) / (b.horizon - a.horizon);
        }
      }
      return pts[pts.length - 1][k];
    };
    const sum = (k) => { let s = 0; for (let h = 1; h <= 8; h++) s += at(k, h); return s; };
    out.push({ unit_id, unit_name: f[0].unit_name, population: f[0].population,
      cases_low: sum("q10"), cases_mid: sum("q50"), cases_high: sum("q90") });
  }
  return out;
}

/** src/allocate.py DEFAULT_ACTIONS */
export const DEFAULT_ACTIONS = [
  { name: "Clean-up drive + container covers", cost_per_person: 15, effect_low: 0.1, effect_central: 0.3, effect_high: 0.5, max_coverage: 0.3 },
  { name: "Targeted fogging", cost_per_person: 25, effect_low: 0, effect_central: 0.05, effect_high: 0.1, max_coverage: 0.1 },
];

/**
 * allocate(): fractional knapsack on cases averted per peso. Funds the best (unit, action) first, up to each
 * action's max coverage, until the budget runs out. Returns the funded lines (low / central / high averted).
 */
export function allocate(forecast, budget, actions = DEFAULT_ACTIONS) {
  const units = expectedCases8wk(forecast);
  const opts = [];
  for (const a of actions) {
    for (const u of units) {
      const max_people = u.population * a.max_coverage;
      opts.push({ ...u, action: a.name, max_cost: max_people * a.cost_per_person, cost_per_person: a.cost_per_person,
        averted_per_peso: (u.cases_mid / u.population) * a.effect_central / a.cost_per_person,
        effects: [a.effect_low, a.effect_central, a.effect_high] });
    }
  }
  opts.sort((x, y) => y.averted_per_peso - x.averted_per_peso);
  const plan = [];
  let left = Number(budget);
  for (const o of opts) {
    if (left <= 0 || !(o.averted_per_peso > 0)) break;
    const spend = Math.min(left, o.max_cost);
    const share = spend / o.cost_per_person / o.population;
    const [lo, mid, hi] = o.effects;
    plan.push({ unit_id: o.unit_id, unit_name: o.unit_name, action: o.action, spend,
      people_covered: spend / o.cost_per_person, share_covered: share,
      averted_low: o.cases_low * share * lo, averted_mid: o.cases_mid * share * mid, averted_high: o.cases_high * share * hi });
    left -= spend;
  }
  return plan;
}

/** brief_table(): per area, the level at the chosen horizon, the peak week, and the 8-week totals. */
export function briefTable(fcAll, fcNow) {
  const peak = new Map(), tot = new Map(expectedCases8wk(fcAll).map((r) => [r.unit_id, r]));
  for (const r of fcAll) { const p = peak.get(r.unit_id); if (!p || r.q50 > p.q50) peak.set(r.unit_id, r); }
  return fcNow.filter((r) => peak.has(r.unit_id) && tot.has(r.unit_id))
    .map((r) => ({ ...r, peak_week: peak.get(r.unit_id).target_week, cases_mid: tot.get(r.unit_id).cases_mid, cases_high: tot.get(r.unit_id).cases_high }))
    .sort((a, b) => LEVELS.indexOf(b.level) - LEVELS.indexOf(a.level) || b.q50_per100k - a.q50_per100k);
}

/** brief_markdown(): the action brief download. */
export function briefMarkdown(rows, { t, lang, i18n, panelLabel, horizon, asOf }) {
  const lines = ["# EpiLag-PH action brief", "", `${t.as_of} ${fmtDay(asOf)} · ${panelLabel} · ${horizon} ${t.weeks_ahead}`, ""];
  for (const r of rows) {
    lines.push(`## ${r.unit_name}: ${i18n.LEVEL_NAME[lang][r.level]}`,
      `- ${t.cases}: ${fmt(r.q50)} (${t.range} ${fmt(r.q10)}–${fmt(r.q90)}), ${t.for_week} ${fmtDay(r.target_week)}`,
      `- ${t.prepare.replace("{n}", fmt(r.cases_high))}`);
    for (const [when, d] of i18n.PLAYBOOK[lang][r.level]) lines.push(`- **${when}**: ${d}`);
    lines.push("");
  }
  lines.push("Source: EpiLag-PH (github.com/Romeo-04/epilag). Forecasts carry uncertainty; see the likely range.");
  return lines.join("\n");
}

/** CSV text from row objects and [header, getter] columns. */
export function toCsv(rows, columns) {
  const q = (v) => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  return [columns.map(([h]) => q(h)).join(","), ...rows.map((r) => columns.map(([, g]) => q(g(r))).join(","))].join("\n") + "\n";
}
