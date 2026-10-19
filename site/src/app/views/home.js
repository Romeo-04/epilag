// Overview: a compact operations readout with status, map, priority areas, action brief, and the forecast clock.
import { LEVELS, briefMarkdown, briefTable, fmt, fmtDay, replayClaim } from "../logic.js";
import { loadGrids, createVoxelMap } from "../../lib/voxel.js";
import { LV, LV_COLOR, LV_HEIGHT, NODATA, cardTitle, count, download, downloadButton, esc, head, infoDisclosure, pill } from "../ui.js";

const STORY_ART = [["props", "cloud"], ["mosquito", "fly1"], ["props", "residents"], ["props", "hospital"]];

export async function render(el, ctx) {
  const { t, labels, lang, i18n, fc, fcH, horizon, mode, panel, area, regionMeta } = ctx;
  const asOf = Math.max(...fcH.map((r) => r.week));
  const target = Math.max(...fcH.map((r) => r.target_week));
  const n = (lv) => fcH.filter((r) => r.level === lv).length;
  const nWarn = n(LEVELS[3]), nWatch = n(LEVELS[2]), nAbove = n(LEVELS[1]);
  const rows = briefTable(fc, fcH);
  const act = rows.filter((r) => r.level === LEVELS[2] || r.level === LEVELS[3]).slice(0, 4);
  const shown = act.length ? act : rows.filter((r) => r.level === LEVELS[1]).slice(0, 3);
  const priority = [...rows].sort((a, b) => b.q50_per100k - a.q50_per100k).slice(0, 6);
  const status = mode === "replay" ? replayStatus(t, horizon, fcH) : nWarn + nWatch === 0 ? quietStatus(t) : "";
  const saveBrief = () => download("epilag_action_brief.md", briefMarkdown(shown, { t, lang, i18n, panelLabel: ctx.panelLabel, horizon, asOf }), "text/markdown");

  el.innerHTML = `
    ${head(t.hello, `${horizon} ${t.weeks_ahead}`, `${t.as_of} ${fmtDay(asOf)} · ${t.for_week} ${fmtDay(target)} · ${ctx.panelLabel}`)}

    <section class="card status-strip" aria-labelledby="home-act-title">
      <div class="status-strip__lead"><span class="home-eyebrow" id="home-act-title">${esc(t.act_now)}</span><div class="status-strip__total">${count(nWarn + nWatch)}<span>${esc(labels.top_areas)}</span></div></div>
      <div class="status-strip__levels" aria-label="${esc(t.act_now)}">
        ${levelStat(LEVELS[3], "warning", nWarn, t)}${levelStat(LEVELS[2], "watch", nWatch, t)}${levelStat(LEVELS[1], "above", nAbove, t)}
      </div>
      <div class="status-strip__message">${status}</div>
      <a class="btn btn--primary btn--sm status-strip__action" href="?page=map" data-go="map">${esc(t.open_map)} <i data-icon="arrowRight" data-size="18"></i></a>
    </section>

    <div class="overview-grid" aria-label="${esc(t.nav_map)}">
      <section class="card overview-map">
        ${cardTitle("forecastMap", t.nav_map, `${t.for_week} ${fmtDay(target)}`)}
        <div class="home-map" id="home-map" role="img" aria-label="${esc(`${t.nav_map}, ${t.for_week} ${fmtDay(target)}`)}"><div class="home-map__tip" id="home-map-tip" hidden></div></div>
        <div class="map-footer"><ul class="home-legend">${LEVELS.map((lv) => `<li data-lv="${LV[lv]}"><span class="sq sq--round"></span>${esc(ctx.levelName(lv))}</li>`).join("")}</ul>
          <a class="inline-link" href="?page=map" data-go="map">${esc(t.open_map)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </section>

      <aside class="card overview-priority">
        ${cardTitle("alert", t.rank, t.rank_sub)}
        ${priority.length ? `<ol class="priority-list" id="home-priority">${priority.map((r, i) => priorityRow(r, i, ctx)).join("")}</ol>` : `<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${esc(t.brief_empty)}</div></div>`}
        <div class="priority-list__footer"><a class="inline-link" href="?page=map" data-go="map">${esc(labels.all_areas)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </aside>
    </div>

    <section class="card brief-card">
      ${cardTitle("actionPlan", t.brief_head, t.brief_sub)}
      ${act.length ? "" : `<div class="callout">${esc(t.brief_empty)}</div>`}
      <div class="brief-list">${shown.map((r) => briefRow(r, ctx)).join("")}</div>
      ${shown.length ? `<div class="brief-footer">${downloadButton("dl-brief", t.download_brief)}</div>` : ""}
    </section>

    <section class="card weeks-card">
      ${cardTitle("alert", t.story_head)}
      <ol class="weeks-rail">${t.story.map(([a, b], i) => `<li class="weeks-step${i === 0 ? " weeks-step--on" : ""}"><span class="weeks-step__art"><pixel-sprite sprite="${STORY_ART[i][0]}" pose="${STORY_ART[i][1]}" scale="${STORY_ART[i][0] === "props" ? 1 : 2}"></pixel-sprite></span><span class="weeks-step__copy"><b>${esc(a)}</b><span>${esc(b)}</span></span></li>`).join("")}</ol>
      ${infoDisclosure(labels.about_this, `<p>${esc(t.story_note)}</p>`)}
    </section>

    <section class="card drill-card">
      <div><div class="kicker">${esc(labels.drill)}</div><h2>${esc(t.drill_head)}</h2><p>${esc(t.drill_sub)}</p></div>
      <a class="btn btn--light btn--sm" href="../drill/"><i data-icon="play" data-size="18"></i>${esc(t.drill_btn)}</a>
    </section>`;

  el.querySelectorAll("[data-go]").forEach((a) => a.addEventListener("click", (e) => {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault(); ctx.go(a.dataset.go, a.dataset.u ? { area: a.dataset.u } : {});
  }));
  el.querySelector("#story-btn")?.addEventListener("click", () => ctx.set({ panel: "province", mode: "replay", region: null, area: null }));
  el.querySelector("#dl-brief")?.addEventListener("click", saveBrief);
  ctx.topDownload(t.download_brief, saveBrief);

  const box = el.querySelector("#home-map"), tip = el.querySelector("#home-map-tip");
  const grids = panel === "province" && regionMeta ? await loadGrids("voxel_regions") : await loadGrids("voxel_ph");
  const grid = panel === "province" && regionMeta ? grids[regionMeta.psgc] : panel === "province" ? grids.province : grids.region;
  const byId = new Map(fcH.map((r) => [r.unit_id, r]));
  const map = await createVoxelMap(box, { grid, pixel: matchMedia("(max-width: 680px)").matches ? 2 : 3, markers: panel !== "province",
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
  return () => { box.removeEventListener("pointerleave", onLeave); priorityList?.removeEventListener("pointerover", onPriorityOver); priorityList?.removeEventListener("pointerleave", onPriorityLeave); priorityList?.removeEventListener("focusin", onPriorityOver); priorityList?.removeEventListener("focusout", onPriorityLeave); map.dispose(); };
}

function levelStat(level, key, value, t) {
  return `<div class="status-level" data-lv="${LV[level]}"><span class="sq sq--round"></span><span class="status-level__copy"><b class="nums">${count(value)}</b><span>${esc(t[`${key}_n`])}</span></span></div>`;
}

function replayStatus(t, horizon, rows) {
  const c = replayClaim(rows);
  return `<div class="status-message__title">${esc(t.then)}</div><p><b>${c.flagged} ${esc(t.of)} ${c.crossed}</b> ${esc(t.then_line.replace("{h}", horizon))}</p>`;
}

function quietStatus(t) {
  return `<div class="status-message__title">${esc(t.quiet)}</div><p>${esc(t.brief_empty)}</p><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${esc(t.replay_story)}</button>`;
}

function priorityRow(r, i, ctx) {
  return `<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(r.unit_id)}" data-u="${esc(r.unit_id)}" data-go="unit" aria-label="${esc(`${r.unit_name}, ${ctx.levelName(r.level)}`)}">
    <span class="priority-row__rank">${i + 1}</span><span class="priority-row__copy"><b>${esc(r.unit_name)}</b><small>${esc(ctx.t.cases)}: ${fmt(r.q50)} (${fmt(r.q10)}–${fmt(r.q90)})</small><small>${esc(ctx.t.peak)} ${fmtDay(r.peak_week, false)}</small></span>
    <span class="priority-row__level">${pill(ctx, r.level)}<small>${r.q50_per100k.toFixed(1)} ${esc(ctx.t.per100k)}</small></span></a></li>`;
}

function briefRow(r, ctx) {
  const [when, d] = ctx.i18n.PLAYBOOK[ctx.lang][r.level][0];
  return `<div class="brief-row" data-lv="${LV[r.level]}"><div><div class="brief-row__name">${esc(r.unit_name)} ${pill(ctx, r.level)}</div>
    <div class="brief-row__meta">${esc(ctx.t.cases)}: <b>${fmt(r.q50)}</b> (${fmt(r.q10)}–${fmt(r.q90)}) · ${esc(ctx.t.peak)} ${fmtDay(r.peak_week, false)}</div></div>
    <div class="brief-row__next"><b>${esc(when)}:</b> ${esc(d)}<div class="brief-row__meta">${esc(ctx.t.prepare.replace("{n}", fmt(r.cases_high)))}</div></div></div>`;
}
