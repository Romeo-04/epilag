// Did it work?: honest backtests, alert hit rates, range coverage, the latest report card, weather contribution,
// and full results tables.
import { recordHorizon, reports, table } from "../data.js";
import { reportCard } from "../logic.js";
import { barChart } from "../chart.js";
import { cardTitle, count, details, esc, infoDisclosure, reportMisses, reportSummary, tableHtml } from "../ui.js";

const FOREST = "#08754F", GREY = "#C5CFC9", SAGE = "#8A9891", WATCH = "#F58220";
const pct = (v) => `${Math.round(v * 100)}%`;
const signed = (v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(Math.round(v * 100))}%`;

export async function render(el, ctx) {
  const { t, labels, lang, horizon, panel } = ctx;
  const rep = (await reports())[panel] || {};
  if (!rep.backtest) { el.innerHTML = `<section class="card empty-state"><span class="empty-state__icon"><i data-icon="info" data-size="20"></i></span><div><b>${esc(labels.no_data)}</b><p>No backtest results for this dataset yet.</p></div></section>`; return; }
  const bt = rep.backtest;
  const h = bt.some((r) => r.horizon === horizon) ? horizon : 4;
  const bh = bt.filter((r) => r.horizon === h);
  const beat = bh.filter((r) => r.mae_epilag < r.mae_seasonal_naive && r.mae_epilag < r.mae_persistence).length;
  const alw = rep.alerts ? rep.alerts.filter((r) => r.horizon === h && r.rule === "warn_upper") : [];
  const range = (k) => `${pct(Math.min(...k))}–${pct(Math.max(...k))}`;
  const years = bh.map((r) => String(r.test_year));
  let gain = [];
  if (rep.backtest_noweather) {
    const nw = new Map(rep.backtest_noweather.map((r) => [`${r.test_year}|${r.horizon}`, r.mae_epilag]));
    gain = bt.map((r) => ({ test_year: r.test_year, horizon: r.horizon, gain: 1 - r.mae_epilag / nw.get(`${r.test_year}|${r.horizon}`) }));
  }
  const g = gain.filter((r) => r.horizon === h);
  const rh = recordHorizon(horizon);
  const [hist, back] = await Promise.all([table(panel, "history"), table(panel, "backtest")]);
  const rc = reportCard(back, hist, rh, 8);
  const names = ctx.meta.names;
  // best record first, then by name
  const sums = rc.rows.map((r) => ({ unit_id: r.unit_id, ...reportSummary(r.cells) }))
    .sort((a, b) => b.inside / b.n - a.inside / a.n || String(names[a.unit_id]).localeCompare(String(names[b.unit_id])));
  const all = reportSummary(rc.rows.flatMap((r) => r.cells));

  el.innerHTML = `
    ${infoDisclosure(labels.about_this, `<p>${esc(t.proof_sub)}</p>`)}
    <div class="grid grid--3"><section class="hero-card"><div class="hero-card__big">${count(beat)}<span class="hero-card__of"> / ${bh.length}</span></div><p>${esc(t.beat.replace("{h}", h))}</p><pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="check" scale="3"></pixel-sprite></section>
      <section class="card kpi"><div class="kpi__lab"><i data-icon="alert" data-size="20"></i>${esc(t.ew_chart.replace("{h}", h))}</div><div class="kpi__val">${alw.length ? range(alw.map((r) => r.share_warned)) : "–"}</div><div class="kpi__desc">${esc(t.caught_share.replace("{h}", h))}</div></section>
      <section class="card kpi"><div class="kpi__lab"><i data-icon="didItWork" data-size="22"></i>${esc(t.range)}</div><div class="kpi__val">${range(bh.map((r) => r.coverage_10_90))}</div><div class="kpi__desc">${esc(t.coverage)}</div></section></div>
    <div class="grid grid--2"><section class="card">${cardTitle("didItWork", t.err_chart.replace("{h}", h))}<div id="err" class="chart-box"></div></section>${alw.length ? `<section class="card">${cardTitle("alert", t.ew_chart.replace("{h}", h))}<div id="ew" class="chart-box"></div></section>` : ""}</div>
    ${rc.rows.length ? `<section class="card report-card" id="report-card">${cardTitle("check", labels.card_head_all, labels.card_sub.replace("{n}", rc.weeks.length).replace("{h}", rh))}
      <div class="rc-verdict rc-verdict--all" data-lean="${all.lean}"><div class="rc-verdict__text"><span class="rc-verdict__head">${esc(labels.card_all_sum.replace("{k}", all.inside).replace("{n}", all.n).replace("{p}", pct(all.inside / all.n)))}</span>
        ${all.high + all.low ? `<span class="rc-verdict__line">${esc(labels.card_all_lean[all.high >= all.low ? "high" : "low"].replace("{a}", all.high).replace("{b}", all.low))}</span>` : ""}</div></div>
      <div class="tbl-wrap rc-table" tabindex="0" role="region" aria-label="${esc(labels.card_head_all)}"><table class="tbl"><thead><tr><th>${esc(labels.card_area)}</th><th class="num">${esc(labels.card_weeks_right)}</th><th aria-hidden="true"></th><th>${esc(labels.card_misses)}</th></tr></thead>
        <tbody>${sums.map((r) => `<tr><td>${esc(names[r.unit_id])}</td><td class="num"><b>${esc(labels.card_of.replace("{k}", r.inside).replace("{n}", r.n))}</b></td>
          <td aria-hidden="true"><span class="rc-bar" data-lean="${r.lean}"><span style="width:${(r.inside / r.n * 100).toFixed(1)}%"></span></span></td><td class="rc-miss" data-lean="${r.lean}">${esc(reportMisses(r, labels))}</td></tr>`).join("")}</tbody></table></div>
      <p class="rc-note">${esc(labels.card_note)}</p>${infoDisclosure(labels.about_this, `<p>${esc(labels.card_note_more.replace("{h}", rh))}</p>`)}</section>` : ""}
    ${g.length ? `<section class="card">${cardTitle("info", t.weather_head)}${infoDisclosure(labels.about_this, `<p>${esc(t.weather_note)}</p>`)}<div id="wx" class="chart-box"></div></section>` : ""}
    ${details(t.tables, [tableHtml(bt, [[labels.test_year, (r) => r.test_year], [labels.weeks_short, (r) => r.horizon, "num"], [labels.epilag_error, (r) => Math.round(r.mae_epilag), "num"], [labels.same_last_year, (r) => Math.round(r.mae_seasonal_naive), "num"], [labels.same_this_week, (r) => Math.round(r.mae_persistence), "num"], [labels.range_coverage, (r) => pct(r.coverage_10_90), "num"]]),
      rep.alerts ? tableHtml([...new Set(rep.alerts.filter((r) => r.horizon === h).map((r) => r.test_year))].map((y) => { const of = (rule, k) => rep.alerts.find((r) => r.horizon === h && r.test_year === y && r.rule === rule)?.[k]; return { y, cw: of("warn_upper", "share_warned"), cm: of("warn_median", "share_warned"), fw: of("warn_upper", "false_alarm_share"), fm: of("warn_median", "false_alarm_share") }; }), [[labels.test_year, (r) => r.y], [labels.caught_watch, (r) => pct(r.cw), "num"], [labels.caught_warning, (r) => pct(r.cm), "num"], [labels.false_watch, (r) => pct(r.fw), "num"], [labels.false_warning, (r) => pct(r.fm), "num"]]) : "",
      gain.length ? tableHtml(gain, [[labels.test_year, (r) => r.test_year], [labels.weeks_short, (r) => r.horizon, "num"], [labels.weather_reduction, (r) => signed(r.gain), "num"]]) : ""].join(""))}`;

  const ds = [barChart(el.querySelector("#err"), { categories: years, fmt: (v) => Math.round(v), groups: [
    { label: "EpiLag-PH", color: FOREST, values: bh.map((r) => r.mae_epilag) }, { label: "Same week last year", color: GREY, values: bh.map((r) => r.mae_seasonal_naive) }, { label: "Same as this week", color: SAGE, values: bh.map((r) => r.mae_persistence) }] })];
  if (alw.length) ds.push(barChart(el.querySelector("#ew"), { categories: alw.map((r) => String(r.test_year)), fmt: pct, text: true, yMax: 1.15, groups: [
    { label: lang === "en" ? "Caught" : "Nahuli", color: FOREST, values: alw.map((r) => r.share_warned) }, { label: lang === "en" ? "False alarms" : "Maling babala", color: WATCH, values: alw.map((r) => r.false_alarm_share) }] }));
  if (g.length) ds.push(barChart(el.querySelector("#wx"), { categories: g.map((r) => String(r.test_year)), fmt: signed, text: true, height: 260,
    groups: [{ values: g.map((r) => r.gain), colors: g.map((r) => (r.gain > 0 ? FOREST : GREY)) }] }));
  return () => ds.forEach((d) => d());
}
