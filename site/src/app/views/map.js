// Forecast map: level counts, replay result, the drill-down map (Philippines -> region -> province or Quezon City ->
// barangay) with a side panel that follows it, the full table, and CSV export.
// Drilling in updates the URL (region, area, focus) without re-rendering, so the camera flight is never cut off;
// choosing a region in the settings re-renders and the map flies in to it from the whole country.
import { LEVELS, fmt, fmtDay, replayClaim, toCsv } from "../logic.js";
import { barangays, forecastFor, meta as loadMeta, table } from "../data.js";
import { createDrillMap, loadDrillGeo } from "../../lib/drill-map.js";
import { LV, count, details, download, esc, infoDisclosure, pill, tableHtml } from "../ui.js";
import { icon } from "../../lib/icons.js";

const fill = (s, o) => s.replace(/\{(\w+)\}/g, (_, k) => o[k] ?? "");
const shortName = (s) => s.replace("Metropolitan Manila ", "Metro Manila ").replace(" District", "").replace(" (pre-2022)", "");
const CODES = { R_NCR: "NCR", R_CAR: "CAR", R_BARMM: "BARMM", R_MIMAROPA: "MIMAROPA" };

/** Region names for the map: full name, short name ("Cagayan Valley") and map tag ("II", "NCR"). */
function regionNames(regions) {
  const out = {};
  for (const r of regions) {
    const m = /\(([^)]+)\)/.exec(r.name), inner = m ? m[1] : r.name;
    const code = CODES[r.id] || r.name.split(" (")[0];
    out[r.id] = { name: r.name, short: CODES[r.id] === "NCR" ? "NCR" : inner.replace(/ Region$/, ""), tag: CODES[r.id] || code.replace(/^Region /, ""), code };
  }
  return out;
}

/** Rows of one horizon, falling back to the nearest one the rows have (replays have only 4 and 8). */
function atHorizon(rows, h) {
  const hs = [...new Set(rows.map((r) => r.horizon))];
  const best = hs.sort((a, b) => Math.abs(a - h) - Math.abs(b - h))[0];
  return new Map(rows.filter((r) => r.horizon === best).map((r) => [r.unit_id, r]));
}

