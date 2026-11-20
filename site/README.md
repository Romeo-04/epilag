# Website, app and game (`site/`)

The source of everything at [romeo-04.github.io/epilag](https://romeo-04.github.io/epilag/). It is a static,
multi-page [Vite](https://vite.dev/) site with no server and no database. `npm run build` writes it to
[`docs/`](../docs/), which GitHub Pages serves.

```bash
npm ci
npm run dev        # http://localhost:5173/epilag/
npm run build      # clears old bundles in docs/assets/build, then builds into ../docs
npm run preview    # serves the build
```

The data the pages load comes from the Python side: run `python scripts/build_web.py` (and the other
[scripts](../scripts/README.md)) first when the forecasts change.

## Pages
| Page | Source | What it is |
| --- | --- | --- |
| `/` | `index.html`, `src/landing/` | The landing page, with the 2019 replay and the demo video |
| `/web/` | `web/index.html`, `src/app/` | The dashboard for health offices: overview, forecast map, area pages, budget plan, proof, residents' page |
| `/drill/` | `drill/index.html`, `src/drill/` | Dengue Drill, the 3D game |
| `/methodology.html` | `methodology.html`, `src/pages/methodology.js` | How the system works, the pilot plan and the roadmap |
| `/research.html` | `research.html`, `src/pages/research.js` | The research after the first round, with a reader for its documents |
| `/data/` | `data/index.html`, `src/pages/data.js` | Open data downloads and alert feeds |

## Source (`src/`)
| Folder | What it holds |
| --- | --- |
| `app/` | The dashboard. `logic.js` holds the alert, threshold, replay and track-record rules (mirrored from `src/` in Python and checked by `tests/test_web_logic.py`); `data.js` loads the JSON; `views/` has one file per page (`home`, `map`, `unit`, `budget`, `proof`, `public`, `qc`, `about`); `i18n.json` has the English and Filipino text |
| `drill/` | Dengue Drill. `rules.js` scores the game (checked against `scripts/drill_data.py` by `tests/test_drill_rules.py`); `board.js` and `world.js` draw the 3D island |
| `landing/` | The landing page's intro and closing scenes |
| `pages/` | The methodology, research and open-data pages |
| `lib/` | Shared pieces: the pixel sprites, voxel maps, icons, navigation and motion helpers |
| `css/` | The design system: `tokens.css` (colours, type, spacing), then `base`, `components` and `surfaces` |
| `sw.js` | The service worker that makes the dashboard work offline after one visit |

## Other folders
| Folder | What it holds |
| --- | --- |
| `public/` | Files copied into the build as they are: app and game data, map grids, sprites, textures, icons, research pages, the social card and the app manifest |
| `scripts/` | `clean-build.mjs` (removes old bundles before a build) and `make-textures.mjs` (draws the pixel textures in `public/`) |
| `vite.config.js` | The page list, the output folder (`../docs`, base `/epilag/`) and the plugin that builds the service worker |
