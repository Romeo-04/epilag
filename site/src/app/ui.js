// Small UI helpers shared by the app views: escaping, level pills, cards, count-up, downloads, segmented controls.
import { icon } from "../lib/icons.js";
import { countUp } from "../lib/motion.js";

export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

/** Python level name -> CSS level key (data-lv) and voxel height. */
export const LV = { "outbreak warning": "warning", watch: "watch", "above usual": "above", normal: "normal" };
export const LV_HEIGHT = { "outbreak warning": 4, watch: 3, "above usual": 2, normal: 1 };
export const LV_COLOR = { "outbreak warning": "#F04B2A", watch: "#F58220", "above usual": "#F7C928", normal: "#0C7A55" };
export const NODATA = "#C9CFC9";

export const pill = (ctx, level) => `<span class="lv${level === "outbreak warning" ? " lv--pulse" : ""}" data-lv="${LV[level]}">${esc(ctx.levelName(level))}</span>`;
export const dot = (level) => `<span class="sq sq--round" data-lv="${LV[level]}"></span>`;

/** Card title with a pixel icon (16-grid art icons at 32 px, 12-grid UI icons at 24 px). */
const ICON16 = new Set(["forecastMap", "areaDetail", "actionPlan", "residents", "barangay", "didItWork", "database", "file", "downloadBox"]);
export const cardTitle = (ic, title, sub = "") =>
  `<div class="ctitle"><span class="ctitle__ic">${icon(ic, { size: ICON16.has(ic) ? 32 : 24 })}</span><div><h2>${esc(title)}</h2>${sub ? `<p>${esc(sub)}</p>` : ""}</div></div>`;

/** Short explanatory copy that stays available without competing with the data. */
export const infoDisclosure = (summary, body, ic = "info") =>
  `<details class="info-disclosure"><summary><span class="info-disclosure__icon">${icon(ic, { size: 18 })}</span><span>${esc(summary)}</span>${icon("chevronRight", { size: 18, className: "info-disclosure__chev" })}</summary><div class="info-disclosure__body">${body}</div></details>`;

/** A number that counts up when it scrolls in (static under reduced motion). */
export const count = (n, cls = "") => `<span class="nums ${cls}" data-count="${Math.round(n)}">${Math.round(n).toLocaleString("en-US")}</span>`;
export function hydrateCounts(root) { root.querySelectorAll("[data-count]").forEach((el) => countUp(el)); }

/** Offer `text` as a file download. */
export function download(name, text, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type: `${type};charset=utf-8` }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export const downloadButton = (id, label) =>
  `<button type="button" class="btn btn--ghost btn--sm" id="${id}">${icon("download", { size: 24 })}${esc(label)}</button>`;

/** Segmented control: options [[value, label]], current value; calls onChange(value). */
export function segmented(el, label, options, current, onChange) {
  el.setAttribute("role", "group");
  el.setAttribute("aria-label", label);
  el.innerHTML = options.map(([v, l]) => `<button type="button" data-v="${esc(v)}" aria-pressed="${String(v) === String(current)}">${esc(l)}</button>`).join("");
  el.onclick = (e) => { const b = e.target.closest("button[data-v]"); if (b && b.getAttribute("aria-pressed") !== "true") onChange(b.dataset.v); };
}

/** A collapsible section (like Streamlit's expander). */
export const details = (summary, body, ic = "menu") =>
  `<details class="card card--flat expander"><summary>${icon(ic, { size: 24 })}<span>${esc(summary)}</span>${icon("chevronRight", { size: 24, className: "expander__chev" })}</summary><div class="expander__body">${body}</div></details>`;

