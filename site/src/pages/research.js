// Research page: static content in research.html (every number is checked against the result files by
// tests/test_research_page.py); this adds pixel icons, scroll reveals, growing bars and the section highlight in the nav.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./pages.css";
import "./research.css";
import { hydrateIcons } from "../lib/icons.js";
import "../lib/nav.js";
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

// the reader: links marked data-doc open their document in a dialog instead of leaving the page (without
// JavaScript they are plain links to the same pages, which are still on this site)
const reader = document.getElementById("reader"), frame = document.getElementById("reader-frame");
function openDoc(a) {
  document.getElementById("reader-title").textContent = a.dataset.docTitle;
  document.getElementById("reader-pdf").hidden = a.dataset.doc !== "paper";
  document.getElementById("reader-tab").href = a.href;
  frame.title = a.dataset.docTitle;
  frame.src = a.href;
  reader.showModal();
}
document.addEventListener("click", (e) => {
  const a = e.target.closest("a[data-doc]");
  if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return; // a modified click still opens a tab
  e.preventDefault();
  openDoc(a);
});
document.getElementById("reader-close").addEventListener("click", () => reader.close());
reader.addEventListener("click", (e) => { if (e.target === reader) reader.close(); }); // a click on the backdrop
reader.addEventListener("close", () => { frame.src = "about:blank"; });
