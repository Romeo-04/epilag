# EpiLag-PH research

After the PJDSC 2026 first round, we tested the submitted EpiLag-PH model more closely. The work has three parts:

- a review of the published work on what drives dengue and how it has been forecast;
- model experiments: three other methods and nine new groups of variables, all on the same test as the submitted model;
- an analysis of why the results came out as they did.

**Start here:** [`EpiLag-PH-research-summary.pdf`](EpiLag-PH-research-summary.pdf) (8 pages). The full write-up is [`writeup/paper.md`](writeup/paper.md).

## Headline findings

- No Philippine forecasting study in our review of 19 studies combines all four of these: weekly forecasts for many areas, calibrated ranges, alerts scored for both catches and false alarms, and several unseen test years. EpiLag-PH has all four.
- The submitted model beat both simple baselines in 5 of 6 test years. It had the lowest error of four methods in 12 of 24 checks.
- Weather helps the Regions + QC model more the further ahead it forecasts. For provinces it gives no measurable gain.
- Every loss traces to a specific cause:
  - the 2019 record epidemic;
  - the flat year 2023;
  - a calibration year (2022) whose model ran low, which made the 2023 range too wide.
- One set of variables did better in 21 of 24 checks: neighbours' cases for provinces, and temperature and humidity for Regions + QC. It was chosen after seeing the test years, so the submitted model in `src/` is unchanged.

## What is where

| Folder | What it holds |
|---|---|
| [`lit/`](lit/) | `references.md` (each source, and what was verified on it), `rrl_matrix.csv` (19 studies compared), `feature_evidence.csv` (the evidence for each variable), `positioning.md` (where EpiLag-PH sits) |
| [`models/`](models/) | Experiment code. `harness.py` runs the shared test, `models.py` holds the four methods, and there are scripts for the new variables, candidate sets and the 2023 calibration check |
| [`results/`](results/) | `README.md` (every result and the file it comes from), `METHODS.md` (how each experiment ran) and the result CSVs |
| [`analysis/`](analysis/) | `causes.md` (why the results came out as they did), `step3_checks.py` (its numbers), plus `out/` and `figures/` |
| [`writeup/`](writeup/) | `paper.md` (full write-up), `summary.html` and `build_summary.py` (the source of the PDF) |

The submitted model in `src/` is unchanged. The only change there is one optional argument in `src/alerts.py`, which lets any model's forecasts be scored by the same alert rules.

## Reproduce

1. Build `data/processed/` (it is gitignored) with the steps under "Rebuild everything from the raw data" in the main [README](../README.md).
2. Install the research requirements, which are in the main `requirements.txt`.
3. Run these in order:

```bash
python research/models/extra_features.py          # research tables: weather, ENSO, elevation, density
python research/models/harness.py province lightgbm negbin random_forest sarimax
python research/models/harness.py region_qc lightgbm negbin random_forest sarimax
python research/models/blend.py
python research/models/influence.py groups province && python research/models/influence.py groups region_qc
python research/models/influence.py shap province && python research/models/influence.py shap region_qc
python research/models/rain_lags.py
python research/models/proposed_features.py
python research/models/candidates.py
python research/models/margin_check.py
python research/models/export_extracts.py
python research/analysis/step3_checks.py
python research/writeup/build_summary.py          # the PDF; needs Playwright with Chromium
```

Run through `harness.py`, LightGBM reproduces the submitted model's scores in `reports/` exactly.
