// Overview: a glanceable forecast, priority areas, action brief, tools, and the Dengue Drill.
import { LEVELS, briefMarkdown, briefTable, fmt, fmtDay, replayClaim } from "../logic.js";
import { loadGrids, createVoxelMap } from "../../lib/voxel.js";
import { LV, LV_COLOR, LV_HEIGHT, NODATA, cardTitle, count, download, downloadButton, esc, head, pill } from "../ui.js";

const TOOL_ICON = { map: "forecastMap", unit: "areaDetail", budget: "actionPlan", public: "residents", qc: "barangay", proof: "didItWork" };
const STORY_ART = [["props", "cloud"], ["mosquito", "fly1"], ["props", "residents"], ["props", "hospital"]];

export async function render(el, ctx) {
  const { t, lang, i18n, fc, fcH, horizon, mode, panel } = ctx;
  const asOf = Math.max(...fcH.map((r) => r.week));
  const target = Math.max(...fcH.map((r) => r.target_week));
  const n = (lv) => fcH.filter((r) => r.level === lv).length;
  const nWarn = n(LEVELS[3]), nWatch = n(LEVELS[2]), nAbove = n(LEVELS[1]);
  const rows = briefTable(fc, fcH);
  const act = rows.filter((r) => r.level === LEVELS[2] || r.level === LEVELS[3]).slice(0, 6);
  const shown = act.length ? act : rows.filter((r) => r.level === LEVELS[1]).slice(0, 3);
  // the priority list ranks every area by forecast cases per 100,000 (as on the forecast map), so it is never empty
  const priority = [...rows].sort((a, b) => b.q50_per100k - a.q50_per100k).slice(0, 6);
  const status = mode === "replay" ? replayStatus(t, horizon, fcH) : nWarn + nWatch === 0 ? quietStatus(t) : "";

  el.innerHTML = `
    ${head(t.hello, `${horizon} ${t.weeks_ahead}`, `${t.as_of} ${fmtDay(asOf)} · ${t.for_week} ${fmtDay(target)} · ${ctx.panelLabel}`)}

    <section class="card home-counts" aria-labelledby="home-act-title">
      <div class="home-counts__lead">
        <span class="home-eyebrow" id="home-act-title">${esc(t.act_now)}</span>
        <div class="home-counts__total">${count(nWarn + nWatch)}</div>
      </div>
      <div class="home-counts__levels" aria-label="${esc(t.act_now)}">
        ${levelStat(LEVELS[3], "warning", nWarn, t)}
        ${levelStat(LEVELS[2], "watch", nWatch, t)}
        ${levelStat(LEVELS[1], "above", nAbove, t)}
      </div>
      <div class="home-counts__state">${status}</div>
      <a class="btn btn--primary btn--sm home-counts__map" href="?page=map" data-go="map">${esc(t.open_map)} <i data-icon="arrowRight" data-size="24"></i></a>
    </section>

    <section class="home-forecast" aria-label="${esc(t.nav_map)}">
      <section class="card home-map-card">
        ${cardTitle("forecastMap", t.nav_map, `${t.for_week} ${fmtDay(target)}`)}
        <div class="home-map" id="home-map" role="img" aria-label="${esc(`${t.nav_map}, ${t.for_week} ${fmtDay(target)}`)}">
          <div class="home-map__tip" id="home-map-tip" hidden></div>
        </div>
        <div class="home-map__footer">
          <ul class="home-legend">${LEVELS.map((lv) => `<li data-lv="${LV[lv]}"><span class="sq sq--round"></span>${esc(ctx.levelName(lv))}</li>`).join("")}</ul>
        </div>
      </section>

      <aside class="card home-priority">
        ${cardTitle("alert", t.rank, t.rank_sub)}
        ${priority.length ? `<ol class="home-priority__list" id="home-priority">${priority.map((r, i) => priorityRow(r, i, ctx)).join("")}</ol>` : `<div class="callout home-priority__empty"><i data-icon="check" data-size="24"></i>${esc(t.brief_empty)}</div>`}
        <a class="home-priority__all" href="?page=map" data-go="map">${esc(t.open_map)} <i data-icon="arrowRight" data-size="24"></i></a>
      </aside>
    </section>

    <section class="card home-brief">
      ${cardTitle("actionPlan", t.brief_head, t.brief_sub)}
      ${act.length ? "" : `<div class="callout home-brief__empty"><i data-icon="check" data-size="24"></i>${esc(t.brief_empty)}</div>`}
      <div class="briefs">${shown.map((r) => briefRow(r, ctx)).join("")}</div>
      ${shown.length ? `<div class="home-brief__footer">${downloadButton("dl-brief", t.download_brief)}</div>` : ""}
    </section>

    <section class="card home-story">
      ${cardTitle("alert", t.story_head)}
      <ol class="home-story__rail">${t.story.map(([a, b], i) => `<li class="home-story__step${i === 0 ? " home-story__step--on" : ""}">
        <span class="home-story__art"><pixel-sprite sprite="${STORY_ART[i][0]}" pose="${STORY_ART[i][1]}" scale="${STORY_ART[i][0] === "props" ? 1 : 2}"></pixel-sprite></span>
        <span class="home-story__copy"><b>${esc(a)}</b><span>${esc(b)}</span></span></li>`).join("")}</ol>
      <div class="callout home-story__note"><i data-icon="alert" data-size="24"></i>${esc(t.story_note)}</div>
    </section>

    <section class="home-tools" aria-labelledby="home-tools-title">
      <div class="home-section-heading"><h2 id="home-tools-title">${esc(t.features_head)}</h2><p>${esc(t.features_sub)}</p></div>
      <div class="home-tools__grid">${Object.keys(TOOL_ICON).map((k) => {
        const [does, why, you] = i18n.FEATURES[lang][k];
        return `<a class="card home-tool" href="?page=${k}" data-go="${k}">
          <span class="home-tool__ic"><i data-icon="${TOOL_ICON[k]}" data-size="32"></i></span>
          <div class="home-tool__body"><h3>${esc(t[`nav_${k}`])}</h3>
            <dl><div><dt>${esc(t.does)}</dt><dd>${esc(does)}</dd></div><div><dt>${esc(t.why_h)}</dt><dd>${esc(why)}</dd></div><div><dt>${esc(t.you)}</dt><dd class="home-tool__you">${esc(you)}</dd></div></dl>
            <span class="home-tool__open">${esc(t.open)} <i data-icon="arrowRight" data-size="24"></i></span>
          </div>
        </a>`;
      }).join("")}</div>
    </section>

    <section class="drill-banner console home-drill">
      <div><div class="kicker">Dengue Drill</div><h2>${esc(t.drill_head)}</h2><p>${esc(t.drill_sub)}</p>
        <a class="btn btn--light btn--sm" href="../drill/"><i data-icon="play" data-size="24"></i>${esc(t.drill_btn)}</a></div>
      <pixel-sprite sprite="frog" pose="watch" scale="3"></pixel-sprite>
    </section>`;

  el.querySelectorAll("[data-go]").forEach((a) => a.addEventListener("click", (e) => { if (e.ctrlKey || e.metaKey) return; e.preventDefault(); ctx.go(a.dataset.go, a.dataset.u ? { area: a.dataset.u } : {}); }));
  el.querySelector("#story-btn")?.addEventListener("click", () => ctx.set({ panel: "province", mode: "replay" }));
  el.querySelector("#dl-brief")?.addEventListener("click", () =>
    download("epilag_action_brief.md", briefMarkdown(shown, { t, lang, i18n, panelLabel: ctx.panelLabel, horizon, asOf }), "text/markdown"));

  const box = el.querySelector("#home-map");
  const tip = el.querySelector("#home-map-tip");
  const grids = await loadGrids("voxel_ph");
  const grid = panel === "province" ? grids.province : grids.region;
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
  })), { duration: 600 });
  const onLeave = () => { tip.hidden = true; map.highlight(null); };
  box.addEventListener("pointerleave", onLeave);
  const priorityList = el.querySelector("#home-priority");
  const onPriorityOver = (e) => map.highlight(e.target.closest("[data-u]")?.dataset.u ?? null);
  const onPriorityLeave = () => map.highlight(null);
  priorityList?.addEventListener("pointerover", onPriorityOver);
  priorityList?.addEventListener("pointerleave", onPriorityLeave);
  return () => { box.removeEventListener("pointerleave", onLeave); priorityList?.removeEventListener("pointerover", onPriorityOver); priorityList?.removeEventListener("pointerleave", onPriorityLeave); map.dispose(); };
}

