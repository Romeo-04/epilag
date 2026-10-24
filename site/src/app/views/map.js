// Forecast map: level counts, replay result, 3D map, linked priority list, full table, and CSV export.
import { LEVELS, fmt, replayClaim, toCsv } from "../logic.js";
import { loadGrids, createVoxelMap } from "../../lib/voxel.js";
import { LV, LV_COLOR, LV_HEIGHT, NODATA, cardTitle, count, details, download, esc, infoDisclosure, pill, tableHtml } from "../ui.js";

export async function render(el, ctx) {
  const { t, labels, fc, fcH, horizon, mode, panel, area, regionMeta } = ctx;
  const table = [...fcH].sort((a, b) => b.q50_per100k - a.q50_per100k);
  const top = table.slice(0, 12), peak = Math.max(table[0]?.q50_per100k ?? 0, 1e-9);
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
    <div class="map-page-grid">
      <section class="card map-card">
        ${cardTitle("forecastMap", t.nav_map)}
        <div class="vmap" id="vmap" role="img" aria-label="${esc(`${t.nav_map}: 3D map, column height and colour show the alert level`)}"><div class="vmap__tip" id="vmap-tip" hidden></div></div>
      </section>
      <section class="card priority-card">
        ${cardTitle("alert", t.rank, labels.per100k_short)}
        <ol class="rank-list" id="rank">${top.map((r, i) => {
          let sub = `${fmt(r.q50)} ${labels.cases_n}`;
          if (mode === "replay" && r.actual != null) sub += ` → ${fmt(r.actual)}`;
          return `<li><a class="rank-row" title="${esc(`${t.range}: ${fmt(r.q10)}–${fmt(r.q90)}`)}" href="?page=unit&area=${encodeURIComponent(r.unit_id)}" data-u="${esc(r.unit_id)}" aria-label="${esc(`${r.unit_name}, ${ctx.levelName(r.level)}`)}">
            <span class="rank-row__rank">${i + 1}</span><span class="rank-row__copy"><b>${esc(r.unit_name)}</b><small>${sub}</small></span><span class="rank-row__level">${pill(ctx, r.level)}</span>
            <span class="rank-row__bar" data-lv="${LV[r.level]}"><i style="width:${((r.q50_per100k / peak) * 100).toFixed(0)}%"></i></span><span class="rank-row__num nums">${r.q50_per100k.toFixed(1)}</span></a></li>`;
        }).join("")}</ol>
      </section>
    </div>
    ${details(t.all_areas, tableHtml(table, [
      [t.area, (r) => esc(r.unit_name)], [t.level, (r) => pill(ctx, r.level)], [t.cases, (r) => fmt(r.q50), "num"],
      [t.range, (r) => `${fmt(r.q10)}–${fmt(r.q90)}`, "num"], [t.per100k, (r) => r.q50_per100k.toFixed(1), "num"],
      ...(mode === "replay" ? [[t.actual_col, (r) => `${fmt(r.actual)} · ${esc(ctx.levelName(r.actual_level))}`]] : [])
    ]))}`;

  el.querySelectorAll("a[data-u]").forEach((a) => a.addEventListener("click", (e) => {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault(); ctx.go("unit", { area: a.dataset.u });
  }));
  ctx.topDownload(t.download_all, saveAll);

  const box = el.querySelector("#vmap"), tip = el.querySelector("#vmap-tip");
  const grids = panel === "province" && regionMeta ? await loadGrids("voxel_regions") : await loadGrids("voxel_ph");
  const grid = panel === "province" && regionMeta ? grids[regionMeta.psgc] : panel === "province" ? grids.province : grids.region;
  const byId = new Map(fcH.map((r) => [r.unit_id, r]));
  const map = await createVoxelMap(box, { grid, pixel: matchMedia("(max-width: 680px)").matches ? 2 : 3, markers: panel !== "province", framing: "land",
    onHover(u, e) {
      const r = u && byId.get(u);
      map?.highlight(u);
      if (!r) { tip.hidden = true; return; }
      const b = box.getBoundingClientRect();
      tip.innerHTML = `<b>${esc(r.unit_name)}</b>${pill(ctx, r.level)}<span>${fmt(r.q50)} (${fmt(r.q10)}–${fmt(r.q90)})</span>`;
      tip.hidden = false;
      tip.style.left = `${Math.max(8, Math.min(e.clientX - b.left + 14, b.width - 205))}px`;
      tip.style.top = `${Math.max(8, Math.min(e.clientY - b.top + 14, b.height - 88))}px`;
    },
    onPick(u) { if (u && byId.has(u)) ctx.go("unit", { area: u }); },
  });
  map.setValues(Object.fromEntries(map.units.map((u) => {
    const r = byId.get(u);
    return [u, r ? { color: LV_COLOR[r.level], height: LV_HEIGHT[r.level] } : { color: NODATA, height: 1 }];
  })), { duration: 620 });
  map.highlight(area);
  const onLeave = () => { tip.hidden = true; map.highlight(area); };
  box.addEventListener("pointerleave", onLeave);
  const rank = el.querySelector("#rank");
  const onRankOver = (e) => map.highlight(e.target.closest("[data-u]")?.dataset.u ?? null);
  const onRankLeave = () => map.highlight(area);
  rank.addEventListener("pointerover", onRankOver);
  rank.addEventListener("pointerleave", onRankLeave);
  rank.addEventListener("focusin", onRankOver);
  rank.addEventListener("focusout", onRankLeave);
  return () => { box.removeEventListener("pointerleave", onLeave); rank.removeEventListener("pointerover", onRankOver); rank.removeEventListener("pointerleave", onRankLeave); rank.removeEventListener("focusin", onRankOver); rank.removeEventListener("focusout", onRankLeave); map.dispose(); };
}
