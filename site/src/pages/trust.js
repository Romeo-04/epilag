// Trust and sustainability page: static content in trust.html; this adds pixel icons, scroll reveals, the count-ups
// and the section highlight in the nav. Everything is readable without it.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./pages.css";
import { hydrateIcons } from "../lib/icons.js";
import "../lib/pixel.js";
import "../lib/nav.js";
import { countUp, reveal } from "../lib/motion.js";

hydrateIcons();
reveal("[data-reveal]");
document.querySelectorAll("[data-count]").forEach((el) => countUp(el));

const links = [...document.querySelectorAll("[data-spy] a")];
const spy = new IntersectionObserver((entries) => entries.forEach((e) => {
  if (!e.isIntersecting) return;
  links.forEach((a) => {
    if (a.getAttribute("href") === `#${e.target.id}`) a.setAttribute("aria-current", "location");
    else a.removeAttribute("aria-current");
  });
}), { rootMargin: "-40% 0px -55% 0px" });
document.querySelectorAll("section[id]").forEach((s) => spy.observe(s));
