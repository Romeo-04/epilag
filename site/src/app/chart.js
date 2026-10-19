// Hand-written SVG charts for the app (no chart library): a time-series chart (lines, range bands, forecast
// points with error bars) and bar charts (grouped, stacked, horizontal). Both draw at the container's width and
// redraw when it changes, show a tooltip on hover, and keep text at its real size on phones.
import { fmtDay } from "./logic.js";

const NS = "http://www.w3.org/2000/svg";
const PAD = { l: 52, r: 16, t: 14, b: 34 };

/** Round tick values that cover [lo, hi]: the first tick is at or below lo, the last at or above hi. */
function niceTicks(lo, hi, n = 5) {
  if (!(hi > lo)) hi = lo + 1;
  const raw = (hi - lo) / n, mag = 10 ** Math.floor(Math.log10(raw)), r = raw / mag;
  const step = (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10) * mag;
  const out = [];
  let v = Math.floor(lo / step + 1e-9) * step;
  do { out.push(+v.toFixed(10)); v += step; } while (out[out.length - 1] < hi - step * 1e-9);
  return out;
}
const short = (v) => (Math.abs(v) >= 1e6 ? `${+(v / 1e6).toFixed(1)}M` : Math.abs(v) >= 1e4 ? `${+(v / 1e3).toFixed(0)}k` : Math.abs(v) >= 1000 ? `${+(v / 1e3).toFixed(1)}k` : `${+v.toFixed(2)}`);

/** Draw `draw(width)` -> svg string into el now and on every resize; returns a disposer. */
function responsive(el, draw, onReady) {
  let w = 0;
  const paint = () => {
    const nw = Math.round(el.clientWidth);
    if (!nw || nw === w) return;
    w = nw;
    el.innerHTML = draw(w);
    onReady?.(el.querySelector("svg"), w);
  };
  const ro = new ResizeObserver(paint);
  ro.observe(el);
  paint();
  return () => ro.disconnect();
}

function tooltip(el) {
  let tip = el.parentElement.querySelector(":scope > .chart-tip");
  if (!tip) { tip = Object.assign(document.createElement("div"), { className: "chart-tip", hidden: true }); el.parentElement.append(tip); }
  return tip;
}

/**
 * Time-series chart. series: [{ type: "line"|"band"|"points", label, color, x: days[], y[], lo[], hi[], width, dash,
 * legend }] ; yTitle; height.
 */
