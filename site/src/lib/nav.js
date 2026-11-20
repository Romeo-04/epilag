// Floating nav: open on the page at the top, a lifted pill once the page has scrolled a little.
// The look of both states is in css/components.css (.top[data-lifted]).
const LIFT_AT = 24;
const top = document.querySelector(".top");

if (top) {
  const update = () => top.toggleAttribute("data-lifted", window.scrollY > LIFT_AT);
  update();
  window.addEventListener("scroll", update, { passive: true });
}
