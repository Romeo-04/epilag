# EpiLag-PH: Weekly dengue forecasts with calibrated ranges for Philippine provinces, regions and Quezon City

Draft research write-up for the PJDSC 2026 final round, in IMRADC order.

**Sources.**
- Every number traces to `reports/`, `research/results/` (Person A), or `research/analysis/out/`, written by `research/analysis/step3_checks.py`.
- Citations are keys in `research/lit/references.md`; study details are in `research/lit/rrl_matrix.csv`.
- Unless stated, results are 4 weeks ahead.

## 1. Introduction

**The problem.**
- Dengue is endemic in the Philippines. The Department of Health declared a national dengue epidemic on 6 August 2019 [doh2019epidemic].
- Response usually starts after cases are already high, because reports arrive after people fall ill. Reported cases also undercount infections, about 4.7 times in one Cebu City study [undurraga2017].
- A forecast weeks ahead gives a health office time to act.

**What the literature says drives dengue.** Climate acts with a delay, through the mosquito life cycle and the virus's incubation:
- Rain matters 5–7 weeks before cases [sumi2017, carvajal2018], with risk peaking at moderate amounts [iguchi2018].
- Humidity matters about 4 weeks before. It was the top weather factor in Metro Manila [carvajal2018] and the only factor linked to the second seasonal peak [xu2020].
- Temperature risk follows an inverted U, peaking near 27.5 °C in 61 Philippine provinces [seposo2023], within the 26–29 °C transmission optimum [mordecai2017].
- Multi-year cycles across Southeast Asia move with El Niño [vanpanhuis2015].
- Elevation and density are linked to infection rates in the Philippines, but not to reported cases [sy2026].

The full evidence for each feature is in `research/lit/feature_evidence.csv`.

**Forecasting work so far.** In the 9 Philippine studies we reviewed, the forecasts cover:
- the national total by month [olana2025]
- one metro area, with no stated lead time [carvajal2018]
- one city [eligado2026]
- high-or-low incidence classes by province, 4 weeks ahead [buczak2014]

Elsewhere in the region, probabilistic forecasts with tested alerts exist at monthly scale [colongonzalez2021, lowe2014], and as weekly national forecasts with intervals [shi2016].

**The gap** (`research/lit/positioning.md`). No Philippine study in the matrix has all four of these:
- weekly forecasts for many areas at several lead times
- calibrated ranges with coverage reported
- alerts scored for both catches and false alarms
- testing on several unseen years, including unusual ones

EpiLag-PH sets out to fill that gap.

## 2. Methods

**Data** (README "Data"):
- **Cases:** weekly reported cases for 86 province-level units, 2016 to January 2021 (DOH Epidemiology Bureau via HDX). Also 17 regions (2016–2019 and 2022–2025) and Quezon City (2010–2025), from the UPRI-NOAH dataset [pelitro2026].
- **Weather:** ERA5 daily weather via Open-Meteo.
- **Population:** PSA-based population.

**Features** (`src/features.py`):
- recent cases (last 4 weeks, 4- and 12-week averages, trend, same week last year)
- weekly rain for 12 weeks, with 4/8/12-week totals and heavy-rain days
- humidity and temperature lags (provinces only in the submitted model)
- week of year and population

**Model** (README "Method"):
- One LightGBM quantile model per lead time (2, 4, 6, 8 weeks) gives the 10th, 50th and 90th percentiles.
- The 10–90% range is widened by conformalized quantile regression [romano2019], fit on the last training year.

**Alerts** (`src/alerts.py`, `src/thresholds.py`):
- The epidemic line is the mean + 2 SD for each area and week of year, from earlier years only.
- **Watch:** the 90th percentile crosses the line.
- **Outbreak warning:** the median crosses it.

**Test design** (`src/backtest.py`, `research/results/METHODS.md`):
- Each test year is forecast by a model trained only on earlier years.
- Test years: provinces 2019 and 2020; Regions + QC 2019, 2023, 2024 and 2025. That makes 6 panel-years × 4 lead times = 24 checks.
- Baselines: "same as this week" (persistence) and "same week last year" (seasonal naive).

**Comparison methods** (`research/results/METHODS.md`). Each goes through the same test and the same calibration:
- negative binomial regression
- quantile random forest
- SARIMAX
- an equal average of all four

**Variable tests** (`research/results/METHODS.md`):
- Each variable group was added to cases + season, and removed from the full research set.
- The new variables were heat, humidity, ENSO, elevation, density, neighbours' cases, heatwave days, a rain anomaly, and rain 12–23 weeks back.
- Candidate final sets were scored on error, coverage and alerts.

