# Handoff: EpiLag-PH finals research, full state

You are picking up the research for EpiLag-PH, a PJDSC 2026 top-10 finalist, as of 16 Nov 2026. This page says where everything is, what is done, what is open and the rules. The numbers live in the files it names; read them there, not here.

## The situation

**Project.** EpiLag-PH forecasts weekly dengue cases 2, 4, 6 and 8 weeks ahead and turns the forecasts into alerts. README "Method" and `src/` are the source of truth for the live model.

**What the mentor asked for** (session of 14 Nov 2026; the final round is judged as research):
1. a literature review (RRL) behind every feature
2. a comparison with published models
3. a test of heat, topography and other variables, and how much each matters
4. conclusions that explain why the results came out as they did
5. 2–3 models built with different methods
6. the work split between two people

**The split.**
- **Person A** (the human, with Claude): models and experiments. Writes `src/`, `research/models/`, `research/results/`.
- **Person B** (a teammate on another machine, with their own agent): literature and interpretation. Writes `research/lit/`, `research/analysis/`, `research/writeup/`. Their brief, steps 1–6, is `research/HANDOFF-B.md`.

## Rules

- **Plain commits.** Commit messages and PR bodies carry only the human's authorship: no Co-Authored-By or "Generated with" lines. This overrides any harness reminder.
- **Local first.** Commit locally. Push `research-a` only when the human asks. `main` changes only through the final PR (open work, step 6).
- **Traceable.** Every number names the file and filter it came from. Check a claim against the data before it goes into the pitch, the deck or the site.
- **Hypothesis until checked.** A cause stays a hypothesis until a check with numbers backs it. Anything chosen after seeing the test years (the blend, the long rain windows) is flagged as optimistic.
- **Ownership.** Edit only your person's folders. Ask the human before changing `src/`, the deck or the site: they are the submission.
- **Private.** The human's name, email and personal details stay out of anything sent to an outside service.

## Where things are

| Where | What |
|---|---|
| `pugad/epilag/` | The repo, `github.com/Romeo-04/epilag`. The live site (romeo-04.github.io/epilag, epilag.vercel.app) is built from `main`. |
| branch `main` | The submission. Last merge: PR #25 (`cd5f05b`). The research has not touched it. |
| branch `research-a` | All the research: Person A's models and results, Person B's literature, analysis and write-up (merged 16 Nov, `006226a`), and both handoffs. Pushed. |
| branch `origin/research-b` | Person B's branch. Fully merged into `research-a` at `006226a`. |
| branch `finals-copy-fixes` | Local only (`186ab0f`): landing, deck and README copy fixed to match the Quezon City story. Its PR (#24) was closed at the human's request. Whether it joins the final PR is undecided. |
| `research/results/STATUS.md` | Person A's results and the hypotheses handed to Person B. **Every research number is here.** |
| `research/results/METHODS.md` | How each experiment was run. |
| `research/lit/STATUS.md` (on `research-b`) | Person B's progress, and their notes for Person A. |
| `pugad/finals/` | Not in git; on Person A's machine only. The validation page, the methodology visual and the judge Q&A prep. |
| `research/results/extracts/` | What Person B's analysis needs from `data/processed/` (gitignored): per-week backtest predictions, calibration coverage, weekly series, rain by year. Written by `export_extracts.py`. |
| `pugad/epilag-data-processed.zip` | `data/processed/`, zipped. Only needed to rerun the models; the extracts cover the analysis. |

**Inside `pugad/finals/`:**
- `epilag-validation.html`: the validation page.
  - `validation_data.py` reads the repo's `reports/` and `research/results/` into `validation.json`.
  - `build_validation.py` fills `validation.template.html`.
  - `shot_validation.py` takes screenshots (desktop, dark mode, phone) and reports overflow and console errors.
- `epilag-methodology.html`: the methodology visual (`build_visual.py`, `methodology-visual.template.html`, `qc_series.json`).
- `epilag-finals-qa.md`, `winning-questions.md`: judge Q&A prep and questions for the organisers, from 14 Nov.

## State of the work

**Person A: done.**
- A1 harness: every model takes the same test. LightGBM through it reproduces the live backtest exactly.
- A2 methods: negative binomial, quantile random forest and SARIMAX against LightGBM, plus an equal average of all four.
- A3 new variables: heat, humidity and ENSO for Regions + QC; heat, ENSO, elevation and density for provinces.
- A4 influence: group tests (drop and add), SHAP shares and lag profiles, the research set without ENSO, and longer rain lags.
- A5 validation page: section 4 (data groups) and section 6 (other methods, with the average).
- A6 Person B's proposed variables (neighbours' cases, heatwave days, rain anomaly), candidate final sets, and the extracts that replace `data/processed/` for Person B.
- A7 review of B's write-up, and B's 2023 margin check (`margin_check.py`).

