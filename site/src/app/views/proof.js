// Did it work?: honest tests. Each test year was forecast only from earlier years; errors against two simple rules,
// early-warning hits and false alarms, range coverage, and whether weather helps.
import { reports } from "../data.js";
import { barChart } from "../chart.js";
import { cardTitle, count, details, esc, head, tableHtml } from "../ui.js";

const FOREST = "#08754F", GREY = "#C5CFC9", SAGE = "#8A9891", WATCH = "#F58220";
const pct = (v) => `${Math.round(v * 100)}%`;
const signed = (v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(Math.round(v * 100))}%`;

export async function render(el, ctx) {
  const { t, lang, horizon, panel } = ctx;
  const rep = (await reports())[panel] || {};
  if (!rep.backtest) { el.innerHTML = `${head(t.proof_head, t.proof_muted, t.proof_sub)}<div class="card callout">No backtest results for this dataset yet.</div>`; return; }
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
    ${head(t.proof_head, t.proof_muted, t.proof_sub)}
    <div class="grid grid--3">
      <section class="hero-card surface tone-night tx-rain"><div class="hero-card__big">${count(beat)}<span class="hero-card__of"> / ${bh.length}</span></div>
        <p>${esc(t.beat.replace("{h}", h))}</p><pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="check" scale="4"></pixel-sprite></section>
      <section class="card kpi"><div class="kpi__lab"><i data-icon="alert" data-size="24"></i>${esc(t.ew_chart.replace("{h}", h))}</div>
        <div class="kpi__val">${alw.length ? range(alw.map((r) => r.share_warned)) : "–"}</div><div class="kpi__desc">${esc(t.caught_share.replace("{h}", h))}</div></section>
      <section class="card kpi"><div class="kpi__lab"><i data-icon="didItWork" data-size="32"></i>${esc(t.range)}</div>
        <div class="kpi__val">${range(bh.map((r) => r.coverage_10_90))}</div><div class="kpi__desc">${esc(t.coverage)}</div></section>
    </div>
    <div class="grid grid--2">
      <section class="card">${cardTitle("didItWork", t.err_chart.replace("{h}", h))}<div id="err" class="chart-box"></div></section>
      ${alw.length ? `<section class="card">${cardTitle("alert", t.ew_chart.replace("{h}", h))}<div id="ew" class="chart-box"></div></section>` : ""}
    </div>
    ${g.length ? `<section class="card">${cardTitle("info", t.weather_head, t.weather_note)}<div id="wx" class="chart-box"></div></section>` : ""}
    ${details(t.tables, [
      tableHtml(bt, [["Test year", (r) => r.test_year], ["Weeks ahead", (r) => r.horizon, "num"], ["EpiLag error", (r) => Math.round(r.mae_epilag), "num"],
        ["Same week last year", (r) => Math.round(r.mae_seasonal_naive), "num"], ["Same as this week", (r) => Math.round(r.mae_persistence), "num"],
        ["Range coverage (target 80%)", (r) => pct(r.coverage_10_90), "num"]]),
      rep.alerts ? tableHtml([...new Set(rep.alerts.filter((r) => r.horizon === h).map((r) => r.test_year))].map((y) => {
        const of = (rule, k) => rep.alerts.find((r) => r.horizon === h && r.test_year === y && r.rule === rule)?.[k];
        return { y, cw: of("warn_upper", "share_warned"), cm: of("warn_median", "share_warned"), fw: of("warn_upper", "false_alarm_share"), fm: of("warn_median", "false_alarm_share") };
      }), [["Test year", (r) => r.y], ["Caught (watch)", (r) => pct(r.cw), "num"], ["Caught (warning)", (r) => pct(r.cm), "num"],
        ["False alarms (watch)", (r) => pct(r.fw), "num"], ["False alarms (warning)", (r) => pct(r.fm), "num"]]) : "",
      gain.length ? tableHtml(gain, [["Test year", (r) => r.test_year], ["Weeks ahead", (r) => r.horizon, "num"], ["Error reduction from weather", (r) => signed(r.gain), "num"]]) : "",
    ].join(""))}`;

  const ds = [barChart(el.querySelector("#err"), { categories: years, fmt: (v) => Math.round(v), groups: [
    { label: "EpiLag-PH", color: FOREST, values: bh.map((r) => r.mae_epilag) },
    { label: "Same week last year", color: GREY, values: bh.map((r) => r.mae_seasonal_naive) },
    { label: "Same as this week", color: SAGE, values: bh.map((r) => r.mae_persistence) }] })];
  if (alw.length) ds.push(barChart(el.querySelector("#ew"), { categories: alw.map((r) => String(r.test_year)), fmt: pct, text: true, yMax: 1.15, groups: [
    { label: lang === "en" ? "Caught" : "Nahuli", color: FOREST, values: alw.map((r) => r.share_warned) },
    { label: lang === "en" ? "False alarms" : "Maling babala", color: WATCH, values: alw.map((r) => r.false_alarm_share) }] }));
  if (g.length) ds.push(barChart(el.querySelector("#wx"), { categories: g.map((r) => String(r.test_year)), fmt: signed, text: true, height: 260,
    groups: [{ values: g.map((r) => r.gain), colors: g.map((r) => (r.gain > 0 ? FOREST : GREY)) }] }));
  return () => ds.forEach((d) => d());
}
