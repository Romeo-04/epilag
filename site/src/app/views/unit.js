// Area detail: one area’s alert, cases and range, what to do, its alert track record and recent report card,
// history chart, and latest-mode drivers. The top-bar menu downloads the brief or prints a one-page report.
import { recordHorizon, table, trackRecordFor } from "../data.js";
import { briefMarkdown, briefTable, fmt, fmtDay, reportCard, thresholds, woy, yearOf } from "../logic.js";
import { barChart, timeChart } from "../chart.js";
import { LV, areaSelect, cardTitle, download, esc, infoDisclosure, reportLegend, reportSquares, trackRecordHtml } from "../ui.js";

const INK = "#071711", FOREST = "#08754F", BAND = "#08754F", RED = "#F04B2A";

export async function render(el, ctx) {
  const { t, labels, lang, i18n, fc, fcH, horizon, mode, origin, panel } = ctx;
  const localScope = panel === "region_qc" && ctx.regionMeta ? new Set([ctx.regionMeta.id, ...(ctx.regionMeta.cities || [])]) : null;
  const names = [...fcH].filter((r) => !localScope || localScope.has(r.unit_id)).sort((a, b) => b.q50_per100k - a.q50_per100k);
  const unit = names.some((r) => r.unit_id === ctx.area) ? ctx.area : names[0].unit_id;
  const row = fcH.find((r) => r.unit_id === unit);
  const one = briefTable(fc.filter((r) => r.unit_id === unit), [row]);
  const b = one[0];
  const saveBrief = () => download(`epilag_brief_${unit}.md`, briefMarkdown(one, { t, lang, i18n, panelLabel: ctx.panelLabel, horizon, asOf: Math.max(...fcH.map((r) => r.week)) }), "text/markdown");

  const rh = recordHorizon(horizon);
  const asOf = mode === "replay" ? origin : Math.max(...fcH.map((r) => r.week));
  el.innerHTML = `
    <header class="print-head" aria-hidden="true"><b>${esc(labels.print_title)}</b><span>${esc(row.unit_name)} · ${esc(t.as_of)} ${fmtDay(asOf)} · ${horizon} ${esc(t.weeks_ahead)}</span></header>
    <div class="unit-header"><div class="unit-pick">${areaSelect("area", t.pick, names, unit)}</div></div>
    <div class="grid grid--unit">
      <section class="hero-card status-hero" data-lv="${LV[row.level]}"><div class="kicker">${esc(row.unit_name)}</div>
        <div class="hero-card__mid"><span class="sq sq--round" data-lv="${LV[row.level]}"></span>${esc(ctx.levelName(row.level))}</div><p>${esc(labels.level_action[row.level])}</p>
        <pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="${row.level === "outbreak warning" ? "alert" : row.level === "watch" ? "search" : row.level === "above usual" ? "clipboard" : "sleepy"}" scale="3"></pixel-sprite>
      </section>
      <section class="card kpi"><div class="kpi__lab">${esc(t.cases)}</div><div class="kpi__val nums">${fmt(row.q50)}</div><div class="kpi__desc">${esc(t.range)}: ${fmt(row.q10)}–${fmt(row.q90)}</div></section>
      <section class="card kpi"><div class="kpi__lab">${esc(t.per100k)}</div><div class="kpi__val nums">${row.q50_per100k.toFixed(1)}</div><div class="kpi__desc">${esc(labels.plan_upto.replace("{n}", fmt(b.cases_high)))}</div></section>
    </div>
    <section class="card playbook">
      ${cardTitle("check", t.todo)}
      <ol class="todo">${i18n.PLAYBOOK[lang][row.level].map(([w, d]) => `<li class="todo__row"><span class="todo__when">${esc(w)}</span><span>${esc(d)}</span></li>`).join("")}</ol>
    </section>
    <div class="grid grid--2 track-grid">
      <section class="card" id="track">${cardTitle("didItWork", labels.track_head, labels.track_sub.replace("{h}", rh))}<div id="track-body" class="track-body"></div>${infoDisclosure(labels.about_this, `<p>${esc(labels.track_note)}</p>`)}</section>
      <section class="card" id="card">${cardTitle("check", labels.card_head, labels.card_sub.replace("{n}", 8).replace("{h}", rh))}<div id="card-body"></div>${infoDisclosure(labels.about_this, `<p>${esc(labels.card_note.replace("{h}", rh))}</p>`)}</section>
    </div>
    <section class="card history-card">${cardTitle("areaDetail", t.history)}<div id="hist" class="chart-box"></div></section>
    ${mode === "replay" ? "" : `<section class="card why-card" id="why">${cardTitle("info", t.why)}${infoDisclosure(labels.about_this, `<p>${esc(t.why_note)}</p>`)}<div id="why-chart" class="chart-box"></div></section>`}
    <p class="print-foot" aria-hidden="true">${esc(labels.print_source)} ${esc(labels.printed)} ${fmtDay(Date.UTC(new Date().getFullYear(), new Date().getMonth(), new Date().getDate()) / 864e5)}.</p>`;

  el.querySelector("#area").addEventListener("change", (e) => ctx.set({ area: e.target.value }, { push: false }));
  ctx.topDownload(t.download_brief, saveBrief, [[labels.print_report, () => print(), "file"]]);

  const [history, backtest, thrTable, drivers, records] = await Promise.all([table(panel, "history"), table(panel, "backtest"),
    mode === "replay" ? null : table(panel, "thresholds"), mode === "replay" ? null : table(panel, "drivers"), trackRecordFor(ctx)]);
  el.querySelector("#track-body").innerHTML = trackRecordHtml(records.get(unit), labels, rh);
  const rc = reportCard(backtest.filter((r) => r.unit_id === unit && (mode !== "replay" || r.target_week <= origin)), history, rh, 8);
  const cells = rc.rows[0]?.cells || [];
  const inside = cells.filter((c) => c.hit === 0).length;
  el.querySelector("#card-body").innerHTML = cells.length ? `<div class="rc-one"><div class="track__lead"><b class="track__big nums">${inside}<span class="track__of"> / ${cells.length}</span></b>
    <span class="track__of">${esc(labels.card_inside.replace("{k}", inside).replace("{n}", cells.length))}</span></div>
    ${reportSquares(cells, labels, fmtDay, fmt)}<div class="rc-dates small muted"><span>${fmtDay(cells[0].target_week)}</span><span>${fmtDay(cells[cells.length - 1].target_week)}</span></div>${reportLegend(labels)}</div>`
    : `<p class="track__none">${esc(labels.track_none)}</p>`;
  let hist = history.filter((r) => r.unit_id === unit).sort((a, c) => a.week - c.week);
  if (mode === "replay") hist = hist.filter((r) => r.week >= origin - 104 * 7 && r.week <= origin + 26 * 7);
  else { const last = hist[hist.length - 1].week; hist = hist.filter((r) => r.week >= last - 156 * 7); }
  const lo = hist[0].week, hi = hist[hist.length - 1].week;
  const bt = backtest.filter((r) => r.unit_id === unit && r.horizon === 4 && r.target_week >= lo && r.target_week <= hi).sort((a, c) => a.target_week - c.target_week);
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
  const disposers = [timeChart(el.querySelector("#hist"), { series, height: 350, yTitle: t.cases })];

  if (mode !== "replay") {
    const dr = drivers.filter((r) => r.unit_id === unit && r.horizon === horizon).sort((a, c) => Math.abs(c.shap) - Math.abs(a.shap)).slice(0, 10);
    const rev = [...dr].reverse();
    disposers.push(barChart(el.querySelector("#why-chart"), { categories: rev.map((d) => d.driver), horizontal: true, fmt: (v) => v.toFixed(2),
      groups: [{ values: rev.map((d) => d.shap), colors: rev.map((d) => (d.shap > 0 ? FOREST : "#C5CFC9")) }] }));
  }
  return () => disposers.forEach((d) => d());
}
