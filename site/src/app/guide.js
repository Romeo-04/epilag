// Onboarding guide: a short spotlight tour of the Overview that says what each part shows and how to read it,
// in English and Filipino. It opens by itself once per device, and any time from "How to use" in the top bar.
// The page behind it is made inert while it is open; Esc closes it and the arrow keys step through it.
import { icon } from "../lib/icons.js";
import { esc } from "./ui.js";
import "./guide.css";

// main.js reads the same key to decide whether to open the guide on a first visit. It is set as soon as the guide
// opens, so a reload half-way through does not bring it back.
function remember() { try { localStorage.setItem("el-guide", "done"); } catch { /* storage may be blocked */ } }

const UI = {
  en: { label: "How to use EpiLag-PH", start: "Start the tour", skip: "Skip", back: "Back", next: "Next", finish: "Finish",
    close: "Close the guide", step: "Step {i} of {n}", open: "Open {page}" },
  fil: { label: "Paano gamitin ang EpiLag-PH", start: "Simulan ang tour", skip: "Laktawan", back: "Bumalik", next: "Susunod", finish: "Tapos na",
    close: "Isara ang gabay", step: "Hakbang {i} sa {n}", open: "Buksan ang {page}" },
};

const b = (s) => `<b>${esc(s)}</b>`;
const lvRow = (c, level, key, text) => `<li><span class="lv" data-lv="${key}">${esc(c.levelName(level))}</span><span>${text}</span></li>`;

/** A small, schematic forecast chart: reported cases up to now, then the forecast and its likely range, against the epidemic line. */
const art = (now) => `<svg class="guide__art" viewBox="0 0 320 132" aria-hidden="true" focusable="false">
  <line x1="8" x2="312" y1="118" y2="118" stroke="#CFD2C4"/>
  <polygon points="184,52 220,34 260,24 300,20 300,78 260,70 220,62 184,52" fill="#08754F" fill-opacity=".16"/>
  <path d="M8 64 C 70 60, 130 72, 190 66 S 280 58, 312 61" fill="none" stroke="#F04B2A" stroke-width="1.6" stroke-dasharray="6 5"/>
  <polyline points="8,108 30,104 52,106 74,98 96,92 118,86 140,76 162,62 184,52" fill="none" stroke="#071711" stroke-width="2.2" stroke-linejoin="round"/>
  <line x1="184" x2="184" y1="16" y2="118" stroke="#63706A" stroke-dasharray="2 3"/>
  <text x="188" y="14" font-size="10" fill="#4A5A51" font-weight="700">${esc(now)}</text>
  <g stroke="#08754F" stroke-width="1.6"><line x1="220" x2="220" y1="34" y2="62"/><line x1="260" x2="260" y1="24" y2="70"/><line x1="300" x2="300" y1="20" y2="78"/></g>
  <g fill="#08754F" stroke="#fff" stroke-width="1.5"><circle cx="220" cy="47" r="4"/><circle cx="260" cy="45" r="4"/><circle cx="300" cy="47" r="4"/></g>
</svg>`;

const key = (kind) => `<span class="guide__key guide__key--${kind}" aria-hidden="true"></span>`;

