# Person B status

- [x] **Step 1 is ready.** `feature_evidence.csv` has 27 rows: 13 current, 11 candidate, 4 proposed. Every row has a mechanism, an expected lag and direction, and either a verified citation or `evidence_strength=none`.
- [x] `references.md`: 26 entries. 21 are verified, Johansson 2019 is partly verified, and 4 are unverified (marked in the file).
- [x] Step 2: `rrl_matrix.csv` has 19 papers, 9 from the Philippines. 17 are fully verified, and two are verified with a caveat (tuan2024) or from the abstract only (rahman2025). Johansson 2019 is partly verified. `build_rrl_matrix.py` regenerates it.
- [ ] Step 3: `causes.md` is in progress. Checks run from `site/public/web/data/*_history.json` and `*_backtest.json`, which reproduce `reports/backtest_region_qc.csv` at 4 weeks exactly. The calibration margins and the rain-anomaly check still need `data/processed/`.
- [ ] Steps 4–6.

## For Person A

**What the literature says about your candidates**
- **Temperature and humidity for Regions + QC:** strong evidence. Humidity was the top weather factor in Metro Manila (carvajal2018) and the only factor linked to the second seasonal peak in a study at region level (xu2020).
- **Heat band 26–29 °C:** strong. The band comes from mordecai2017, and Philippine risk peaks at 27.5 °C (seposo2023).
- **Heat index:** no verified dengue study. Its parts are already features, so it may duplicate them.
- **ENSO:** mixed. The evidence is for 2–5 year cycles (vanpanhuis2015). This supports your hypothesis 1, that with about one cycle in the province data the model learns ENSO as a label for the year.
- **Elevation and density:** mixed. A nationwide Philippine study (sy2026) links both to infection rates but **not** to reported incidence. A null or small effect in a forecast that already knows recent cases is what the literature predicts.
- **Rain lags:** studies use lags up to 12–20 weeks (tuan2024, seposo2023, shi2016). Your SHAP peak at 10–11 weeks suggests extending the window.

**Proposed new features** (evidence `mixed` or `weak`; your call)
- heatwave days above the local 95th percentile, and a drought index (both from ith2025)
- rain lags of 12–20 weeks
- cases in neighbouring areas (buczak2014)

**Corrections to the handoff**
- PMC8898531 is a laboratory study of mosquito eggs (edillo2022), not the nationwide elevation study. That study is sy2026.
- tuan2024's results table does not show negative binomial regression with the lowest error; SARIMAX has a lower MAE. So don't cite it as proof that negative binomial wins.
- The M5/LightGBM paper (makridakis2022) and the Mandaue elevation paper could not be opened. They stay unverified.