export function timeChart(el, { series, height = 380, yTitle = "", fmt = (v) => Math.round(v).toLocaleString("en-US") }) {
  const xs = series.flatMap((s) => s.x), ys = series.flatMap((s) => [...(s.y || []), ...(s.hi || []), ...(s.lo || [])]).filter(Number.isFinite);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), yTicks = niceTicks(0, Math.max(...ys, 1) * 1.05);
  const y1 = yTicks[yTicks.length - 1];
  const legend = series.filter((s) => s.legend !== false && s.label);
  const parent = el;
  parent.classList.add("chart");
  const plot = document.createElement("div");
  parent.innerHTML = "";
  parent.append(plot);
  if (legend.length) parent.insertAdjacentHTML("beforeend", `<ul class="chart-legend">${legend.map((s) => `<li><i style="--c:${s.color}" class="${s.type === "band" ? "band" : s.dash ? "dash" : ""}"></i>${s.label}</li>`).join("")}</ul>`);

  let X, Y;
  const dispose = responsive(plot, (w) => {
    const iw = w - PAD.l - PAD.r, ih = height - PAD.t - PAD.b;
    X = (d) => PAD.l + ((d - x0) / Math.max(1, x1 - x0)) * iw;
    Y = (v) => PAD.t + ih - (v / y1) * ih;
    const years = [];
    for (let y = new Date(x0 * 864e5).getUTCFullYear(); y <= new Date(x1 * 864e5).getUTCFullYear() + 1; y++) years.push(Date.UTC(y, 0, 1) / 864e5);
    const months = [];
    if ((x1 - x0) < 400) for (let d = new Date(x0 * 864e5); d <= new Date(x1 * 864e5); d.setUTCMonth(d.getUTCMonth() + 2, 1)) months.push(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 864e5);
    const xt = (months.length ? months : years).filter((d) => d >= x0 && d <= x1);
    let s = `<svg xmlns="${NS}" width="${w}" height="${height}" viewBox="0 0 ${w} ${height}" class="chart-svg">`;
    s += yTicks.map((v) => `<line x1="${PAD.l}" x2="${w - PAD.r}" y1="${Y(v)}" y2="${Y(v)}" class="grid"/><text x="${PAD.l - 8}" y="${Y(v) + 4}" text-anchor="end">${short(v)}</text>`).join("");
    s += xt.map((d) => `<line x1="${X(d)}" x2="${X(d)}" y1="${PAD.t}" y2="${height - PAD.b}" class="grid grid--x"/><text x="${X(d)}" y="${height - PAD.b + 18}" text-anchor="middle">${months.length ? fmtDay(d, false).slice(3) : new Date(d * 864e5).getUTCFullYear()}</text>`).join("");
    if (yTitle) s += `<text class="ytitle" x="12" y="${PAD.t + ih / 2}" transform="rotate(-90 12 ${PAD.t + ih / 2})" text-anchor="middle">${yTitle}</text>`;
    for (const se of series) {
      if (se.type === "band") {
        for (const seg of segments(se)) {
          const top = seg.map((i) => `${X(se.x[i])},${Y(se.hi[i])}`), bot = seg.slice().reverse().map((i) => `${X(se.x[i])},${Y(se.lo[i])}`);
          s += `<polygon points="${[...top, ...bot].join(" ")}" fill="${se.color}" opacity="${se.opacity ?? 0.18}"/>`;
        }
      } else if (se.type === "line") {
        for (const seg of segments(se)) {
          s += `<polyline points="${seg.map((i) => `${X(se.x[i])},${Y(se.y[i])}`).join(" ")}" fill="none" stroke="${se.color}" stroke-width="${se.width ?? 2}" ${se.dash ? `stroke-dasharray="${se.dash}"` : ""} stroke-linejoin="round"/>`;
        }
      } else if (se.type === "points") {
        se.x.forEach((d, i) => {
          if (se.lo) s += `<line x1="${X(d)}" x2="${X(d)}" y1="${Y(se.lo[i])}" y2="${Y(se.hi[i])}" stroke="${se.color}" stroke-width="2"/><line x1="${X(d) - 4}" x2="${X(d) + 4}" y1="${Y(se.hi[i])}" y2="${Y(se.hi[i])}" stroke="${se.color}" stroke-width="2"/><line x1="${X(d) - 4}" x2="${X(d) + 4}" y1="${Y(se.lo[i])}" y2="${Y(se.lo[i])}" stroke="${se.color}" stroke-width="2"/>`;
        });
        s += `<polyline points="${se.x.map((d, i) => `${X(d)},${Y(se.y[i])}`).join(" ")}" fill="none" stroke="${se.color}" stroke-width="3"/>`;
        s += se.x.map((d, i) => `<rect x="${X(d) - 5}" y="${Y(se.y[i]) - 5}" width="10" height="10" fill="${se.color}" stroke="#fff" stroke-width="2"/>`).join("");
      }
    }
    s += `<line class="cross" x1="0" x2="0" y1="${PAD.t}" y2="${height - PAD.b}" visibility="hidden"/></svg>`;
    return s;
  }, (svg) => {
    const tip = tooltip(plot), cross = svg.querySelector(".cross");
    const all = [...new Set(series.filter((se) => se.type !== "band").flatMap((se) => se.x))].sort((a, b) => a - b);
    svg.addEventListener("pointermove", (e) => {
      const r = svg.getBoundingClientRect(), px = e.clientX - r.left;
      let best = all[0];
      for (const d of all) if (Math.abs(X(d) - px) < Math.abs(X(best) - px)) best = d;
      const lines = series.filter((se) => se.label && se.type !== "band").map((se) => {
        const i = se.x.indexOf(best);
        if (i < 0 || !Number.isFinite(se.y[i])) return "";
        return `<div><i style="background:${se.color}"></i>${se.label}: <b>${fmt(se.y[i])}</b>${se.lo ? ` (${fmt(se.lo[i])}–${fmt(se.hi[i])})` : ""}</div>`;
      }).join("");
      if (!lines) { tip.hidden = true; return; }
      cross.setAttribute("x1", X(best)); cross.setAttribute("x2", X(best)); cross.setAttribute("visibility", "visible");
      tip.innerHTML = `<b>${fmtDay(best)}</b>${lines}`;
      tip.hidden = false;
      tip.style.left = `${Math.min(X(best) + 12, r.width - 230)}px`;
      tip.style.top = `${PAD.t + 6}px`;
    });
    svg.addEventListener("pointerleave", () => { tip.hidden = true; cross.setAttribute("visibility", "hidden"); });
  });
  return dispose;
}

/** Index runs where a series has finite values (gaps break lines and bands). */
function segments(se) {
  const vals = se.type === "band" ? se.x.map((_, i) => se.lo[i] + se.hi[i]) : se.y;
  const out = [];
  let cur = [];
  vals.forEach((v, i) => { if (Number.isFinite(v)) cur.push(i); else if (cur.length) { out.push(cur); cur = []; } });
  if (cur.length) out.push(cur);
  return out;
}

/**
 * Bar chart. categories: labels; groups: [{ label, color | colors[], values[] }]; mode "group" | "stack";
 * horizontal; fmt for axis and tooltips; text: show value labels; yMax; height.
 */
