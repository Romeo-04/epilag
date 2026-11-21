// Action plan: budget, cases averted, spend by area, and the funded plan; costs and effects sit in a drawer.
import { LEVELS, allocate, budgetCurve, curveAt, fmt, toCsv } from "../logic.js";
import { curveChart } from "../chart.js";
import { LV, LV_HEIGHT, cardTitle, count, details, download, esc, hydrateCounts, tableHtml } from "../ui.js";

const A = "Clean-up drive + container covers", B = "Targeted fogging";
const inputs = { priority: "level", budget: 5_000_000, costA: 15, effA: [0.1, 0.5], costB: 25, effB: [0, 0.1] };

export function render(el, ctx) {
  const { t, labels, fc, lang, i18n } = ctx;
  const trig = i18n.TRIGGERS[lang];
  // where the current forecast says to start each action: areas at its level or higher, worst first
  const fcH = ctx.fcH || [];
  const whereNow = (lv) => {
    const at = fcH.filter((r) => LV_HEIGHT[r.level] >= LV_HEIGHT[lv])
      .sort((a, b) => LV_HEIGHT[b.level] - LV_HEIGHT[a.level] || b.q50_per100k - a.q50_per100k);
    if (!at.length) return `<span class="todo__now todo__now--none">${esc(trig.now_none)}</span>`;
    if (at.length === fcH.length) return `<span class="todo__now">${esc(trig.now_all.replace("{n}", at.length))}</span>`;
    const names = at.slice(0, 3).map((r) => r.unit_name).join(", ") + (at.length > 3 ? ` ${trig.now_more.replace("{n}", at.length - 3)}` : "");
    return `<span class="todo__now">${esc(trig.now_some.replace("{n}", at.length).replace("{names}", names))}</span>`;
  };
  const actionName = (name) => name === A ? labels.clean_up : labels.fogging;
  const effField = (id, [lo, hi]) => `<div class="effect"><span class="field__label">${esc(labels.effect_short)}</span>
    <div class="effect__pair"><label>${esc(labels.low)}<input type="range" id="${id}-lo" min="0" max="0.8" step="0.05" value="${lo}"><output>${pct(lo)}</output></label>
    <label>${esc(labels.high)}<input type="range" id="${id}-hi" min="0" max="0.8" step="0.05" value="${hi}"><output>${pct(hi)}</output></label></div></div>`;

  el.innerHTML = `
    <div class="grid grid--plan">
      <section class="card plan-inputs">
        <label class="field"><span class="field__label">${esc(t.budget)}</span><input type="number" id="budget" min="0" step="500000" value="${inputs.budget}" inputmode="numeric"></label>
        <label class="field"><span class="field__label">${esc(trig.priority)}</span><select id="priority">${["level", "value"].map((v, i) => `<option value="${v}"${inputs.priority === v ? " selected" : ""}>${esc(trig.priority_opts[i])}</option>`).join("")}</select></label>
        <details class="plan-assume"><summary>${esc(labels.assumptions)}</summary><div class="plan-assume__body">
          <div class="kicker">${esc(labels.clean_up)}</div>
          <label class="field"><span class="field__label">${esc(labels.cost_short)}</span><input type="number" id="costA" step="1" min="1" value="${inputs.costA}"></label>${effField("effA", inputs.effA)}
          <div class="kicker">${esc(labels.fogging)}</div>
          <label class="field"><span class="field__label">${esc(labels.cost_short)}</span><input type="number" id="costB" step="1" min="1" value="${inputs.costB}"></label>${effField("effB", inputs.effB)}
          <p class="small muted">${esc(t.plan_gives)}</p>
        </div></details>
      </section>
      <div class="plan-out" id="out"></div>
    </div>
    <section class="card area-plan">${cardTitle("check", trig.plan_head)}<p class="small muted">${esc(trig.plan_sub)}</p><div id="area-plan"></div><p class="small muted" id="fog-note" style="margin-top:10px"></p></section>
    <section class="card">${cardTitle("actionPlan", labels.curve_head)}<p class="small muted">${esc(labels.curve_sub)}</p>
      <div id="curve" class="chart-box"></div><p class="small" id="curve-note" style="margin-top:10px"></p><p class="small muted">${esc(labels.curve_scenario)}</p></section>
    <section class="card triggers">${cardTitle("check", trig.head)}<p class="small muted">${esc(trig.sub)}</p>
      <ol class="todo todo--3"><li class="todo__row todo__head">${trig.cols.map((c) => `<span>${esc(c)}</span>`).join("")}</li>
        ${trig.rows.map(([lv, a, w]) => `<li class="todo__row"><span class="todo__when"><span class="sq sq--round" data-lv="${LV[lv]}"></span> ${esc(ctx.levelName(lv))}</span><b>${esc(a)}</b><span>${esc(w)}</span>${whereNow(lv)}</li>`).join("")}</ol>
      <p class="small muted">${esc(trig.note)}</p></section>
    ${details(t.plan, `<div id="plan-table"></div>`)}`;

  let plan = [], disposeCurve = null;
  // each area only gets the actions its current alert level calls for (the "When to act" table)
  const levels = Object.fromEntries(fcH.map((r) => [r.unit_id, r.level]));

  function update() {
    const v = (id) => Number(el.querySelector(`#${id}`).value);
    Object.assign(inputs, { priority: el.querySelector("#priority").value, budget: Math.max(0, v("budget")), costA: Math.max(0.01, v("costA")), costB: Math.max(0.01, v("costB")),
      effA: [Math.min(v("effA-lo"), v("effA-hi")), Math.max(v("effA-lo"), v("effA-hi"))],
      effB: [Math.min(v("effB-lo"), v("effB-hi")), Math.max(v("effB-lo"), v("effB-hi"))] });
    el.querySelectorAll(".effect input").forEach((i) => { i.nextElementSibling.textContent = pct(Number(i.value)); });
    const actions = [
      { name: A, cost_per_person: inputs.costA, effect_low: inputs.effA[0], effect_central: (inputs.effA[0] + inputs.effA[1]) / 2, effect_high: inputs.effA[1], max_coverage: 0.3 },
      { name: B, cost_per_person: inputs.costB, effect_low: inputs.effB[0], effect_central: (inputs.effB[0] + inputs.effB[1]) / 2, effect_high: inputs.effB[1], max_coverage: 0.1, min_level: "watch" },
    ];
    const fc4 = fc.filter((r) => [2, 4, 6, 8].includes(r.horizon));
    plan = allocate(fc4, inputs.budget, actions, levels, inputs.priority);
    drawCurve(budgetCurve(fc4, actions, levels, inputs.priority));
    drawAreaPlan();
    el.querySelector("#fog-note").textContent = fogNote(actions);
    const out = el.querySelector("#out");
    if (!plan.length) out.innerHTML = `<div class="card empty-state"><span class="empty-state__icon"><i data-icon="info" data-size="20"></i></span><div><b>${esc(labels.results)}</b><p>${esc(labels.no_funded)}</p></div></div>`;
    else {
      const sum = (k) => plan.reduce((s, r) => s + r[k], 0), mid = sum("averted_mid");
      out.innerHTML = `<section class="hero-card"><div class="kicker">${esc(t.averted)}</div><div class="hero-card__big">${count(mid)}</div>
        <div class="chips"><span class="chip chip--night">${fmt(sum("averted_low"))}–${fmt(sum("averted_high"))}</span><span class="chip chip--night">${esc(labels.per_case_short)}: ₱${mid ? fmt(sum("spend") / mid) : "–"}</span><span class="chip chip--night">${esc(t.people)}: ${fmt(sum("people_covered"))}</span></div>
        <pixel-sprite class="hero-card__sprite" sprite="props" pose="broom" scale="2"></pixel-sprite></section>`;
      hydrateCounts(out);
    }
    el.querySelector("#plan-table").innerHTML = tableHtml(plan, [[t.area, (r) => esc(r.unit_name)], [labels.action, (r) => esc(actionName(r.action))],
      [labels.spend, (r) => fmt(r.spend), "num"], [labels.people_covered, (r) => fmt(r.people_covered), "num"],
      [labels.cases_low, (r) => fmt(r.averted_low), "num"], [labels.cases_central, (r) => fmt(r.averted_mid), "num"],
      [labels.cases_high, (r) => fmt(r.averted_high), "num"]]);
  }
  // the plan grouped by alert level, worst first. Each group names the other actions its level calls for once (the
  // uncosted rows of the "When to act" table), lists its funded areas with a spend bar and the cases averted, and
  // folds its unfunded areas into one line. Normal areas only appear when they get money.
  function drawAreaPlan() {
    const by = new Map();
    for (const r of plan) {
      const a = by.get(r.unit_id) || { spend: { [A]: 0, [B]: 0 }, total: 0, lo: 0, mid: 0, hi: 0 };
      a.spend[r.action] += r.spend; a.total += r.spend; a.lo += r.averted_low; a.mid += r.averted_mid; a.hi += r.averted_high;
      by.set(r.unit_id, a);
    }
    const need = fcH.filter((r) => r.level !== LEVELS[0]), maxTotal = Math.max(1, ...[...by.values()].map((a) => a.total));
    const [cArea, , cFunded, cAverted] = trig.plan_cols;
    const summary = need.length ? labels.plan_summary.replace("{funded}", need.filter((r) => by.has(r.unit_id)).length).replace("{n}", need.length) : labels.plan_summary_none;
    const pctOf = (v) => `${((v / maxTotal) * 100).toFixed(2)}%`;
    const row = (r) => { const a = by.get(r.unit_id);
      const parts = [[A, a.spend[A]], [B, a.spend[B]]].filter(([, v]) => v > 0);
      const detail = parts.map(([n, v]) => `${actionName(n)} ₱${short(v)}`).join(" · ");
      return `<li class="ap__row"><b class="ap__name">${esc(r.unit_name)}</b>
        <span class="ap__bar" role="img" aria-label="${esc(detail)}" title="${esc(detail)}">${parts.map(([n, v]) => `<i class="ap__seg ap__seg--${n === A ? "clean" : "fog"}" style="width:${pctOf(v)}"></i>`).join("")}</span>
        <span class="ap__spend nums">₱${short(a.total)}</span>
        <span class="ap__cases"><b class="nums">${fmt(a.mid)}</b><small class="nums">${fmt(a.lo)}–${fmt(a.hi)}</small></span></li>`; };
    const groups = LEVELS.slice().reverse().map((lv) => {
      const at = fcH.filter((r) => r.level === lv);
      const funded = at.filter((r) => by.has(r.unit_id)).sort((x, y) => by.get(y.unit_id).total - by.get(x.unit_id).total);
      const unfunded = lv === LEVELS[0] ? [] : at.filter((r) => !by.has(r.unit_id)).sort((x, y) => y.q50_per100k - x.q50_per100k);
      if (!funded.length && !unfunded.length) return "";
      const n = funded.length + unfunded.length;
      const due = trig.rows.filter(([l], i) => !trig.costed.includes(i) && LEVELS.indexOf(l) <= LEVELS.indexOf(lv)).map(([, a]) => esc(a));
      return `<section class="level-list ap__group" data-lv="${LV[lv]}">
        <header class="level-list__head"><span class="sq sq--round"></span><h3>${esc(ctx.levelName(lv))}</h3><span class="level-list__n nums">${esc(n === 1 ? labels.plan_area_one : labels.plan_areas.replace("{n}", n))}</span></header>
        ${due.length ? `<p class="ap__also"><span>${esc(labels.plan_also)}</span>${due.join(" · ")}</p>` : ""}
        ${funded.length ? `<ul class="ap__rows">${funded.map(row).join("")}</ul>` : ""}
        ${unfunded.length ? `<p class="ap__unfunded">${esc(labels.plan_unfunded_list.replace("{names}", unfunded.map((r) => r.unit_name).join(", ")))}</p>` : ""}
      </section>`;
    }).join("");
    el.querySelector("#area-plan").innerHTML = `<div class="ap">
      <div class="ap__top"><p class="ap__summary">${esc(summary)}</p>
        <span class="ap__legend"><span><i class="ap__key ap__seg--clean"></i>${esc(labels.clean_up)}</span><span><i class="ap__key ap__seg--fog"></i>${esc(labels.fogging)}</span></span></div>
      ${plan.length ? `<div class="ap__cols" aria-hidden="true"><span>${esc(cArea)}</span><span>${esc(cFunded)}</span><span>${esc(cAverted)}</span></div>` : ""}
      ${groups}</div>`;
  }
  // why the plan funds no fogging, or "" when it funds some (app/streamlit_app.py fog_note)
  function fogNote([clean, fog]) {
    if (plan.some((r) => r.action === B)) return "";
    if (!fcH.some((r) => LEVELS.indexOf(r.level) >= LEVELS.indexOf(fog.min_level))) return trig.fog_level;
    if (!(fog.effect_central > 0)) return trig.fog_zero;
    const x = (clean.effect_central / clean.cost_per_person) / (fog.effect_central / fog.cost_per_person);
    return trig.fog_ratio.replace("{x}", x >= 10 ? Math.round(x) : x.toFixed(1));
  }
  function drawCurve(curve) {
    const full = curve[curve.length - 1].spend, b = inputs.budget;
    // past this budget every extra peso buys less than half as much as the first: the curve's bend, which the chart
    // should show. With the worst level funded first the slope can rise again, so it is the last point above half.
    const slope = (i) => (curve[i].averted_mid - curve[i - 1].averted_mid) / (curve[i].spend - curve[i - 1].spend);
    let last = 1;
    for (let i = 2; i < curve.length; i++) if (slope(i) >= slope(1) / 2) last = i;
    const hi = last < curve.length - 1 ? last + 1 : -1, half = hi > 0 ? curve[last].spend : full;
    // show the bend and four times the budget (at least ₱20M), but not far past the point where every area is funded
    const xMax = Math.max(Math.min(Math.max(4 * b, 20e6, half * 1.25), full * 1.1), b * 1.1, 1e6);
    const xs = [...new Set([...Array.from({ length: 81 }, (_, i) => (xMax * i) / 80), ...curve.map((p) => p.spend).filter((v) => v < xMax)])].sort((a, c) => a - c);
    const pts = xs.map((v) => curveAt(curve, v)), now = curveAt(curve, b);
    disposeCurve?.();
    disposeCurve = curveChart(el.querySelector("#curve"), { x: xs, y: pts.map((p) => p.averted_mid), lo: pts.map((p) => p.averted_low), hi: pts.map((p) => p.averted_high),
      color: "#08754F", xFmt: (v) => `₱${short(v)}`, fmt: (v) => fmt(v), tipTitle: (v) => `₱${short(v)}`,
      mark: { x: b, label: `${labels.curve_you}: ${fmt(now.averted_mid)}` }, labels: { line: labels.curve_line, band: labels.curve_band } });
    const first = curveAt(curve, 1e6).averted_mid, next = curveAt(curve, b + 1e6).averted_mid - now.averted_mid;
    const bend = hi > 0 ? ` ${labels.curve_half.replace("{x}", `₱${short(half)}`)}` : "";
    el.querySelector("#curve-note").textContent = `${labels.curve_first.replace("{n}", fmt(first))}${bend} ${b >= full ? labels.curve_full : labels.curve_next.replace("{n}", fmt(next))}`;
  }
  el.querySelector(".plan-inputs").addEventListener("input", update);
  const savePlan = () => download("epilag_funded_plan.csv", toCsv(plan, [
    [t.area, (r) => r.unit_name], [trig.plan_cols[1], (r) => ctx.levelName(levels[r.unit_id] || LEVELS[0])], [labels.action, (r) => actionName(r.action)], [labels.spend, (r) => Math.round(r.spend)],
    [labels.people_covered, (r) => Math.round(r.people_covered)], [labels.cases_low, (r) => Math.round(r.averted_low)],
    [labels.cases_central, (r) => Math.round(r.averted_mid)], [labels.cases_high, (r) => Math.round(r.averted_high)]]), "text/csv");
  ctx.topDownload(t.download_plan, savePlan);
  update();
  return () => { disposeCurve?.(); };
}

const pct = (v) => `${Math.round(v * 100)}%`;
const short = (v) => (v >= 1e6 ? `${+(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${+(v / 1e3).toFixed(0)}k` : `${Math.round(v)}`);