/** Plain HTML table: columns [[header, getter, className?]]. */
export const tableHtml = (rows, columns) =>
  `<div class="tbl-wrap"><table class="tbl"><thead><tr>${columns.map(([h, , c]) => `<th class="${c || ""}">${esc(h)}</th>`).join("")}</tr></thead><tbody>${
    rows.map((r) => `<tr>${columns.map(([, g, c]) => `<td class="${c || ""}">${g(r)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;

/** Area picker (<select>) sorted as given; returns HTML. */
export const areaSelect = (id, label, rows, current) =>
  `<label class="field"><span class="field__label">${esc(label)}</span><select id="${id}">${rows.map((r) => `<option value="${esc(r.unit_id)}"${r.unit_id === current ? " selected" : ""}>${esc(r.unit_name)}</option>`).join("")}</select></label>`;

/** Alert track record of one area (logic.trackRecord row, or undefined when there are no earlier test years). */
export function trackRecordHtml(rec, labels, h) {
  if (!rec) return `<p class="track__none">${esc(labels.track_none)}</p>`;
  const share = rec.reliability == null ? "–" : `${Math.round(rec.reliability * 100)}%`;
  return `<div class="track" data-grade="${esc(rec.grade.replace(" ", "-"))}">
    <div class="track__lead"><span class="track__grade">${esc(labels.track_grade[rec.grade])}</span><b class="track__big nums">${share}</b>
      <span class="track__of">${esc(labels.track_right.replace("{right}", rec.alert_weeks_right).replace("{n}", rec.alert_weeks))}</span></div>
    <ul class="track__facts">
      <li>${rec.onsets ? esc(labels.track_caught.replace("{c}", rec.onsets_caught).replace("{o}", rec.onsets)) : esc(labels.track_no_onsets)}</li>
      <li>${esc(labels.track_years)}: ${esc(rec.years.join(", "))} · ${esc(labels.weeks_short)}: ${h}</li>
    </ul></div>`;
}

/** Report card (logic.reportCard cells): weeks inside the likely range ("right"), and which way the misses lean.
 * hit -1: reported below the range, so the forecast was too high; hit 1: above it, too low. */
export function reportSummary(cells) {
  const inside = cells.filter((c) => c.hit === 0).length, high = cells.filter((c) => c.hit < 0).length, low = cells.filter((c) => c.hit > 0).length;
  return { inside, high, low, n: cells.length, lean: inside >= 0.75 * cells.length ? "good" : high >= low ? "high" : "low" };
}
const result = (c) => (c.hit === 0 ? "right" : c.hit < 0 ? "high" : "low");

/** The headline: "7 of 8 weeks right: good", and what it means for the reader. */
export function reportVerdict(s, labels) {
  const v = labels.card_verdict[s.lean];
  return `<div class="rc-verdict" data-lean="${s.lean}"><b class="rc-verdict__big nums">${esc(labels.card_of.replace("{k}", s.inside).replace("{n}", s.n))}</b>
    <div class="rc-verdict__text"><span class="rc-verdict__head">${esc(v.head)}</span><span class="rc-verdict__line">${esc(v.line.replace("{k}", s.lean === "low" ? s.low : s.high))}</span></div></div>`;
}

/** One row per week, newest first: what the forecast said, what was reported, Right / Too high / Too low. */
export function reportWeeks(cells, labels, fmtDay, fmt) {
  const day = (d) => esc(fmtDay(d)).replace(/ (\d{4})$/, '<span class="rc-yr"> $1</span>'); // the year is dropped on phones
  const rows = [...cells].reverse().map((c) => `<tr><td class="rc-day">${day(c.target_week)}</td><td class="num">${fmt(c.q10)}–${fmt(c.q90)}</td><td class="num"><b>${fmt(c.actual)}</b></td>
    <td><span class="rc-result" data-r="${result(c)}">${esc(labels.card_result[result(c)])}</span></td></tr>`).join("");
  return `<div class="tbl-wrap rc-weeks"><table class="tbl"><thead><tr><th>${esc(labels.card_week)}</th><th class="num">${esc(labels.card_said)}</th><th class="num">${esc(labels.card_reported)}</th><th>${esc(labels.card_result_head)}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

/** "3 too high, 1 too low", or "None". */
export function reportMisses(s, labels) {
  const parts = [s.high ? labels.card_miss.high.replace("{k}", s.high) : "", s.low ? labels.card_miss.low.replace("{k}", s.low) : ""].filter(Boolean);
  return parts.length ? parts.join(", ") : labels.card_miss.none;
}
