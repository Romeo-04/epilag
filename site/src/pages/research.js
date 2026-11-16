// Research page: static content in research.html (every number is checked against the result files by
// tests/test_research_page.py); this adds pixel icons, scroll reveals, growing bars and the section highlight in the nav.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./pages.css";
import "./research.css";
import { hydrateIcons } from "../lib/icons.js";
import "../lib/pixel.js";
import { gsap, reduced, reveal } from "../lib/motion.js";

hydrateIcons();
reveal("[data-reveal]");

// bars grow in pixel steps when their chart scrolls into view
if (!reduced()) {
  const grow = (sel, from, origin) => document.querySelectorAll(sel).forEach((box) =>
    gsap.from(box.querySelectorAll("i"), { ...from, transformOrigin: origin, duration: 0.5, ease: "steps(5)", stagger: 0.06,
      scrollTrigger: { trigger: box, start: "top 90%", once: true } }));
  grow(".hbars", { scaleX: 0 }, "0 50%");
  grow(".cols", { scaleY: 0 }, "50% 100%");
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
