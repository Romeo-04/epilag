# How Person A's experiments were run

Code: `research/models/`. The live model in `src/` is unchanged apart from one optional argument in `src/alerts.py`, which lets any model's forecasts be scored.

## The same test for every model (`harness.py`)

**Training and test split**
- For each test year Y and lead time h (2, 4, 6, 8 weeks), a model trains on rows whose target week is before 1 January of Y.
- It then forecasts every week of Y.
- These are the same rows and splits as `src/backtest.py`.

**Calibration**
- Every model's 10–90% range goes through the same conformal calibration.
- A copy of the model is fit without the last 52 weeks, and its misses on that year set a margin in log space.
- A negative margin means the raw range was too wide, and calibration narrows it (Romano et al. 2019 allow this).

**Scoring.** Scores use the weeks where both baselines also exist, so every model is scored on identical rows.
- **Error:** mean absolute error of the middle forecast, in cases per area-week.
- **`rel_mae_vs_*`:** the model's error divided by a baseline's error. Below 1 means the model beat that baseline.
- **Coverage:** the share of real counts inside the calibrated range. `coverage_raw` is the same share before calibration.
- **Alerts:** `src/alerts.py` rules, with an epidemic line from earlier years only.
  - Watch = q90 above the line.
  - Outbreak warning = q50 above the line.
  - Baselines have no range, so they only get the Outbreak-warning rule.

**Check.** LightGBM run through the harness reproduces `reports/backtest_region_qc.csv` and `reports/alerts_region_qc.csv` exactly. The largest difference in error, coverage and Watch catches is 0.

## The four models (`models.py`)

| Model | Method | Inputs | Range | Settings |
|---|---|---|---|---|
| `lightgbm` | Gradient-boosted trees, one quantile model per quantile (EpiLag-PH today) | All features in `src/features.py`; gaps left as they are | Quantile loss at 0.1, 0.5 and 0.9 | As in `src/backtest.py`: 400 trees, learning rate 0.03, 31 leaves |
| `negbin` | Negative binomial regression (NB2), log link, counts of cases at t+h | Same features. Gaps filled with the training median, plus a flag where last year's count is missing; standardised | Quantiles of the fitted negative binomial | Dispersion from the Cameron–Trivedi auxiliary regression on a Poisson fit |
| `random_forest` | Quantile regression forest (Meinshausen 2006), `quantile-forest` 1.5 | Same features; gaps handled by the trees | Weighted quantiles of training targets in the same leaves | 300 trees, at least 5 rows per leaf, a third of the features per split, seed 0 |
| `sarimax` | One ARIMA(2,0,1) model with regression inputs per area, on log(cases + 1) | Each area's own series. Also a constant, two yearly Fourier pairs, and 4-week rain (plus temperature and humidity for provinces) taken h weeks before the target week, so they are known at forecast time | Normal quantiles of the h-step forecast | The order was picked by mean AIC on data up to 2018 for QC and 6 provinces: (2,0,1) 250.8, (2,0,0) 253.3, (1,0,1) 286.6, (1,0,0) 325.0. Missing weeks are handled by the Kalman filter. Forecasts from each week use only data up to that week; checked against statsmodels' own forecasts to within 1e-5 |

## New candidate variables (`extra_features.py`)

| Group | Features | Source | Panels |
|---|---|---|---|
| heat | `heat_band4`: days with mean temperature in 26–29 °C over the last 4 weeks. `heat_band4_lag4`: the same, 4 weeks earlier. `heat_hot4`: days at or above 34 °C (maximum temperature). `heat_hi4`: 4-week mean heat index (NWS Rothfusz, from daily mean temperature and humidity) | ERA5 daily via Open-Meteo | Both |
| heat, humidity | `temp_lag0/2/4/6/8`, `tmax_max4`, `rh_lag0/2/4/6/8`, the inputs the province model already had | ERA5 daily via Open-Meteo, at one population-weighted point per region and the Quezon City centre | Regions + QC |
| enso | `enso_oni`: Oceanic Niño Index for the 3-month season centred 2 months before week t, already published at forecast time. `enso_oni_lag3`: centred 5 months before | NOAA CPC `oni.ascii.txt` | Both |
| topography | `topo_elev_mean`: area-weighted mean elevation. `topo_low_share`: area share below 100 m | 42,048 barangay centroids (COD-AB), with elevation from SRTM 90 m (NASA) via the OpenTopoData public API | Provinces only |
| population | `pop_density_log`: log of people per km² | `data/processed/units.csv` | Provinces only |

**Why not Regions + QC for topography and density:** with 18 areas, a fixed per-area value has 18 distinct values, which works like an area label rather than a measured effect.

**Daily temperature range:** left out. It needs daily minimum temperature, and the cached province weather lacks it.

## How much each variable group matters (`influence.py`)

**Groups** come from feature-name prefixes (`GROUPS` in `extra_features.py`): cases, season, rain, heat, humidity, enso, topography, population.

**Group tests** (`feature_groups.csv`). LightGBM goes through the same harness on the research table:
- `full` uses every feature.
- `base` uses recent cases plus the time of year.
- `drop` is the full set minus one group.
- `add` is the base plus one group.

Each test reports:
- `change_pct`: error against its reference (full for `drop`, base for `add`), minus 1.
- Effect of having a group: base→add for `add`, drop→full for `drop`. Negative means the group helped.

**SHAP** (`shap_groups.csv`, `shap_lags.csv`):
- The 50th-percentile LightGBM model is fit on all usable rows, as `src/train_final.py` does, once for the live feature set (`current`) and once for the research table (`plus`).
- Mean |SHAP| is taken over a fixed sample of 4,000 area-weeks (seed 0).
- A group's share is its features' summed mean |SHAP| over the total.
- Lag profiles keep the per-lag values for `rain_lag*`, `temp_lag*` and `rh_lag*`.

## Blends (`blend.py`)

- **What:** each method's saved, calibrated 10%, 50% and 90% forecasts, averaged in log(cases + 1) space, quantile by quantile ("quantile averaging", Lichtendahl, Grushka-Cockayne and Winkler 2013).
- **Blends:** `blend_all4` (all four methods) and `blend_lgb_negbin` (LightGBM + negative binomial). Equal weights.
- **No fitting:** nothing is refit, no weight is tuned, and the blend gets no calibration of its own. Its range is the average of the four ranges, each calibrated on the last training year.
- **Scoring:** the harness's `score()`, so error, range and both alert rules are directly comparable with the single methods in `model_comparison.csv`.
