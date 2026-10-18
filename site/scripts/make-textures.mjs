// Generate the tileable pixel textures and section-edge masks in public/ from small text grids.
// Usage: node scripts/make-textures.mjs   (re-run after editing a pattern; the SVGs are committed)
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const OUT = resolve(import.meta.dirname, "../public");
const SAGE = "#789373", SKY = "#9CCFDD", SKY_2 = "#BFE2EC", NIGHT = "#0A2A1D", LEAF = "#CFE0C9", LEAF_2 = "#A9C79F";

// rows of text -> crisp rects; `colors` maps a character to a fill, `scale` is the size of one art pixel
function grid(rows, colors, scale = 4, ox = 0, oy = 0) {
  let s = "";
  rows.forEach((row, y) => {
    for (let x = 0; x < row.length; ) {
      const c = row[x];
      if (!colors[c]) { x++; continue; }
      let end = x;
      while (end < row.length && row[end] === c) end++;
      s += `<rect x="${(ox + x) * scale}" y="${(oy + y) * scale}" width="${(end - x) * scale}" height="${scale}" fill="${colors[c]}"/>`;
      x = end;
    }
  });
  return s;
}
const svg = (w, h, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges">${body}</svg>\n`;
function write(path, text) { mkdirSync(resolve(OUT, path, ".."), { recursive: true }); writeFileSync(resolve(OUT, path), text); console.log(path); }

// base field: sparse pixel dots (a quiet paper grain)
write("textures/field.svg", svg(64, 64, grid([
  "x...............",
  "................",
  "................",
  "................",
  "................",
  "................",
  "................",
  "................",
  "........x.......",
  "................",
  "................",
  "................",
  "................",
  "................",
  "................",
  "................",
], { x: SAGE }, 4)));

// rain: short diagonal streaks of art pixels (weather blue is for maps, rain and data graphics only)
write("textures/rain.svg", svg(64, 64, grid([
  "....x...........",
  "...x............",
  "..x.........y...",
  "...........y....",
  "..........y.....",
  "................",
  "................",
  "......y.........",
  ".....y.......x..",
  "....y.......x...",
  "...........x....",
  "................",
  ".x..............",
  "x...............",
  "................",
  "................",
], { x: SKY, y: SKY_2 }, 4)));

// mosquito tracks: tiny pixel "x" marks and dot pairs
write("textures/tracks.svg", svg(96, 96, grid([
  "........................",
  "..x.x...................",
  "...x....................",
  "..x.x...............o...",
  "....................o...",
  "........................",
  "...........o............",
  "............o...........",
  "........................",
  "..................x.x...",
  "...................x....",
  "..................x.x...",
  "........................",
  "....o...................",
  ".....o..................",
  "........................",
  "...........x.x..........",
  "............x...........",
  "...........x.x..........",
  "........................",
  ".......................o",
  "......................o.",
  "........................",
  "........................",
], { x: SAGE, o: SAGE }, 4)));

// contour: dotted iso-lines (round pixels along curves), like the mockup's "contour / grid" swatch
write("textures/contour.svg", `<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240"><g fill="none" stroke="${SAGE}" stroke-width="3" stroke-linecap="square" stroke-dasharray="0 9" opacity=".55">`
  + `<path d="M-10 60 C 40 20, 90 100, 140 60 S 220 20, 250 60"/>`
  + `<path d="M-10 120 C 50 80, 100 160, 150 120 S 220 90, 250 120"/>`
  + `<path d="M-10 180 C 40 150, 100 220, 150 180 S 210 150, 250 180"/>`
  + `<path d="M-10 238 C 40 210, 100 270, 150 238 S 210 210, 250 238"/>`
  + `</g></svg>\n`);

// leaves: pixel leaf cluster for canopy edges (repeat-x along a section edge)
const LEAF_ROWS = [
  "......ll............LL..........",
  ".....llLl..........LllL.........",
  "....llLlll........LlllLL......ll",
  "...llLllll.......LlllllL.....lLl",
  "..llLlllll......LllllllL....lLll",
  "..lLllllll......LlllllLL...lLlll",
  ".lLlllllll.....LllllllL...lLllll",
  ".lLllllll......LlllllL....lLllll",
  ".Llllllll.....LllllllL...lLlllll",
  "Lllllllll.....LlllllL....Llllll.",
  ".Lllllll.....LlllllL.....Lllll..",
  "..Llllll.....LllllL......Llll...",
  "...LllL......LlllL.......Lll....",
  "....LL........LLL.........L.....",
];
write("textures/leaves.svg", svg(128, 56, grid(LEAF_ROWS, { l: LEAF, L: LEAF_2 }, 4)));

// town: pixel skyline strip (houses, trees, a clinic) for section bottoms, like the mockup's tool-row footer
write("textures/town.svg", svg(192, 64, grid([
  "................................................",
  "...........................ttt..................",
  "..........................ttttt.................",
  "......hh..................ttttt.......cccccc....",
  ".....hhhh.................ttttt.......c.++.c....",
  "....hhhhhh.........hh......ttt........c++++c....",
  "...hhhhhhhh.......hhhh......t.........c.++.c....",
  "....w....w.......hhhhhh.....t.........c....c....",
  "....w.ww.w........w..w......t.........c.ww.c....",
  "....w.ww.w........w..w......t.........c.ww.c....",
  "gggggggggggggggggggggggggggggggggggggggggggggggg",
  "gggggggggggggggggggggggggggggggggggggggggggggggg",
], { h: LEAF_2, w: LEAF_2, t: LEAF_2, c: LEAF_2, "+": "#E9A3A3", g: LEAF }, 4, 0, 4)));

// dither bands: ordered (Bayer 4x4) dots in the night colour, light to heavy, for fading into dark sections
const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];
for (const [name, level] of [["lo", 3], ["mid", 7], ["hi", 12]]) {
  const rows = BAYER.map((r) => r.map((v) => (v < level ? "x" : ".")).join(""));
  write(`textures/dither-${name}.svg`, svg(16, 16, grid(rows, { x: NIGHT }, 4)));
}

// section edges: stepped pixel masks (white = visible). 32x16 tile, repeat-x.
const STEP = ["........xxxxxxxx", "....xxxxxxxxxxxx", "xxxxxxxxxxxxxxxx", "xxxxxxxxxxxxxxxx"];
write("seams/edge-top.svg", svg(64, 16, grid(STEP.map((r) => r + [...r].reverse().join("")), { x: "#fff" }, 4)));
write("seams/edge-bottom.svg", svg(64, 16, grid([...STEP].reverse().map((r) => r + [...r].reverse().join("")), { x: "#fff" }, 4)));
