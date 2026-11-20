# Scripts (`scripts/`)

Scripts that turn the pipeline's results into what the website, the app, the game and the documents show.
Each one is safe to re-run, and the docstring at the top of each file says exactly what it writes.
Run them from the repository root, for example `python scripts/build_web.py`.

Files written to `site/public/` are copied into the built site (`docs/`) by `npm run build` in [`site/`](../site/README.md).

## Web app and open data
| Script | Writes | What for |
| --- | --- | --- |
| `build_web.py` | `site/public/web/data/` | Forecasts, history, thresholds, track records and English/Filipino copy for the web app |
| `export_open_data.py` | `docs/data/` | Open forecasts and track records as CSV and JSON, the RSS alert feed and the calendar feed |
| `landing_data.py` | `site/public/data/` | The landing page's 2 June 2019 replay, and a recheck of the "30 of 32 provinces" claim |

## Weekly checks
| Script | Writes | What for |
| --- | --- | --- |
| `validate_cases.py` | nothing | Checks a weekly case file against the [data contract](../data/contract/README.md); exits 1 on an error, so the weekly job stops |
| `model_gate.py` | nothing | The promotion gate: a retrained model goes live only if its latest test year still beats the baselines and its range covers 70–90%; exits 1 otherwise |
| `scale_benchmark.py` | `reports/scale_benchmark.csv` | Times a full retrain with the production code at 86, 400 and 1,600 areas |

Both checks run in CI on every pull request and in the weekly job (`.github/workflows/`).

## Dengue Drill (the game)
| Script | Writes | What for |
| --- | --- | --- |
| `drill_data.py` | `site/public/drill/data.json` | The 2019 missions, region by region; also scores the two computer players |
| `qc_drill_data.py` | `site/public/drill/qc.json`, `site/public/geo/voxel_qc.json` | The Quezon City 2024–25 mission, barangay by barangay (estimates from yearly shares) |
| `drill_models.py` | `site/public/drill/models.json` | Round 2 forecasts for every model the player can pick |

## Maps
| Script | Writes | What for |
| --- | --- | --- |
| `voxel_data.py` | `site/public/geo/*.json` | The province and region maps as grids for the 3D pixel maps |
| `drill_map/` | `site/public/geo/drill.json` | The app's drill-down map boundaries. Run `boundaries.sh` (downloads the PSA shapes and prepares them; needs Node for mapshaper), then `build.py` |

## Research page
| Script | Writes | What for |
| --- | --- | --- |
| `research_docs.py` | `site/public/research/` | The research documents as pages the Research page opens in its reader |
| `research_numbers.py` | nothing | Recomputes every number on the Research page from `research/results/`; `tests/test_research_page.py` uses it |

## Images
| Script | Writes | What for |
| --- | --- | --- |
| `make_figures.py` | `docs/figures/` | Figures (SVG) from the committed reports and app data |
| `screenshots.py` | `docs/screenshots/` | README and deck screenshots, from the built site |
| `pr_gifs.py` | `docs/screenshots/features/` | Short GIFs of dashboard features, for pull requests (serve the build first) |
| `og_image.py` | `site/public/og.png` | The social card shown when the site is shared |
| `pwa_icons.py` | `site/public/icons/` | Icons for the installable app |

`screenshots.py`, `pr_gifs.py` and `og_image.py` use Playwright (`pip install playwright`, then `playwright install chromium`).
