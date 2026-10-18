// Motion tokens and small GSAP helpers shared by every page (REDESIGN_PLAN.md section 7).
// Every helper respects prefers-reduced-motion: it jumps to the end state instead of animating.
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";

gsap.registerPlugin(ScrollTrigger, SplitText);

export { gsap, ScrollTrigger, SplitText };

export const DUR = { instant: 0.08, fast: 0.14, base: 0.22, slow: 0.36, pointer: 0.52 };
export const EASE = { out: "power3.out", inOut: "power2.inOut", point: "back.out(1.6)", step: "steps(2)" };

export const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Fade and rise each element once as it scrolls into view. */
export function reveal(targets, { y = 18, stagger = 0.06, start = "top 85%" } = {}) {
  const els = gsap.utils.toArray(targets);
  if (reduced()) return gsap.set(els, { autoAlpha: 1, y: 0 });
  gsap.set(els, { autoAlpha: 0, y });
  return ScrollTrigger.batch(els, {
    start,
    once: true,
    onEnter: (batch) => gsap.to(batch, { autoAlpha: 1, y: 0, duration: 0.7, ease: "expo.out", stagger }),
  });
}

/** Count a number up to its data-count value when it scrolls into view. Keeps any text after the number. */
export function countUp(el, { duration = 1.2 } = {}) {
  const to = Number(el.dataset.count);
  if (reduced() || !Number.isFinite(to)) { el.textContent = el.dataset.count; return; }
  const v = { n: 0 };
  ScrollTrigger.create({
    trigger: el, start: "top 90%", once: true,
    onEnter: () => gsap.to(v, { n: to, duration, ease: "power2.out", onUpdate: () => { el.textContent = Math.round(v.n).toLocaleString("en"); } }),
  });
}

/** Split a headline into characters that rise into place. Returns the timeline (paused if `paused`). */
export function riseChars(el, { stagger = 0.03, paused = false } = {}) {
  const tl = gsap.timeline({ paused });
  if (reduced()) return tl;
  const split = SplitText.create(el, { type: "chars,words", mask: "chars" });
  tl.from(split.chars, { yPercent: 110, duration: 0.55, stagger, ease: "expo.out" });
  return tl;
}

/**
 * Cover an element with a grid of coloured cells that shrink away (the "pixel curtain").
 * Returns a timeline; the curtain removes itself when it finishes.
 */
export function curtain(el, { cell = 18, colors = ["#08754F", "#0C7A55", "#E3F0E7", "#789373", "#071711"], paused = false } = {}) {
  const tl = gsap.timeline({ paused });
  if (reduced()) return tl;
  const cols = Math.ceil(el.offsetWidth / cell), rowsN = Math.ceil(el.offsetHeight / cell);
  const wrap = document.createElement("div");
  wrap.setAttribute("aria-hidden", "true");
  Object.assign(wrap.style, { position: "absolute", inset: "0", display: "grid", zIndex: "5", pointerEvents: "none",
    gridTemplateColumns: `repeat(${cols}, 1fr)`, gridTemplateRows: `repeat(${rowsN}, 1fr)` });
  for (let i = 0; i < cols * rowsN; i++) {
    const c = document.createElement("i");
    c.style.background = colors[Math.floor(Math.random() * colors.length)];
    wrap.append(c);
  }
  if (getComputedStyle(el).position === "static") el.style.position = "relative";
  el.append(wrap);
  tl.to(wrap.children, { scale: 0, duration: 0.3, ease: "power2.in", stagger: { amount: 0.55, grid: [rowsN, cols], from: "start" } })
    .call(() => wrap.remove());
  return tl;
}

/** Run `fn` once per browser session (any key), unless ?intro is in the URL. Storage may be unavailable. */
export function oncePerSession(key, fn) {
  let seen = false;
  try { seen = sessionStorage.getItem(key) === "1"; sessionStorage.setItem(key, "1"); } catch { /* private mode */ }
  if (!seen || /[?&]intro\b/.test(location.search)) fn();
}
