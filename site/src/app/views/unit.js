// Area detail: one area's level and what it means, the week-by-week checklist (with a brief to download),
// cases against the epidemic threshold with past and current forecasts, and why the model says so.
import { table } from "../data.js";
import { briefMarkdown, briefTable, fmt, fmtDay, thresholds, woy, yearOf } from "../logic.js";
import { barChart, timeChart } from "../chart.js";
import { LV, areaSelect, cardTitle, download, downloadButton, esc, head } from "../ui.js";

const INK = "#071711", FOREST = "#08754F", BAND = "#08754F", RED = "#F04B2A";

export async function render(el, ctx) {
  const { t, lang, i18n, fc, fcH, horizon, mode, origin, panel } = ctx;
  const names = [...fcH].sort((a, b) => b.q50_per100k - a.q50_per100k);
  const unit = names.some((r) => r.unit_id === ctx.area) ? ctx.area : names[0].unit_id;
  const row = fcH.find((r) => r.unit_id === unit);
  const one = briefTable(fc.filter((r) => r.unit_id === unit), [row]);
  const b = one[0];
  const alertText = i18n.ALERT_TEXT[lang][row.level];

  el.innerHTML = `
    ${head(t.nav_unit, `${horizon} ${t.weeks_ahead}`, t.tagline)}
    <div class="unit-pick">${areaSelect("area", t.pick, names, unit)}</div>
    <div class="grid grid--unit">
      <section class="hero-card surface tone-night tx-rain" data-lv="${LV[row.level]}">
        <div class="kicker">${esc(row.unit_name)} · ${esc(t.level)}</div>
        <div class="hero-card__mid"><span class="sq sq--round"></span> ${esc(ctx.levelName(row.level))}</div>
        <p>${esc(alertText)}</p>
        <pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="${row.level === "outbreak warning" ? "alert" : row.level === "watch" ? "search" : row.level === "above usual" ? "clipboard" : "sleepy"}" scale="4"></pixel-sprite>
      </section>
      <section class="card kpi"><div class="kpi__lab">${esc(t.cases)} · ${horizon} wk</div><div class="kpi__val nums">${fmt(row.q50)}</div>
        <div class="kpi__desc">${esc(t.range)}: ${fmt(row.q10)}–${fmt(row.q90)} · ${esc(t.for_week)} ${fmtDay(row.target_week)}</div></section>
      <section class="card kpi"><div class="kpi__lab">${esc(t.per100k)}</div><div class="kpi__val nums">${row.q50_per100k.toFixed(1)}</div>
        <div class="kpi__desc">${esc(t.prepare.replace("{n}", fmt(b.cases_high)))}</div></section>
    </div>
    <section class="card">
      ${cardTitle("check", t.todo, alertText.split(":")[0])}
      <div class="todo"><div class="todo__row todo__row--head"><span>${esc(t.when)}</span><span>${esc(t.do)}</span><span>${esc(t.gives)}</span></div>
        ${i18n.PLAYBOOK[lang][row.level].map(([w, d, g]) => `<div class="todo__row"><span class="todo__when">${esc(w)}</span><span>${esc(d)}</span>
          <span class="todo__gives">${esc(g.replace("{n}", fmt(b.cases_high)))}</span></div>`).join("")}</div>
      <div class="btn-row">${downloadButton("dl-unit", t.download_brief)}</div>
    </section>
    <section class="card">${cardTitle("areaDetail", t.history)}<div id="hist" class="chart-box"></div></section>
    ${mode === "replay" ? "" : `<section class="card" id="why">${cardTitle("info", t.why, t.why_note)}<div class="why-list" id="why-list"></div><div id="why-chart" class="chart-box"></div></section>`}`;

  el.querySelector("#area").addEventListener("change", (e) => ctx.set({ area: e.target.value }, { push: false }));
  el.querySelector("#dl-unit").addEventListener("click", () => download(`epilag_brief_${unit}.md`,
    briefMarkdown(one, { t, lang, i18n, panelLabel: ctx.panelLabel, horizon, asOf: Math.max(...fcH.map((r) => r.week)) }), "text/markdown"));

  // history: reported cases, the epidemic threshold, 4-week-ahead forecasts from the backtest, and the current forecast
  const [history, backtest, thrTable, drivers] = await Promise.all([table(panel, "history"), table(panel, "backtest"),
    mode === "replay" ? null : table(panel, "thresholds"), mode === "replay" ? null : table(panel, "drivers")]);
  let hist = history.filter((r) => r.unit_id === unit).sort((a, c) => a.week - c.week);
  if (mode === "replay") hist = hist.filter((r) => r.week >= origin - 104 * 7 && r.week <= origin + 26 * 7);
  else { const last = hist[hist.length - 1].week; hist = hist.filter((r) => r.week >= last - 156 * 7); }
  const lo = hist[0].week, hi = hist[hist.length - 1].week;
  const bt = backtest.filter((r) => r.unit_id === unit && r.horizon === 4 && r.target_week >= lo && r.target_week <= hi).sort((a, c) => a.target_week - c.target_week);
  // in replay, thresholds come only from years before the replayed year (as in the backtest)
  let epi;
  if (mode === "replay") {
    const cut = Date.UTC(yearOf(origin), 0, 1) / 864e5, thr = thresholds(history.filter((r) => r.week < cut));
    epi = (d) => thr.get(`${unit}|${woy(d)}`)?.epidemic;
  } else {
    const m = new Map(thrTable.filter((r) => r.unit_id === unit).map((r) => [r.woy, r.epidemic]));
    epi = (d) => m.get(woy(d));
  }
  const now = fc.filter((r) => r.unit_id === unit).sort((a, c) => a.target_week - c.target_week);
  const series = [];
  const years = [...new Set(bt.map((r) => r.test_year))];
  years.forEach((y, i) => {
    const g = bt.filter((r) => r.test_year === y);
    series.push({ type: "band", color: BAND, x: g.map((r) => r.target_week), lo: g.map((r) => r.q10), hi: g.map((r) => r.q90), legend: false });
    series.push({ type: "line", label: t.fc4, legend: i === 0, color: FOREST, width: 1.5, dash: "2 4", x: g.map((r) => r.target_week), y: g.map((r) => r.q50) });
  });
  series.push({ type: "line", label: t.actual, color: INK, width: 2, x: hist.map((r) => r.week), y: hist.map((r) => r.cases ?? NaN) });
  series.push({ type: "line", label: t.epi_line, color: RED, width: 1.5, dash: "6 5", x: hist.map((r) => r.week), y: hist.map((r) => epi(r.week) ?? NaN) });
  series.push({ type: "points", label: mode === "latest" ? t.fcnow : `${t.fcnow} (${fmtDay(origin)})`, color: FOREST,
    x: now.map((r) => r.target_week), y: now.map((r) => r.q50), lo: now.map((r) => r.q10), hi: now.map((r) => r.q90) });
  const disposers = [timeChart(el.querySelector("#hist"), { series, height: 400, yTitle: t.cases })];

  if (mode !== "replay") {
    const dr = drivers.filter((r) => r.unit_id === unit && r.horizon === horizon).sort((a, c) => Math.abs(c.shap) - Math.abs(a.shap)).slice(0, 10);
    el.querySelector("#why-list").innerHTML = dr.slice(0, 3).map((d) => `<div><span class="lv" data-lv="${d.shap > 0 ? "normal" : "nodata"}">${d.shap > 0 ? "+" : "−"}${Math.abs(d.shap).toFixed(2)}</span><b>${esc(d.driver)}</b> ${esc(d.shap > 0 ? t.up : t.down)}</div>`).join("");
    const rev = [...dr].reverse();
    disposers.push(barChart(el.querySelector("#why-chart"), { categories: rev.map((d) => d.driver), horizontal: true, fmt: (v) => v.toFixed(2),
      groups: [{ values: rev.map((d) => d.shap), colors: rev.map((d) => (d.shap > 0 ? FOREST : "#C5CFC9")) }] }));
  }
  return () => disposers.forEach((d) => d());
}
