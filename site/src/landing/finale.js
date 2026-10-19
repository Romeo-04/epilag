// The last section's finale. When the frog's stage is fully on screen (the bottom of the page), the mascot
// mosquito that followed the reader flies down into it, buzzes up to the frog, and the frog watches, strikes
// with its tongue, gulps, chews and smiles. Scrolling away and back replays it; "Again" brings a new mosquito.
// Under reduced motion (or without the mascot) it shows the end pose.
import { gsap, reduced } from "../lib/motion.js";

const MOUTH = [13, 28]; // frog `strike` mouth, in art pixels (UI mockup/sprites/notes.txt)
const BODY = [16, 18]; // mosquito body centre, in art pixels (its sprite anchor)

export function playFinale(stage, mascot) {
  const frog = stage.querySelector(".finale__frog"), tongue = stage.querySelector(".finale__tongue");
  const again = stage.querySelector(".finale__again");
  const pose = (p) => frog.setAttribute("pose", p);
  if (!mascot) { pose("happy"); return; }

  let tl = null;
  const reset = () => {
    tl?.kill();
    tl = null;
    gsap.set(tongue, { scaleX: 0 });
    stage.classList.remove("done");
    pose("watch");
  };
  const inView = () => {
    const r = stage.getBoundingClientRect();
    return r.height > 0 && r.top >= -8 && r.bottom <= innerHeight + 8;
  };

  function hunt(s) {
    reset();
    if (reduced()) { s.hidden = true; pose("happy"); return; }
    const f = frog.getBoundingClientRect(), k = f.width / 48;
    const mouth = { x: f.left + MOUTH[0] * k, y: f.top + MOUTH[1] * k };
    const b = mascot.box("finale"), body = { x: b.x + BODY[0] * b.cell, y: b.y + BODY[1] * b.cell };
    // offsets (from the slot) that put the mosquito's body 170px left of the mouth, at its height
    const hover = { x: s.dx + mouth.x - 170 - body.x, y: s.dy + mouth.y - 8 - body.y };
    tl = gsap.timeline({ onComplete: () => stage.classList.add("done") });
    tl.to(s, { dx: hover.x * 0.4, dy: hover.y - 60, duration: 0.42, ease: "steps(6)" })
      .to(s, { dx: hover.x * 0.75, dy: hover.y + 16, duration: 0.36, ease: "steps(5)" })
      .call(() => pose("watchClose"))
      .to(s, { dx: hover.x, dy: hover.y, duration: 0.3, ease: "steps(4)" })
      .call(() => {
        // the tongue runs from the mouth to the mosquito's body (measured now, in case the reader scrolled)
        pose("strike");
        const st = stage.getBoundingClientRect(), fr = frog.getBoundingClientRect(), bx = mascot.box("finale");
        const mx = fr.left + MOUTH[0] * k - st.left, my = fr.top + MOUTH[1] * k - st.top, x = bx.x + BODY[0] * bx.cell - st.left;
        Object.assign(tongue.style, { left: `${x}px`, top: `${my - 6}px`, width: `${mx - x}px` });
      })
      .to(tongue, { scaleX: 1, duration: 0.1, ease: "steps(3)" })
      // caught: the tongue pulls back and the mosquito goes with it, into the mouth
      .to(tongue, { scaleX: 0, duration: 0.16, ease: "steps(4)" }, "+=0.05")
      .to(s, { dx: hover.x + 170 - 10, dy: hover.y + 8, duration: 0.16, ease: "steps(4)" }, "<")
      .call(() => { s.hidden = true; pose("gulp"); })
      .call(() => pose("chew"), [], "+=0.3")
      .call(() => pose("idle"), [], "+=0.25")
      .call(() => pose("chew"), [], "+=0.2")
      .call(() => pose("happy"), [], "+=0.3");
  }

  mascot.register({ id: "finale", section: stage, slot: stage.querySelector(".finale__slot"), frames: ["fly1", "fly2"], fps: 14,
    flip: false, when: inView, onLand: hunt, onLeave: (s) => { reset(); Object.assign(s, { hidden: false, dx: 0, dy: 0 }); } });
  again.addEventListener("click", () => mascot.relaunch("finale"));
}
