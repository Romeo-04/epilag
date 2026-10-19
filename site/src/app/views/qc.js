// Quezon City barangays: city forecast, top-five allocation shortlist, chart, and the full barangay table.
import { barangays } from "../data.js";
import { barChart } from "../chart.js";
import { cardTitle, count, details, esc, head, infoDisclosure, tableHtml } from "../ui.js";

export async function render(el, ctx) {
  const { t, labels, lang, i18n, fc, horizon, panel } = ctx;
  if (panel !== "region_qc") {
    el.innerHTML = `${head(t.qc_head, t.qc_muted)}${infoDisclosure(labels.about_this, `<p>${esc(t.qc_note)}</p>`)}<section class="card empty-state"><span class="empty-state__icon"><i data-icon="info" data-size="20"></i></span><div><b>${esc(labels.switch_data)}</b><p>${esc(labels.latest_panel_available)}</p><div class="btn-row"><button type="button" class="btn btn--primary btn--sm" id="switch">${esc(labels.switch_to_regions)}</button></div></div></section>`;
    el.querySelector("#switch").addEventListener("click", () => ctx.set({ panel: "region_qc" }));
    return;
  }
  const qc = fc.filter((r) => r.unit_id === "QC").sort((a, b) => a.horizon - b.horizon);
  const qc8 = (qc.reduce((s, r) => s + r.q50, 0) / qc.length) * 8;
  const lvl = qc.find((r) => r.horizon === horizon).level;
  const brgy = (await barangays()).map((b) => ({ ...b, expected_8wk: b.share * qc8 }));
  const top5 = brgy.slice(0, 5);

  el.innerHTML = `
    ${head(t.qc_head, t.qc_muted)}${infoDisclosure(labels.about_this, `<p>${esc(t.qc_note)}</p>`)}
    <div class="grid grid--qc">
      <div class="stack"><section class="hero-card" data-lv="${lvl}"><div class="kicker">${esc(t.city_fc)}</div><div class="hero-card__big">${count(qc8)}</div><div class="chips"><span class="chip chip--night"><span class="sq sq--round" data-lv="${lvl}"></span>${esc(ctx.levelName(lvl))}</span></div><p>${esc(i18n.ALERT_TEXT[lang][lvl])}</p><pixel-sprite class="hero-card__sprite" sprite="props" pose="school" scale="2"></pixel-sprite></section>
        <section class="card qc-top5">${cardTitle("barangay", labels.top_barangays)}<ol class="rank-list">${top5.map((r, i) => `<li><div class="rank-row"><span class="rank-row__rank">${i + 1}</span><span class="rank-row__copy"><b>${esc(r.Barangay)}</b><small>${(r.share * 100).toFixed(1)}% · ${Math.round(r.cases_2025).toLocaleString("en-US")} (2025)</small></span><span class="rank-row__num nums">${Math.round(r.expected_8wk)}</span></div></li>`).join("")}</ol></section></div>
      <section class="card">${cardTitle("forecastMap", t.brgy_chart)}<div id="bchart" class="chart-box"></div></section>
    </div>
    ${details(labels.all_areas, tableHtml(brgy, [[labels.barangay, (r) => esc(r.Barangay)], [labels.cases_2022_2025, (r) => Math.round(r.cases_2022_2025).toLocaleString("en-US"), "num"], [labels.cases_2025, (r) => Math.round(r.cases_2025).toLocaleString("en-US"), "num"], [labels.share_city, (r) => `${(r.share * 100).toFixed(1)}%`, "num"], [labels.expected_8, (r) => r.expected_8wk.toFixed(1), "num"]]))}`;

  const top = brgy.slice(0, 20);
  return barChart(el.querySelector("#bchart"), { categories: top.map((r) => r.Barangay), horizontal: true, height: 480, fmt: (v) => Math.round(v),
    groups: [{ values: top.map((r) => r.expected_8wk), colors: top.map((_, i) => `rgba(8,117,79,${(1 - (0.65 * i) / 19).toFixed(2)})`) }] });
}
