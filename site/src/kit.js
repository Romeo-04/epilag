// Component kit: every token, icon, texture and component on one page, to check against the UI mockups.
import "./css/tokens.css";
import "./css/base.css";
import "./css/surfaces.css";
import "./css/components.css";
import { ICONS, hydrateIcons, icon } from "./lib/icons.js";
import { TOOLS } from "./lib/content.js";

const $ = (id) => document.getElementById(id);

const CORE = [["Ink", "--ink", "#071711", true], ["Forest", "--forest", "#08754F", true], ["Sage", "--sage", "#789373", true],
  ["Warm white", "--paper", "#FBFAF4"], ["Amber", "--amber", "#F5A51C"], ["Weather blue", "--sky", "#BFE2EC"]];
const LEVELS = [["Warning", "warning", "#F04B2A"], ["Watch", "watch", "#F58220"], ["Above usual", "above", "#F7C928"], ["Normal", "normal", "#0C7A55"], ["No data", "nodata", "#C9CFC9"]];

$("sw-core").innerHTML = CORE.map(([n, v, hex, dark]) =>
  `<div class="sw" style="background:var(${v});color:${dark ? "#fff" : "var(--ink)"}"><b>${n}</b>${hex}</div>`).join("");
$("sw-level").innerHTML = LEVELS.map(([n, lv, hex]) =>
  `<div class="sw" data-lv="${lv}" style="background:var(--c);color:var(--c-ink)"><b>${n}</b>${hex}</div>`).join("");

const fig = (name, size) => `<figure>${icon(name, { size })}<figcaption>${name}</figcaption></figure>`;
const ui = Object.entries(ICONS).filter(([, [g]]) => g === 12).map(([n]) => n);
const art = Object.entries(ICONS).filter(([, [g]]) => g === 16).map(([n]) => n);
$("ic-ui").innerHTML = ui.map((n) => fig(n, 24)).join("") + ui.slice(0, 3).map((n) => fig(n, 36)).join("");
$("ic-art").innerHTML = art.map((n) => fig(n, 48)).join("") + fig("logo", 64);

$("tools").innerHTML = TOOLS.map((t, i) => `<a class="card tool" href="#">
  <span class="ic">${icon(t.icon, { size: 48 })}</span>
  <div><h3>${i + 1}. ${t.name}</h3><p>${t.short}</p></div>
  <span class="go">${icon("arrowRight", { size: 24 })}</span></a>`).join("");

hydrateIcons();
document.getElementById("kit").dataset.ready = "1";
