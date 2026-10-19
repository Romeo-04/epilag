// The ending. When the frog's stage is fully on screen (the bottom of the page), the mascot mosquito that
// followed the reader flies down the dotted path and hovers above the frog. The frog watches, its tongue shoots
// up to the mosquito, sparks pop, the tongue pulls it into the mouth, and the frog gulps, chews and smiles.
// Scrolling away and back replays it; "Again" brings a new mosquito. Under reduced motion (or without the
// mascot) it shows the end pose.
import { gsap, reduced } from "../lib/motion.js";

const MOUTH = [12, 27]; // frog `strikeUp` mouth, in art pixels (strike without its tongue stub, scripts/sprites.py)
const BODY = [16, 18]; // mosquito body centre, in art pixels (its sprite anchor)

export function playFinale(stage, mascot) {
  const frog = stage.querySelector(".finale__frog"), tongue = stage.querySelector(".finale__tongue");
  const again = stage.querySelector(".finale__again"), sparks = stage.querySelectorAll(".finale__spark");
  const pose = (p) => frog.setAttribute("pose", p);
  if (!mascot) { pose("happy"); return; }

  let tl = null;
  const reset = () => {
    tl?.kill();
    tl = null;
    gsap.set(tongue, { scaleX: 0 });
    gsap.set(sparks, { scale: 0 });
    stage.classList.remove("done");
    pose("watch");
  };
  const inView = () => {
    const r = stage.getBoundingClientRect();
    return r.height > 0 && r.top >= -8 && r.bottom <= innerHeight + 48;
  };
  // mouth and mosquito body, in stage px, measured now (the reader may scroll during the scene)
  const points = () => {
    const st = stage.getBoundingClientRect(), f = frog.getBoundingClientRect(), k = f.width / 48, b = mascot.box("finale");
    return { mouth: { x: f.left + MOUTH[0] * k - st.left, y: f.top + MOUTH[1] * k - st.top },
      body: { x: b.x + BODY[0] * b.cell - st.left, y: b.y + BODY[1] * b.cell - st.top } };
  };

  function hunt(s) {
    reset();
    if (reduced()) { s.hidden = true; pose("happy"); return; }
    tl = gsap.timeline({ onComplete: () => stage.classList.add("done") });
    // a short buzz in place while the frog takes aim
    tl.to(s, { dx: 18, dy: -10, duration: 0.24, ease: "steps(3)" })
      .to(s, { dx: -14, dy: 6, duration: 0.24, ease: "steps(3)" })
      .call(() => pose("watchClose"))
      .to(s, { dx: 0, dy: 0, duration: 0.2, ease: "steps(2)" })
      .call(() => {
        // the tongue is a bar anchored at the mouth, turned to point at the mosquito
        pose("strikeUp");
        const { mouth, body } = points(), len = Math.hypot(body.x - mouth.x, body.y - mouth.y);
        const angle = Math.atan2(body.y - mouth.y, body.x - mouth.x) * 180 / Math.PI - 180;
        Object.assign(tongue.style, { left: `${mouth.x - len}px`, top: `${mouth.y - 8}px`, width: `${len + 6}px` });
        gsap.set(tongue, { rotation: angle, scaleX: 0 });
      })
      .to(tongue, { scaleX: 1, duration: 0.12, ease: "steps(4)" })
      .to(sparks, { scale: 1, duration: 0.12, ease: "steps(2)", stagger: 0.05 })
      // caught: the tongue pulls back and the mosquito goes with it, into the mouth
      .addLabel("pull", "+=0.08")
      .to(tongue, { scaleX: 0, duration: 0.2, ease: "steps(5)" }, "pull")
      .to(s, { dx: () => { const p = points(); return s.dx + p.mouth.x - p.body.x - 8; },
        dy: () => { const p = points(); return s.dy + p.mouth.y - p.body.y; }, duration: 0.2, ease: "steps(5)" }, "pull")
      .to(sparks, { scale: 0, duration: 0.2, ease: "steps(2)" }, "pull+=0.1")
      .call(() => { s.hidden = true; pose("gulp"); }, [], "pull+=0.22")
      .call(() => pose("chew"), [], "+=0.3")
      .call(() => pose("idle"), [], "+=0.25")
      .call(() => pose("chew"), [], "+=0.2")
      .call(() => pose("happy"), [], "+=0.3");
  }

  mascot.register({ id: "finale", section: stage, slot: stage.querySelector(".finale__slot"), frames: ["fly1", "fly2"], fps: 14,
    flip: false, when: inView, onLand: hunt, onLeave: (s) => { reset(); Object.assign(s, { hidden: false, dx: 0, dy: 0 }); } });
  again.addEventListener("click", () => mascot.relaunch("finale"));
}
