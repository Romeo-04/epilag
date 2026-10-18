// The last section's finale: a mosquito flies in, the frog watches, strikes with its tongue, gulps, chews and smiles.
// Plays once when the section scrolls into view; "Again" replays it. Under reduced motion it shows the end pose.
import { gsap, ScrollTrigger, reduced } from "../lib/motion.js";

const MOUTH = [13, 28]; // frog `strike` mouth, in art pixels (UI mockup/sprites/notes.txt)

export function playFinale(stage) {
  const frog = stage.querySelector(".finale__frog"), mosq = stage.querySelector(".finale__mosq");
  const tongue = stage.querySelector(".finale__tongue"), again = stage.querySelector(".finale__again");
  const pose = (p) => frog.setAttribute("pose", p);
  if (reduced()) { pose("happy"); mosq.style.display = "none"; return; }

  function run() {
    stage.classList.remove("done");
    gsap.killTweensOf([mosq, tongue]);
    gsap.set(mosq, { autoAlpha: 1, x: 0, y: 0 });
    gsap.set(tongue, { scaleX: 0 });
    pose("watch");
    const s = stage.getBoundingClientRect(), f = frog.getBoundingClientRect(), m = mosq.getBoundingClientRect();
    const scale = f.width / 48;
    const mouth = { x: f.left - s.left + MOUTH[0] * scale, y: f.top - s.top + MOUTH[1] * scale };
    // where the mosquito hovers before the strike: a little left of and above the mouth
    const hover = { x: mouth.x - 150 - (m.left - s.left), y: mouth.y - 40 - (m.top - s.top) };
    const tl = gsap.timeline({ onComplete: () => stage.classList.add("done") });
    tl.to(mosq, { x: hover.x * 0.5, y: hover.y - 60, duration: 0.9, ease: "steps(9)" })
      .call(() => pose("watchClose"))
      .to(mosq, { x: hover.x, y: hover.y, duration: 0.8, ease: "steps(8)" })
      .call(() => {
        pose("strike");
        const mm = mosq.getBoundingClientRect(), tx = mm.left - s.left + mm.width / 2;
        Object.assign(tongue.style, { left: `${tx}px`, top: `${mouth.y - 6}px`, width: `${mouth.x - tx}px` });
      })
      .to(tongue, { scaleX: 1, duration: 0.12, ease: "steps(4)" })
      .to(tongue, { scaleX: 0, duration: 0.16, ease: "steps(4)" }, "+=0.06")
      .to(mosq, { x: `+=${150}`, y: `+=${40}`, autoAlpha: 0, duration: 0.16, ease: "steps(4)" }, "<")
      .call(() => pose("gulp"))
      .call(() => pose("chew"), [], "+=0.35")
      .call(() => pose("idle"), [], "+=0.3")
      .call(() => pose("chew"), [], "+=0.25")
      .call(() => pose("happy"), [], "+=0.35");
  }
  ScrollTrigger.create({ trigger: stage, start: "top 75%", once: true, onEnter: run });
  again.addEventListener("click", run);
}
