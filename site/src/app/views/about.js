// Data & limits: what EpiLag-PH does, the method, the data sources, the limits, and the symbols used for data.
import { cardTitle, esc, head } from "../ui.js";

const BLOCKS = [
  ["areaDetail", "What EpiLag-PH does",
    "It forecasts weekly dengue cases 2-8 weeks ahead for each area, from recent cases, season, and rain, heat and "
    + "humidity in the past 12 weeks. It flags areas likely to pass the epidemic threshold, explains each forecast, "
    + "and ranks where a limited budget prevents the most cases."],
  ["didItWork", "Method",
    "LightGBM quantile models (10th, 50th, 90th percentile), one per horizon. Ranges are calibrated with conformalized "
    + "quantile regression. Thresholds per area and week of year from earlier years only: usual = mean, "
    + "epidemic = mean + 2 SD. Explanations with SHAP."],
  ["forecastMap", "Data",
    "<ul><li>DOH Epidemiology Bureau dengue cases and deaths, 2016-2021, via HDX (PJDSC official catalogue).</li>"
    + "<li>UPRI-NOAH weekly dengue and rainfall: 17 regions (2016-2019, 2022-2025) and Quezon City (2010-2025), "
    + "Zenodo 19448695, ODC-ODbL.</li><li>Weather: ERA5 reanalysis via the Open-Meteo archive API, at each area's centroid.</li>"
    + "<li>Population: OCHA COD-PS (PSA-based), 2022. Codes and boundaries: OCHA COD-AB; maps: faeldon/philippines-json-maps (MIT).</li></ul>"],
  ["alert", "Limits (read before use)",
    "<ul><li>Province data ends in January 2021; the province view is a historical replay.</li>"
    + "<li>Reported cases undercount true infections (about 4.7 times in one Cebu City study).</li>"
    + "<li>One weather point per area: large provinces are simplified.</li>"
    + "<li>Weather adds only a modest gain over recent cases and season.</li>"
    + "<li>The 'watch' level catches most outbreak starts but has many false alarms; the 'warning' level is stricter.</li>"
    + "<li>Budget effects and costs are assumptions, shown as ranges and editable.</li>"
    + "<li>Barangay ranking in Quezon City uses yearly shares, not weekly barangay forecasts.</li></ul>"],
];

// the symbols for kinds of data (from the mockup's "Data and limits" sheet)
const SYMBOLS = [
  ["observed", "Observed", "Reported cases from DOH or UPRI-NOAH, as published."],
  ["forecast", "Forecast", "A model's estimate of a future week, always with a likely range."],
  ["derived", "Derived", "Computed from other numbers: thresholds, cases per 100,000, 8-week totals."],
  ["userEntered", "You enter it", "Costs and effects in the Action plan: example values to replace with your own."],
  ["unavailable", "Not available", "No data for this area or week; shown in grey, never as zero."],
  ["calendarGap", "Calendar gap", "Years with no reports (regions: 2020-2021), so some charts break."],
  ["weatherCell", "Weather grid cell", "One ERA5 point per area: rain and heat are simplified for big provinces."],
  ["undercount", "Undercount", "Reports show only part of the true infections (about 4.7 times fewer)."],
];

export function render(el, ctx) {
  const { t } = ctx;
  el.innerHTML = `
    ${head(t.about_head, t.about_muted)}
    <div class="grid grid--2">${BLOCKS.map(([ic, h, body]) => `<section class="card prose">${cardTitle(ic, h)}<div>${body.startsWith("<") ? body : `<p>${esc(body)}</p>`}</div></section>`).join("")}</div>
    <section class="card">${cardTitle("database", "Data and limits symbols")}
      <ul class="symbols">${SYMBOLS.map(([ic, name, text]) => `<li><span class="symbols__ic"><i data-icon="${ic}" data-size="36"></i></span><div><b>${esc(name)}</b><span>${esc(text)}</span></div></li>`).join("")}</ul></section>`;
}