**Why this model** (`research/writeup/qa.md`):
- The literature's drivers are non-linear, as above. Boosted trees learn such shapes from data, train fast [ke2017], and explain each forecast through SHAP.
- Tree models have done well for dengue elsewhere [carvajal2018, rahman2025].
- The comparison below tests that choice directly.

## 3. Results

### 3.1 The submitted model

| | Regions + QC | Provinces |
|---|---|---|
| Error vs "same as this week" | 18% lower (2019), 32% (2024), 20% (2025); **4% higher (2023)** | 22% lower (2019), 20% (2020) |
| Error vs "same week last year" | 32–70% lower | 36% (2019), 89% (2020) lower |
| Share of weeks inside the 10–90% range (target 80%) | 70–92% | 77–79% |
| Outbreak starts caught by Watch | 79–100% | 87% (2019) |
| False alarms on Watch | 42–63% | 46% (2019) |

Sources: `reports/backtest_<panel>.csv` (horizon 4) and `reports/alerts_<panel>.csv` (rule `warn_upper`, horizon 4).

### 3.2 Four methods on the same test

Lowest error among the four, out of 24 checks (`research/results/model_comparison.csv`):

| LightGBM | Negative binomial | SARIMAX | Random forest |
|---|---|---|---|
| 12 | 7 | 5 | 0 |

- **Negative binomial** won Regions + QC 2023 at every lead, and 2019 at 2 and 4 weeks.
- **SARIMAX** won Regions + QC 2019 at 6–8 weeks and 2025 at 4–8 weeks. It caught the most outbreak starts on Watch (88%), but the fewest on Outbreak warning (17%).
- **Random forest** stayed close to LightGBM, at a median of 2.6% higher error.
- **Calibration:**
  - Before calibration, LightGBM's range held 46–73% of weeks, the narrowest of the four.
  - After calibration, all four held about 80%.
- **The average of the four** (`blend_all4`):
  - lowest error in 11 of 24 checks against the four methods
  - error below LightGBM's in 17 of 24, median −2.6%
  - beat "same as this week" in 24 of 24
  - but caught 30% of outbreak starts on Outbreak warning, against 36% for LightGBM

  The idea of blending was picked after seeing these test years (`research/results/STATUS.md`).

### 3.3 What each variable group adds

**Recent cases.** Removing them makes the error 21–303% worse (`research/results/feature_groups.csv`, mode drop). They carry 48–76% of SHAP attention (`research/results/STATUS.md`).

**Weather, Regions + QC.** Heat, humidity and rain each helped when added to cases + season, in 14, 15 and 12 of 16 checks. The gain grows with lead time (`research/analysis/out/f3_weather_by_horizon.csv`):

| Weeks ahead | 2 | 4 | 6 | 8 |
|---|---|---|---|---|
| Error change from weather, live model (median) | +0.5% | 0.0% | −2.2% | −4.9% |
| Weather's share of SHAP attention, live model | 11% | 18% | 22% | 24% |
| Heat added to cases + season (median) | −2.2% | −3.9% | −4.1% | −7.3% |

**Weather, provinces.** No measurable gain at any lead.

**ENSO.** It hurt province forecasts in all 8 checks. For Regions + QC it was neutral: 8 of 16.

**Elevation (provinces).** It helped when added alone (7 of 8 checks, −1.9%), but not inside the full set.

**Proposed variables** (`research/results/proposed_features.csv`, `rain_lags.csv`):
- Neighbours' cases helped provinces in all 8 checks on top of the research set, at a median of −2.8%.
- Heatwave days, the rain anomaly and rain 12–23 weeks back added nothing on top.

### 3.4 Final variables

`research/results/STATUS.md`, "Final variables"; `candidates.csv`.
- **Provinces:** the live features plus neighbours' cases.
- **Regions + QC:** the live features plus heat and humidity, without ENSO.

**Against the live model:**
- better in 21 of 24 checks, median −1.4% (range −6.1% to +2.1%)
- beat "same as this week" in 21 of 24, against 19. The two new wins are Regions + QC 2023 at 2 and 4 weeks.
- range held 80%
- Watch caught 1,050 outbreak starts against 1,049; Outbreak warning caught 473 against 458

These are research findings. The submitted model in `src/` and `reports/` is unchanged.

## 4. Discussion

Details and checks are in `research/analysis/causes.md`.