export function barChart(el, { categories, groups, mode = "group", horizontal = false, height, fmt = short, text = false, yMax, zero = true }) {
  el.classList.add("chart");
  const plot = document.createElement("div");
  el.innerHTML = "";
  el.append(plot);
  if (groups.length > 1 || groups[0].label) {
    el.insertAdjacentHTML("beforeend", `<ul class="chart-legend">${groups.filter((g) => g.label).map((g) => `<li><i style="--c:${g.color || g.colors?.[0]}"></i>${g.label}</li>`).join("")}</ul>`);
  }
  const n = categories.length;
  const totals = categories.map((_, i) => (mode === "stack" ? groups.reduce((s, g) => s + Math.max(0, g.values[i]), 0) : Math.max(...groups.map((g) => g.values[i]))));
  const mins = categories.map((_, i) => Math.min(0, ...groups.map((g) => g.values[i])));
  const vMax = yMax ?? Math.max(...totals, 0) * (text ? 1.15 : 1.04), vMin = Math.min(...mins) * (text ? 1.25 : 1.05);
  const ticks = niceTicks(vMin, vMax > vMin ? vMax : vMin + 1); // all-negative data keeps 0 as the top
  const t0 = Math.min(ticks[0], 0), t1 = ticks[ticks.length - 1];
  const H = height ?? (horizontal ? Math.max(160, n * 30 + 50) : 300);
  return responsive(plot, (w) => {
    const labelW = horizontal ? Math.min(180, Math.max(...categories.map((c) => String(c).length)) * 7 + 12) : 0;
    const pad = { ...PAD, l: horizontal ? labelW : PAD.l, r: horizontal ? 40 : PAD.r };
    const iw = w - pad.l - pad.r, ih = H - pad.t - pad.b;
    const band = (horizontal ? ih : iw) / n, gw = band * 0.72, bw = mode === "stack" ? gw : gw / groups.length;
    const V = (v) => (horizontal ? pad.l + ((v - t0) / (t1 - t0)) * iw : pad.t + ih - ((v - t0) / (t1 - t0)) * ih);
    let s = `<svg xmlns="${NS}" width="${w}" height="${H}" viewBox="0 0 ${w} ${H}" class="chart-svg">`;
    s += ticks.map((v) => horizontal
      ? `<line x1="${V(v)}" x2="${V(v)}" y1="${pad.t}" y2="${H - pad.b}" class="grid grid--x"/><text x="${V(v)}" y="${H - pad.b + 18}" text-anchor="middle">${fmt(v)}</text>`
      : `<line x1="${pad.l}" x2="${w - pad.r}" y1="${V(v)}" y2="${V(v)}" class="grid"/><text x="${pad.l - 8}" y="${V(v) + 4}" text-anchor="end">${fmt(v)}</text>`).join("");
    if (zero && t0 < 0) s += horizontal ? `<line x1="${V(0)}" x2="${V(0)}" y1="${pad.t}" y2="${H - pad.b}" class="zero"/>` : `<line x1="${pad.l}" x2="${w - pad.r}" y1="${V(0)}" y2="${V(0)}" class="zero"/>`;
    categories.forEach((c, i) => {
      const c0 = (horizontal ? pad.t : pad.l) + band * i + (band - gw) / 2;
      s += horizontal
        ? `<text x="${pad.l - 8}" y="${pad.t + band * i + band / 2 + 4}" text-anchor="end" class="cat">${esc(c)}</text>`
        : `<text x="${pad.l + band * i + band / 2}" y="${H - pad.b + 18}" text-anchor="middle" class="cat">${esc(c)}</text>`;
      let acc = 0;
      groups.forEach((g, k) => {
        const v = g.values[i], color = g.colors ? g.colors[i] : g.color;
        if (!Number.isFinite(v)) return;
        const a = mode === "stack" ? acc : 0, b = a + v;
        acc = mode === "stack" ? b : acc;
        const pos = mode === "stack" ? c0 : c0 + bw * k;
        const lo = Math.min(V(a), V(b)), len = Math.abs(V(b) - V(a));
        const title = `<title>${esc(c)}${g.label ? ` · ${esc(g.label)}` : ""}: ${fmt(v)}</title>`;
        s += horizontal
          ? `<rect x="${lo}" y="${pos}" width="${Math.max(len, 0.5)}" height="${bw}" fill="${color}" rx="2">${title}</rect>`
          : `<rect x="${pos}" y="${lo}" width="${bw}" height="${Math.max(len, 0.5)}" fill="${color}" rx="2">${title}</rect>`;
        if (text) s += horizontal
          ? `<text x="${V(b) + (v >= 0 ? 6 : -6)}" y="${pos + bw / 2 + 4}" text-anchor="${v >= 0 ? "start" : "end"}" class="val">${fmt(v)}</text>`
          : `<text x="${pos + bw / 2}" y="${v >= 0 ? V(b) - 6 : V(b) + 14}" text-anchor="middle" class="val">${fmt(v)}</text>`;
      });
    });
    return `${s}</svg>`;
  });
}

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
