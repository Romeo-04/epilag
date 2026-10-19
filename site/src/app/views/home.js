// Overview: alert counts, trend, fastest risers and this week's actions, then the map and priority list.
// The action brief is the top-bar download.
import { table } from "../data.js";
import { LEVELS, briefMarkdown, briefTable, fmt, replayClaim } from "../logic.js";
import { barChart } from "../chart.js";
import { loadGrids, createVoxelMap } from "../../lib/voxel.js";
import { LV, LV_COLOR, LV_HEIGHT, NODATA, cardTitle, count, dot, download, esc, pill } from "../ui.js";

export async function render(el, ctx) {
  const { t, labels, lang, i18n, fc, fcH, horizon, mode, panel, area, regionMeta } = ctx;
  const asOf = Math.max(...fcH.map((r) => r.week));
  const n = (lv) => fcH.filter((r) => r.level === lv).length;
  const nWarn = n(LEVELS[3]), nWatch = n(LEVELS[2]), nAbove = n(LEVELS[1]);
  const rows = briefTable(fc, fcH);
  const act = rows.filter((r) => r.level === LEVELS[2] || r.level === LEVELS[3]).slice(0, 4);
  const shown = act.length ? act : rows.filter((r) => r.level === LEVELS[1]).slice(0, 3);
  const priority = [...rows].sort((a, b) => b.q50_per100k - a.q50_per100k).slice(0, 6);
  const status = mode === "replay" ? replayStatus(labels, horizon, fcH) : nWarn + nWatch === 0 ? quietStatus(t, labels) : "";
  // reported cases in the forecast's own week: the "now" every change is measured from
  const ids = new Set(fcH.map((r) => r.unit_id));
  const nowBy = new Map((await table(panel, "history")).filter((r) => r.week === asOf && ids.has(r.unit_id) && r.cases != null).map((r) => [r.unit_id, r.cases]));
  const hs = [...new Set(fc.map((r) => r.horizon))].sort((a, b) => a - b);
  const total = (h) => fc.filter((r) => r.horizon === h).reduce((s, r) => s + r.q50, 0);
  const nowTotal = [...nowBy.values()].reduce((s, v) => s + v, 0);
  const change = nowBy.size ? total(horizon) / Math.max(nowTotal, 1) - 1 : null;
  const rising = fcH.filter((r) => (nowBy.get(r.unit_id) ?? 0) >= 5).map((r) => ({ ...r, now: nowBy.get(r.unit_id), pct: r.q50 / nowBy.get(r.unit_id) - 1 }))
    .filter((r) => r.pct > 0).sort((a, b) => b.pct - a.pct).slice(0, 5);
  const saveBrief = () => download("epilag_action_brief.md", briefMarkdown(shown, { t, lang, i18n, panelLabel: ctx.panelLabel, horizon, asOf }), "text/markdown");

  el.innerHTML = `
    <section class="card status-strip" aria-labelledby="home-act-title">
      <div class="status-strip__lead"><span class="home-eyebrow" id="home-act-title">${esc(labels.act_now)}</span><div class="status-strip__total">${count(nWarn + nWatch)}<span>${esc(labels.on_alert)}</span></div></div>
      <div class="status-strip__levels" aria-label="${esc(labels.act_now)}">
        ${levelStat(LEVELS[3], "warning", nWarn, t)}${levelStat(LEVELS[2], "watch", nWatch, t)}${levelStat(LEVELS[1], "above", nAbove, t)}
      </div>
      <div class="status-strip__message">${status}</div>
    </section>

    <div class="overview-insights">
      <section class="card">
        ${cardTitle("areaDetail", labels.trend, labels.trend_sub)}
        ${change == null ? "" : `<div class="trend-head" data-dir="${change > 0 ? "up" : "down"}"><b class="nums">${change > 0 ? "▲" : "▼"} ${Math.abs(Math.round(change * 100))}%</b><span>${esc(labels.vs_now.replace("{h}", horizon))}</span></div>`}
        <div id="home-trend" class="chart-box"></div>
      </section>
      <section class="card">
        ${cardTitle("alert", labels.rising, labels.rising_sub)}
        ${rising.length ? `<ol class="priority-list">${rising.map((r, i) => riseRow(r, i, ctx)).join("")}</ol>` : `<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${esc(labels.no_rising)}</div></div>`}
      </section>
      <section class="card">
        ${cardTitle("check", labels.do_week)}
        ${shown.length ? `<div class="do-list">${shown.slice(0, 3).map((r) => doRow(r, ctx)).join("")}</div>` : `<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${esc(labels.quiet)}</div></div>`}
      </section>
    </div>

    <div class="overview-grid" aria-label="${esc(t.nav_map)}">
      <section class="card overview-map">
        ${cardTitle("forecastMap", t.nav_map)}
        <div class="home-map" id="home-map" role="img" aria-label="${esc(t.nav_map)}"><div class="home-map__tip" id="home-map-tip" hidden></div></div>
        <div class="map-footer"><ul class="home-legend">${LEVELS.map((lv) => `<li data-lv="${LV[lv]}"><span class="sq sq--round"></span>${esc(ctx.levelName(lv))}</li>`).join("")}</ul>
          <a class="inline-link" href="?page=map" data-go="map">${esc(t.open_map)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </section>

      <aside class="card overview-priority">
        ${cardTitle("alert", t.rank)}
        ${priority.length ? `<ol class="priority-list" id="home-priority">${priority.map((r, i) => priorityRow(r, i, ctx)).join("")}</ol>` : `<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${esc(labels.quiet)}</div></div>`}
        <div class="priority-list__footer"><a class="inline-link" href="?page=map" data-go="map">${esc(labels.all_areas)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </aside>
    </div>`;

  el.querySelectorAll("[data-go]").forEach((a) => a.addEventListener("click", (e) => {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault(); ctx.go(a.dataset.go, a.dataset.u ? { area: a.dataset.u } : {});
  }));
  el.querySelector("#story-btn")?.addEventListener("click", () => ctx.set({ panel: "province", mode: "replay", region: null, area: null }));
  ctx.topDownload(t.download_brief, saveBrief);
  const disposeTrend = barChart(el.querySelector("#home-trend"), { height: 170, text: true,
    categories: [labels.now, ...hs.map((h) => labels.wk_ahead.replace("{h}", h))],
    groups: [{ values: [nowTotal, ...hs.map(total)], colors: ["#8A9891", ...hs.map((h) => (h === horizon ? "#08754F" : "#9FCBA6"))] }] });

  const box = el.querySelector("#home-map"), tip = el.querySelector("#home-map-tip");
  const grids = panel === "province" && regionMeta ? await loadGrids("voxel_regions") : await loadGrids("voxel_ph");
  const grid = panel === "province" && regionMeta ? grids[regionMeta.psgc] : panel === "province" ? grids.province : grids.region;
  const byId = new Map(fcH.map((r) => [r.unit_id, r]));
  const map = await createVoxelMap(box, { grid, pixel: matchMedia("(max-width: 680px)").matches ? 2 : 3, markers: panel !== "province", framing: "land",
    onHover(u, e) {
      const r = u && byId.get(u);
      map.highlight(u);
      if (!r) { tip.hidden = true; return; }
      const b = box.getBoundingClientRect();
      tip.innerHTML = `<b>${esc(r.unit_name)}</b>${pill(ctx, r.level)}<span>${fmt(r.q50)} (${fmt(r.q10)}–${fmt(r.q90)})</span>`;
      tip.hidden = false;
      tip.style.left = `${Math.max(8, Math.min(e.clientX - b.left + 14, b.width - 190))}px`;
      tip.style.top = `${Math.max(8, Math.min(e.clientY - b.top + 14, b.height - 88))}px`;
    },
    onPick(u) { if (u && byId.has(u)) ctx.go("unit", { area: u }); },
  });
  map.setValues(Object.fromEntries(map.units.map((u) => {
    const r = byId.get(u);
    return [u, r ? { color: LV_COLOR[r.level], height: LV_HEIGHT[r.level] } : { color: NODATA, height: 1 }];
  })), { duration: 520 });
  map.highlight(area);
  const onLeave = () => { tip.hidden = true; map.highlight(area); };
  box.addEventListener("pointerleave", onLeave);
  const priorityList = el.querySelector("#home-priority");
  const onPriorityOver = (e) => map.highlight(e.target.closest("[data-u]")?.dataset.u ?? null);
  const onPriorityLeave = () => map.highlight(area);
  priorityList?.addEventListener("pointerover", onPriorityOver);
  priorityList?.addEventListener("pointerleave", onPriorityLeave);
  priorityList?.addEventListener("focusin", onPriorityOver);
  priorityList?.addEventListener("focusout", onPriorityLeave);
  return () => { disposeTrend(); box.removeEventListener("pointerleave", onLeave); priorityList?.removeEventListener("pointerover", onPriorityOver); priorityList?.removeEventListener("pointerleave", onPriorityLeave); priorityList?.removeEventListener("focusin", onPriorityOver); priorityList?.removeEventListener("focusout", onPriorityLeave); map.dispose(); };
}