**Why EpiLag usually wins.**
- The drivers are non-linear (Introduction), and boosted trees fit those shapes.
- LightGBM won every province check at 4 weeks or more, and all of Regions + QC 2024: a large, on-schedule season.

**Where it lost, and why.**
- **2019 at 2 weeks: 18% worse than "same as this week".**
  - The record epidemic rose beyond anything in the training years. Trees can't forecast past their training range [olana2025].
  - The log-linear negative binomial carried the rise forward instead.
  - Margins and level shifts are in `causes.md`, finding 5 and step 5.
- **2023: 4% worse than "same as this week".**
  - It was the flattest year in the data, with the lowest peak-to-mean ratio (1.94) and the lowest 4-week volatility (0.40; `out/f1_region_year_shape.csv`). In such a year, "same as this week" is a strong forecast.
- **2023's range was too wide (92%).**
  - The raw range was normal (68%), but the calibration margin, fit on 2022, was the largest (0.227 against 0.094–0.097; `research/results/extracts/calibration.csv`).
  - 2022's case level and rain were ordinary.
  - The regional data skip 2020–2021, so the 2022 calibration year had no "same week last year" input. This is a hypothesis, pending Person A's rerun.
- **"Same week last year" in 2020.**
  - It copied the 2019 epidemic into a year 79% lower in every province, with the drop starting in late March 2020 (`out/f2_*`).
  - The 89% skill in 2020 shows that baseline failing. It isn't typical skill.

**Why weather helps more further ahead.**
- Published lags are about 4 weeks for humidity [carvajal2018, shi2016], 5–7 weeks for rain [sumi2017], and 10–18 weeks for temperature [mordecai2017, seposo2023].
- A 2-week forecast is made after most of that weather has already shown up in cases.
- Weather's added value and attention rise steadily to 8 weeks.

**Weather does not help most in unusual years.**
- It helped most in 2024 (−9% at 4 weeks), whose wet-season rain was within 10% of normal.
- It helped little in very wet 2025 (+33%) and dry 2019 (−21%) (`out/f4_rain_anomaly_vs_weather_gain.csv`).
- Extreme years sit outside the training range, and very wet conditions lower dengue risk [ith2025].

**Expectation against result for each variable** (`causes.md`, step 5):
- **Agree with the literature:** cases, season, and weather for Regions + QC.
- **Disagree:** weather for provinces. Likely causes: unusual test years, one weather point per province, and only 3 training years, against the 10 years behind the published effects [seposo2023, xu2020].
- **ENSO:** behaves as the literature predicts. It acts on 2–5 year cycles [vanpanhuis2015], and five years of province data hold about one cycle.
- **Elevation:** also as predicted. It tracks infection, not reported cases [sy2026], and recent cases already carry each area's level.
- **Neighbours' cases:** helped provinces more than the weak evidence suggested [buczak2014, vanpanhuis2015].

**Limitations.**
- **Where the data end.** Province data stop in January 2021, so provinces have only two test years, both unusual (2019 and 2020). Regional data skip 2020–2021.
- **Choices made after seeing the test years:** the average of the four, neighbours' cases, and dropping ENSO. Their gains are optimistic, and no unseen year is left to score them.
- **Reports, not infections.** The model forecasts reported cases, which undercount infections [undurraga2017].
- **One weather point per area.**
- **Watch has a high false-alarm share (42–63%).** Outbreak warning is stricter, but catches fewer outbreak starts.
- **Calibration rests on one year**, so a gap or an unusual year carries into the next test year.
- **Unverified sources:** makridakis2022, the Mandaue study and senson2026 are unverified, and none of them supports a claim here (`references.md`).

## 5. Conclusion

**What the evidence supports.**
- The submitted LightGBM quantile model, with conformal calibration, beat both simple baselines in 5 of 6 test years. It had the lowest error of four methods in 12 of 24 checks, and ranges that held about 80% after calibration.
- Its losses have specific causes: a record year beyond the training range, a flat year, and a calibration year after a data gap.
- Weather helps the regional model at 6–8 weeks, matching the mosquito-cycle lags in the literature. Elevation and ENSO add little, also as the literature predicts.
- The research found a better set of variables: neighbours' cases for provinces, and heat and humidity for regions. It was better in 21 of 24 checks.

**Next steps.**
1. Score the final variables on a new season they haven't seen.
2. Fix the calibration-year gap, and calibrate on more than one year.
3. Test a calibrated average of the methods that keeps Outbreak-warning catches.
4. Add province data after 2021.
