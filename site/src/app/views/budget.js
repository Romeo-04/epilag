// Action plan: budget, cases averted, spend by area, and the funded plan; costs and effects sit in a drawer.
import { allocate, fmt, toCsv } from "../logic.js";
import { barChart } from "../chart.js";
import { cardTitle, count, details, download, esc, hydrateCounts, tableHtml } from "../ui.js";

const A = "Clean-up drive + container covers", B = "Targeted fogging";
const inputs = { budget: 5_000_000, costA: 15, effA: [0.1, 0.5], costB: 25, effB: [0, 0.1] };

export function render(el, ctx) {
  const { t, labels, fc } = ctx;
  const actionName = (name) => name === A ? labels.clean_up : labels.fogging;
  const effField = (id, [lo, hi]) => `<div class="effect"><span class="field__label">${esc(labels.effect_short)}</span>
    <div class="effect__pair"><label>${esc(labels.low)}<input type="range" id="${id}-lo" min="0" max="0.8" step="0.05" value="${lo}"><output>${pct(lo)}</output></label>
    <label>${esc(labels.high)}<input type="range" id="${id}-hi" min="0" max="0.8" step="0.05" value="${hi}"><output>${pct(hi)}</output></label></div></div>`;

  el.innerHTML = `
    <div class="grid grid--plan">
      <section class="card plan-inputs">
        <label class="field"><span class="field__label">${esc(t.budget)}</span><input type="number" id="budget" min="0" step="500000" value="${inputs.budget}" inputmode="numeric"></label>
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
    <section class="card">${cardTitle("forecastMap", t.spend_chart)}<div id="spend" class="chart-box"></div></section>
    ${details(t.plan, `<div id="plan-table"></div>`)}`;

  let plan = [], disposeChart = null;

  function update() {
    const v = (id) => Number(el.querySelector(`#${id}`).value);
    Object.assign(inputs, { budget: Math.max(0, v("budget")), costA: Math.max(0.01, v("costA")), costB: Math.max(0.01, v("costB")),
      effA: [Math.min(v("effA-lo"), v("effA-hi")), Math.max(v("effA-lo"), v("effA-hi"))],
      effB: [Math.min(v("effB-lo"), v("effB-hi")), Math.max(v("effB-lo"), v("effB-hi"))] });
    el.querySelectorAll(".effect input").forEach((i) => { i.nextElementSibling.textContent = pct(Number(i.value)); });
    const actions = [
      { name: A, cost_per_person: inputs.costA, effect_low: inputs.effA[0], effect_central: (inputs.effA[0] + inputs.effA[1]) / 2, effect_high: inputs.effA[1], max_coverage: 0.3 },
      { name: B, cost_per_person: inputs.costB, effect_low: inputs.effB[0], effect_central: (inputs.effB[0] + inputs.effB[1]) / 2, effect_high: inputs.effB[1], max_coverage: 0.1 },
    ];
    plan = allocate(fc.filter((r) => [2, 4, 6, 8].includes(r.horizon)), inputs.budget, actions);
    const out = el.querySelector("#out");
    if (!plan.length) out.innerHTML = `<div class="card empty-state"><span class="empty-state__icon"><i data-icon="info" data-size="20"></i></span><div><b>${esc(labels.results)}</b><p>${esc(labels.no_funded)}</p></div></div>`;
    else {
      const sum = (k) => plan.reduce((s, r) => s + r[k], 0), mid = sum("averted_mid");
      out.innerHTML = `<section class="hero-card"><div class="kicker">${esc(t.averted)}</div><div class="hero-card__big">${count(mid)}</div>
        <div class="chips"><span class="chip chip--night">${fmt(sum("averted_low"))}–${fmt(sum("averted_high"))}</span><span class="chip chip--night">${esc(labels.per_case_short)}: ₱${mid ? fmt(sum("spend") / mid) : "–"}</span><span class="chip chip--night">${esc(t.people)}: ${fmt(sum("people_covered"))}</span></div>
        <pixel-sprite class="hero-card__sprite" sprite="props" pose="broom" scale="2"></pixel-sprite></section>`;
      hydrateCounts(out);
    }
    const byArea = new Map();
    for (const r of plan) { const a = byArea.get(r.unit_name) || { [A]: 0, [B]: 0, total: 0 }; a[r.action] += r.spend; a.total += r.spend; byArea.set(r.unit_name, a); }
    const top = [...byArea].sort((x, y) => y[1].total - x[1].total).slice(0, 12);
    disposeChart?.();
    disposeChart = top.length ? barChart(el.querySelector("#spend"), { categories: top.map(([n]) => n), mode: "stack", horizontal: true, fmt: (v) => `₱${short(v)}`,
      groups: [{ label: labels.clean_up, color: "#08754F", values: top.map(([, a]) => a[A]) }, { label: labels.fogging, color: "#F7C928", values: top.map(([, a]) => a[B]) }] }) : null;
    if (!top.length) el.querySelector("#spend").innerHTML = "";
    el.querySelector("#plan-table").innerHTML = tableHtml(plan, [[t.area, (r) => esc(r.unit_name)], [labels.action, (r) => esc(actionName(r.action))],
      [labels.spend, (r) => fmt(r.spend), "num"], [labels.people_covered, (r) => fmt(r.people_covered), "num"],
      [labels.cases_low, (r) => fmt(r.averted_low), "num"], [labels.cases_central, (r) => fmt(r.averted_mid), "num"],
      [labels.cases_high, (r) => fmt(r.averted_high), "num"]]);
  }
  el.querySelector(".plan-inputs").addEventListener("input", update);
  const savePlan = () => download("epilag_funded_plan.csv", toCsv(plan, [
    [t.area, (r) => r.unit_name], [labels.action, (r) => actionName(r.action)], [labels.spend, (r) => Math.round(r.spend)],
    [labels.people_covered, (r) => Math.round(r.people_covered)], [labels.cases_low, (r) => Math.round(r.averted_low)],
    [labels.cases_central, (r) => Math.round(r.averted_mid)], [labels.cases_high, (r) => Math.round(r.averted_high)]]), "text/csv");
  ctx.topDownload(t.download_plan, savePlan);
  update();
  return () => disposeChart?.();
}

const pct = (v) => `${Math.round(v * 100)}%`;
const short = (v) => (v >= 1e6 ? `${+(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${+(v / 1e3).toFixed(0)}k` : `${Math.round(v)}`);