function levelStat(level, key, value, t) {
  return `<div class="home-counts__level" data-lv="${LV[level]}"><span class="sq sq--round"></span><div><b>${count(value)}</b><span>${esc(t[`${key}_n`])}</span></div></div>`;
}

function replayStatus(t, horizon, rows) {
  const c = replayClaim(rows);
  return `<div class="home-state__eyebrow">${esc(t.then)}</div><p><b>${c.flagged} ${esc(t.of)} ${c.crossed}</b> ${esc(t.then_line.replace("{h}", horizon))}</p>`;
}

function quietStatus(t) {
  return `<div class="home-state__eyebrow">${esc(t.quiet)}</div><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${esc(t.replay_story)}</button>`;
}

function priorityRow(r, i, ctx) {
  return `<li><a class="home-priority__row" href="?page=unit&area=${encodeURIComponent(r.unit_id)}" data-u="${esc(r.unit_id)}" data-go="unit">
    <span class="home-priority__rank">${i + 1}</span><span class="home-priority__copy"><b>${esc(r.unit_name)}</b><small>${esc(ctx.t.cases)}: ${fmt(r.q50)} (${fmt(r.q10)}–${fmt(r.q90)})</small><small>${esc(ctx.t.peak)} ${fmtDay(r.peak_week, false)}</small></span>
    <span class="home-priority__level">${pill(ctx, r.level)}<small>${r.q50_per100k.toFixed(1)} ${esc(ctx.t.per100k)}</small></span>
  </a></li>`;
}

function briefRow(r, ctx) {
  const [when, d] = ctx.i18n.PLAYBOOK[ctx.lang][r.level][0];
  return `<div class="brief-row home-brief-row" data-lv="${LV[r.level]}"><div class="home-brief-row__area"><div class="brief-row__nm">${esc(r.unit_name)} ${pill(ctx, r.level)}</div>
    <div class="brief-row__meta">${esc(ctx.t.cases)}: <b>${fmt(r.q50)}</b> (${fmt(r.q10)}–${fmt(r.q90)}) · ${esc(ctx.t.peak)} ${fmtDay(r.peak_week, false)}</div></div>
    <div class="brief-row__next"><b>${esc(when)}:</b> ${esc(d)}<div class="brief-row__meta">${esc(ctx.t.prepare.replace("{n}", fmt(r.cases_high)))}</div></div></div>`;
}
