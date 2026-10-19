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

/** Page title row: title, muted part, sub line. */
export const head = (title, muted, sub = "") =>
  `<header class="vhead"><h1>${esc(title)} <span>${esc(muted)}</span></h1>${sub ? `<p class="vhead__sub">${esc(sub)}</p>` : ""}</header>`;

/** Card title with a pixel icon (16-grid art icons at 32 px, 12-grid UI icons at 24 px). */
const ICON16 = new Set(["forecastMap", "areaDetail", "actionPlan", "residents", "barangay", "didItWork", "database", "file", "downloadBox"]);
export const cardTitle = (ic, title, sub = "") =>
  `<div class="ctitle"><span class="ctitle__ic">${icon(ic, { size: ICON16.has(ic) ? 32 : 24 })}</span><div><h2>${esc(title)}</h2>${sub ? `<p>${esc(sub)}</p>` : ""}</div></div>`;

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
