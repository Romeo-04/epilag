// For residents: a plain-language area status, DOH 4S actions, warning signs, and a shareable advisory.
import { fmtDay } from "../logic.js";
import { LV, areaSelect, cardTitle, esc, head, infoDisclosure, pill } from "../ui.js";

const DO_ART = { drop: ["props", "container"], shirt: ["props", "people"], hospital: ["props", "clinicBag"], bug: ["mosquito", "sleepy"] };
const MASCOT = { "outbreak warning": ["mosquito", "alert"], watch: ["mosquito", "search"], "above usual": ["frog", "watch"], normal: ["frog", "happy"] };

export function render(el, ctx) {
  const { t, labels, lang, i18n, fcH, horizon } = ctx;
  const P = i18n.PUBLIC[lang];
  const localScope = ctx.panel === "region_qc" && ctx.regionMeta ? new Set([ctx.regionMeta.id, ...(ctx.regionMeta.cities || [])]) : null;
  const names = [...fcH].filter((r) => !localScope || localScope.has(r.unit_id)).sort((a, b) => a.unit_name.localeCompare(b.unit_name));
  const unit = names.some((r) => r.unit_id === ctx.area) ? ctx.area : names[0].unit_id;
  const row = fcH.find((r) => r.unit_id === unit);
  const status = P.status[row.level].replace("{area}", row.unit_name).replace("{h}", horizon);
  const msg = P.msg.replace("{area}", row.unit_name).replace("{week}", fmtDay(row.target_week)).replace("{status}", status);
  const [sheet, pose] = MASCOT[row.level];

  el.innerHTML = `
    ${head(P.head, P.muted, P.sub)}
    <div class="unit-header"><div class="unit-pick">${areaSelect("area", P.pick, names, unit)}</div><span class="small muted">${esc(ctx.panelLabel)} · ${esc(t.for_week)} ${fmtDay(row.target_week)}</span></div>
    <div class="grid grid--public">
      <section class="hero-card hero-card--public" data-lv="${LV[row.level]}"><div class="kicker">${esc(row.unit_name)} · ${esc(t.for_week)} ${fmtDay(row.target_week)}</div><div>${pill(ctx, row.level)}</div>
        <p class="hero-card__status">${esc(status)}</p><pixel-sprite class="hero-card__sprite" sprite="${sheet}" pose="${pose}" scale="${sheet === "frog" ? 3 : 4}"></pixel-sprite></section>
      <section class="card">${cardTitle("alert", P.signs_head)}<ul class="signs">${P.signs.map((s) => `<li><span class="sq sq--round" data-lv="warning"></span>${esc(s)}</li>`).join("")}</ul></section>
    </div>
    <h2 class="vsub">${esc(P.do_head)}</h2>
    <div class="public-actions">${P.do.map(([ic, h, body]) => `<section class="card public-action"><span class="public-action__ic"><pixel-sprite sprite="${DO_ART[ic][0]}" pose="${DO_ART[ic][1]}" scale="${DO_ART[ic][0] === "props" ? 1 : 2}"></pixel-sprite></span><h3>${esc(h)}</h3><p>${esc(body)}</p></section>`).join("")}</div>
    <section class="card">${cardTitle("residents", P.share_head)}<div class="share"><p id="msg">${esc(msg)}</p><button type="button" class="btn btn--primary btn--sm" id="copy">${esc(labels.copy)}</button>${infoDisclosure(labels.about_this, `<p>${esc(P.note)}</p>`)}</div></section>`;

  el.querySelector("#area").addEventListener("change", (e) => ctx.set({ area: e.target.value }, { push: false }));
  el.querySelector("#copy").addEventListener("click", async (e) => {
    const b = e.currentTarget;
    try { await navigator.clipboard.writeText(msg); b.textContent = labels.copied; }
    catch { getSelection().selectAllChildren(el.querySelector("#msg")); }
  });
}
