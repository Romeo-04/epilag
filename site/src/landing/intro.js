// First-visit intro (once per session, ?intro forces it): coloured pixels gather into the logo tile, the name rises,
// a badge pops, then the tile flies into the nav logo and the page appears. Any wheel, touch, key or click skips it.
// Same sequence as getcko.vercel.app's intro.
import { gsap, SplitText } from "../lib/motion.js";

const COLORS = ["#08754F", "#0C7A55", "#789373", "#071711", "#F5A51C", "#E3F0E7"];

export function playIntro(onDone) {
  const root = document.documentElement, intro = document.querySelector(".intro");
  const tile = intro.querySelector(".intro__tile"), bg = intro.querySelector(".intro__tile-bg");
  const word = intro.querySelector(".intro__word"), badge = intro.querySelector(".intro__badge"), skip = intro.querySelector(".intro__skip");
  const mark = document.querySelector("[data-nav-mark] .lg");
  try { sessionStorage.setItem("el-intro", "1"); } catch { /* storage may be blocked */ }

  // pixels that gather into the tile
  const box = tile.getBoundingClientRect(), cells = [];
  for (let i = 0; i < 64; i++) {
    const c = document.createElement("i");
    c.className = "intro__cell";
    c.style.background = COLORS[i % COLORS.length];
    c.style.left = `${box.left + (i % 8) * 20}px`;
    c.style.top = `${box.top + Math.floor(i / 8) * 20}px`;
    intro.append(c);
    cells.push(c);
  }
  gsap.set([tile, word, badge], { autoAlpha: 0 });
  gsap.set(tile, { autoAlpha: 1 });
  gsap.set(tile.querySelector(".px-icon"), { autoAlpha: 0 });

  const split = SplitText.create(word, { type: "chars", mask: "chars" });
  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    ["wheel", "touchmove", "keydown", "pointerdown"].forEach((ev) => removeEventListener(ev, skipNow));
    root.classList.remove("intro-pending");
    intro.remove();
    onDone?.();
    gsap.from(".top", { autoAlpha: 0, y: -12, duration: 0.6, ease: "expo.out" });
  };
  const tl = gsap.timeline({ defaults: { ease: "power3.out" }, onComplete: finish });
  tl.fromTo(cells, {
    autoAlpha: 0,
    x: () => gsap.utils.random(-0.5, 0.5) * innerWidth,
    y: () => gsap.utils.random(-0.45, 0.45) * innerHeight,
    scale: () => gsap.utils.random(0.5, 2.4),
  }, { autoAlpha: 1, x: 0, y: 0, scale: 1, duration: 0.9, ease: "expo.out", stagger: { amount: 0.45, from: "random" } }, 0)
    .fromTo(bg, { scale: 0.3, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.5, ease: "back.out(1.6)" }, 1)
    .to(cells, { scale: 0, duration: 0.25, stagger: { amount: 0.2, from: "center" } }, 1.05)
    .to(tile.querySelector(".px-icon"), { autoAlpha: 1, duration: 0.01 }, 1.3)
    .set(word, { autoAlpha: 1 }, 1.2)
    .from(split.chars, { yPercent: 110, duration: 0.55, stagger: 0.035, ease: "expo.out" }, 1.2)
    .fromTo(badge, { autoAlpha: 0, scale: 0 }, { autoAlpha: 1, scale: 1, duration: 0.22, ease: "steps(2)" }, 1.6)
    .to([word, badge, skip], { autoAlpha: 0, y: -14, duration: 0.3, ease: "power2.in" }, 2.15);
  // the tile flies into the nav logo (measured, so it lands exactly)
  if (mark) {
    tl.add(() => {
      const a = tile.getBoundingClientRect(), b = mark.getBoundingClientRect();
      gsap.to(tile, { x: b.left + b.width / 2 - (a.left + a.width / 2), y: b.top + b.height / 2 - (a.top + a.height / 2),
        scale: b.width / a.width, duration: 0.8, ease: "expo.inOut" });
    }, 2.25);
  }
  tl.to(intro, { backgroundColor: "rgba(251,250,244,0)", duration: 0.5 }, 2.6).to({}, { duration: 0.5 }, 2.6);

  const skipNow = () => tl.progress(1);
  ["wheel", "touchmove", "keydown", "pointerdown"].forEach((ev) => addEventListener(ev, skipNow, { passive: true, once: true }));
  gsap.fromTo(skip, { autoAlpha: 0 }, { autoAlpha: 1, delay: 0.4, duration: 0.3 });
}