/** The tour, in the user's language. Step 0 is the welcome; the last step explains how to read a forecast. */
function steps(c) {
  const { t, labels } = c;
  const mobile = matchMedia("(max-width: 720px)").matches;
  const nav = mobile ? "#mobile-menu" : "#tabs";
  const pages = ["map", "unit", "budget", "public", "qc", "proof", "about"];
  if (c.lang === "fil") {
    const what = { map: "lahat ng lugar nang sabay.", unit: "ang forecast chart, checklist at mga dahilan ng forecast para sa isang lugar.",
      budget: "kung saan pinakamaraming kasong maiiwasan ng budget.", public: "simpleng mensaheng maibabahagi, sa Ingles at Filipino.",
      qc: "aling barangay ng Quezon City ang uunahin.", proof: "gaano kahusay ang mga nakaraang forecast.", about: "pinagmulan ng datos at ang hindi kaya ng tool." };
    return [
      { title: "Maligayang pagdating sa EpiLag-PH",
        body: `<p>Nagbibigay ang EpiLag-PH ng forecast ng kaso ng dengue 2–8 linggo nang maaga para sa bawat lugar. Sinasabi rin nito kung aling mga lugar ang kailangang kumilos at kung ano ang gagawin.</p>
          <p>Ipapakita ng maikling tour na ito kung nasaan ang lahat at paano ito basahin. Mga isang minuto lang.</p>` },
      { target: "#ctx", title: "Piliin ang titingnan",
        body: `<ul><li>${b(labels.region)} at ${b(labels.province_city)}: ang lugar. Iwan sa ${b(labels.all_philippines)} para makita ang buong bansa.</li>
          <li>${b(t.mode)}: ang ${b(t.mode_latest)} ay gumagamit ng pinakabagong datos. Ang ${b(t.mode_replay)} ay nagpapakita ng sinabi ng EpiLag-PH noon, para maikumpara sa talagang nangyari.</li>
          <li>${b(t.horizon)}: gaano kalayo ang titingnan, 2 hanggang 8 linggo. Mas malayo, mas maagang babala, pero mas malawak ang saklaw.</li></ul>
          <p class="guide__note">Hanggang Enero 2021 lang ang datos ng probinsya, kaya pagbabalik-tanaw ang bukas na view ng mga probinsya.</p>` },
      { target: '[data-guide="status"]', title: "Dito magsimula: aling lugar ang kailangang kumilos",
        body: `<p>Bawat lugar ay may isa sa apat na antas ng alerto, batay sa forecast nito at sa sarili nitong threshold ng epidemya:</p>
          <ul class="guide__levels">${lvRow(c, "outbreak warning", "warning", "Lampas na sa threshold ang forecast. Kumilos na.")}
          ${lvRow(c, "watch", "watch", "Maaaring umabot sa threshold: ang itaas ng malamang na saklaw ay lampas na. Maghanda.")}
          ${lvRow(c, "above usual", "above", "Mas maraming kaso kaysa karaniwan sa panahong ito ng taon. Patuloy na magbantay.")}
          ${lvRow(c, "normal", "normal", "Karaniwang pagbabantay.")}</ul>
          <p>Ang malaking numero ay ang bilang ng lugar na nasa bantayan o babala.</p>` },
      { target: '[data-guide="trend"]', title: "Saan papunta ang kaso",
        body: `<p>Ang abong bar ay ang kabuuang kasong naiulat sa pinakahuling linggo. Ang mga berdeng bar ay ang forecast para sa mga susunod na linggo; ang madilim na berde ay ang pinili mong ${b(t.horizon)}.</p>
          <p>Ikinukumpara ng porsyento ang forecast na iyon sa ngayon.</p>` },
      { target: '[data-guide="rising"]', title: labels.rising,
        body: `<p>Mga lugar na pinakamalaki ang itataas ng forecast mula sa huling naiulat na linggo. Ipinapakita ang bawat isa bilang kaso ngayon → forecast.</p>
          <p>Puwedeng maliit pa rin ang bilang kahit malaki ang porsyento, kaya tingnan din ang antas ng alerto (ang may kulay na tuldok). Piliin ang lugar para makita ang detalye.</p>` },
      { target: '[data-guide="do"]', title: labels.do_week,
        body: `<p>Ang mga lugar na pinakakailangang tutukan, kasama ang hakbang na angkop sa antas ng alerto nito. Piliin ang isa para sa buong checklist.</p>
          <p>Gamitin ang ${b(labels.download)} sa itaas para mag-save ng isang pahinang buod ng aksyon na maibabahagi.</p>` },
      { target: '[data-guide="map"]', title: t.nav_map,
        body: `<p>Ipinapakita ng kulay at taas ang antas ng alerto: kapag mas mataas at mas pula, mas apurahan.</p>
          <p>Ituro ang lugar para makita ang forecast at ${b(t.range.toLowerCase())}. Piliin ito para buksan ang detalye.</p>` },
      { target: '[data-guide="priority"]', title: t.rank,
        body: `<p>Nakaayos ang mga lugar ayon sa forecast na kaso bawat 100,000 tao, para patas ang paghahambing ng maliit na probinsya at malaking lungsod.</p>` },
      { target: nav, noScroll: true, title: "Tumingin nang mas malalim",
        body: `${mobile ? "<p>Buksan ang menu para sa iba pang pahina:</p>" : ""}<ul>${pages.map((p) => `<li>${b(t[`nav_${p}`])}: ${what[p]}</li>`).join("")}</ul>` },
      { target: "#guide-top", title: "Ulitin ang tour anumang oras",
        body: `<p>Isang beses lang kusang bubukas ang tour na ito sa device na ito. Para makita ulit, ${mobile ? `pindutin ang ${b("?")} (${esc(labels.guide)})` : `piliin ang ${b(labels.guide)}`} sa itaas ng anumang pahina.</p>` },
      { title: "Paano basahin ang forecast", wide: true,
        body: `${art(labels.now)}<ul class="guide__legend">
          <li>${key("actual")}<span>${b(t.actual)}: ang iniulat ng mga klinika at ospital bawat linggo.</span></li>
          <li>${key("fc")}<span>${b(t.fcnow)}: ang gitnang tantya para sa bawat linggo sa hinaharap.</span></li>
          <li>${key("band")}<span>${b(t.range)}: ginawa ito para masaklaw ang totoong bilang mga 8 sa bawat 10 beses. Kapag mas malapad, mas hindi tiyak.</span></li>
          <li>${key("epi")}<span>${b(t.epi_line)}: ang karaniwang bilang para sa linggong ito ng taon, dagdag ang palugit (mean + 2 SD ng mga nakaraang taon). Kapag lampas dito, outbreak na.</span></li></ul>
          <p>Kapag ang gitnang tantya ay lampas sa pulang linya, ${b(c.levelName("outbreak warning"))} ito. Kapag ang itaas lang ng saklaw ang lampas, ${b(c.levelName("watch"))}.</p>
          <p class="guide__note">Gabay ang forecast, hindi pangako: gamitin ito kasama ng lokal na ulat at sariling pagpapasya.</p>` },
    ];
  }
  const what = { map: "every area at once.", unit: "one area's forecast chart, checklist and the reasons behind the forecast.",
    budget: "where a budget prevents the most cases.", public: "a plain message to share, in English and Filipino.",
    qc: "which Quezon City barangays to prioritise.", proof: "how well past forecasts did.", about: "the data sources and what the tool cannot do." };
  return [
    { title: "Welcome to EpiLag-PH",
      body: `<p>EpiLag-PH forecasts dengue cases 2–8 weeks ahead for each area. It also says which areas need action and what to do.</p>
        <p>This short tour shows where everything is and how to read it. It takes about a minute.</p>` },
    { target: "#ctx", title: "Choose what to look at",
      body: `<ul><li>${b(labels.region)} and ${b(labels.province_city)}: the area. Leave Region on ${b(labels.all_philippines)} to see the whole country.</li>
        <li>${b(t.mode)}: ${b(t.mode_latest)} uses the newest data. ${b(t.mode_replay)} shows what EpiLag-PH said at the time, so you can check it against what happened.</li>
        <li>${b(t.horizon)}: how far ahead to look, 2 to 8 weeks. Further ahead gives earlier warning, but a wider range.</li></ul>
        <p class="guide__note">Province data ends in January 2021, so provinces open as a replay.</p>` },
    { target: '[data-guide="status"]', title: "Start here: which areas need action",
      body: `<p>Each area gets one of four alert levels, from its forecast and its own epidemic threshold:</p>
        <ul class="guide__levels">${lvRow(c, "outbreak warning", "warning", "The forecast is above the threshold. Act now.")}
        ${lvRow(c, "watch", "watch", "The forecast could reach the threshold: the top of its likely range is above it. Get ready.")}
        ${lvRow(c, "above usual", "above", "More cases than usual for this time of year. Keep watch.")}
        ${lvRow(c, "normal", "normal", "Routine surveillance.")}</ul>
        <p>The big number counts the areas on watch or warning.</p>` },
    { target: '[data-guide="trend"]', title: "Where cases are heading",
      body: `<p>The grey bar is all cases reported in the latest week. The green bars are the forecasts for the weeks ahead; the dark one is the ${b(t.horizon.toLowerCase())} you chose.</p>
        <p>The percentage compares that forecast with now.</p>` },
    { target: '[data-guide="rising"]', title: labels.rising,
      body: `<p>The areas whose forecast rises most above their latest reported week, shown as cases now → forecast.</p>
        <p>A big percentage can still be a small number of cases, so check the alert level (the coloured dot) too. Select an area to see its details.</p>` },
    { target: '[data-guide="do"]', title: labels.do_week,
      body: `<p>The areas that need attention most, each with the step that fits its alert level. Select one for the full checklist.</p>
        <p>Use ${b(labels.download)} at the top to save a one-page action brief to share.</p>` },
    { target: '[data-guide="map"]', title: t.nav_map,
      body: `<p>Colour and height show the alert level: the taller and redder an area, the more urgent.</p>
        <p>Point at an area to see its forecast and ${b(t.range.toLowerCase())}. Select it to open its details.</p>` },
    { target: '[data-guide="priority"]', title: t.rank,
      body: `<p>Areas ranked by forecast cases per 100,000 people, so a small province and a big city can be compared fairly.</p>` },
    { target: nav, noScroll: true, title: "Go deeper",
      body: `${mobile ? "<p>Open the menu for the other pages:</p>" : ""}<ul>${pages.map((p) => `<li>${b(t[`nav_${p}`])}: ${what[p]}</li>`).join("")}</ul>` },
    { target: "#guide-top", title: "Replay this tour any time",
      body: `<p>This tour opens by itself only once on this device. To see it again, ${mobile ? `tap the ${b("?")} button (${esc(labels.guide)})` : `select ${b(labels.guide)}`} at the top of any page.</p>` },
    { title: "How to read a forecast", wide: true,
      body: `${art(labels.now)}<ul class="guide__legend">
        <li>${key("actual")}<span>${b(t.actual)}: what clinics and hospitals reported each week.</span></li>
        <li>${key("fc")}<span>${b(t.fcnow)}: the middle estimate for each week ahead.</span></li>
        <li>${key("band")}<span>${b(t.range)}: built to hold the real count about 8 times in 10. The wider it is, the less certain the forecast.</span></li>
        <li>${key("epi")}<span>${b(t.epi_line)}: the usual count for this week of the year, plus a margin (mean + 2 SD of earlier years). Above it counts as an outbreak.</span></li></ul>
        <p>If the middle estimate is above the red line, the area is on ${b(c.levelName("outbreak warning"))}. If only the top of the range is, it is on ${b(c.levelName("watch"))}.</p>
        <p class="guide__note">A forecast is a guide, not a promise: use it with local reports and your own judgement.</p>` },
  ];
}

