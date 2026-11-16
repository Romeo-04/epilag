# Where EpiLag-PH sits in the published work

Step 4 of the Person B handoff. Every claim about another study points to its row in `rrl_matrix.csv`, by key; full citations are in `references.md`. EpiLag numbers come from `reports/` and `research/results/model_comparison.csv`.

Raw errors can't be compared across studies, because places, scales and case counts differ. Skill is therefore given **relative to a simple baseline**, and only where a study reports one.

## Forecasting studies compared

Association-only studies (iguchi2018, seposo2023, sumi2017, xu2020, sy2026, mordecai2017, liuhelmersson2014, vanpanhuis2015, ith2025) don't make forecasts. They back the features (`feature_evidence.csv`) and are left out here.

| Study | Methods | Area level | Lead time | Ranges given | Alerts tested | Tested on unseen years | Skill vs a simple baseline |
|---|---|---|---|---|---|---|---|
| **EpiLag-PH** | LightGBM quantile regression with conformal calibration; also compared with negative binomial, random forest and SARIMAX | 86 provinces, 17 regions and Quezon City, weekly | 2, 4, 6, 8 weeks | yes: 10–90%, calibrated to 80% (holds 70–92% across test years at 4 weeks) | yes: outbreak starts caught (Watch 79–100%) **and** false-alarm share (42–63%) | yes: 2019, 2020 (provinces); 2019, 2023, 2024, 2025 (regions) | 4 weeks ahead: 18–32% lower error than "same as this week" for regions, except 2023 (+4%); 20–22% lower for provinces. 32–89% lower than "same week last year" |
| carvajal2018 | GAM, SARIMAX, random forest, gradient boosting | Metro Manila, weekly | none stated | no | no | yes: 2013 | not reported against a naive baseline |
| olana2025 | SARIMA, NNAR, random forest, LSTM, TBATS, Prophet | national, monthly | 12 months | yes (confidence intervals) | no | yes: 2024 | MASE reported; no direct naive comparison |
| buczak2014 | fuzzy association rule classifier | 40 provinces, weekly | 4 weeks | no | yes: high incidence = mean + 1.5 SD; sensitivity 0.63, specificity 0.97 | yes: 2011 (and 2012) | better than a seasonal moving average per the page summary (sensitivity 0.31); not seen verbatim |
| eligado2026 | DWT-SARMA, DWT-SARMA-LSTM | Quezon City, weekly | not reported | not reported | yes: model thresholds against a 3-year moving mean | not reported | not reported (MAPE 12.4% for the best model) |
| shi2016 | LASSO, SARIMA, stepwise regression | Singapore, weekly | 1–12 weeks | yes: 95%, coverage checked | no | yes: 2011–2012, applied to 2013 | no naive baseline; MAPE 24% against 29% for SARIMA at 3 months |
| tuan2024 | negative binomial, SARIMAX, XGBoost, LSTM | one province (Vietnam), weekly | not reported | no | no | yes, but dispersion tuned on the test set | no naive baseline |
| colongonzalez2021 | Bayesian superensemble | 63 provinces (Vietnam), monthly | 1–6 months | yes (probabilistic) | yes: detection 69% against 54.5% for the baseline | yes: hindcast 2007–2016 and 2020 | beat a seasonal-average baseline at 1–3 months, not at 4–6 |
| lowe2014 | hierarchical Bayesian | 553 microregions (Brazil) | 3 months | yes (probabilistic) | yes: risk triggers tuned on past Junes | past Junes assessed | not reported in the abstract |
| johansson2019 | 16 team models plus ensembles | 2 cities, weekly | within season | yes (probabilistic) | no | yes: 4 seasons (summary only) | the ensemble beat the null model for every target (summary only) |
| rahman2025 | random forest, XGBoost, LightGBM, with SHAP | Bangladesh | not reported | not reported | an early warning tool is described | not reported | not reported |

**Sources for the EpiLag row.**
- Errors: `reports/backtest_region_qc.csv` and `reports/backtest_province.csv`, horizon 4 (`skill_vs_persistence`, `skill_vs_seasonal`, `coverage_10_90`).
- Alerts: `reports/alerts_region_qc.csv`, rule `warn_upper`, as summarised in the README "Does it work?" table.
- The 2023 exception is explained in `research/analysis/causes.md`, finding 1.

## The gap EpiLag fills

1. **Weekly forecasts for many Philippine areas at once, with lead times a health office can act on.** Among the Philippine forecasting rows:
   - olana2025 forecasts the national total by month.
   - carvajal2018 forecasts one metro area and states no lead time.
   - eligado2026 forecasts one city.
   - Only buczak2014 forecasts provinces weekly at a fixed lead (4 weeks), as a high/low classifier.

   EpiLag forecasts 104 areas weekly at four lead times.
2. **Calibrated ranges.**
   - None of the four Philippine forecasting rows reports calibrated ranges. olana2025 shows confidence intervals, but no coverage check.
   - Among the others, shi2016 checks 95% coverage, and colongonzalez2021, lowe2014 and johansson2019 are probabilistic.
   - EpiLag reports the share of weeks inside its 10–90% range for every test year, before and after calibration (`model_comparison.csv`).
3. **Alerts scored for both hits and false alarms.**
   - buczak2014 reports sensitivity and specificity.
   - colongonzalez2021 reports detection rates.
   - eligado2026 compares thresholds, but no hit rate appears in its abstract.
   - EpiLag reports both the share of outbreak starts caught and the share of alerts that were false, at each lead time and test year.
4. **Testing on several unseen years, including unusual ones**: a record epidemic (2019) [doh2019epidemic], a reporting collapse (2020), and a flat year (2023).
   - Most rows test one held-out year (carvajal2018: 2013; olana2025: 2024) or one period.
   - Of the forecasting rows, colongonzalez2021 tests the most, with a hindcast over 2007–2016.
5. **Comparison with naive baselines.**
   - Several rows compare only against other complex models: carvajal2018, shi2016 and tuan2024 have no naive baseline.
   - EpiLag reports skill against both "same as this week" and "same week last year".
   - It also reports where it *lost*: Regions + QC 2023, and the 2-week forecasts for 2019.

## What not to claim

- **"Most accurate dengue model in the Philippines."** Errors are not comparable across studies, and no shared benchmark exists.
- **"Better than LSTM."** EpiLag did not test an LSTM. olana2025 found NNAR best nationally, while LSTM was best in other countries' studies, as cited within olana2025 (not verified here).
- **"Weather drives the forecast."** In EpiLag, recent cases carry most of the attention, and weather helps only Regions + QC at longer leads (`research/analysis/causes.md`, finding 3). That is consistent with johansson2019 (summary only: models using climate data did not score higher).
- **"Elevation predicts dengue cases."** sy2026 finds elevation linked to infection rates but not to reported incidence.