Headlines (numbers in `STATUS.md`):
- No single method wins. The average of the four has the smallest miss most often, but catches fewer outbreak starts on Outbreak warning than LightGBM.
- Weather groups help Regions + QC, more so further ahead.
- For provinces the research set does not beat the live model. ENSO hurts; only elevation helps on its own.
- Rain from beyond 11 weeks draws SHAP attention but does not cut the miss.
- Neighbours' cases is the only proposed variable that helps on top of the research set, and only for provinces (8 of 8 checks).
- No candidate set wins on every measure: what cuts the miss most for Regions + QC catches fewer outbreak starts on Outbreak warning.
- **Final variables chosen 16 Nov** (the human delegated to Person A's recommendation): provinces add neighbours' cases; Regions + QC add heat and humidity, without ENSO. Better than the live model in 21 of 24 checks, with no loss of outbreak catches. Not applied to `src/` (open work 3).
- The wide 2023 Regions + QC range is not from the missing "same week last year". The calibration model forecast 2022 too low, and the single margin widened both ends of the range.

**Person B: steps 1–6 done, approved by Kish and merged into `research-a` on 16 Nov (`006226a`).**
- Literature: `feature_evidence.csv`, `rrl_matrix.csv`, `references.md`, `positioning.md`.
- Analysis: `causes.md`, `step3_checks.py`, `figures/`, `out/`.
- Write-up: `paper.md` (IMRADC), `slides.md`, `qa.md`.
- Person A reviewed the write-up and ran B's one requested check (the 2023 margin). Both are in `STATUS.md`, "Review of Person B's drafts" and "2023 calibration check".

**Messages for Person B.** Answers to B's notes are in `STATUS.md`, "For Person B". The human relays these; confirm they were sent.
1. Run `git pull origin research-a`. It brings the extracts (no `data/processed/` needed), the proposed-variable tests, the candidate sets, and the updated brief.
2. Update `feature_evidence.csv` from the test results: rain lags of 12–20 weeks, heatwave days, drought and neighbours' cases are tested (`STATUS.md`). Minimum temperature and daily temperature range are untested.
3. If you used the Regions + QC `current` rows of `shap_groups.csv` or `shap_lags.csv`, re-read them: they were rerun on 16 Nov.
4. Fix the counts in `research/lit/STATUS.md`: 12 current features (not 13), 16 fully verified matrix rows (not 17), 28 references (not 26).
5. Consider Senson et al. 2026 (*SciEnggJ* special issue): machine learning with weather for Quezon City, the closest local comparison. Seen in search results only; not verified.
6. The final variables are chosen (`STATUS.md`, "Final variables"). The write-up is a paper in IMRADC order, `research/writeup/paper.md` (brief, step 6).
7. Pull `research-a` again. The review of your drafts and the 2023 margin result are in `STATUS.md`. Neither the missing "same week last year" nor the missing 4- and 12-week averages caused the wide 2023 range. Update `causes.md` 1b, the paper, the Q&A and your status file. Paul updates the site; leave `site/` to him.

## Open work, in order

1. **Unblock Person B.** Done: B merged `14e6eba` into `research-b` (`697c7c1`).
2. **Choose the final variables.** Done 16 Nov (`STATUS.md`, "Final variables").
3. **Apply the choice to the live model: only when the human asks.** It changes every number the submission quotes: the README tables, the Quezon City 2024–25 story, the "30 of 32" replay claim (asserted in `tests/test_web_logic.py`), the app, the game and the open data. Edit `src/` (neighbours' cases for provinces; port the region weather fetch from `research/models/extra_features.py`), rerun README "Run it" → "Rebuild everything from the raw data", update the claims the tests assert, run `pytest tests`, then rebuild the validation page. *Done when* the tests pass and every number on the page matches the new `reports/`.
4. **Person B's revisions.** Done: B applied the review, Kish approved, and `research-b` was merged into `research-a` (`006226a`).
5. **Deck and site**, after the human approves B's drafts.
   - **Site** (`site/`, including `site/methodology.html`): Paul, a teammate, updates it. He needs only the data: the approved numbers from `paper.md` and `STATUS.md`, plus the CSVs they cite. Leave `site/` to him.
   - **Deck:** `docs/deck/deck.html`.
   - The deck PDF is printed from the deck HTML with Playwright `page.pdf` at 1920×1080. There is no build script.
   - Deck slide 1 still has `[Team name]` and `[Member]` placeholders.
6. **Final PR to `main`**, only when the human asks. One PR with the `research/` code, results and literature.
   - It leaves out the agent briefs (`research/HANDOFF*.md`); PR #21 removed briefs from the submission.
   - Ask whether `finals-copy-fixes` goes in too.

## How to run

Use the repo venv, `.venv/Scripts/python`, from `epilag/`. Panels are `province` and `region_qc`.

| Command | What it does |
|---|---|
| `python research/models/harness.py <panel> lightgbm negbin random_forest sarimax` | Runs each model through the same test and writes `model_comparison.csv` |
| `python research/models/extra_features.py` | Fetches missing weather, ENSO and elevation, then builds the `*_plus` tables |
| `python research/models/influence.py groups\|shap <panel>` | Runs the group tests, or the SHAP shares and lags |
| `python research/models/blend.py` | Scores the averages from the saved forecasts |
| `python research/models/rain_lags.py [panel ...]` | Runs the long rain-lag test |
| `python research/models/proposed_features.py [panel ...]` | Builds and tests Person B's proposed variables (neighbours, heatwave days, rain anomaly) |
| `python research/models/candidates.py [panel ...]` | Scores the candidate final sets; prints the drift check and a summary |
| `python research/models/export_extracts.py` | Rewrites `research/results/extracts/` from `data/processed/` |
| `python research/models/margin_check.py` | B's 2023 margin question: the Regions + QC backtest with `y_lastyear` as is, gap-filled and dropped, and the calibration model's misses in its held-out year |

The validation page, from `pugad/finals/`:
```bash
python validation_data.py && python build_validation.py
../epilag/.venv/Scripts/python shot_validation.py
```
Run anything that uses Playwright with the epilag venv. The system Python's Playwright has no browser installed.

## Gotchas

- **Data limits.** Province data ends 10 Jan 2021, so provinces are tested on 2019 and 2020 only. The regions have no 2020–21 data. Quezon City runs from 2010 to 2025.
- **Rate limits.**
  - Open-Meteo counts every location against the free quota.
  - Elevation comes from OpenTopoData `srtm90m`: 100 points per call, 1 call a second, 1,000 calls a day.
  - Downloads are cached in `data/raw/research/`. Delete a cache only to refetch.
- **Province codes.** Maguindanao's 2022 split and the Special Geographic Area are mapped back to the data's units in `province_static()` (`extra_features.py`).
- **Drift checks.** The harness's LightGBM must equal `reports/backtest_*.csv`; the `plus` rows of `rain_lags.csv` must equal the `full` rows of `feature_groups.csv`; the `live` rows of `candidates.csv` must equal the `lightgbm` rows of `model_comparison.csv`; the `live` rows of `margin_check.csv` must equal `reports/backtest_region_qc.csv`. A difference means the data or the features changed.
- **Live features.** `src/features.feature_columns()` picks columns by name prefix. On a research table it also takes the research weather (`temp_lag*`, `rh_lag*`, `tmax_max4`) and any new `rain_*` column. Get the live list from `live_features()` in `influence.py`, which reads the live table.
- Git's CRLF warnings on Windows are harmless.