function levelStat(level, key, value, t) {
  return `<div class="status-level" data-lv="${LV[level]}"><span class="sq sq--round"></span><span class="status-level__copy"><b class="nums">${count(value)}</b><span>${esc(t[`${key}_n`])}</span></span></div>`;
}

function replayStatus(labels, horizon, rows) {
  const c = replayClaim(rows);
  return `<p><b>${c.flagged} / ${c.crossed}</b> ${esc(labels.flagged_early.replace("{h}", horizon))}</p>`;
}

function quietStatus(t, labels) {
  return `<div class="status-message__title">${esc(labels.quiet)}</div><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${esc(t.replay_story)}</button>`;
}

function priorityRow(r, i, ctx) {
  return `<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(r.unit_id)}" data-u="${esc(r.unit_id)}" data-go="unit" aria-label="${esc(`${r.unit_name}, ${ctx.levelName(r.level)}`)}" title="${esc(`${ctx.t.range}: ${fmt(r.q10)}–${fmt(r.q90)}`)}">
    <span class="priority-row__rank">${i + 1}</span><span class="priority-row__copy"><b>${esc(r.unit_name)}</b><small>${fmt(r.q50)} ${esc(ctx.labels.cases_n)}</small></span>
    <span class="priority-row__level">${pill(ctx, r.level)}<small>${r.q50_per100k.toFixed(1)} ${esc(ctx.labels.per100k_short)}</small></span></a></li>`;
}

function riseRow(r, i, ctx) {
  return `<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(r.unit_id)}" data-u="${esc(r.unit_id)}" data-go="unit" aria-label="${esc(`${r.unit_name}, +${Math.round(r.pct * 100)}%, ${ctx.levelName(r.level)}`)}" title="${esc(ctx.levelName(r.level))}">
    <span class="priority-row__rank">${i + 1}</span><span class="priority-row__copy"><b>${esc(r.unit_name)}</b><small>${fmt(r.now)} → ${fmt(r.q50)} ${esc(ctx.labels.cases_n)}</small></span>
    <span class="rise-pct nums">${dot(r.level)}+${Math.round(r.pct * 100)}%</span></a></li>`;
}

function doRow(r, ctx) {
  return `<a class="do-row" data-lv="${LV[r.level]}" href="?page=unit&area=${encodeURIComponent(r.unit_id)}" data-u="${esc(r.unit_id)}" data-go="unit">
    <span class="do-row__name">${esc(r.unit_name)} ${pill(ctx, r.level)}</span><small>${esc(ctx.labels.level_action[r.level])}</small></a>`;
}
