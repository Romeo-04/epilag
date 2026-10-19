# EpiLag-PH redesign plan

Rebuild the EpiLag-PH website as one pixel-art brand: a new landing page, a fast JavaScript app in place of the
Streamlit/stlite web view, and 3D pixel (voxel) maps and a 3D Dengue Drill. Written 19 Oct 2026, before any code changes.

**Sources of truth**

| What | Where | Used for |
| --- | --- | --- |
| UI mockups | `UI mockup/` (6 images) | Page structure, sections, copy, colours, type, pixel assets |
| Motion reference | <https://getcko.vercel.app/> | How things move: intro, mascot, hero loop, pinned scrub, textures |
| Current site | `docs/index.html`, `docs/web/`, `docs/drill/`, `docs/methodology.html`, `docs/data/` | Content, numbers and features to keep |
| Numbers | `README.md`, `reports/*.csv` | Every claim on the new pages must match these |

Contents: [1 Goals](#1-goals) · [2 Decisions](#2-decisions) · [3 Reference analysis](#3-reference-analysis) ·
[4 Architecture](#4-architecture) · [5 Design system](#5-design-system) · [6 Pixel sprite system](#6-pixel-sprite-system) ·
[7 Motion system](#7-motion-system) · [8 Landing page](#8-landing-page) · [9 Voxel map engine](#9-voxel-map-engine) ·
[10 JavaScript web app](#10-javascript-web-app) · [11 3D Dengue Drill](#11-3d-dengue-drill) ·
[12 Other pages and media](#12-other-pages-and-media) · [13 Testing and quality](#13-testing-and-quality) ·
[14 Phases and checklist](#14-phases-and-checklist) · [15 Risks](#15-risks) · [16 File map](#16-file-map)

---

## 1. Goals

1. **One brand.** Warm-white paper, forest green and pixel art: the mosquito is the threat and the frog is the hero.
   The landing page, app, drill, methodology and data pages all share it.
2. **getcko-level motion.** A pixel intro, a mascot that follows the reader from section to section, a looping
   hero scene, a pinned scroll section, and textured sections with pixel seams. Every effect has a reduced-motion
   version.
3. **Fast app.** Replace the stlite app (about a 1-minute first load, because it downloads Python into the browser) with
   plain JavaScript that loads in seconds and has the same 8 pages and features.
4. **3D pixel maps everywhere.** One voxel map engine for the hero preview, the app's forecast map, the drill
   board and the methodology figures.
5. **Same honesty.** Same numbers, same limits, same "Did it work?" page. No claim beyond `README.md`.
6. **Stay static.** It stays on GitHub Pages from `docs/`, with no server.

Non-goals: changing the model, the pipeline in `src/`, or the forecasts themselves.

## 2. Decisions

| # | Decision | Status |
| --- | --- | --- |
| D1 | Web view: rebuild the Streamlit app in plain JavaScript | **Decided** (19 Oct 2026) |
| D2 | Maps and game in 3D pixel (voxel) style | **Decided** |
| D3 | Visual source: `UI mockup/`; motion source: getcko | **Decided** |
| D4 | Build setup: **Vite**, source in `site/`, `npm run build` writes into `docs/` (GitHub Pages unchanged) | **Decided** (19 Oct 2026) |
| D5 | Drill actions: **one response team type**; clean-up + covers + info shown as the team's cost breakdown (see 11.4) | **Decided** |
| D6 | Font: **Inter Tight** (SIL Open Font License, Google Fonts). Checked 19 Oct 2026: the free Nimbus Sans (ArtifexSoftware/urw-base35-fonts) is AGPL-3.0 with an exception only for embedding in PDF/PostScript, and it has no Extra Bold weight, so it is not used on the web | **Decided** |
| D7 | Re-record the film in the new style, at the end (Phase 7) | **Decided** |
| D8 | Keep `app/streamlit_app.py` for local use until the JS app has every feature, then retire `docs/web/epilag_app.zip` | Recommended |
| D9 | App forecast map: build with **our Three.js voxel engine** first. Later, prototype a MapLibre `fill-extrusion` version of the same map and compare the two side by side (look, smoothness, size, phone speed) before the final pick | **Decided** (comparison in Phase 5) |

### Other repos checked
- **stimmie.dev** (<https://github.com/smmariquit/stimmie.dev>): a Next.js personal portfolio with no 3D or map code.
  Nothing to use.
- **Room TBA** (<https://github.com/uplbtools/room-tba>, MIT): the UPLB campus map (Astro, Svelte 5, MapLibre GL 6,
  Three.js 0.186). Useful as a pattern source for the voxel engine, not as a drop-in. See [9.3](#93-patterns-borrowed-from-room-tba).

---

## 3. Reference analysis

### 3.1 getcko.vercel.app: how its motion works
Read from its production bundle (React 19, Tailwind, GSAP 3.15 with ScrollTrigger and SplitText) and 20 headless
Chrome captures of the intro and each scroll position.

| Technique | Mechanics | Our version |
| --- | --- | --- |
| **Pixel intro** (about 3.7 s, once per session; `?intro` forces it) | Coloured cells fly in from random viewport positions (`expo.out`, random stagger). A logo tile scales in (`back.out(1.6)`). SplitText reveals the name char by char (`yPercent 110 → 0`, stagger .035). A badge pops in with a `steps(2)` ease. The tile then flies into the nav logo (measured FLIP), and nav links and hero copy stagger in. A "pixel curtain" (grid of random-colour cells over the hero window) shrinks away cell by cell with a grid stagger. Any wheel, touch or key skips it. | Mosquito-pixel cells form the EpiLag logo tile, "EpiLag-PH" reveals char by char, a "ACT WEEKS EARLIER." badge pops in, the tile flies into the nav, and the curtain lifts off the hero map. |
| **Sprites from text grids** | Each pose is an array of strings (22×27). Each letter maps to a palette colour. Drawn once to an offscreen canvas, then scaled with `imageSmoothingEnabled = false` and `image-rendering: pixelated`. Blink and flip are derived from the base grid. Positions snap to whole cells. | Mosquito and frog poses as text grids, built from our sprite sheets (section 6). |
| **Mascot controller** | One fixed full-viewport canvas. Sections register a slot (`id`, element, pose, flip, target). Each frame it picks the slot whose section crosses the viewport middle. On change, the mascot scatters into pixel "sparks" and the new pose re-forms from particles (curved paths, per-row delays, colour swap at 62%). After landing, a yellow ring pulses on the slot's target. Random blinks every 3–6 s. | The mosquito moves between sections. At the final CTA the frog catches it. |
| **Hero loop** (6.6 s, repeats) | One GSAP timeline drives a time value. A pure function maps time to position and pose: walk frames alternate every 0.13 s, the path arcs with a parabolic hop, and positions round to the cell. Chips fade in and out at named beats. The beat row under the headline lights up with a growing underline. | The mosquito flies the dotted route from a rain cloud to Guimaras. Guimaras gets a ring, the "35 cases · likely 15–65" chip appears, and the beats are Rain · Forecast · Alert · Act. |
| **Pinned scrub** ("How it works") | On ≥1100 px: pin, `end: +=140%`, `scrub: .6`. A background strip scrolls 1280 px. Each step animates `--on 0 → 1`, an underline `scaleX`, its icon with `steps(2)`, and connector dots pop. Below 1100 px: no pin, scrub across the section. Reduced motion: final state. | "Dengue follows the rain": rain → mosquitoes → sick → hospital, with week labels. |
| **Textured sections** | `.surface-*` classes tile SVG textures (footprints, leaves, weave, skin), each with subtle, standard and bold intensities. `.seam` masks give sections pixel zig-zag top and bottom edges; dither textures fade into the dark section. | Rain, contour, mosquito-track, leaf-canopy and pixel-town textures from the mockup sheet. |
| **Particle flow** | Pixels fly from a source rectangle into target cards, and each card updates when its pixels arrive. | Rain and case pixels flow into the forecast card, and data pixels flow into the CSV/JSON chips. |
| **Active list item** | An IntersectionObserver with `rootMargin: -45% 0px -45% 0px` makes the item at the viewport middle active. The mascot walks to it (GSAP `snap: {y: cell}`) with 2-frame walk poses. | The Six tools list, or the evidence list. |
| **Motion tokens** | Durations: instant .08 · fast .14 · base .22 · slow .36 · pointer .52 s. Eases: `power3.out`, `power2.inOut`, `back.out(1.6)`, `steps(2)`. | Same tokens (section 7.1). |
| **Reduced motion** | `gsap.matchMedia()` branches. The mascot settles instantly. Timelines jump to their end state. | Same. |

Captures for comparison: `scratchpad/cko_shots/` (intro frames, scroll frames, contact sheets). Local only.

### 3.2 UI mockup inventory (`UI mockup/`)

| File | Content | Format | Use |
| --- | --- | --- | --- |
| `EpiLag-PH_ Forecasting Dengue Risk Ahead.png` (724×2172) | **Final full landing page**: 10 sections | RGB | Page structure and copy (section 8) |
| `850432863_…png` (398×2048) | Earlier full-page variant (alternative hero, drill stats row, film section) | RGB | Second reference |
| `851374043_…png` (768×2048) | **Component and asset sheet**: textures, hero mosquito, flight routes, map components, evidence badges, delay-story props, timeline parts, console frame, allocation tokens, tool icons, open-data icons, action brief, frog progression, mosquito flight poses, nav, footer symbols | RGB (no alpha) | Guide for redrawing icons, textures and components as SVG |
| `856149787_…png` (1600×1000) | **Visual foundations**: type and palette | RGBA | Design tokens (section 5) |
| `844825300_…png` (1774×887) | **Frog sheet**: mosquito + frog progression (peek → watch → watch close → idle; tongue strike → gulp → chew → satisfied) | RGBA, transparent | Sprites (section 6) |
| `845642964_…png` (1402×1122) | **Mosquito sheet**: 20 poses (idle, flap, turn, dash, loop route, pin, house, alert, target ring, building, coin, clipboard, magnifier, front alert, happy, check, sleepy) | RGBA, transparent | Sprites (section 6) |

**Asset quality caveat.** The sheets look AI-generated. Pixel sizes vary within a sprite, there are coloured fringe
halos (red and yellow around the "!" marks), and the props in the RGB sheets sit on a painted background. Direct use
would look blurry. Sprites go through the conversion script in section 6. Icons, textures and props are redrawn as
crisp SVG on a 24 px or 32 px grid, using the sheets as the reference.

**Copy caveat.** Mockup text is mostly right. Two places need fixing to stay honest:
- The hero says "using weather and environmental data". Use "from recent cases, the season and rain", because the
  README reports that weather adds little.
- The evidence row must keep the "Weather adds modest value in some years and little or none in others" card.

---

## 4. Architecture

### 4.1 Stack (D4 = Vite)
- **Vite** multi-page build, plain JavaScript ES modules (no React, no TypeScript requirement). Node 20+ for the
  build only; the published site stays static.
- npm dependencies with exact versions in `site/package.json` + lockfile:
  - `gsap` **3.15.0** (core + ScrollTrigger + SplitText; all plugins are free since 3.13).
  - `three` **0.186.0**, imported dynamically on pages with a map (code-split chunk).
  - `vite` **8.3.1**. All three were released more than two weeks before 19 Oct 2026.
  - `maplibre-gl` only for the D9 comparison prototype (separate chunk, dropped if Three.js wins).
  - Dev only: `vite`. Tests run with Python Playwright, so no JS test runner is needed.
- Each page is an HTML entry with a module that mounts its sections. The app (section 10) is a small router plus views.
- Python stays the data side: scripts write JSON into `site/public/…`, which Vite copies to `docs/` on build.

**Build and deploy**
```
cd site && npm ci && npm run build      # writes pages + hashed assets into ../docs
```
- `vite.config.js`: `root: "site"`, `build.outDir: "../docs"`, `build.emptyOutDir: false` (so `docs/data/*.csv|json`,
  `demo.mp4`, `deck/`, `screenshots/`, `film/` are kept), hashed bundles under `docs/assets/build/`.
  A pre-build step deletes only `docs/assets/build/` so old hashed files don't pile up.
- `base: "/epilag/"` for GitHub Pages; `npm run dev` serves at `localhost:5173/epilag/`.
- Inputs: `site/index.html`, `site/web/index.html`, `site/drill/index.html`, `site/methodology.html`,
  `site/data/index.html`, `site/kit.html` (component kit, not linked from the site).
- The built `docs/` output is committed, as today, so GitHub Pages keeps serving `docs/` unchanged.

### 4.2 Source layout (`site/`)
```
site/
  package.json  package-lock.json  vite.config.js
  index.html  web/index.html  drill/index.html  methodology.html  data/index.html  kit.html
  src/
    css/      tokens.css  base.css  surfaces.css  components.css
    lib/      motion.js  pixel.js  mascot.js  voxel.js  data.js  i18n.js  icons.js  a11y.js  chart.js
    landing/  main.js  sections/*.js
    web/      app.js  router.js  views/*.js  logic.js  allocate.js  thresholds.js  brief.js  playbook.js  public.js  panels.js
    drill/    game.js  rules.js  board.js  hud.js  style.css
  public/                                   (copied as-is to docs/)
    sprites/  mosquito.json  frog.json      (text-grid poses + palette)
    icons/    *.svg                         (24 px pixel icons, shape-rendering: crispEdges)
    textures/ *.svg                         (tileable, subtle/standard/bold)
    seams/    seam-top.svg  seam-bottom.svg  seam-fill.svg
    fonts/    (D6)
    geo/      voxel_ph.json  voxel_regions.json   (from scripts/voxel_data.py)
    web/data/ *.json                        (from scripts/build_web.py)
    drill/    data.js                       (from scripts/drill_data.py)
```
Every page imports shared code from `src/lib/` and `src/css/`. Where this plan says `docs/assets/js/x.js` or
`docs/assets/...`, read `site/src/lib/x.js` or `site/public/...`; the built copies land in `docs/`.

### 4.3 URLs
| URL | Page | Notes |
| --- | --- | --- |
| `/epilag/` | Landing | `docs/index.html` |
| `/epilag/web/` | JS app | Reads `?page=` (existing deep links from README and old landing) and `#/view` |
| `/epilag/drill/` | 3D Dengue Drill | |
| `/epilag/methodology.html` | Methodology | Restyled |
| `/epilag/data/` | Open data | Restyled. File URLs unchanged (`epilag_forecast_*.csv/json`) |

---

## 5. Design system

### 5.1 Colour tokens (from the Visual foundations sheet)
```css
:root {
  --ink: #071711;  --forest: #08754F;  --sage: #789373;  --paper: #FBFAF4;  --amber: #F5A51C;  --sky: #BFE2EC;
  --lv-warning: #F04B2A;  --lv-watch: #F58220;  --lv-above: #F7C928;  --lv-normal: #0C7A55;  --lv-nodata: #C9CFC9;
  --night: #0A2A1D;  --night-2: #0E3726;      /* drill / dark sections (mockup dark green) */
  --line: #E4E6DC;  --muted: #4E5E55;  --surface: #FFFFFF;
}
```
Rules from the sheet: ink for all body and interface text, forest for emphasis, and blue for maps, rain and data
graphics only, never for text. Every level colour also carries a text label (never colour alone).
Check contrast: amber and yellow are for fills, not text on paper. White text on `--lv-watch` must meet 4.5:1, or use
ink text.

### 5.2 Type
- Display: Nimbus Sans Extra Bold, 56–72 px, tight leading (D6, fallback Inter Tight 800).
- Body: Regular, 18–24 px, line height 1.4–1.55.
- Section labels: 14–18 px, tracked uppercase, forest.
- Numbers: tabular figures.
- Two-tone headlines as in the mockup: line 1 ink, line 2 forest ("Rain starts the clock. / We read what comes next.").

### 5.3 Components (from the component sheet)
Buttons (pill, forest fill and ghost), level pill and status tile, priority row, compact status strip, evidence badge,
timeline rail (today, week node active and inactive, week bracket label), console frame (dark, modular),
scenario selector, allocation tokens, chart surface, action brief card, structural data badge, nav, footer links.
Each one gets a CSS class in `components.css` and a static demo in `docs/assets/kit.html`, a private page for checking
the components visually.

### 5.4 Icons
Six tool icons (Forecast Map, Area Detail, Action Plan, Resident Advisory, QC Barangay Planning, Did It Work),
open-data icons (database, CSV, JSON, download), and the data and limits symbols (observed, forecast, derived,
user-entered, unavailable, calendar gap, weather grid cell, reporting undercount). All are redrawn as 24 px pixel SVG
(`shape-rendering: crispEdges`), following getcko's 24-grid rule.

### 5.5 Textures and seams
Tileable SVGs at three intensities: `rain`, `contour`, `tracks` (mosquito footprints), `leaves`, `town` (pixel
skyline strip), `dither-lo/mid/hi` (fades into dark sections). Seam masks give a 16×96 px pixel zig-zag on section
edges (same technique as getcko's `.seam`).

---

## 6. Pixel sprite system

### 6.1 Conversion script: `scripts/sprites.py`
1. **Slice**: find connected alpha blobs in each RGBA sheet, then group nearby blobs into poses (wing, body and
   badge parts belong together). A small manual override table names each pose and fixes the grouping.
2. **Clean**: drop fringe pixels (red or yellow halo with low alpha or no neighbours), and threshold alpha at 50%.
3. **Grid**: downscale with nearest neighbour to a fixed grid (mosquito 32×32, frog 40×32; tune by eye), anchored at
   the feet or body centre so poses line up.
4. **Palette**: quantise to a fixed brand palette of about 8–10 letters (`K` ink outline, `G` body green,
   `D` dark green, `L` light belly, `A` amber eye, `W` wing, `w` wing shade, `T` tongue, `.` transparent).
5. **Export** `docs/assets/sprites/{mosquito,frog}.json`:
   `{ "palette": {...}, "size": [w,h], "anchor": [x,y], "poses": { "fly1": ["....KK..", ...], ... } }`
6. **Preview**: write a contact-sheet PNG in the scratchpad. A human fixes stray pixels in the JSON by hand. The
   JSON is the source of truth after this, and is versioned.

Pose catalogue:
- **Mosquito:** `fly1 fly2` (wing flap), `turn`, `dash`, `loop`, `pin`, `house`, `alert`, `ring`, `building`,
  `coin`, `clipboard`, `search`, `front`, `happy`, `check`, `sleepy`.
- **Frog:** `peek`, `watch`, `watchClose`, `idle`, `strike`, `gulp`, `chew`, `happy`.
- **Derived in code:** `blink` (eye rows swapped), `flip` (mirror), `hit` (white flash).

### 6.2 Runtime: `docs/assets/js/pixel.js`
- `grid(name, pose, {flip})` returns cached frozen rows.
- `bake(rows, palette)` returns a 1× offscreen canvas.
- `<pixel-sprite pose="fly1" scale="4">` custom element: draws a sprite crisply at the device pixel ratio.
- `cells(rows)` returns `[{x, y, color}]` for particle effects.
- `toTexture(rows)` returns a Three.js `CanvasTexture` with `NearestFilter`, for sprites inside 3D scenes.

### 6.3 Mascot controller: `docs/assets/js/mascot.js`
A port of getcko's controller to plain JS: one fixed `<canvas>` overlay, `register({id, section, slot, pose, flip,
target})`, `setPose(id, pose)`, `flow(sourceEl, targets, onArrive)`, `scatter()`, morph particles, a halo pulse on
the target (box-shadow ring, 2 pulses), random blinks, and DPR-aware redraws only when the scene changes.
Reduced motion: no particles; it appears in place.

---

## 7. Motion system

### 7.1 Tokens (`motion.js`)
```js
export const DUR  = { instant: .08, fast: .14, base: .22, slow: .36, pointer: .52 };
export const EASE = { out: "power3.out", inOut: "power2.inOut", point: "back.out(1.6)", step: "steps(2)" };
```
Plus custom eases `mosquitoFlit` (small sine wobble) and `frogHop` (hop arc), made with `CustomEase` or plain functions.

### 7.2 Helpers
- `reveal(el)`: rise 8 px plus fade, `DUR.base`, played once by ScrollTrigger.
- `stagger(els)`: the same with 0.06 s steps.
- `countUp(el)`: number tween for evidence stats.
- `halo(el)` / `unhalo(el)`: target ring pulse (getcko `Js`/`Ys`).
- `curtain(el, cell)`: pixel curtain over an element. Returns its cells so a timeline can shrink them.
- `route(svgPath, sprite)`: moves a sprite along a dotted SVG path, snapping to the cell.
- `once("intro")`: sessionStorage gate (wrapped in try/catch). `?intro` forces it.

### 7.3 Rules
- Every timeline lives inside `gsap.matchMedia()` with three branches: desktop, mobile (<1100 px) and reduced motion
  (final state, no movement).
- Animate only `transform` and `opacity` (plus CSS custom properties for colour states).
- Pause canvases and voxel scenes that are off screen (IntersectionObserver) or in a hidden tab.
- No scroll-jacking except the one pinned section, and only on desktop.

---

## 8. Landing page

Structure follows the final mockup. Each section lists its content, motion and mascot slot.

| # | Section | Content (from mockup) | Motion | Mascot |
| --- | --- | --- | --- | --- |
| 0 | **Intro** | Logo tile from mosquito pixels, "EpiLag-PH", badge "ACT WEEKS EARLIER." | 7.2 intro (about 3.5 s, skippable, once per session) | none |
| 1 | **Nav** | Logo · Story · Drill · Features · Action · Proof · Film · Methodology · **Open the app** | Fades in at the end of the intro. Sticky, paper blur. Active link follows scroll. | none |
| 2 | **Hero** | Label "THE RISK"; "Rain starts the clock. **We read what comes next.**"; support line; CTAs Open the app / Watch the film; trust row (Early warning · Local action · Healthier communities); **app preview window** (tabs Overview · Forecast Map · Area Detail · Action Plan; voxel PH map of the 2 Jun 2019 replay; legend; priority list Guimaras / Iloilo / Capiz with ranges; timeline 2 Jun 2019 → +2/+4/+8 weeks); pixel trees and house | Headline chars rise (SplitText). Curtain lifts off the window. **Hero loop** (6–7 s): mosquito flies the dotted route from the rain cloud, lands on Guimaras, halo, forecast chip, the timeline knob steps +2 → +8 weeks with voxel columns growing, and the beat row Rain · Forecast · Alert · Act lights up. | `hero` (pose `fly1`/`pin`) |
| 3 | **Problem** | "Dengue follows the rain. **Reports follow the hospitals.**"; prop chain: rain cloud (Week 0) → house (+1–2 weeks, mosquito populations increase) → water container (+2–4 weeks, people get sick) → sick residents (+4–8 weeks, cases reported) → hospital → ambulance; callout "There's a gap between changing weather and hospital reports. EpiLag-PH helps close it."; **Where EpiLag-PH helps** timeline: Today / Week 0 / 1–4 weeks / 4–8 weeks | **Pinned scrub** on desktop (7.1, getcko How section): the prop strip scrolls sideways, each step lights up (`--on`), its week label pops (`steps(2)`), connector dots appear, and the mosquito flies the dotted line above. Mobile: no pin, steps reveal as they scroll in. | `problem` (pose `house`, then `alert`) |
| 4 | **Dengue Drill** (dark) | "Play the 2019 outbreak. **Then play it again with EpiLag-PH.**"; 3 how-to rows (pick a region and budget · respond to rising cases · try again with forecasts); stats (about 5 minutes · 8 turns · 11 of 17 regions); CTAs Play the drill / See how it works; **console frame** with a live voxel Western Visayas board (Budget ₱5M · Week 6 of 17 · cases sparkline · level legend · Guimaras ring) and the frog in the corner | Dither seam into the dark section. The console boots: scanline sweep, then panels stagger in. The voxel board rotates slowly while in view (paused when off screen). The frog peeks up (`peek → watch`). | `drill` (frog `watch`) |
| 5 | **Six tools** | "Six tools. **Each one leads to an action.**"; cards 1–6 with pixel icons and arrows; open data row (CSV · JSON · download) | Cards rise in a stagger. Icons do a 2-frame hover (`steps(2)`). Data pixels flow into the CSV and JSON chips. The active card follows the viewport middle, and the mosquito walks beside it. | `tools` (pose `search`) |
| 6 | **From alert to action** | "Each alert **comes with a plan.**"; Guimaras card (forecast made 2 Jun 2019 · **35** cases forecast for the week ending 30 Jun · likely **15–65** · **82** cases were reported); tilted **Guimaras action brief** (priority areas, recommended actions); voxel Guimaras heat map; timeline Today / Weeks 1–2 / Weeks 2–4 with props (people, broom and bin, hospital) | The brief slides in with a slight rotation and its lines reveal. The numbers count up. The timeline nodes fill as you scroll (scrub). Guimaras voxels rise. | `action` (pose `clipboard`) |
| 7 | **Film + Inside the app** | "Can dengue be seen **before hospitals fill up?**"; "Follow the signal from rain to forecast to local action, in 1:58" (fix to the real film length, 1:48); video player (poster in the new style); app link list (Overview, Forecast Map, Area Detail, Action Plan, Did It Work?, For Residents) | Player frame reveal. The list items' arrows nudge on hover. | `film` (pose `front`) |
| 8 | **Evidence** | "Evidence from real outbreaks": **30 of 32** outbreaks flagged 4 weeks ahead · **79–100%** outbreak starts caught at watch · **70–92%** likely-range coverage, target near 80% · weather note card; link to the full "Did it work?" page | Badges stamp in (`back.out`). Numbers count up. | `proof` (pose `check`) |
| 9 | **Final CTA** | "Hospitals see dengue a month late. **EpiLag-PH sees it now.**"; support line; **Open EpiLag-PH**; trust row (Data-driven · Open access · Built for the Philippines); big frog | **Finale**: the mascot mosquito flies in, the frog goes `watch → strike` (tongue drawn as a pixel line to the mosquito), `gulp → chew → happy`, and pixel sparks. Plays once per visit, replayable on click. | `cta` (frog) |
| 10 | **Footer** | Logo, nav links, Methodology · Open data · Source code · External link; data credits; PJDSC 2026 | Leaf-canopy seam on top. | none |

Accessibility: mascot canvases are `aria-hidden`. The hero map has a text alternative (the priority list). The pinned
section reads correctly without motion. All CTAs are real links.

---

## 9. Voxel map engine

### 9.1 Data: `scripts/voxel_data.py`
- Input: `app/data/province.geojson` (86 units, `unit_id` like `PH01028`) and `app/data/region.geojson`
  (17 units, `R_REGION_*`). Quezon City has no polygon, so it is drawn as a marker column inside NCR.
- Rasterise each polygon onto a grid with an equirectangular projection, longitude × cos(mean latitude) (the same
  projection as `drill_data.py`). Use point-in-polygon on cell centres in vectorised numpy (no new dependency).
- Grids:
  - **National**: cell 0.05° (about 194×330 cells, about 12k land cells). Unit index per cell.
  - **Per region** (drill boards, Guimaras close-up): cell about 0.015°, fitted to a fixed board.
  - **Mobile**: national at 0.08°.
- Output: `docs/assets/data/voxel_ph.json`, `voxel_regions.json`:
  `{cell, origin, w, h, units: ["PH01028", ...], rows: ["<RLE of unit index per row>", ...]}` (run-length so it stays
  well under 200 kB).
- Also write a land and coast mask so the coastline gets a "beach" voxel tint and a 1-step sea-shelf outline.

### 9.2 Runtime: `docs/assets/js/voxel.js`
```js
const map = createVoxelMap(canvas, { grid, pixelScale: 3, iso: true });
map.setValues(unitId => ({ level, ratio }));   // colour by level, height by cases ÷ epidemic line
map.animateTo(values, { duration, stagger: "south-north" });
map.highlight(unitId); map.ring(unitId, color); map.on("pick", unitId => …);
map.rain(intensity); map.swarm(unitId, count); map.dropToken(unitId);
map.focus(unitIds | "all"); map.pause(); map.resume(); map.dispose();
```
- **Rendering**: Three.js `InstancedMesh` (one cube geometry, about 12k instances), `MeshLambertMaterial` with
  per-instance colour, one directional plus hemisphere light, flat shading. Orthographic camera at an isometric angle
  (yaw 45°, pitch about 35°).
- **Pixel look**: render to a low-resolution target (`pixelScale` 2–4) and upscale on screen with
  `image-rendering: pixelated`. Light posterisation in the colour ramp. 1-voxel ink outline via an edge pass on
  the low-resolution buffer.
- **Heights**: base 1 voxel. Columns stack by level (normal 1, above usual 2, watch 3, warning 4), or continuously by
  cases ÷ epidemic line, capped at 6. Animate with GSAP on a per-unit value, then rewrite the instance matrices for
  that unit.
- **Picking**: raycast against instances, then cell, then unit. Hover tooltip as an HTML overlay positioned by
  projecting the unit centroid.
- **Effects**: rain as instanced 1×3 voxels falling. Swarms as billboard sprites from `pixel.js` textures. Rings as a
  voxel square outline that pulses. Tokens as a voxel shield that drops with a bounce.
- **Accessibility and fallback**: every map has a linked list or table of units with the same data, and keyboard focus
  moves through that list (it also highlights on the map). No WebGL, or `prefers-reduced-data`, means a 2D top-down
  pixel canvas from the same grid.
- **Performance budget**: at most 15k instances; 60 fps on a mid laptop and at least 30 fps on a mid phone; render
  only on change or animation; pause when off screen.

Used by: landing hero preview, drill teaser console, Guimaras close-up, app forecast map, area detail mini-map,
budget map, residents page, drill board, methodology figures.

### 9.3 Patterns borrowed from Room TBA
Room TBA (`src/components/svelte/Building3DViewer.svelte`, `Map.svelte`, MIT) solves the same Three.js problems
we have. Borrow the patterns (and credit the repo in a code comment where code is adapted):

| Pattern in Room TBA | Where | Our use |
| --- | --- | --- |
| Three.js and addons loaded with `import()` only when the 3D view opens | `Building3DViewer.svelte:287–300` | Load `three` only on pages and views with a map, after first paint; landing hero shows a static pixel poster until it loads |
| Footprint → local coordinates → `THREE.Shape` → `ExtrudeGeometry` (no bevel), plus `EdgesGeometry` outlines with `polygonOffset` so lines win the depth test | `:468–520` | Ink outlines around each province's voxel block (1-voxel outline); optional "smooth extrusion" mode for the methodology page |
| `CSS2DRenderer` labels placed at 3D points, with overlap culling each frame | `:532`, `:601`, `cullOverlappingLabels` | Province names, forecast tags (▲35) and "+N cases" floaters as crisp HTML over the 3D scene, hidden when they collide |
| Raycast only when the pointer or camera actually moved | `:765–775` | Hover picking on the voxel map and drill board without per-frame cost |
| `OrbitControls` with clamped tilt, camera tweens and a compass bearing | `:80`, `:382`, `stepCameraTween` | Bounded drag-orbit on the drill board; tween to a province on selection; reset each turn |
| `renderer.setPixelRatio(min(dpr, 2))`, `ResizeObserver` on the container | `:369`, `:750` | Same, then our low-resolution pixel render target on top |
| Full disposal of geometries, materials, textures and the renderer on close | `:729–743` | `map.dispose()` when switching app views or drill rounds (no GPU leaks) |
| MapLibre `fill-extrusion` with a 2D/3D toggle by pitch (`map-dimension.ts`) | `Map.svelte` | **Comparison prototype for the app's forecast map (D9)**: our voxel cells as square GeoJSON polygons with `fill-extrusion` heights (no basemap tiles needed), giving real pan, zoom and geography. Built after the Three.js map, compared side by side, and the better one is kept. |

Not borrowed: the Svelte/Astro app structure, MapLibre basemaps and terrain (need tile servers), campus data and editor.

---

## 10. JavaScript web app

Replaces `docs/web/` (stlite). The same 8 pages, both data panels, latest and replay modes, 2/4/6/8-week horizons,
and EN/FIL.

### 10.1 Data export (`scripts/build_web.py`, rewritten)
Write per-panel JSON to `docs/web/data/`. Columns are kept compact and floats rounded as the current CSV export does
(`%.4g`):

| File | From | Loaded by |
| --- | --- | --- |
| `{panel}_forecast.json` | `app/data/{panel}_forecast.parquet` | home, map, budget, public |
| `{panel}_history.json` | `{panel}_history.parquet` | unit, replay |
| `{panel}_thresholds.json` | `{panel}_thresholds.parquet` | all (alert level) |
| `{panel}_backtest.json` | `{panel}_backtest.parquet` | replay, proof |
| `{panel}_drivers.json` | `{panel}_drivers.parquet` | unit (why flagged) |
| `qc_barangays.json` | `qc_barangays.csv` | qc |
| `reports.json` | `reports/*.csv` | proof |
| `meta.json` | units, names, populations, region of each unit, data dates | all |

Fetch lazily per page and cache in memory. Show a skeleton while loading.

### 10.2 Logic port (Python → JS, one module each)
| Python (source) | JS module | Notes |
| --- | --- | --- |
| `alert_level()` `app/streamlit_app.py:560` | `logic.js` `alertLevel` | warning if q50 > epidemic; watch if q90 > epidemic; above if q50 > alert |
| `replay_origins()`, `replay_forecast()` `:569`, `:578` | `logic.js` | Replay of a past week from the backtest |
| `_thresholds()`, `threshold_series()` `:597`, `:799`; `src/thresholds.py` | `thresholds.js` | usual = mean, epidemic = mean + 2 SD, per week of year |
| `brief_table()`, `brief_markdown()` `:636`, `:643` | `brief.js` | Action brief rows and download (Markdown, plus print CSS for PDF) |
| `src/allocate.py` | `allocate.js` | Fractional knapsack on cases averted per peso, low/central/high |
| `T`, `LEVEL_NAME`, `ALERT_TEXT` `:33–:195` | `i18n.js` | EN and FIL strings, moved to `docs/web/i18n/{en,fil}.json` |
| `PLAYBOOK` `:197` | `playbook.js` | When / do this / EpiLag-PH gives you, per level |
| `FEATURES` `:256` | `features.js` | Shared with the landing page's Six tools |
| `PUBLIC` `:1052` | `public.js` | Residents' outlook text, 4S steps, warning signs, share message |
| `PANELS` `:24` | `panels.js` | Panel labels, notes, geo |

**Parity rule**: the JS output must equal the Python output on the same inputs (section 13.2).

### 10.3 Shell
- Top bar (getcko-style pill nav, mockup app window): logo; tabs Overview · Forecast map · Area detail · Action plan ·
  For residents · QC barangays · Did it work? · Data & limits; EN/FIL switch.
- Control bar: Data (Regions + QC / Provinces) · Forecast (Latest / Replay a past week + week picker) · Weeks ahead
  (2/4/6/8).
- State lives in the URL (`?page=map&panel=province&mode=replay&origin=2019-06-02&h=4&lang=fil`), so every view
  can be linked and old `?page=` links keep working.
- "Replay the June 2019 outbreak" shortcut, as on the current home page (`go_replay_story`).

### 10.4 Views (`docs/web/js/views/`)
| View | Keeps (from Streamlit page) | New in JS |
| --- | --- | --- |
| `home` | Areas to act on now (counts by level), "Why weeks matter" timeline, tool cards, Drill banner, action brief + download | Voxel mini-map, mascot slot, count-up |
| `map` | Alert map, priority list, replay note, `data-crossed`/`data-flagged` claim | Voxel map with level heights, timeline scrubber across horizons, hover cards, list ↔ map link |
| `unit` | Forecast range against the epidemic threshold, history, checklist, drivers (SHAP groups), brief download | SVG chart with range band and threshold line, drivers bar, mini voxel locator |
| `budget` | Budget input, ranked plan, low/central/high, editable costs and effects, CSV export | Peso-token animation into areas, voxel map coloured by allocation |
| `public` | This week's level in FIL/EN, 4S steps, warning signs, share message | Large frog or mosquito sprite per level, copy-to-clipboard |
| `qc` | Barangay shortlist from yearly shares | Ranked bars, pixel icons |
| `proof` | Backtest errors vs baselines, early-warning hits and false alarms, weather ablation | SVG charts in the honest-testing style from the mockup sheet |
| `about` | Data sources, limits, licences | Data and limits symbols legend |

Charts: small hand-written SVG helpers (`chart.js`: line, band, bars, sparkline). No chart library.

---

## 11. 3D Dengue Drill

### 11.1 Keep exactly
- Data: `docs/drill/data.js` from `scripts/drill_data.py` (weeks, turns, kit, regions → provinces with cases, rain,
  epi, usual, fc).
- Rules and scoring: `peak`, `score`, `autopilot` (`docs/drill/index.html:137–168`), mirrored in `drill_data.py`.
  Move them to `docs/drill/rules.js` and keep the Python copy in sync. The parity test checks both.
- Flow: title → rain receipt → round 1 (reports only) → report → round 2 (EpiLag intel) → report → debrief with the
  2 computer players and the honest 11/6 region note.

### 11.2 Changes
| Part | Now | New |
| --- | --- | --- |
| Board | 2D SVG paths, heat fill | **Voxel region board** (`voxel.js`, per-region grid). Column height = cases ÷ epidemic line this week; colour = same heat ramp. Camera orbits a little with drag (bounded), resets on turn. |
| Selection | Click a path | Raycast pick plus a **province list** (keyboard and screen reader), synced both ways |
| Round 2 intel | SVG rings + ▲ labels, radar sweep | Voxel rings pulse by level, projected HTML forecast tags, a scan-line sweep across the voxels |
| Teams | SVG shield badge | Voxel shield token drops with a bounce and dust pixels; the count shows on the token |
| Mosquitoes | 2D canvas specks | Billboard pixel mosquitoes (`fly1/fly2`) swarming over provinces, count from rain (same formula) |
| Rain | 2D canvas streaks | Instanced voxel rain inside the 3D scene |
| Turn change | "2 weeks later" warp overlay | Same overlay, plus columns animating to the new week and "+N cases" floaters projected from 3D |
| Title screen | Region rail + SVG outline | Region rail + rotating voxel region preview; the frog peeks from the bottom |
| Report and debrief | Grade, badges, sparklines, bars | Same content in the console-frame style; the frog's reaction depends on the grade (S/A: `strike → happy`, B: `watch`, C/D: `peek`) |
| Style | Dark terminal (Chakra Petch) | Mockup dark green console frame, brand type, level tokens; the sound effects stay |

### 11.3 HUD (from the mockup console)
Budget · Week n of 8 (dates) · Cases this week with a sparkline and % change · Rain this week · Outbreak pressure
meter · level legend · **Take action** panel · End turn.

### 11.4 Action types (decision D5)
The mockup shows 4 actions with different costs. Adding them means each action needs its own effect size from
published evidence (the current single effect is cautious, 10/30/50% from Bowman et al. 2016). Hospital preparation
reduces severe outcomes, not cases, so it would need a second score. **Recommendation**: ship the 3D drill with one
team type first. Show the other actions as the cost breakdown of a team (clean-up + covers + info), not as separate
choices. Revisit after we find sources.

---

## 12. Other pages and media

| Task | Output |
| --- | --- |
| Restyle methodology: new tokens, type, textures; voxel figures where maps appear; keep all content | `docs/methodology.html` |
| Restyle open data: file table with pixel CSV/JSON icons, column definitions; file URLs unchanged | `docs/data/index.html` |
| Rewrite screenshots for the new static site: no Streamlit selectors, serve `docs/` locally, capture landing sections, every app view (latest + 2019 replay), drill title / round 2 / report, at 1440 px and 390 px | `scripts/screenshots.py`, `docs/screenshots/*.png` |
| README: new screenshots, links, "Run it" section (serve `docs/`, `python scripts/build_web.py`), Streamlit marked as local or legacy, tests | `README.md` |
| Film (D7): new-style scenes in `docs/film/index.html`, re-record with `scripts/record_film.py` | `docs/film/*`, `docs/demo.mp4` |
| Deck refresh (optional): new screenshots and palette | `docs/deck/deck.html`, `EpiLag-PH_deck.pdf` |
| Social card: `og.png` 1200×630 in the new style, meta tags on every page | `docs/og.png` |

---

## 13. Testing and quality

### 13.1 Python (pytest, existing suite)
- `tests/test_allocate.py` stays.
- `tests/test_app.py` (Streamlit) stays while `app/streamlit_app.py` exists (D8).

### 13.2 Parity tests (`tests/test_web_logic.py`)
Serve `docs/` with `http.server` in a fixture, open the page in Playwright, call the JS functions through
`page.evaluate`, and compare with Python on the same inputs:
- `alertLevel` vs `alert_level` for every unit and horizon in both panels.
- `allocate` vs `src/allocate.py` across budgets ₱0.5M–₱20M.
- `replayForecast(2019-06-02)`: crossed and flagged counts, and the README claim that **30 of 32** provinces were
  flagged.
- Drill `score` and `autopilot` vs `scripts/drill_data.py` `play()` for all 17 regions, so the 11/1/5 result holds.

### 13.3 Site checks (`tests/test_site.py`, Playwright)
For every page (landing, 8 app views × 2 panels × 2 modes × 2 languages, drill screens, methodology, data):
- Loads with no console errors and no failed requests.
- Works at **390 px** (no horizontal scroll) and 1440 px.
- With `reducedMotion: "reduce"`: no pinned section, mascot static, content fully visible.
- Keyboard: tab order reaches every control; the province list drives the 3D board; focus is visible.
- axe-core scan (injected from a pinned CDN build): no serious or critical issues.
- WebGL disabled: maps fall back to 2D.

### 13.4 Budgets
| Metric | Target |
| --- | --- |
| Landing first contentful paint | < 1.5 s on fast 4G |
| App ready (latest view) | < 3 s (was about 60 s) |
| JS from CDN (gzip) | GSAP + plugins about 60 kB; Three.js about 160 kB, loaded only on pages with a 3D map, after first paint |
| Data per view | < 500 kB (lazy) |
| Frame rate | 60 fps desktop, at least 30 fps mid phone; scenes paused when off screen |

`requirements.txt`: add `playwright` (already used by `scripts/record_film.py` and `scripts/screenshots.py`,
but not listed).

---

## 14. Phases and checklist

Each phase ends with a commit on its own branch and a PR, following the repo history (`Romeo-04/<topic>` branches
merged by PR).

### Phase 0: decisions (done 19 Oct 2026)
- [x] D4 build setup: Vite, `site/` → `docs/`
- [x] D5 drill actions: one team type
- [x] D6 font: check Nimbus Sans licence, else Inter Tight
- [x] D7 film: re-record in Phase 7
- [x] D9 app forecast map: Three.js voxel engine

### Phase 0.5: Vite scaffold
- [x] `site/` with `package.json` (exact versions), `vite.config.js` (multi-page, `outDir ../docs`, `emptyOutDir: false`,
      `base /epilag/`), pre-build clean of `docs/assets/build/` (`site/scripts/clean-build.mjs`)
- [x] Stub `kit.html` builds to `docs/kit.html`; `vite preview` serves it and the existing pages under `/epilag/`
- [ ] Python scripts write to `site/public/…`: done page by page in the phase that rebuilds the page that reads them,
      so the current pages keep working until they are replaced
- [x] README "Run it": `cd site && npm ci && npm run dev | build`
- **Done when** `npm run build` produces `docs/` pages that open from a local static server under `/epilag/`, and
  nothing outside `docs/assets/build/` and the rebuilt pages changes.

### Phase 1: design system
- [x] `site/src/css/tokens.css`, `base.css`, `surfaces.css`, `components.css`
- [x] Font loading (D6: Inter Tight from Google Fonts)
- [x] Pixel icons as text grids → crisp SVG (`site/src/lib/icons.js`): UI chrome (12 grid), 6 tools and open data
      (16 grid), frog-face logo
- [ ] Data and limits symbols (observed, forecast, derived, user-entered, unavailable, calendar gap, weather grid
      cell, reporting undercount): add with the app's "Data & limits" view (Phase 5)
- [x] Textures (field, rain, tracks, contour, leaves, town, dither lo/mid/hi) and stepped edge masks, generated by
      `site/scripts/make-textures.mjs`
- [x] `site/kit.html` → `docs/kit.html` showing every component; checked at 1440 px and 390 px (no horizontal scroll)
- Contrast: white text on warning red is 3.7:1, so level pills use ink text on warning, watch and above usual
  (`--lv-*-ink` tokens); sage is never used for text
- **Done when** the kit page matches the mockup's component sheet and foundations sheet side by side.

### Phase 2: sprites and the mascot
- [x] Sprite art from Codex (`site/briefs/sprites.md` → `UI mockup/sprites/`, 1 px = 1 art pixel, exact palette);
      revision round requested for frog `happy`/`chew` and mosquito `sleepy`/`fly2`
- [x] `scripts/sprites.py` (sheet → text-grid JSON, counts off-palette pixels; 0 on the first Codex set)
- [x] `mosquito.json` (12 poses), `frog.json` (8 poses)
- [x] `pixel.js` (load, mirror, blink, bake, cells, `<pixel-sprite>`), `mascot.js` (slots, morph, scatter, halo,
      blink, reduced motion). Particle `flow()` into cards: add with the landing page (Phase 4)
- [x] `motion.js` tokens and helpers
- **Done when** the kit page shows every pose crisp at 2×/4×/8×, and a test page morphs the mosquito between 3 slots
  on scroll, including a reduced-motion version.

### Phase 3: voxel engine
- [x] `scripts/voxel_data.py` → `site/public/geo/voxel_ph.json` (54 kB: provinces and regions at 0.05° and 0.08°,
      QC marker) and `voxel_regions.json` (33 kB: one board per Dengue Drill region); 4 s, numpy only
- [x] `voxel.js`: one InstancedMesh, low-resolution render scaled with `pixelated`, orthographic camera, level
      heights with tweening, lit tops and shaded walls, picking, highlight, `project()` for HTML labels, render on
      demand, 2D fallback without WebGL, full disposal
- [ ] Rings, rain, swarms, tokens, drag-orbit: add with the 3D drill (Phase 6), where they are used
- [ ] Pause when off screen: add with the landing page (Phase 4)
- **Done when** a test page shows the 2 Jun 2019 province replay as voxels with the correct levels, picking works,
  and the 2D fallback works.

### Phase 4: landing page
- [x] Sections 0–10 (section 8) with their motion and mascot slots (`site/index.html`, `site/src/landing/`)
- [x] Hero loop and the live preview window, from `scripts/landing_data.py` → `site/public/data/replay_2019-06-02.json`
      (same method as the app's replay). The backtest has 4- and 8-week horizons only, so the timeline shows
      +4 and +8 weeks (the mockup's +2 is not available). Priority list is computed (Guimaras, Capiz, Zamboanga del
      Sur at 4 weeks), not the mockup's example. The "30 of 32" claim is recomputed from the data (30/32 at 4 weeks).
- [x] Pinned problem section (desktop) and scrubbed mobile version
- [x] Finale (frog catches the mosquito; "Again" replays; end pose under reduced motion)
- [x] Props sheet from Codex (12 props, 48×48) for the problem chain, hero and action steps
- [x] Checked at 1440 px and 390 px: no horizontal scroll, no console errors or failed requests; reduced motion
      shows every section (only the finale's "Again" button stays hidden)
- **Done when** it matches the final mockup at 1440 px, works at 390 px, the reduced-motion version reads fully, and
  every number matches the README.

### Phase 5: JavaScript web app
- [x] `build_web.py` JSON export: columnar tables in `site/public/web/data/` (largest view about 140 kB gzip), plus
      `site/src/app/i18n.json` read from `app/streamlit_app.py` with `ast`, so both apps share the EN/FIL copy
- [x] Logic modules + parity tests passing: `site/src/app/logic.js`; `tests/test_web_logic.py` (21 tests: alert
      levels, thresholds, replay forecasts for 4 weeks of both panels, the 30-of-32 claim at 4 weeks, the budget
      plan at PHP 0.5M–20M and with custom actions)
- [x] Shell, router, controls, i18n (`site/web/index.html`, `site/src/app/main.js`): state in the URL, lazy views
- [x] 8 views (section 10.4), with 3D pixel maps on the forecast map (hover card, click to the area, list ↔ map) and
      the action plan (spend by area); SVG charts in `site/src/app/chart.js`; Quezon City drawn as its own marker
      area inside NCR (`decode(grid, { markers })`)
- [x] Downloads (action brief Markdown, all forecasts CSV, funded plan CSV)
- [x] Old `?page=` links work (same URL, same parameter)
- [x] Data and limits symbols (8 pixel icons) on the Data & limits view
- [x] Checked: 8 views × 1440 px and 390 px, both panels, both modes, EN and FIL, reduced motion: no console errors,
      no failed requests, no horizontal scroll. Ready in about 2.9 s on throttled fast 4G (was about 60 s).
- [x] `docs/web/epilag_app.zip` (stlite) retired (D8); `app/streamlit_app.py` stays for local use
- [x] D9 comparison: MapLibre `fill-extrusion` prototype (`site/src/lib/maplibre-map.js`, hidden `?map=maplibre` on
      the forecast map). Result:

      | | Three.js voxel map | MapLibre fill-extrusion |
      | --- | --- | --- |
      | Look | Crisp pixel-art cubes (low-res render, `pixelated`), matches the brand | Smooth, antialiased; reads as a normal 3D map |
      | Pan, zoom, rotate | Fixed camera (drag-orbit comes in Phase 6) | Built in |
      | Bundle (gzip) | 187 kB, already used by the landing page and the drill | 210 kB + 9 kB CSS, extra |
      | Frame rate (1440 px, idle) | 60 fps | 60 fps |

      **Kept: Three.js** (brand look, one engine for the landing, app and drill, smaller). The prototype stays behind
      the hidden switch until the team has compared them, then goes with the `maplibre-gl` dependency.
- **Done when** every feature of the Streamlit app is present, parity tests are green, and the app is ready in under 3 s.

### Phase 6: 3D Dengue Drill
- [x] `site/src/drill/rules.js` extracted (peak, score, computer players, grade, heat, pressure); parity:
      `tests/test_drill_rules.py` (bots for all 17 regions and one-team scores equal `scripts/drill_data.py`; the
      11/1/5 summary holds) and a one-off check against the old page (102 random plans, every score identical)
- [x] Data moved to `site/public/drill/data.json` (no SVG outlines, 80 kB instead of 255 kB); `drill_data.py`,
      `voxel_data.py` and `landing_data.py` read or write it there
- [x] Voxel board (`site/src/drill/board.js` on `voxel.js`): column height = cases ÷ epidemic line, heat colours,
      bounded drag-orbit with reset, pick ↔ province list (keyboard and screen reader) in sync, intel rings pulsing
      by level and a scan line (round 2), projected names, forecast tags and "+N cases" floaters, shield tokens that
      drop with a bounce and dust, pixel mosquitoes swarming by rain, voxel rain on turn change
- [x] `voxel.js` gained what the board needs: tickers (paused off screen), drag-orbit, `setView`, scene access
- [x] Title (region rail + turning 3D preview + frog peeking), rain receipt, HUD from the mockup console (budget
      tokens, week n of 8, cases with sparkline and change, rain, pressure meter), Take action panel (one team type,
      D5, with its cost breakdown), reports and debrief restyled; the frog reacts to the grade
- [x] Checked: full 2-round games at 1440 px and 390 px with no errors or horizontal scroll, and a keyboard-only round
- **Done when** a full 2-round game plays on desktop and phone, the scores equal the current version for the same
  moves, and keyboard-only play works.

### Phase 7: pages, media, quality
- [ ] Methodology and open data restyle
- [ ] Screenshots script rewrite + new screenshots
- [ ] README update
- [ ] og image + meta
- [ ] Film re-record (if D7)
- [ ] Deck refresh (optional)
- [ ] `tests/test_site.py` green (phones, reduced motion, keyboard, axe, no console errors)
- [ ] Retire `docs/web/epilag_app.zip` + stlite shell (D8)
- **Done when** all tests are green, Lighthouse accessibility is at least 95 on the landing page and the app, and the
  README links and images all resolve.

Suggested order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7. Phases 4 and 5 can run in parallel after 3, because both use
the shared assets.

---

## 15. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| AI-generated sprite sheets don't convert cleanly | Messy sprites | The script gets close and a person fixes the JSON. Treat the JSON as source. |
| 3D is heavy on low-end phones | Jank, battery drain | Lower resolution grid on mobile, pixel render target, render on demand, pause off screen, 2D fallback |
| 3D canvases aren't accessible | Fails keyboard and screen-reader users | Every map has a synced list or table; keyboard drives the map |
| JS port drifts from the Python logic | Wrong alerts or budgets | Parity tests (13.2) in CI; keep the Python app until parity is proven |
| Motion overload | Distracts from the message | One mascot, one pinned section, everything skippable; reduced-motion version |
| Nimbus Sans licence | Can't self-host | Inter Tight fallback (D6) |
| Copy drift from the mockup | Over-claiming | All numbers from the README; weather wording fixed (3.2) |
| Drill actions without evidence | Unfounded scores | One team type until sources exist (11.4) |
| CDN outage | Site breaks | Pinned versions; optionally vendor GSAP and Three.js into `docs/assets/vendor/` |
| Scope creep | Late delivery | Phase gates with "done when" checks; landing + app first, film last |

---

## 16. File map

**New (source)**
```
REDESIGN_PLAN.md
site/  (whole tree, see 4.2)
scripts/sprites.py  scripts/voxel_data.py
tests/test_web_logic.py  tests/test_site.py
```

**Generated by the build (committed)**
```
docs/index.html  docs/web/index.html  docs/drill/index.html  docs/methodology.html  docs/data/index.html
docs/assets/build/*  docs/sprites/  docs/icons/  docs/textures/  docs/seams/  docs/geo/  docs/web/data/  docs/og.png
```

**Rewritten**
```
scripts/build_web.py (JSON into site/public/web/data)  scripts/drill_data.py (output path only → site/public/drill/data.js)
scripts/screenshots.py  README.md  requirements.txt (+ playwright)  .gitignore (+ site/node_modules)
```

**Unchanged**
```
src/*  app/data/*  reports/*  scripts/drill_data.py (unless D5 changes rules)  scripts/export_open_data.py
docs/data/*.csv|json  docs/deck/*  (until Phase 7)
```

**Retired after parity (D8)**
```
docs/web/epilag_app.zip  (stlite shell in docs/web/index.html is replaced)
app/streamlit_app.py + tests/test_app.py → kept for local use, or removed in a later PR
```
