# Person A status

How the experiments were run: `METHODS.md`.

- [x] Harness: every model takes the same test. LightGBM through the harness reproduces `reports/backtest_*.csv` and `reports/alerts_*.csv` exactly, for both panels.
- [x] `model_comparison.csv`: negbin, random_forest and sarimax against lightgbm and the two baselines, both panels.
- [x] `blend_check.csv` (exploratory): equal average of the methods' middle forecasts.
- [ ] New variables: Regions + QC table built (heat, humidity, ENSO). Province table (adds elevation and density) building.
- [ ] `feature_groups.csv`: Regions + QC running, provinces next.
- [ ] `shap_groups.csv`, `shap_lags.csv`
- [ ] Validation page updated

## Ready now: four methods on the same test

24 checks: 6 test years × 4 lead times.

| | LightGBM (EpiLag-PH) | Negative binomial | Random forest | SARIMAX |
|---|---|---|---|---|
| Smallest miss of the four | 12 | 7 | 0 | 5 |
| Beat "same as this week" | 19 | 23 | 19 | 18 |
| Beat "same week last year" | 24 | 24 | 24 | 24 |
| Median miss vs LightGBM, 2 / 4 / 6 / 8 weeks | 0 | +2% / +5% / +10% / +12% | +1% / +3% / +4% / +3% | +5% / +6% / +2% / 0% |
| Range held after calibration (target 80%) | 70–96% | 67–92% | 67–93% | 69–96% |
| Range held before calibration | 46–73% | 59–89% | 67–87% | 58–89% |
| Outbreak starts caught by Watch, pooled | 83% | 84% | 82% | 88% |
| Caught by Outbreak warning, pooled | 36% | 37% | 38% | 17% |

Where each method won:
- Negative binomial: Regions + QC 2023 at every lead time, Regions + QC 2019 at 2 and 4 weeks, Provinces 2019 at 2 weeks.
- SARIMAX: Regions + QC 2019 at 6 and 8 weeks, and 2025 at 4–8 weeks.
- LightGBM: everything else, including every province check at 4 weeks or more, and all of 2024.

How to read it:
- No method wins everywhere. LightGBM is best most often. In Regions + QC 2023, LightGBM, random forest and SARIMAX all lost to "same as this week" at every lead time; negative binomial did not.
- LightGBM's raw range is the narrowest, so calibration has to do the most work for it. After calibration, all four hold about 80% on average.
- SARIMAX catches the most outbreak starts on Watch but the fewest on Outbreak warning (17%). Its middle forecast is not biased low overall (median log error −0.06 to +0.03), so why it rarely crosses the epidemic line early is open: a hypothesis to test, not a finding.
- **Blend (exploratory, `blend_check.csv`):** averaging all four middle forecasts had the smallest miss in 9 of 24 checks, against 7 for LightGBM alone. Its median miss was 2.6% below LightGBM's, and it was never more than 5% worse. No weights were tuned. Its range and alerts were not calibrated, so this is a lead, not a result.

Waiting on: `research/lit/feature_evidence.csv` from Person B (final choice of variables).
