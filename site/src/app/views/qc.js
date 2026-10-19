// QC barangays: the city-wide Quezon City forecast shared out by each barangay's share of cases in 2022-2025.
import { barangays } from "../data.js";
import { barChart } from "../chart.js";
import { cardTitle, count, details, esc, head, LV, tableHtml } from "../ui.js";

export async function render(el, ctx) {
  const { t, lang, i18n, fc, horizon, panel } = ctx;
  if (panel !== "region_qc") {
    el.innerHTML = `${head(t.qc_head, t.qc_muted, t.qc_note)}
      <section class="card"><div class="callout"><i data-icon="info" data-size="24"></i>${esc(t.switch_qc)}</div>
      <div class="btn-row"><button type="button" class="btn btn--primary btn--sm" id="switch">${esc(t.switch_btn)}</button></div></section>`;
    el.querySelector("#switch").addEventListener("click", () => ctx.set({ panel: "region_qc" }));
    return;
  }
  const qc = fc.filter((r) => r.unit_id === "QC").sort((a, b) => a.horizon - b.horizon);
  const qc8 = (qc.reduce((s, r) => s + r.q50, 0) / qc.length) * 8;
  const lvl = qc.find((r) => r.horizon === horizon).level;
  const brgy = (await barangays()).map((b) => ({ ...b, expected_8wk: b.share * qc8 }));
  const top5 = brgy.slice(0, 5);

  el.innerHTML = `
    ${head(t.qc_head, t.qc_muted, t.qc_note)}
    <div class="grid grid--qc">
      <div class="stack">
        <section class="hero-card surface tone-night tx-rain" data-lv="${LV[lvl]}">
          <div class="kicker">${esc(t.city_fc)}</div><div class="hero-card__big">${count(qc8)}</div>
          <div class="chips"><span class="chip chip--night"><span class="sq sq--round"></span>${esc(ctx.levelName(lvl))}</span></div>
          <p>${esc(i18n.ALERT_TEXT[lang][lvl])}</p>
          <pixel-sprite class="hero-card__sprite" sprite="props" pose="school" scale="2"></pixel-sprite>
        </section>
        <section class="card">${cardTitle("barangay", "Top 5")}
          <ol class="rank">${top5.map((r, i) => `<li><div class="rank__row rank__row--3"><span class="rank__rk">${i + 1}</span>
            <span class="rank__nm">${esc(r.Barangay)}<small>${(r.share * 100).toFixed(1)}% · ${Math.round(r.cases_2025).toLocaleString("en-US")} (2025)</small></span>
            <span class="rank__num nums">${Math.round(r.expected_8wk)}</span></div></li>`).join("")}</ol></section>
      </div>
      <section class="card">${cardTitle("forecastMap", t.brgy_chart)}<div id="bchart" class="chart-box"></div></section>
    </div>
    ${details(t.all_areas, tableHtml(brgy, [["Barangay", (r) => esc(r.Barangay)], ["Cases 2022-2025", (r) => Math.round(r.cases_2022_2025).toLocaleString("en-US"), "num"],
      ["Cases 2025", (r) => Math.round(r.cases_2025).toLocaleString("en-US"), "num"], ["Share of city", (r) => `${(r.share * 100).toFixed(1)}%`, "num"],
      ["Expected, next 8 weeks", (r) => r.expected_8wk.toFixed(1), "num"]]))}`;

  const top = brgy.slice(0, 20);
  return barChart(el.querySelector("#bchart"), { categories: top.map((r) => r.Barangay), horizontal: true, height: 560, fmt: (v) => Math.round(v),
    groups: [{ values: top.map((r) => r.expected_8wk), colors: top.map((_, i) => `rgba(8,117,79,${(1 - (0.65 * i) / 19).toFixed(2)})`) }] });
}
