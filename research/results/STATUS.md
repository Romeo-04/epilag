# Person A status

How the experiments were run: `METHODS.md`.

- [x] Harness: every model takes the same test. LightGBM through the harness reproduces `reports/backtest_*.csv` and `reports/alerts_*.csv` exactly, for both panels.
- [x] `model_comparison.csv`: negbin, random_forest and sarimax against lightgbm and the two baselines, both panels.
- [x] Blends in `model_comparison.csv` (`blend_all4`, `blend_lgb_negbin`): equal average of the methods' calibrated forecasts, scored like any model (error, range, both alert rules).
- [x] New variables: heat, humidity and ENSO for Regions + QC; heat, ENSO, elevation and density for provinces (`METHODS.md`).
- [x] `feature_groups.csv`: each group removed from the full set, and added to cases + season. LightGBM, same test, both panels.
- [x] `shap_groups.csv`, `shap_lags.csv` (rows with `feature_set = plus` use the research table; `current` is the live feature set).
- [x] Validation page: new sections 4 (data groups) and 6 (other methods). The page lives outside the repo, in `pugad/finals/`.

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

**Average of the four (`blend_all4`).** An equal average, in log space, of the four methods' calibrated 10/50/90% forecasts. No refitting, no tuned weights (`METHODS.md`).

| | Average of the four | LightGBM alone |
|---|---|---|
| Smallest miss, against the four methods | 11 of 24 | 7 (negative binomial 4, SARIMAX 2) |
| Beat "same as this week" | 24 of 24 | 19 |
| Miss vs LightGBM, median at 2 / 4 / 6 / 8 weeks | −4% / −4% / −2% / −2% (range −18% to +4%; better in 17 of 24) | 0 |
| Range held (target 80%) | 73–97%, mean 81% | 70–96%, mean 80% |
| Watch: caught, pooled / false alarms, average | 87% / 58% | 83% / 58% |
| Outbreak warning: caught / false alarms | 30% / 27% | 36% / 30% |

- Where it lost to LightGBM: Provinces 2020 (+2% to +4%) and Regions + QC 2024 (0% to +4%).
- The trade-off is on Outbreak warning: fewer starts caught. SARIMAX, which catches 17% on that rule, is one of the four inputs; whether it is the cause is untested.
- Averaging only LightGBM and negative binomial (`blend_lgb_negbin`) gains less: median −0.6%, worst +9.8%.
- Caveat: the idea of blending was picked after seeing these test years. Weights were not, so there is little room to overfit, but a fresh year is the real test.

## Ready now: what each data group adds

**Effect** = change in average miss from having the group in the model. Negative means the group helped.
- **Add:** cases + time of year, plus the group, compared with cases + time of year alone.
- **Remove:** the full research set compared with the same set minus the group.

Counts are checks where the group helped: 16 for Regions + QC (4 years × 4 lead times), 8 for provinces (2 × 4).

| Group | Regions + QC, add | Regions + QC, median effect at 2 / 4 / 6 / 8 weeks | Provinces, add | Provinces, remove |
|---|---|---|---|---|
| Rain | 12 of 16 | 0% / −1% / −3% / −4% | 2 of 8 | helped in 2 of 8 |
| Heat | 14 of 16 | −2% / −4% / −4% / −7% | 3 of 8 | 3 of 8 |
| Humidity | 15 of 16 | −3% / −3% / −5% / −6% | 4 of 8 | 4 of 8 |
| ENSO | 8 of 16 | +1% / −2% / −3% / −4% | 2 of 8 | **0 of 8** (hurt every time) |
| Elevation | not tested | | **7 of 8**; −1.9% median, −4.7% at 8 weeks | 3 of 8 |
| Population | 15 of 16 (but fixed per area: acts as an area label) | −2% / −3% / −6% / −9% | 4 of 8 | 3 of 8 |
| Recent cases | in base | | in base | removing it makes the miss 21–303% bigger |

**Research table compared with the live model** (all research variables against today's features, LightGBM):
- **Regions + QC:** better in 2023 at every lead time (−5% to −14%) and in 2024 (−1% to −4%); mixed in 2025; slightly worse in 2019 (+1% to +3%). At 4 weeks, 2023 drops from 58.0 to 54.0, which now beats "same as this week" (55.6).
- **Provinces:** worse in all 8 checks (+0.4% to +9.5%). The largest drop is 2020 at 8 weeks.
- **Overall:** better in 11 of 24 checks, median +0.5%. Watch caught 1,066 outbreak starts, against 1,049 for the live model (of 1,260 across lead times).

**SHAP (final model, research table).**
- Recent cases carry 48–76% of the model's attention, falling with lead time.
- Then come time of year (7–13%) and rain (Regions + QC 8–17%, provinces 5–8%).
- ENSO gets 4–11% of the provinces' attention, despite making their forecasts worse.
- **Lag profiles (`shap_lags.csv`):**
  - Rain's largest share is at the longest lag offered (10–11 weeks) in 3 of 4 lead times, for both panels. The lag window may be too short.
  - Temperature peaks 4–8 weeks back. Humidity: 8 weeks for provinces.

**Hypotheses for Person B to check against the literature (not findings):**
1. ENSO hurts provinces because 5 years of province data (2016–2020) hold about one El Niño cycle. The model can use ENSO as a label for the year, and that pattern does not carry over to a new year. For Regions + QC it helped in 2023 and 2024 from 4 weeks ahead, not in 2019, and was mixed in 2025. QC alone has 16 years of data.
2. Weather groups help Regions + QC more than provinces. Region weather is one population-weighted point per region, while province weather is one point per province. Region counts are larger and smoother, too. Or the province test years (2019 record epidemic, 2020 COVID) are unusual.
3. Elevation helps provinces on its own but not inside the full set. It may stand in for something the other variables already carry (rain, temperature or urbanisation).
4. Rain peaking at the longest lag offered suggests effects beyond 12 weeks (lag plus lead). Compare with `expected_lag_weeks` in the literature.

Waiting on: `research/lit/feature_evidence.csv` from Person B (final choice of variables).