export async function render(el, ctx) {
  const { t, labels, fc, fcH, horizon, mode, panel, origin } = ctx;
  const L = labels.dmap;
  const table_ = [...fcH].sort((a, b) => b.q50_per100k - a.q50_per100k);
  const n = (lv) => fcH.filter((r) => r.level === lv).length;
  const claim = mode === "replay" ? replayClaim(fcH) : null;
  const saveAll = () => {
    const cols = Object.keys(fc[0]).filter((k) => !["test_year"].includes(k));
    download(`epilag_forecast_${panel}_${mode}.csv`, toCsv(fc, cols.map((k) => [k, (r) => (k.includes("week") ? new Date(r[k] * 864e5).toISOString().slice(0, 10) : r[k])])), "text/csv");
  };

  el.innerHTML = `
    ${claim ? `<section class="card replay-banner">
      <div class="replay-banner__copy"><span class="kicker">${esc(labels.replay)}</span>
        <div class="replay-result" data-crossed="${claim.crossed}" data-flagged="${claim.flagged}"><strong>${count(claim.flagged)}</strong><small>/ ${claim.crossed} ${esc(labels.flagged_early.replace("{h}", horizon))}</small></div>
        ${infoDisclosure(labels.about_this, `<p>${esc(t.replay_note)}</p>`)}
      </div><pixel-sprite sprite="mosquito" pose="check" scale="3"></pixel-sprite></section>` : ""}
    <ul class="level-counts" aria-label="${esc(t.level)}">${LEVELS.slice().reverse().map((lv) => `<li data-lv="${LV[lv]}" title="${esc(t[`${LV[lv]}_d`])}"><span class="sq sq--round${lv === LEVELS[3] && n(lv) ? " lv--pulse" : ""}"></span><b class="nums">${count(n(lv))}</b><span>${esc(ctx.levelName(lv))}</span></li>`).join("")}</ul>
    <div class="map-page-grid map-page-grid--drill">
      <section class="card map-card">
        <div class="map-card__head">
          <div class="ctitle"><span class="ctitle__ic">${icon("forecastMap", { size: 32 })}</span><div><h2>${esc(t.nav_map)}</h2></div></div>
          <div class="dsearch">
            <label class="sr-only" for="dsearch">${esc(L.search)}</label>
            <input id="dsearch" type="search" placeholder="${esc(L.search)}" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="dsearch-list" aria-autocomplete="list">
            <ul class="dsearch__list" id="dsearch-list" role="listbox" hidden></ul>
          </div>
        </div>
        <div class="vmap vmap--drill" id="dmap" role="application" aria-label="${esc(L.map_label)}" tabindex="0"></div>
      </section>
      <section class="card drill-panel" id="dpanel" aria-live="polite"><div class="skeleton" aria-label="Loading"><i></i><i></i><i></i></div></section>
    </div>
    ${details(t.all_areas, tableHtml(table_, [
      [t.area, (r) => esc(r.unit_name)], [t.level, (r) => pill(ctx, r.level)], [t.cases, (r) => fmt(r.q50), "num"],
      [t.range, (r) => `${fmt(r.q10)}–${fmt(r.q90)}`, "num"], [t.per100k, (r) => r.q50_per100k.toFixed(1), "num"],
      ...(mode === "replay" ? [[t.actual_col, (r) => `${fmt(r.actual)} · ${esc(ctx.levelName(r.actual_level))}`]] : []),
    ]))}`;
  ctx.topDownload(t.download_all, saveAll);

  // ---------------------------------------------------------------- data for every level
  // Regions and Quezon City follow the current settings when they are on the Regions data, otherwise the latest run.
  // Provinces follow the settings when they are on the Provinces data, otherwise the latest province run (Jan 2021).
  const regionMode = panel === "region_qc" ? { panel, mode, origin } : { panel: "region_qc", mode: "latest", origin: null };
  const provMode = panel === "province" ? { panel, mode, origin } : { panel: "province", mode: "latest", origin: null };
  const [geo, mAll, regionRows, provRows, brgyRows, regionHist, provHist] = await Promise.all([
    loadDrillGeo(), loadMeta(), forecastFor(regionMode), forecastFor(provMode), barangays(),
    table("region_qc", "history"), table("province", "history"),
  ]);
  if (!el.isConnected) return;
  const rFc = atHorizon(regionRows, horizon), pFc = atHorizon(provRows, horizon);
  const qcRows = regionRows.filter((r) => r.unit_id === "QC");
  const qc8 = qcRows.length ? (qcRows.reduce((s, r) => s + r.q50, 0) / qcRows.length) * 8 : 0;
  const byPcode = new Map(brgyRows.map((b, i) => [b.ADM4_PCODE, { ...b, rank: i + 1, exp: b.share * qc8 }]));
  const ranked = [...byPcode.values()].sort((a, b) => b.share - a.share);
  ranked.forEach((b, i) => { b.rank = i + 1; });
  const maxExp = ranked[0]?.exp || 1, medianExp = ranked[Math.floor(ranked.length / 2)]?.exp || 0;
  const histOf = (rows) => { const m = new Map(); for (const r of rows) { if (!m.has(r.unit_id)) m.set(r.unit_id, []); m.get(r.unit_id).push(r); } for (const v of m.values()) v.sort((a, b) => a.week - b.week); return m; };
  const rHist = histOf(regionHist), pHist = histOf(provHist);
  const names = {
    region: regionNames(mAll.regions || []),
    province: Object.fromEntries(Object.entries(mAll.panels.province.names).map(([k, v]) => [k, shortName(v)])),
    city: mAll.panels.region_qc.names.QC || "Quezon City", special: L.special,
  };

  const fcOf = (node) => (!node ? null : node.kind === "province" ? pFc.get(node.id) : node.kind === "barangay" ? null : rFc.get(node.id)) || null;
  const lvOf = (node) => { const f = fcOf(node); return f ? LV[f.level] : "none"; };
  const bOf = (node) => byPcode.get(node.pcode) || null;
  const pillLv = (lv) => (lv === "none" ? `<span class="lv" data-lv="nodata">${esc(L.nodata)}</span>` : pill(ctx, Object.keys(LV).find((k) => LV[k] === lv)));
  const nm = (node) => (node.kind === "region" ? names.region[node.id]?.short || node.name : node.name);
  const days = (d) => fmtDay(d);

  // ---------------------------------------------------------------- panel pieces
  const stamp = (node) => {
    const f = fcOf(node);
    if (!f) return "";
    const old = node.kind === "province" && provMode.mode === "latest";
    return `<p class="dpanel__stamp">${esc(fill(node.kind === "province" ? L.province_run : L.run, { d: days(f.week) }))} · ${esc(fill(L.target, { d: days(f.target_week) }))}${old ? ` <span class="dpanel__old">${esc(L.older)}</span>` : ""}</p>`;
  };
  const stats = (cells) => `<div class="dpanel__stats">${cells.map(([v, k]) => `<div><b class="nums">${v}</b><span>${esc(k)}</span></div>`).join("")}</div>`;
  const head = (eyebrow, title, sub = "") => `<div class="dpanel__head"><p class="dpanel__eyebrow">${eyebrow.map(esc).join(" · ")}</p><h2>${esc(title)}</h2>${sub ? `<p class="dpanel__sub">${esc(sub)}</p>` : ""}</div>`;
  const row = (i, node, val, frac, colour, extra = "") => `<li><button type="button" class="rank-row" data-go="${esc(node.id)}" data-hl="${esc(node.id)}">
      <span class="rank-row__rank">${i}</span><span class="rank-row__copy"><b>${esc(nm(node))}${extra}</b></span><span class="rank-row__num nums">${val}</span>
      <span class="rank-row__bar"><i style="width:${Math.max(2, frac * 100).toFixed(0)}%;background:${colour}"></i></span></button></li>`;
  const sect = (title, body, aside = "") => `<section class="dpanel__sect"><h3>${esc(title)}${aside ? `<small>${esc(aside)}</small>` : ""}</h3>${body}</section>`;
  const link = (label, act) => `<button type="button" class="inline-link" data-act="${act}">${esc(label)}${icon("chevronRight", { size: 16 })}</button>`;
  const chips = (list) => `<div class="dpanel__chips">${list.map(([node, colour, extra = ""]) => `<button type="button" class="dpanel__chip" data-go="${esc(node.id)}" data-hl="${esc(node.id)}"><span class="sq" style="background:${colour}"></span>${esc(nm(node))}${extra}</button>`).join("")}</div>`;

  function gauge(f) {
    const max = Math.max(f.epidemic * 1.2, f.q90 * 1.08, 1), w = 320, x = (v) => 8 + (Math.min(v, max) / max) * (w - 16);
    if (!Number.isFinite(f.alert) || !Number.isFinite(f.epidemic)) return "";
    return `<svg class="dpanel__gauge" viewBox="0 0 ${w} 62" role="img" aria-label="${esc(`${fmt(f.q10)}–${fmt(f.q90)} · ${L.alert} ${fmt(f.alert)} · ${L.epidemic} ${fmt(f.epidemic)}`)}">
      <rect x="8" y="22" width="${x(f.alert) - 8}" height="12" fill="var(--lv-normal)" opacity=".22"/>
      <rect x="${x(f.alert)}" y="22" width="${x(f.epidemic) - x(f.alert)}" height="12" fill="var(--lv-above)" opacity=".4"/>
      <rect x="${x(f.epidemic)}" y="22" width="${w - 8 - x(f.epidemic)}" height="12" fill="var(--lv-warning)" opacity=".32"/>
      <rect x="${x(f.q10)}" y="18" width="${Math.max(3, x(f.q90) - x(f.q10))}" height="20" fill="var(--ink)"/>
      <rect x="${x(f.q50) - 5}" y="23" width="10" height="10" fill="var(--paper)" stroke="var(--ink)" stroke-width="2"/>
      <line x1="${x(f.alert)}" x2="${x(f.alert)}" y1="14" y2="42" stroke="var(--muted)" stroke-dasharray="2 2"/>
      <line x1="${x(f.epidemic)}" x2="${x(f.epidemic)}" y1="14" y2="42" stroke="var(--muted)" stroke-dasharray="2 2"/>
      <text x="${x(f.alert)}" y="9" text-anchor="middle">${esc(L.alert)} ${fmt(f.alert)}</text><text x="${x(f.epidemic)}" y="9" text-anchor="middle">${esc(L.epidemic)} ${fmt(f.epidemic)}</text>
      <text x="${x(f.q10)}" y="56" text-anchor="middle">${fmt(f.q10)}</text><text x="${x(f.q90)}" y="56" text-anchor="middle">${fmt(f.q90)}</text></svg>`;
  }
  /** The last 26 weeks of cases, then the forecast fan (q10–q90) and median for 2–8 weeks ahead. */
  function spark(hist, rows, lv, scale = 1, showAlert = true) {
    if (!hist?.length || !rows.length) return "";
    const wk = rows[0].week, past = hist.filter((r) => r.week <= wk).slice(-26).map((r) => r.cases * scale);
    if (past.length < 2) return "";
    const fcs = [...rows].sort((a, b) => a.horizon - b.horizon), w = 320, h = 120, pl = 6, pr = 6, pt = 12, pb = 20;
    const xs = (v) => pl + ((v + past.length - 1) / (past.length - 1 + 8)) * (w - pl - pr);
    const topV = Math.max(...past, ...fcs.map((f) => f.q90 * scale), ...(showAlert ? fcs.map((f) => (Number.isFinite(f.alert) ? f.alert * scale : 0)) : [])) * 1.08 || 1;
    const ys = (v) => h - pb - (v / topV) * (h - pb - pt);
    const last = past[past.length - 1];
    const line = past.map((v, i) => `${i ? "L" : "M"}${xs(i - past.length + 1).toFixed(1)} ${ys(v).toFixed(1)}`).join("");
    const area = `${line}L${xs(0).toFixed(1)} ${ys(0)}L${xs(-(past.length - 1)).toFixed(1)} ${ys(0)}Z`;
    const band = `M${xs(0)} ${ys(last)}${fcs.map((f) => `L${xs(f.horizon).toFixed(1)} ${ys(f.q90 * scale).toFixed(1)}`).join("")}${[...fcs].reverse().map((f) => `L${xs(f.horizon).toFixed(1)} ${ys(f.q10 * scale).toFixed(1)}`).join("")}Z`;
    const mid = `M${xs(0)} ${ys(last)}${fcs.map((f) => `L${xs(f.horizon).toFixed(1)} ${ys(f.q50 * scale).toFixed(1)}`).join("")}`;
    const alert = showAlert && fcs.every((f) => Number.isFinite(f.alert)) ? fcs.map((f, i) => `${i ? "L" : "M"}${xs(f.horizon).toFixed(1)} ${ys(f.alert * scale).toFixed(1)}`).join("") : "";
    const hf = fcs.reduce((a, b) => (Math.abs(b.horizon - horizon) < Math.abs(a.horizon - horizon) ? b : a));
    return `<svg class="dpanel__spark" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(L.weekly)}">
      <line x1="${pl}" x2="${w - pr}" y1="${ys(0)}" y2="${ys(0)}" stroke="var(--line-strong)"/>
      <line x1="${xs(0)}" x2="${xs(0)}" y1="${pt - 6}" y2="${h - pb}" stroke="var(--line-strong)" stroke-dasharray="2 3"/>
      <path d="${area}" fill="var(--dm-ramp-hi)" opacity=".1"/><path d="${line}" fill="none" stroke="var(--dm-ramp-hi)" stroke-width="2" stroke-linejoin="round"/>
      <path d="${band}" fill="var(--lv-${lv === "none" ? "normal" : lv})" opacity=".3"/>
      ${alert ? `<path d="${alert}" fill="none" stroke="var(--muted)" stroke-dasharray="3 3"/>` : ""}
      <path d="${mid}" fill="none" stroke="var(--ink)" stroke-width="2"/>
      <rect x="${xs(hf.horizon) - 4}" y="${ys(hf.q50 * scale) - 4}" width="8" height="8" fill="var(--paper)" stroke="var(--ink)" stroke-width="2"/>
      <text x="${pl}" y="${h - 5}">${esc(fill(L.weeks_ago, { n: past.length }))}</text><text x="${xs(0)}" y="${h - 5}" text-anchor="middle">${esc(L.now)}</text>
      <text x="${w - pr}" y="${h - 5}" text-anchor="end">${esc(L.plus8)}</text>
      ${alert ? `<text x="${w - pr}" y="${Math.max(pt, ys(fcs[fcs.length - 1].alert * scale) - 5)}" text-anchor="end">${esc(L.alert_line)}</text>` : ""}</svg>`;
  }
  const rowsOf = (node) => (node.kind === "province" ? provRows : regionRows).filter((r) => r.unit_id === node.id);
  const histFor = (node) => (node.kind === "province" ? pHist : rHist).get(node.id);

  // ---------------------------------------------------------------- panel per level
  function panelCountry() {
    const list = [...map.nodes.regions.values()].sort((a, b) => (fcOf(b)?.q50_per100k ?? -1) - (fcOf(a)?.q50_per100k ?? -1));
    const peak = Math.max(fcOf(list[0])?.q50_per100k ?? 0, 1e-9);
    const first = fcOf(list[0]);
    const top = ranked[0], topNode = top && [...map.nodes.barangays.values()].find((b) => b.pcode === top.ADM4_PCODE);
    return `${head([L.philippines, `${list.length} ${labels.regions.toLowerCase()}`], fill(L.title_country, { h: horizon }))}
      ${first ? `<p class="dpanel__stamp">${esc(fill(L.run, { d: days(first.week) }))} · ${esc(fill(L.target, { d: days(first.target_week) }))}</p>` : ""}
      ${topNode ? `<div class="dpanel__tour"><b>${esc(L.tour_title)}</b><p>${esc(fill(L.tour_body, { b: topNode.name }))}</p><button type="button" class="btn btn--primary btn--sm" data-act="tour">${icon("chevronRight", { size: 18 })}${esc(L.play)}</button></div>` : ""}
      ${sect(L.regions_ranked, `<ol class="rank-list">${list.map((r, i) => { const f = fcOf(r); return row(i + 1, r, f ? f.q50_per100k.toFixed(1) : "–", f ? f.q50_per100k / peak : 0, `var(--lv-${lvOf(r)})`); }).join("")}</ol>`, labels.wk_short.replace("{h}", horizon))}`;
  }
  function panelRegion(r) {
    const f = fcOf(r), info = names.region[r.id];
    const ps = [...map.nodes.provinces.values()].filter((p) => p.region === r.id).sort((a, b) => (fcOf(b)?.q50_per100k ?? -1) - (fcOf(a)?.q50_per100k ?? -1));
    const peak = Math.max(...ps.map((p) => fcOf(p)?.q50_per100k ?? 0), 1e-9);
    const qc = r.id === "R_NCR" ? map.nodes.city : null;
    return `${head([L.k_region, info?.code || r.id, `${(mAll.panels.region_qc.population[r.id] / 1e6).toFixed(1)}M`], nm(r), r.name)}
      <div class="dpanel__lv">${pillLv(lvOf(r))}${stamp(r)}</div>
      ${f ? stats([[fmt(f.q50), L.expected], [`${fmt(f.q10)}–${fmt(f.q90)}`, L.range], [f.q50_per100k.toFixed(1), L.per100k]]) : `<p class="dpanel__note">${esc(L.no_forecast)}</p>`}
      ${f ? sect(L.vs_thresholds, gauge(f)) : ""}
      ${f ? sect(L.weekly, spark(histFor(r), rowsOf(r), lvOf(r)), fill(L.to_date, { d: days(f.week) })) : ""}
      ${qc ? sect(L.city_with_bgy, `<ul class="rank-list">${row("", qc, fcOf(qc) ? `${fmt(fcOf(qc).q50)} ${labels.cases_n}` : "–", 1, `var(--lv-${lvOf(qc)})`, ` <span class="dpanel__tag">${esc(fill(L.n_bgy, { n: map.nodes.barangays.size }))}</span>`)}</ul>`) : ""}
      ${sect(L.provinces_ranked, `<ol class="rank-list">${ps.map((p, i) => { const pf = fcOf(p); return row(i + 1, p, pf ? pf.q50_per100k.toFixed(1) : "–", pf ? pf.q50_per100k / peak : 0, `var(--lv-${lvOf(p)})`); }).join("")}</ol>`, provMode.mode === "latest" ? L.older : "")}
      <div class="dpanel__links">${link(L.area_details, "unit")}</div>`;
  }
  function panelProvince(p) {
    const f = fcOf(p), r = map.nodes.regions.get(p.region), info = names.region[p.region];
    const sib = [...map.nodes.provinces.values()].filter((x) => x.region === p.region && x !== p).map((x) => [x, `var(--lv-${lvOf(x)})`]);
    if (p.region === "R_NCR") sib.push([map.nodes.city, `var(--lv-${lvOf(map.nodes.city)})`]);
    const pop = mAll.panels.province.population[p.id];
    return `${head([L.k_province, info?.code || "", ...(pop ? [`${(pop / 1e6).toFixed(2)}M`] : [])].filter(Boolean), p.name, nm(r))}
      <div class="dpanel__lv">${pillLv(lvOf(p))}${stamp(p)}</div>
      ${f ? `${stats([[fmt(f.q50), L.expected], [`${fmt(f.q10)}–${fmt(f.q90)}`, L.range], [f.q50_per100k.toFixed(1), L.per100k]])}
      ${sect(L.vs_thresholds, gauge(f))}${sect(L.weekly, spark(histFor(p), rowsOf(p), lvOf(p)), fill(L.to_date, { d: days(f.week) }))}` : `<p class="dpanel__note">${esc(L.no_forecast)}</p>`}
      <p class="dpanel__note"><b>${esc(L.no_towns)}</b> ${esc(L.no_towns_body)}</p>
      ${sect(fill(L.other_provinces, { r: info?.code || nm(r) }), chips(sib))}
      ${f ? `<div class="dpanel__links">${link(L.area_details, "unit")}</div>` : ""}`;
  }
  function panelCity() {
    const qc = map.nodes.city, f = fcOf(qc);
    const list = ranked.slice(0, 12).map((b) => [b, [...map.nodes.barangays.values()].find((x) => x.pcode === b.ADM4_PCODE)]).filter(([, node]) => node);
    return `${head([L.k_city, "NCR", `${(mAll.panels.region_qc.population.QC / 1e6).toFixed(2)}M`], qc.name, fill(L.city_pick, { n: map.nodes.barangays.size }))}
      <div class="dpanel__lv">${pillLv(lvOf(qc))}${stamp(qc)}</div>
      <div class="dpanel__big"><b class="nums">${fmt(qc8)}</b><span>${esc(L.city_8wk)}</span></div>
      ${f ? stats([[fmt(f.q50), fill(L.week_n, { h: f.horizon })], [`${fmt(f.q10)}–${fmt(f.q90)}`, L.range], [f.q50_per100k.toFixed(1), L.per100k]]) : ""}
      ${f ? sect(L.weekly, spark(histFor(qc), rowsOf(qc), lvOf(qc)), fill(L.to_date, { d: days(f.week) })) : ""}
      ${sect(L.top_bgy, `<ol class="rank-list">${list.map(([b, node]) => row(b.rank, node, fmt(b.exp), b.exp / maxExp, rampCss(b.exp))).join("")}</ol>`, fill(L.top_of, { k: list.length, n: ranked.length }))}
      <p class="dpanel__note">${esc(L.bgy_note)}</p>
      <div class="dpanel__links">${link(L.qc_page, "qc")}${link(L.area_details, "unit")}</div>`;
  }
  function panelBarangay(node) {
    const b = bOf(node);
    if (!b) return head([L.k_barangay, names.city], node.name);
    const nbs = node.nb.map((id) => map.get(id)).filter(Boolean).map((x) => [x, bOf(x)]).filter(([, v]) => v).sort((a, c) => a[1].rank - c[1].rank);
    const vs = medianExp ? b.exp / medianExp : 1, topB = ranked[0];
    const qc = map.nodes.city;
    return `${head([L.k_barangay, names.city, b.ADM4_PCODE], node.name, fill(L.rank_of, { r: b.rank, n: ranked.length }))}
      <div class="dpanel__big"><b class="nums">${fmt(b.exp)}</b><span>${esc(L.bgy_8wk)}</span></div>
      ${stats([[`${(b.share * 100).toFixed(1)}%`, L.share_city], [Math.round(b.cases_2025).toLocaleString("en-US"), L.cases_2025], [Math.round(b.cases_2022_2025).toLocaleString("en-US"), L.cases_all]])}
      ${sect(L.compare, `<div class="dpanel__cmp">
        <div><span>${esc(node.name)}</span><i style="width:${((b.exp / maxExp) * 100).toFixed(1)}%;background:${rampCss(b.exp)}"></i><em class="nums">${fmt(b.exp)}</em></div>
        <div><span>${esc(L.median)}</span><i style="width:${((medianExp / maxExp) * 100).toFixed(1)}%;background:var(--line-strong)"></i><em class="nums">${fmt(medianExp)}</em></div>
        ${b.rank === 1 ? "" : `<div><span>${esc(fill(L.highest, { b: topB.Barangay }))}</span><i style="width:100%;background:var(--dm-ramp-hi)"></i><em class="nums">${fmt(maxExp)}</em></div>`}
      </div><p class="dpanel__sub">${esc(vs >= 1 ? fill(L.x_median, { x: vs.toFixed(1) }) : fill(L.x_below, { x: (1 / vs).toFixed(1) }))}</p>`)}
      ${sect(L.city_trend, spark(histFor(qc), rowsOf(qc), "normal", b.share, false), fill(L.share_tag, { s: (b.share * 100).toFixed(1) }))}
      ${nbs.length ? sect(L.neighbours, chips(nbs.map(([x, v]) => [x, rampCss(v.exp), ` <span class="nums">${fmt(v.exp)}</span>`])), String(nbs.length)) : ""}
      <p class="dpanel__note">${esc(L.bgy_note)}</p>
      <div class="dpanel__links">${link(L.qc_page, "qc")}</div>`;
  }

  // ---------------------------------------------------------------- the map
  const box = el.querySelector("#dmap"), dpanel = el.querySelector("#dpanel");
  let rampCss = () => "var(--dm-ramp-hi)";
  const cssOf = (n) => getComputedStyle(box).getPropertyValue(n).trim();
  {
    const lo = cssOf("--dm-ramp-lo"), hi = cssOf("--dm-ramp-hi");
    const hex = (s) => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16));
    if (/^#[0-9a-f]{6}$/i.test(lo) && /^#[0-9a-f]{6}$/i.test(hi)) {
      const a = hex(lo), c = hex(hi);
      rampCss = (v) => { const k = Math.sqrt(Math.min(1, Math.max(0, v / maxExp))); return `rgb(${a.map((x, i) => Math.round(x + (c[i] - x) * k)).join(",")})`; };
    }
  }
  const initial = (() => {
    if (ctx.focus) return ctx.focus;
    if (ctx.area === "QC") return "QC";
    if (panel === "province" && ctx.area && ctx.area !== ctx.region) return ctx.area;
    return ctx.region || null;
  })();
  let current = null, map = null;
  map = await createDrillMap(box, {
    geo, names, initial, keyRoot: el.querySelector(".map-page-grid--drill"), pixel: matchMedia("(max-width: 680px)").matches ? 2 : 3,
    level: lvOf, expected: (b) => bOf(b)?.exp ?? 0, maxExpected: maxExp, text: L,
    tip(node) {
      if (node.kind === "barangay") {
        const b = bOf(node);
        return `<b>${esc(node.name)}</b><span>${esc(L.k_barangay)} · ${esc(names.city)}</span>${b ? `<span>${esc(labels.expected_8)}: <b class="nums">${fmt(b.exp)}</b></span><span>${esc(labels.share_city)}: ${(b.share * 100).toFixed(1)}%</span>` : ""}`;
      }
      const f = fcOf(node);
      return `<b>${esc(nm(node))}</b>${pillLv(lvOf(node))}${f ? `<span>${fmt(f.q50)} (${fmt(f.q10)}–${fmt(f.q90)})</span><span>${f.q50_per100k.toFixed(1)} ${esc(labels.per100k_short)}</span>` : `<span>${esc(L.no_forecast)}</span>`}`;
    },
    legend(kind) {
      if (kind === "expected") {
        const stops = Array.from({ length: 11 }, (_, i) => rampCss(maxExp * (i / 10) ** 2)).join(",");
        return `<h4>${esc(L.legend_exp)}</h4><div class="dmap__ramp" style="background:linear-gradient(90deg,${stops})"></div><div class="dmap__ticks nums"><span>0</span><span>${fmt(maxExp / 4)}</span><span>${fmt(maxExp)}</span></div>`;
      }
      return `<h4>${esc(L.legend_level)} · ${esc(labels.wk_short.replace("{h}", horizon))}</h4><ul>${LEVELS.slice().reverse().map((lv) => `<li><span class="sq" data-lv="${LV[lv]}"></span>${esc(ctx.levelName(lv))}</li>`).join("")}</ul>`;
    },
    onFocus(node, ch, api) {
      map = api; current = node;
      dpanel.innerHTML = `<div class="dpanel" data-kind="${node ? node.kind : "country"}">${!node ? panelCountry() : node.kind === "region" ? panelRegion(node) : node.kind === "province" ? panelProvince(node) : node.kind === "city" ? panelCity() : panelBarangay(node)}</div>`;
      dpanel.scrollTop = 0;
      // keep the URL and the settings bar in step without re-rendering the page
      const region = ch[0] || null, focus = node?.id || null;
      // the province panel needs a province as its area, so above province level only the map focus moves there
      const patch = panel === "province"
        ? (node?.kind === "province" ? { focus, region: region.id, area: node.id } : { focus })
        : { focus, region: region?.id || null, area: !region ? null : ch[1]?.kind === "city" ? "QC" : region.id };
      if ((ctx.focus || null) !== focus || ("region" in patch && ctx.region !== patch.region)) {
        Object.assign(ctx, { focus, ...("region" in patch ? { region: patch.region } : {}) });
        ctx.setQuiet?.(patch);
      }
    },
  });
  if (!el.isConnected) { map.dispose(); return; }

  // panel: drill from rows and chips, highlight on hover, links out
  const onPanelClick = (e) => {
    const go = e.target.closest("[data-go]");
    if (go) { map.go(go.dataset.go); return; }
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (act === "tour") {
      const top = ranked[0] && [...map.nodes.barangays.values()].find((b) => b.pcode === ranked[0].ADM4_PCODE);
      if (top) (map.current() ? map.go(null).then(() => map.go(top)) : map.go(top));
    } else if (act === "qc") ctx.go("qc", { region: "R_NCR", area: "QC", panel: "region_qc" });
    else if (act === "unit" && current) {
      const ch = map.chain(current);
      if (current.kind === "province") ctx.go("unit", { region: current.region, panel: "province", area: current.id, mode: panel === "province" ? mode : "replay" });
      else ctx.go("unit", { region: ch[0].id, panel: "region_qc", area: ch[1]?.kind === "city" ? "QC" : ch[0].id });
    }
  };
  const onPanelOver = (e) => map.hover(e.target.closest("[data-hl]")?.dataset.hl || null);
  const onPanelLeave = () => map.hover(null);
  dpanel.addEventListener("click", onPanelClick);
  dpanel.addEventListener("pointerover", onPanelOver);
  dpanel.addEventListener("pointerleave", onPanelLeave);

  // search: regions, provinces, Quezon City and its barangays
  const input = el.querySelector("#dsearch"), list = el.querySelector("#dsearch-list");
  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const index = [
    ...[...map.nodes.regions.values()].map((r) => ({ id: r.id, kind: L.k_region, label: nm(r), sub: names.region[r.id]?.code || "", key: norm(`${r.name} ${nm(r)} ${names.region[r.id]?.code}`) })),
    ...[...map.nodes.provinces.values()].map((p) => ({ id: p.id, kind: L.k_province, label: p.name, sub: names.region[p.region]?.code || "", key: norm(p.name) })),
    { id: "QC", kind: L.k_city, label: names.city, sub: "NCR", key: norm(`${names.city} qc`) },
    ...[...map.nodes.barangays.values()].map((b) => ({ id: b.id, kind: L.k_barangay, label: b.name, sub: names.city, key: norm(b.name) })),
  ];
  let hits = [], sel = 0;
  const show = () => {
    const v = norm(input.value.trim());
    if (!v) { list.hidden = true; input.setAttribute("aria-expanded", "false"); return; }
    hits = index.filter((x) => x.key.includes(v)).sort((a, b) => (a.key.startsWith(v) ? 0 : 1) - (b.key.startsWith(v) ? 0 : 1)).slice(0, 8);
    sel = 0;
    list.innerHTML = hits.length ? hits.map((h, i) => `<li role="option" id="dsr-${i}" data-i="${i}" aria-selected="${i === sel}"><span class="dsearch__kind">${esc(h.kind)}</span><b>${esc(h.label)}</b><small>${esc(h.sub)}</small></li>`).join("") : `<li class="dsearch__none">${esc(L.no_match)}</li>`;
    list.hidden = false; input.setAttribute("aria-expanded", "true");
  };
  const pick = (i) => { const h = hits[i]; if (!h) return; list.hidden = true; input.value = ""; input.setAttribute("aria-expanded", "false"); map.go(h.id); box.focus({ preventScroll: true }); };
  const onKey = (e) => {
    if (list.hidden) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + hits.length) % Math.max(hits.length, 1);
      list.querySelectorAll("li[data-i]").forEach((li, i) => li.setAttribute("aria-selected", String(i === sel))); input.setAttribute("aria-activedescendant", `dsr-${sel}`);
    } else if (e.key === "Enter") { e.preventDefault(); pick(sel); } else if (e.key === "Escape") { list.hidden = true; }
  };
  const onDown = (e) => { const li = e.target.closest("li[data-i]"); if (li) { e.preventDefault(); pick(+li.dataset.i); } };
  const onBlur = () => setTimeout(() => { list.hidden = true; input.setAttribute("aria-expanded", "false"); }, 120);
  input.addEventListener("input", show); input.addEventListener("keydown", onKey); input.addEventListener("blur", onBlur); list.addEventListener("pointerdown", onDown);

  return () => {
    dpanel.removeEventListener("click", onPanelClick); dpanel.removeEventListener("pointerover", onPanelOver); dpanel.removeEventListener("pointerleave", onPanelLeave);
    input.removeEventListener("input", show); input.removeEventListener("keydown", onKey); input.removeEventListener("blur", onBlur); list.removeEventListener("pointerdown", onDown);
    map.dispose();
  };
}
