// Overview: areas to act on now (or the replay result), why weeks matter, the tools, the Drill, and the action brief.
import { LEVELS, briefMarkdown, briefTable, fmt, fmtDay, replayClaim } from "../logic.js";
import { cardTitle, count, download, downloadButton, esc, head, pill, LV } from "../ui.js";

const TOOL_ICON = { map: "forecastMap", unit: "areaDetail", budget: "actionPlan", public: "residents", qc: "barangay", proof: "didItWork" };
const STORY_ART = [["props", "cloud"], ["mosquito", "fly1"], ["props", "residents"], ["props", "hospital"]];

export function render(el, ctx) {
  const { t, lang, i18n, fc, fcH, horizon, mode } = ctx;
  const asOf = Math.max(...fcH.map((r) => r.week)), target = Math.max(...fcH.map((r) => r.target_week));
  const n = (lv) => fcH.filter((r) => r.level === lv).length;
  const nWarn = n(LEVELS[3]), nWatch = n(LEVELS[2]), nAbove = n(LEVELS[1]);

  let status;
  if (mode === "replay") {
    const c = replayClaim(fcH);
    status = `<div class="hero-card__then">${esc(t.then)}</div>
      <div class="hero-card__claim"><b>${c.flagged} ${esc(t.of)} ${c.crossed}</b> ${esc(t.then_line.replace("{h}", horizon))}</div>`;
  } else if (nWarn + nWatch === 0) {
    status = `<p class="hero-card__quiet">${esc(t.quiet)}</p>
      <button type="button" class="btn btn--light btn--sm" id="story-btn">${esc(t.replay_story)}</button>`;
  } else status = "";

  const rows = briefTable(fc, fcH);
  const act = rows.filter((r) => r.level === LEVELS[2] || r.level === LEVELS[3]).slice(0, 6);
  const shown = act.length ? act : rows.filter((r) => r.level === LEVELS[1]).slice(0, 3);

  el.innerHTML = `
    ${head(t.hello, `${horizon} ${t.weeks_ahead}`, `${t.as_of} ${fmtDay(asOf)} · ${t.for_week} ${fmtDay(target)} · ${ctx.panelLabel}`)}
    <div class="grid grid--home">
      <section class="hero-card surface tone-night tx-rain">
        <div class="kicker">${esc(t.act_now)}</div>
        <div class="hero-card__big">${count(nWarn + nWatch)}</div>
        <div class="chips">
          <span class="chip chip--night">${dotOf("outbreak warning")}${nWarn} ${esc(t.warning_n)}</span>
          <span class="chip chip--night">${dotOf("watch")}${nWatch} ${esc(t.watch_n)}</span>
          <span class="chip chip--night">${dotOf("above usual")}${nAbove} ${esc(t.above_n)}</span>
        </div>
        ${status}
        <a class="btn btn--light btn--sm hero-card__go" href="?page=map" data-go="map">${esc(t.open_map)} <i data-icon="arrowRight" data-size="24"></i></a>
        <pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="${nWarn ? "alert" : nWatch ? "search" : "sleepy"}" scale="4"></pixel-sprite>
      </section>
      <section class="card">
        ${cardTitle("alert", t.story_head)}
        <ol class="story">${t.story.map(([a, b], i) => `<li class="story__step${i === 0 ? " story__step--on" : ""}">
          <span class="story__art"><pixel-sprite sprite="${STORY_ART[i][0]}" pose="${STORY_ART[i][1]}" scale="${STORY_ART[i][0] === "props" ? 1 : 2}"></pixel-sprite></span>
          <b>${esc(a)}</b><span>${esc(b)}</span></li>`).join("")}</ol>
        <div class="callout story__note"><i data-icon="alert" data-size="24"></i>${esc(t.story_note)}</div>
      </section>
    </div>

    <h2 class="vsub">${esc(t.features_head)} <span>${esc(t.features_sub)}</span></h2>
    <div class="grid grid--3 feats">${Object.keys(TOOL_ICON).map((k) => {
      const [does, why, you] = i18n.FEATURES[lang][k];
      return `<a class="card feat" href="?page=${k}" data-go="${k}">
        <span class="feat__ic"><i data-icon="${TOOL_ICON[k]}" data-size="48"></i></span>
        <h3>${esc(t[`nav_${k}`])}</h3>
        <dl><dt>${esc(t.does)}</dt><dd>${esc(does)}</dd><dt>${esc(t.why_h)}</dt><dd>${esc(why)}</dd><dt>${esc(t.you)}</dt><dd class="feat__you">${esc(you)}</dd></dl>
        <span class="feat__open">${esc(t.open)} <i data-icon="arrowRight" data-size="24"></i></span></a>`;
    }).join("")}</div>

    <section class="drill-banner console">
      <div><div class="kicker">Dengue Drill</div><h2>${esc(t.drill_head)}</h2><p>${esc(t.drill_sub)}</p>
        <a class="btn btn--light btn--sm" href="../drill/"><i data-icon="play" data-size="24"></i>${esc(t.drill_btn)}</a></div>
      <pixel-sprite sprite="frog" pose="watch" scale="4"></pixel-sprite>
    </section>

    <section class="card">
      ${cardTitle("actionPlan", t.brief_head, t.brief_sub)}
      ${act.length ? "" : `<div class="callout"><i data-icon="check" data-size="24"></i>${esc(t.brief_empty)}</div>`}
      <div class="briefs">${shown.map((r) => {
        const [when, d] = i18n.PLAYBOOK[lang][r.level][0];
        return `<div class="brief-row" data-lv="${LV[r.level]}"><div><div class="brief-row__nm">${esc(r.unit_name)} ${pill(ctx, r.level)}</div>
          <div class="brief-row__meta">${esc(t.cases)}: <b>${fmt(r.q50)}</b> (${fmt(r.q10)}–${fmt(r.q90)}) · ${esc(t.peak)} ${fmtDay(r.peak_week, false)}</div></div>
          <div class="brief-row__next"><b>${esc(when)}:</b> ${esc(d)}<div class="brief-row__meta">${esc(t.prepare.replace("{n}", fmt(r.cases_high)))}</div></div></div>`;
      }).join("")}</div>
      ${shown.length ? downloadButton("dl-brief", t.download_brief) : ""}
    </section>`;

  el.querySelectorAll("[data-go]").forEach((a) => a.addEventListener("click", (e) => { if (e.ctrlKey || e.metaKey) return; e.preventDefault(); ctx.go(a.dataset.go); }));
  el.querySelector("#story-btn")?.addEventListener("click", () => ctx.set({ panel: "province", mode: "replay" }));
  el.querySelector("#dl-brief")?.addEventListener("click", () =>
    download("epilag_action_brief.md", briefMarkdown(shown, { t, lang, i18n, panelLabel: ctx.panelLabel, horizon, asOf }), "text/markdown"));
}

const dotOf = (lv) => `<span class="sq sq--round" data-lv="${LV[lv]}"></span>`;