const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), Math.max(lo, hi));
const M = 12, GAP = 14, PAD = 6;

/** Wait (up to `ms`) for a visible element: the Overview renders its cards after the data loads. */
function waitFor(sel, ms = 8000) {
  return new Promise((done) => {
    const t0 = performance.now();
    const tick = () => {
      const el = document.querySelector(sel);
      if (el && el.getBoundingClientRect().height > 0) return done(el);
      if (performance.now() - t0 > ms) return done(null);
      setTimeout(tick, 60);
    };
    tick();
  });
}

let open = false;
/**
 * Start the guide. `c` = { lang, t, labels, levelName, go(page), returnTo? }. The caller makes sure the Overview is showing.
 * Resolves when the guide closes.
 */
export function startGuide(c) {
  if (open) return Promise.resolve();
  open = true;
  remember();
  const S = steps(c), n = S.length - 1, ui = UI[c.lang] || UI.en;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const mobile = () => matchMedia("(max-width: 720px)").matches;
  const opener = c.returnTo || document.activeElement;

  const root = document.createElement("div");
  root.className = "guide";
  root.setAttribute("role", "dialog");
  root.setAttribute("aria-modal", "true");
  root.setAttribute("aria-labelledby", "guide-title");
  root.setAttribute("aria-describedby", "guide-body");
  root.innerHTML = `<div class="guide__catch"></div><div class="guide__spot" aria-hidden="true"></div><div class="guide__card" id="guide-card"></div>`;
  const spot = root.querySelector(".guide__spot"), card = root.querySelector(".guide__card");
  const hidden = [...document.body.children].filter((e) => !e.inert);
  document.body.append(root);
  document.body.classList.add("guide-open");
  hidden.forEach((e) => { e.inert = true; });

  let i = 0, target = null, raf = 0, token = 0, finish;
  const closed = new Promise((r) => { finish = r; });

  function cardHtml(s) {
    const first = i === 0, last = i === n;
    const btn = (act, label, primary) => `<button type="button" class="btn btn--sm ${primary ? "btn--primary" : "btn--ghost"}" data-act="${act}">${esc(label)}</button>`;
    return `<div class="guide__head"><span class="guide__step">${esc(first ? ui.label : ui.step.replace("{i}", i).replace("{n}", n))}</span>
        <button type="button" class="guide__close" data-act="close" aria-label="${esc(ui.close)}">${icon("close", { size: 18 })}</button></div>
      <h2 class="guide__title" id="guide-title" tabindex="-1">${esc(s.title)}</h2>
      <div class="guide__body" id="guide-body">${s.body}</div>
      <div class="guide__foot">
        ${first ? "" : `<span class="guide__dots" aria-hidden="true">${Array.from({ length: n }, (_, k) => `<i${k + 1 === i ? ' class="on"' : ""}></i>`).join("")}</span>`}
        <span class="guide__btns">${first ? btn("close", ui.skip) + btn("next", ui.start, true)
          : last ? btn("back", ui.back) + btn("area", ui.open.replace("{page}", c.t.nav_unit)) + btn("close", ui.finish, true)
          : btn("back", ui.back) + btn("next", ui.next, true)}</span>
      </div>`;
  }

  function layout() {
    raf = 0;
    if (!root.isConnected) return;
    root.classList.toggle("guide--center", !target);
    let r;
    if (target) {
      const t = target.getBoundingClientRect();
      r = { top: t.top - PAD, left: t.left - PAD, width: t.width + 2 * PAD, height: t.height + 2 * PAD };
    } else r = { top: innerHeight / 2, left: innerWidth / 2, width: 0, height: 0 };
    Object.assign(spot.style, { top: `${r.top}px`, left: `${r.left}px`, width: `${r.width}px`, height: `${r.height}px` });
    if (mobile()) { card.style.top = ""; card.style.left = ""; return; } // docked as a bottom sheet by CSS
    const vw = document.documentElement.clientWidth, vh = innerHeight, cw = card.offsetWidth, ch = card.offsetHeight;
    let top, left;
    if (!target) { top = (vh - ch) / 2; left = (vw - cw) / 2; }
    else {
      const cx = clamp(r.left + r.width / 2 - cw / 2, M, vw - cw - M);
      if (r.top + r.height + GAP + ch <= vh - M) { top = r.top + r.height + GAP; left = cx; }
      else if (r.top - GAP - ch >= M) { top = r.top - GAP - ch; left = cx; }
      else if (r.left + r.width + GAP + cw <= vw - M) { left = r.left + r.width + GAP; top = clamp(r.top, M, vh - ch - M); }
      else if (r.left - GAP - cw >= M) { left = r.left - GAP - cw; top = clamp(r.top, M, vh - ch - M); }
      else { left = cx; top = vh - ch - M; }
    }
    card.style.top = `${Math.max(M, top)}px`;
    card.style.left = `${left}px`;
  }
  const queue = () => { if (!raf) raf = requestAnimationFrame(layout); };

  /** Scroll so the target and the card both fit; on phones, the target sits above the bottom sheet. */
  function bring(el) {
    const t = el.getBoundingClientRect(), vh = innerHeight;
    let want;
    if (mobile()) want = 76; // clear of the fixed menu button
    else {
      const need = t.height + GAP + card.offsetHeight;
      want = need <= vh - 2 * M ? (vh - need) / 2 : Math.max(16, (vh - t.height) / 2);
    }
    const dy = t.top - want;
    if (Math.abs(dy) > 2) scrollTo({ top: scrollY + dy, behavior: reduce ? "auto" : "smooth" });
  }

  async function show(k) {
    const my = ++token;
    i = clamp(k, 0, n);
    const s = S[i];
    card.classList.toggle("guide__card--wide", !!s.wide);
    card.innerHTML = cardHtml(s);
    target = null;
    queue();
    const el = s.target ? await waitFor(s.target) : null;
    if (my !== token || !root.isConnected) return;
    target = el;
    if (el && !s.noScroll) bring(el);
    layout();
    card.querySelector("#guide-title").focus({ preventScroll: true });
  }

  function close(then) {
    token++;
    removeEventListener("scroll", queue, true);
    removeEventListener("resize", queue);
    document.removeEventListener("keydown", onKey);
    cancelAnimationFrame(raf);
    hidden.forEach((e) => { e.inert = false; });
    document.body.classList.remove("guide-open");
    root.remove();
    open = false;
    if (then === "area") c.go("unit");
    else (opener?.isConnected && opener !== document.body ? opener : document.getElementById("view"))?.focus({ preventScroll: true });
    finish();
  }

  card.addEventListener("click", (e) => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (act === "next") show(i + 1);
    else if (act === "back") show(i - 1);
    else if (act === "close") close();
    else if (act === "area") close("area");
  });
  function onKey(e) {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
    else if (e.key === "ArrowRight" && i < n) { e.preventDefault(); show(i + 1); }
    else if (e.key === "ArrowLeft" && i > 0) { e.preventDefault(); show(i - 1); }
    else if (e.key === "Tab") { // keep focus inside the card
      const f = [...card.querySelectorAll("button")];
      if (!f.length) return;
      const [a, z] = [f[0], f[f.length - 1]];
      if (e.shiftKey && (document.activeElement === a || document.activeElement.id === "guide-title")) { e.preventDefault(); z.focus(); }
      else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); }
    }
  }
  document.addEventListener("keydown", onKey);
  addEventListener("scroll", queue, true);
  addEventListener("resize", queue);
  show(0);
  return closed;
}
