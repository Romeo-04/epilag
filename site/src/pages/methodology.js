// Methodology page: static content in methodology.html; this adds pixel icons, scroll reveals, the count-ups,
// the rain-lag bars and the section highlight in the nav. Everything is readable without it.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./pages.css";
import { hydrateIcons } from "../lib/icons.js";
import "../lib/pixel.js";
import { gsap, countUp, reduced, reveal } from "../lib/motion.js";

hydrateIcons();
reveal("[data-reveal]");
document.querySelectorAll("[data-count]").forEach((el) => countUp(el));

// rain lags grow up in pixel steps, this week first
if (!reduced()) {
  gsap.from(".lag i", { scaleY: 0, transformOrigin: "50% 100%", duration: 0.5, ease: "steps(4)", stagger: 0.05,
    scrollTrigger: { trigger: ".lag", start: "top 90%", once: true } });
}

// highlight the section in view
const links = [...document.querySelectorAll("[data-spy] a")];
const spy = new IntersectionObserver((entries) => entries.forEach((e) => {
  if (!e.isIntersecting) return;
  links.forEach((a) => {
    if (a.getAttribute("href") === `#${e.target.id}`) a.setAttribute("aria-current", "location");
    else a.removeAttribute("aria-current");
  });
}), { rootMargin: "-40% 0px -55% 0px" });
document.querySelectorAll("section[id]").forEach((s) => spy.observe(s));
