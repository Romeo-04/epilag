// Did it work?: honest backtests, alert hit rates, range coverage, weather contribution, and full results tables.
import { reports } from "../data.js";
import { barChart } from "../chart.js";
import { cardTitle, count, details, esc, head, infoDisclosure, tableHtml } from "../ui.js";

const FOREST = "#08754F", GREY = "#C5CFC9", SAGE = "#8A9891", WATCH = "#F58220";
const pct = (v) => `${Math.round(v * 100)}%`;
const signed = (v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(Math.round(v * 100))}%`;

export async function render(el, ctx) {
  const { t, labels, lang, horizon, panel } = ctx;
  const rep = (await reports())[panel] || {};
  if (!rep.backtest) { el.innerHTML = `${head(t.proof_head, t.proof_muted)}<section class="card empty-state"><span class="empty-state__icon"><i data-icon="info" data-size="20"></i></span><div><b>${esc(labels.no_data)}</b><p>No backtest results for this dataset yet.</p></div></section>`; return; }
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

  el.innerHTML = `
    ${head(t.proof_head, t.proof_muted)}${infoDisclosure(labels.about_this, `<p>${esc(t.proof_sub)}</p>`)}
    <div class="grid grid--3"><section class="hero-card"><div class="hero-card__big">${count(beat)}<span class="hero-card__of"> / ${bh.length}</span></div><p>${esc(t.beat.replace("{h}", h))}</p><pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="check" scale="3"></pixel-sprite></section>
      <section class="card kpi"><div class="kpi__lab"><i data-icon="alert" data-size="20"></i>${esc(t.ew_chart.replace("{h}", h))}</div><div class="kpi__val">${alw.length ? range(alw.map((r) => r.share_warned)) : "–"}</div><div class="kpi__desc">${esc(t.caught_share.replace("{h}", h))}</div></section>
      <section class="card kpi"><div class="kpi__lab"><i data-icon="didItWork" data-size="22"></i>${esc(t.range)}</div><div class="kpi__val">${range(bh.map((r) => r.coverage_10_90))}</div><div class="kpi__desc">${esc(t.coverage)}</div></section></div>
    <div class="grid grid--2"><section class="card">${cardTitle("didItWork", t.err_chart.replace("{h}", h))}<div id="err" class="chart-box"></div></section>${alw.length ? `<section class="card">${cardTitle("alert", t.ew_chart.replace("{h}", h))}<div id="ew" class="chart-box"></div></section>` : ""}</div>
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
