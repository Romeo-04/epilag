# Person B status

- [x] **Step 1 is ready.** `feature_evidence.csv` has 27 rows: 12 current, 11 candidate, 4 proposed.
  - Every row has a mechanism, an expected lag and direction, and either a verified citation or `evidence_strength=none`.
  - The notes now carry Person A's test results for the proposed rows. Minimum temperature and daily temperature range are marked untested.
- [x] `references.md`: 29 entries. Senson 2026 is added as unverified (no record found yet).
- [x] Step 2: `rrl_matrix.csv` has 19 papers, 9 from the Philippines.
  - 16 are fully verified.
  - Two are verified with a caveat (tuan2024) or from the abstract only (rahman2025), and johansson2019 is partly verified.
  - `build_rrl_matrix.py` regenerates it.
- [x] Step 3: `research/analysis/causes.md` is updated with Person A's extracts (margins, raw coverage, rain anomaly). Run `step3_checks.py` to reproduce it. One check needs a model rerun (below).
- [x] Step 4: `research/lit/positioning.md` is drafted.
- [x] Step 5: `causes.md` covers the four methods, the average of the four, the variable groups, the proposed variables, the longer rain lags, and the final variables.
- [x] Step 6: `research/writeup/paper.md` is drafted in IMRADC order. `slides.md` and `qa.md` are updated with the new numbers: Regions + QC SHAP weather share 11–24%, the average of the four, and the final variables. `discussion.md` was folded into the paper.
  - **For Person A:** please check the paper's Methods and Results against `METHODS.md` and `STATUS.md`. The brief makes that a condition for step 6 being done.
- Nothing from steps 3–6 is committed yet. Everything waits for Kish's approval.

## For Person A

- **2023 over-wide range.** The 2022 calibration year has no `y_lastyear` because the regions skip 2020–2021. Could you rerun `conformal_margin` for 2023 without `y_lastyear`, or with the gap filled? If the margin (0.227) falls toward 0.09–0.10, the cause is confirmed.
- **Hypothesis 4 (long rain lags).** Studies tested lags up to 18–20 weeks, but the rain effects they report are 5–12 weeks [sumi2017, carvajal2018, iguchi2018]. So the attention at 12–15 weeks more likely marks where the year is in the season.
- **Hypotheses 1–3** are answered in `causes.md`, step 5.
- **LightGBM's raw ranges** are about 17 points narrower than random forest's (median 64% against 81%).

## Corrections made

- PMC8898531 is edillo2022, a study of mosquito eggs. The nationwide elevation study is sy2026.
- tuan2024's table doesn't show negative binomial with the lowest error.
- makridakis2022, the Mandaue study and senson2026 are unverified.
