# Asset brief: EpiLag-PH pixel sprites (mosquito + frog)

For: Codex (image generation). From: the EpiLag-PH redesign (`REDESIGN_PLAN.md`, section 6).
Style reference: `UI mockup/844825300_…png` (frog sheet) and `UI mockup/845642964_…png` (mosquito sheet).
Keep the same characters, but redraw them as **true pixel art** on a strict grid.

## Why the format is strict
A script turns every sprite into a text grid (one letter per colour) and then animates the pixels:
blinks, wing flaps, the mosquito breaking into pixels and re-forming. This only works if each image pixel is
exactly one art pixel and uses only the palette colours below.

## Hard rules (every file)
1. **PNG, RGBA, 1 image pixel = 1 art pixel.** No upscaling. We scale it up in code.
2. **No anti-aliasing, no blur, no gradients, no glow, no drop shadows.** Every pixel is either fully transparent
   (alpha 0) or fully opaque (alpha 255).
3. **Only the palette colours below**, with exact hex values. Nothing else, including near-misses like `#072711`.
4. **1-pixel outline** in Ink `#071711` around each character (selective outline is fine on the light side).
5. **Light from the top left.** Highlights go top-left, shade goes bottom-right.
6. **Same canvas size and anchor for every pose** of a character, so poses swap without jumping (see below).
7. Transparent background. No halos or stray pixels around the edges.

## Palette
| Letter | Name | Hex | Used for |
| --- | --- | --- | --- |
| K | Ink | `#071711` | outlines, pupils, legs |
| D | Body dark | `#1F3320` | mosquito body, frog spots |
| G | Body | `#3D6B35` | frog body |
| H | Body light | `#6E9A4A` | frog highlights |
| B | Belly / stripes | `#F2E3B3` | frog belly, mosquito stripes, toes |
| A | Amber | `#F5A51C` | eye rings, toe tips, alert marks |
| W | White | `#FFFFFF` | eye whites, eye glint |
| L | Wing light | `#D5E3DA` | mosquito wings |
| M | Wing shade | `#A8BFB2` | mosquito wing shade |
| T | Tongue | `#E5604F` | frog tongue |
| R | Alert red | `#F04B2A` | "!" marks only |

## Mosquito: `mosquito.png`
- **Frame:** 32 × 32 px. **Anchor:** body centre at (16, 18) in every frame.
- **Sheet:** frames left to right in one row, in the order below (so `mosquito.png` is 32·N × 32).
  Also export each frame as `mosquito_<name>.png`.
- **Facing:** right. We mirror in code for left.

| # | Name | Pose |
| --- | --- | --- |
| 1 | `fly1` | Flying, wings up |
| 2 | `fly2` | Flying, wings down (same body as `fly1`, only the wings move) |
| 3 | `turn` | Three-quarter view, turning toward the viewer |
| 4 | `dash` | Fast flight, body tilted forward, 2–3 speed-line pixels behind |
| 5 | `pin` | Hovering, pointing down with the proboscis (as if marking a map spot) |
| 6 | `alert` | Surprised: wide eyes, red "!" above the head |
| 7 | `clipboard` | Holding a small clipboard with checklist lines |
| 8 | `search` | Holding a small magnifying glass |
| 9 | `front` | Facing the viewer, wings spread |
| 10 | `happy` | Eyes closed in a smile (^ ^) |
| 11 | `check` | Next to a small green check disc |
| 12 | `sleepy` | Eyes half closed, drooping |

## Frog: `frog.png`
- **Frame:** 48 × 40 px. **Anchor:** feet on the bottom row (y = 39), body centred at x = 24.
- **Sheet:** one row in the order below. Also export each frame as `frog_<name>.png`.
- **Facing:** left (toward the mosquito in the finale). We mirror in code.

| # | Name | Pose |
| --- | --- | --- |
| 1 | `peek` | Only the eyes and top of the head above the bottom edge (rows below are transparent) |
| 2 | `watch` | Sitting, looking up and left |
| 3 | `watchClose` | Sitting, leaning forward, eyes wide |
| 4 | `idle` | Sitting, relaxed |
| 5 | `strike` | Mouth open, tongue starting out (tongue reaches the frame edge at the mouth height) |
| 6 | `gulp` | Mouth closed, cheeks puffed |
| 7 | `chew` | Chewing, one eye squinting |
| 8 | `happy` | Eyes closed in a smile (^ ^) |

The long tongue is drawn in code (a pixel line from the mouth to the mosquito). Only draw the start of the
tongue in `strike`, and mark the mouth position in a reply: `mouth = (x, y)`.

## Nice to have (same rules, 48 × 48 each, one sheet `props.png`)
Rain cloud with drops · sun · house with tree · water container with a mosquito · two sick residents · hospital ·
ambulance · pixel tree · small house. These are for the "Dengue follows the rain" chain on the landing page.
Props may also use Sky `#BFE2EC`, Sky dark `#7FB9CB`, Roof red `#C8553D` and Wall `#F3EEE0`.

## Deliverables
```
mosquito.png  mosquito_<name>.png ×12
frog.png      frog_<name>.png ×8
props.png     (optional)
notes.txt     frog mouth position; anything that deviates from this brief
```
Put them in `UI mockup/sprites/`. The script `scripts/sprites.py` will read them from there.

## Checks before sending
- Open each PNG at 800% zoom: hard square pixels only, no soft edges.
- Count the colours: only the palette above (plus transparent).
- Flip through the frames: the body does not jump between poses.
