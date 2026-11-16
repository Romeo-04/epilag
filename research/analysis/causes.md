# Why the current results came out as they did

Step 3 of the Person B handoff. All numbers are 4 weeks ahead unless stated.

**How to reproduce.** Run `python research/analysis/step3_checks.py`. It writes the tables in `research/analysis/out/` and the charts in `research/analysis/figures/`. Its full printout is `research/analysis/out/step3_console.txt`.

**Inputs.**
- Weekly cases come from `site/public/web/data/<panel>_history.json`.
- Out-of-sample forecasts come from `site/public/web/data/<panel>_backtest.json`, which holds horizons 4 and 8. Both files are built from `data/processed/` by `scripts/build_web.py`.
- Recomputed from these files, the Regions + QC errors and coverage at 4 weeks match `reports/backtest_region_qc.csv` exactly (`out/f1_region_qc_h4_by_year.csv`). For example, 2023 gives EpiLag 57.96, persistence 55.57 and coverage 0.923.
- Margins, raw coverage and rain anomalies come from Person A's extracts in `research/results/extracts/` (`calibration.csv`, `rain_by_year.csv`), exported from `data/processed/` by `research/models/export_extracts.py`.
- Rerunning a model needs `data/processed/`, which is not on this machine. Checks that need a rerun are marked **needs a rerun**.

**Verdicts.**
- *Supported*: a check with numbers backs the hypothesis.
- *Not supported*: the numbers go against it.
- *Can't tell from this data*: the check can't separate the hypothesis from the alternatives.

---

## 1. Regions + QC 2023: EpiLag lost to "same as this week", and the range was too wide

**Result.** EpiLag's error was 57.96 against 55.57 for persistence, and the range held 92.3% of weeks against an 80% target (`reports/backtest_region_qc.csv`, test_year 2023, horizon 4).

### 1a. 2023 was a flat year

**Hypothesis.** In a flat year, "same as this week" is hard to beat.

**Check.** For each year, the shape of the 17 regions' weekly curves (`out/f1_region_year_shape.csv`):

| Year | Median peak ÷ mean | Median spread of 4-week change in log cases |
|---|---|---|
| 2016 | 2.26 | 0.45 |
| 2017 | 2.49 | 0.51 |
| 2018 | 2.26 | 0.41 |
| 2019 | 3.00 | 0.57 |
| 2022 | 2.44 | 0.53 |
| **2023** | **1.94** | **0.40** |
| 2024 | 2.68 | 0.48 |
| 2025 | 2.14 | 0.48 |

**Verdict: supported.** 2023 has the lowest peak-to-mean ratio and the lowest 4-week volatility of all 8 years. Over 4 weeks the case level barely moved, which is exactly when "same as this week" is a strong forecast. The 2.4-case gap (4%) is small next to persistence's 55.6.

Chart: `figures/f1_regions_weekly_total.png`.

### 1b. The range was too wide because of the calibration year (2022)

**Hypothesis.** The calibration year, 2022, was unusual, so it produced the largest widening.

**Check 1: the raw range was not the problem.** Before calibration, LightGBM's range held 67.9% of weeks in 2023 (`research/results/model_comparison.csv`, region_qc, 2023, h=4, lightgbm, `coverage_raw`). That is close to 2024 (69.4%) and 2025 (64.4%). After calibration, 2023 jumped to 92.3%, while 2024 landed at 79.8% and 2025 at 78.0%.
- The widening itself was set by the misses on 2022.
- Margins in log scale (`research/results/extracts/calibration.csv`; `out/f1_calibration_margins.csv`):

| Test year (calibration year) | 2 weeks | 4 weeks | 6 weeks | 8 weeks |
|---|---|---|---|---|
| 2019 (2018) | 0.120 | 0.176 | 0.243 | 0.275 |
| **2023 (2022)** | 0.119 | **0.227** | **0.346** | **0.476** |
| 2024 (2023) | 0.058 | 0.094 | 0.143 | 0.176 |
| 2025 (2024) | 0.040 | 0.097 | 0.142 | 0.184 |

  From 4 weeks ahead, 2023's margin is the largest of the four regional test years, and at 8 weeks it is 2.6–2.7 times 2024's and 2025's.

**Check 2: the range width.** The median log width of the 10–90% range was 1.07 in 2023, against 0.79 in 2024 and 0.82 in 2025 (`out/f1_region_qc_h4_by_year.csv`).

**Check 3: a mechanism found in the data layout.**
- The regional series skip 2020 and 2021. `region_qc_history.json` has 18 areas in 2016–2019 and 2022–2025, but only Quezon City in 2020–2021. `src/features.py` (`region_qc_panel`) says the same.
- `conformal_margin` in `src/backtest.py` fits on targets before 2022 and measures misses on 2022.
- In 2022, every region's "same week last year" (`y_lastyear`, a 52-week shift) is missing, because 2021 is missing.
- The early weeks of 2022 also lack the 4- and 12-week averages.
- So the calibration model forecast 2022 with less information than it will have in any later year. Its misses were larger, and the 2023 range was widened by more than 2023 needed.
- No other test year has this problem. 2024 calibrates on 2023, which has 2022 behind it, and 2025 calibrates on 2024.

**Check 4: was 2022 unusual?**
- **Case level:** the median shift of each region's yearly mean (log scale) from all earlier years is 0.51 for 2022. That is in the middle of the range: 2019 is 0.82, 2024 is 0.66, and 2023 is 0.35 (`out/f1_region_year_shape.csv`).
- **Rain:** 2022's wet-season rain was +1.0% against the areas' other years, the median over Regions + QC areas (`research/results/extracts/rain_by_year.csv`, panel region_qc, year 2022).

**Verdict: supported** that calibration on 2022 caused the over-wide range: the raw range was normal, the 2022 margin was the largest, and calibration overshot.
- The "unusual post-pandemic year" explanation is *not supported*. 2022's case level and rain were both ordinary.
- The likelier cause is the missing 2020–2021 data, which leaves the calibration year without last-year and long-average features. This is a *hypothesis* until Person A reruns `conformal_margin` for 2023 with `y_lastyear` dropped, or with the gap filled (**needs a rerun**).
- The extracts can't test it, because they hold forecasts for the test years, not for the calibration year.

**Supporting detail.** The no-weather model shows the same over-coverage in 2023 (0.935, `reports/backtest_region_qc_noweather.csv`). So the cause isn't the weather features.

---

## 2. Provinces 2020: "same week last year" failed badly

**Result.** Error 85.5 for seasonal naive against 9.7 for EpiLag (`reports/backtest_province.csv`, 2020, h=4: `mae_seasonal_naive` and `mae_epilag`).

**Hypothesis.** It copied the 2019 national epidemic into a year of COVID lockdowns and lower reporting.

**Check 1: national totals** (`out/f2_province_national_totals.csv`):

| Year | Reported cases, 86 provinces |
|---|---|
| 2016 | 209,544 |
| 2017 | 154,155 |
| 2018 | 250,783 |
| 2019 | 441,902 |
| 2020 | 91,041 |

- 2019 was 76% above 2018 and the largest year in the data. The DOH declared a national dengue epidemic on 6 August 2019 [doh2019epidemic].
- 2020 was 79% below 2019, and every one of the 86 provinces reported fewer cases in 2020 than in 2019.

**Check 2: when did 2020 fall?** Weekly 2020 totals divided by the 2016–2018 average for the same week (`out/f2_2020_weekly_ratio.csv`):
- Weeks 1–12 ran at 0.8 to 1.8 times the usual level (week 12: 1.33).
- The ratio then dropped to 0.85 in week 13, 0.55 in week 15, 0.34 in week 21, and about 0.2 from week 31 onward.

**Verdict: supported.**
- Seasonal naive forecast 2020 from 2019, the largest year on record, while 2020 was the smallest. Its error is the gap between the two curves (`figures/f2_province_2019_vs_2020.png`).
- The collapse starts in late March 2020, not at the start of the year. This fits a break in transmission or reporting around the COVID-19 lockdown rather than a naturally quiet season.
- These data can't separate "fewer infections" from "fewer reports". The lockdown date itself is not yet cited in `references.md`.
- EpiLag avoided the error because it leans on recent weeks (SHAP: recent cases carry most of the attention, `research/results/shap_groups.csv`), which fell with the reports.

**Caveat for the write-up.** Provinces' 89% skill against seasonal naive in 2020 (README) mostly reflects how badly that baseline fails in a break year. It shouldn't be presented as typical skill.

---

## 3. Weather helps little at 2 weeks and more at 8

**Hypothesis.** At short range, recent cases already carry the weather signal. Weather acts through the mosquito life cycle over several weeks.

**Check.** Error change from adding weather to the live model, as the median over test years (`out/f3_weather_by_horizon.csv`, from `reports/backtest_<panel>.csv` against `_noweather.csv`; negative means weather helped). Alongside it, weather's SHAP share (rain + heat + humidity, `research/results/shap_groups.csv`, feature_set = current):

| Weeks ahead | Regions + QC: error change | Regions + QC: weather SHAP share | Provinces: error change | Provinces: weather SHAP share |
|---|---|---|---|---|
| 2 | +0.5% | 11% | +0.6% | 9% |
| 4 | 0.0% | 18% | +1.3% | 13% |
| 6 | −2.2% | 22% | −0.4% | 16% |
| 8 | −4.9% | 24% | +0.7% | 18% |

The Regions + QC SHAP shares use Person A's rerun of 16 Nov (`research/results/METHODS.md`). An earlier draft quoted the pre-rerun shares of 15–32%.

Person A's add-one-group test on the research table, Regions + QC (`research/results/feature_groups.csv`, mode = add, median over years) points the same way:
- heat: −2.2% at 2 weeks, −7.3% at 8 weeks
- humidity: −2.7% at 2 weeks, −6.2% at 8 weeks
- rain: 0.0% at 2 weeks, −4.2% at 8 weeks

**Verdict: supported for Regions + QC, not supported for provinces.**
- For regions, the gain from weather and weather's share of attention both grow steadily with lead time.
- This matches the literature lags: rain 5–7 weeks [sumi2017, carvajal2018], humidity about 4 weeks [carvajal2018, shi2016], temperature 10–18 weeks [mordecai2017, seposo2023, carvajal2018]. A 2-week forecast is made from data that already sits inside those lags, so recent cases have absorbed the weather.
- For provinces, the SHAP share grows, but the error never improves. That is attention without gain. See finding 4 and Person A's hypothesis 2: weather is one ERA5 point per province, and the test years are 2019's record epidemic and 2020's break.

Chart: `figures/f3_weather_gain_by_horizon.png`.

---

## 4. Weather helped Regions + QC in 2024 but not in 2019, 2023 or 2025

**Result.** In 2024 the error was 101.2 with weather against 111.3 without (`reports/backtest_region_qc.csv` against `_noweather.csv`).

**Effect of weather by year** (% change in error, `out/f3_f4_weather_gain.csv`):

| Year | 2 weeks | 4 weeks | 6 weeks | 8 weeks |
|---|---|---|---|---|
| 2019 | +1.7 | 0.0 | −1.7 | −3.8 |
| 2023 | −0.7 | +1.5 | +8.2 | +12.2 |
| 2024 | −1.2 | −9.1 | −11.3 | −9.4 |
| 2025 | +3.5 | +0.1 | −2.6 | −5.9 |

**Hypothesis.** Weather adds most when a year departs from its usual season.

**Check 1: rain anomaly.** Each year's rain against the same area's other years, as the median over Regions + QC areas (`research/results/extracts/rain_by_year.csv`; `out/f4_rain_anomaly_vs_weather_gain.csv`):

| Year | Wet-season rain (Jun–Nov) vs other years | Whole-year rain vs other years | Weather effect at 4 / 8 weeks |
|---|---|---|---|
| 2019 | −20.8% (dry) | −24.1% | 0.0% / −3.8% |
| 2023 | −8.0% | +1.1% | +1.5% / +12.2% |
| 2024 | +9.0% | +1.8% | **−9.1% / −9.4%** |
| 2025 | **+32.5% (very wet)** | +26.0% | +0.1% / −5.9% |

**Check 2: case-curve shape.** How far each year's case curve departs from its usual seasonal shape. For each area, I correlated the year's weekly log cases with the mean of earlier years by week of year, then took the median across areas (`out/f4_season_departure.csv`; lower means more unusual):

| Year | Median correlation with the usual season |
|---|---|
| 2019 | 0.80 |
| 2023 | 0.76 |
| 2024 | **0.86** (most typical) |
| 2025 | **0.41** (most unusual) |

**Verdict: not supported.** By both measures, the year where weather helped most is one of the *least* unusual:
- **2024:** rain within ±10% of usual, and the most typical case curve.
- **2025:** the wettest year (+33%) and the most unusual curve, yet weather helped only at 6–8 weeks.
- **2019:** the driest year (−21%), and weather barely helped.

**What may explain it instead (hypotheses).**
- 2024 was large (397,143 regional cases against 212,025 in 2023, `out/f1_region_year_shape.csv`) but on schedule. Weather plausibly helped size a normal-timed season.
- A very wet or very dry year sits outside what the model saw in training, the same extrapolation limit as finding 5 and step 5. Very wet conditions also lower dengue risk in Southeast Asia [ith2025], so "more rain" doesn't mean "more cases" at the extremes.
- In 2023, weather *hurt* at 6–8 weeks, by +8% and +12%. Rain was near normal (−8% in the wet season), but cases stayed flat (finding 1a), so weather-driven forecasts called for a rise that didn't come. Immunity after the 2022 season is one reason a normal-weather year could stay quiet; it can't be tested with these data.

---

## 5. Before calibration, the 10–90% ranges held only 46–73% of real weeks (LightGBM)

**Hypothesis.** Each new year differs from the training years, so the raw model is overconfident.

**Check 1: coverage before and after calibration, all 24 checks per model** (`research/results/model_comparison.csv`; `out/f5_coverage_raw_vs_calibrated.csv`):

| Model | Before: min–max (median) | After: min–max (median) |
|---|---|---|
| LightGBM | 46–73% (64%) | 70–96% (79%) |
| Negative binomial | 59–89% (76%) | 67–92% (79%) |
| Random forest | 67–87% (81%) | 67–93% (80%) |
| SARIMAX | 58–89% (75%) | 69–96% (78%) |

**Check 2: does raw coverage fall in years that differ more?** Regions + QC, LightGBM, 4 weeks ahead. The year shift is the median level shift from earlier years, from finding 1:

| Test year | Year shift | Raw coverage |
|---|---|---|
| 2019 | 0.82 | 47.6% |
| 2024 | 0.66 | 69.4% |
| 2023 | 0.35 | 67.9% |
| 2025 | 0.30 | 64.4% |

The year with by far the largest shift, 2019's record epidemic, has by far the lowest raw coverage. The other three are close together.

**Verdict: partly supported.**
- Year-to-year change explains the worst case (2019).
- It does not explain why LightGBM's raw ranges are narrower than the other three models' on the *same* years. Random forest is 17 points higher at the median.
- That points to a second cause in the model itself. Each LightGBM quantile is fit separately with quantile loss, on 400 boosted trees. Trees fit the training years closely, so the training errors that set the quantiles are too small. A *hypothesis*: it could be tested by checking raw coverage on the training years, or with fewer trees or larger leaves (Person A's area).
- Calibration fixed this on average: about 79% after, against an 80% target. But it inherits finding 1b's weakness: one calibration year sets the margin for the whole next year.

Chart: `figures/f5_coverage_before_after.png`.

---

## Summary

| Finding | Verdict | Main source |
|---|---|---|
| 1a. 2023 was flat | Supported | `out/f1_region_year_shape.csv` |
| 1b. Too-wide range came from calibrating on 2022 | Supported (2022 margin largest from 4 weeks: 0.227 against 0.094–0.176). Cause: likely the 2020–21 data gap, not an unusual 2022 (hypothesis, needs a rerun) | `extracts/calibration.csv`, `model_comparison.csv`, `src/backtest.py` |
| 2. Seasonal naive copied the 2019 epidemic into 2020 | Supported. The drop starts in late March 2020 | `out/f2_*` |
| 3. Weather matters more at longer leads | Supported for Regions + QC, not for provinces | `out/f3_weather_by_horizon.csv`, `shap_groups.csv`, `feature_groups.csv` |
| 4. Weather helps most in unusual years | Not supported: on rain and on case shape, weather helped most in the most ordinary year (2024) | `out/f4_rain_anomaly_vs_weather_gain.csv`, `out/f4_season_departure.csv` |
| 5. Raw ranges too narrow because years differ | Partly supported: also a LightGBM-specific narrowness | `model_comparison.csv`, `extracts/calibration.csv` |

**Still needs a model rerun (Person A):** the 2023 calibration without `y_lastyear` (finding 1b).


---

# Step 5: Why Person A's models and variable groups came out as they did

**Sources.**
- `research/results/model_comparison.csv`: error by model, test year and lead time, plus coverage and alerts.
- `research/results/feature_groups.csv`: the add and drop tests.
- `research/results/proposed_features.csv`, `rain_lags.csv`, `rain_lag_shap.csv` and `candidates.csv`.
- `research/results/STATUS.md`, "Final variables".

"Relative error" means a model's error divided by LightGBM's on the same rows, so below 1 means it beat LightGBM.

## Models

**Wins.** Across 24 checks (6 panel-years × 4 lead times), the lowest error went to LightGBM 12 times, negative binomial 7, SARIMAX 5, and random forest 0.

### LightGBM: best overall, worst in record and flat years at short range

**Where it won.**
- Every province check at 4 weeks or more.
- All of Regions + QC 2024. There, negative binomial was 14–22% worse and LightGBM was 22–34% better than "same as this week".

**Why.**
- Boosted trees fit non-linear effects without being told their shape. The literature says the key drivers are non-linear:
  - temperature risk is an inverted U peaking near 27.5–29 °C [seposo2023, mordecai2017]
  - rain risk peaks at moderate amounts [iguchi2018]
  - humidity works through a threshold [xu2020]
- A large, on-schedule season like 2024 rewards that flexibility.

**Where it lost.**
- Regions + QC 2019 at 2 weeks: 18% worse than "same as this week".
- Regions + QC 2023 at every lead.

**Why.**
- Trees can't forecast beyond the range of their training data [olana2025 notes this for random forest; it applies to every tree model]. In 2019, the regional curve rose higher than anything in 2016–2018 (2019's level shift from earlier years was 0.82, the largest; `out/f1_region_year_shape.csv`). So at short range, LightGBM's median was capped below the actual rise.
- 2023 is the flat year of finding 1a.

### Negative binomial: wins in record and flat years, loses in big normal years

**Results.**
- Best in Regions + QC 2023 at every lead (2–19% below LightGBM).
- Best in Regions + QC 2019 at 2 and 4 weeks (31% and 14% below).
- Best in Provinces 2019 at 2 weeks (5% below).
- Worst in Provinces 2020 (15–29% above) and Regions + QC 2024 (14–22% above).

**Why.**
- It is a log-linear model of the same features. A rising log-case trend therefore carries straight into the forecast with no ceiling, which helps when a year breaks records (2019).
- When nothing changes, its forecast stays close to "this week" (2023: 0.90–0.99 of persistence's error).
- It can't bend the effect of season or temperature, so it misses a large season with the usual shape (2024).
- In 2020, the year that followed the record, it was worse than LightGBM by the most. A *hypothesis*: its linear term on last year's count (`y_lastyear`) carried part of 2019's epidemic into 2020, the same trap as finding 2. This can be checked from the fitted coefficient (Person A).
- **Literature.** tuan2024's authors name negative binomial best in a Vietnamese province, but their table, seen only in a summary, does not show it. So the literature gives no clear expectation here.

### SARIMAX: wins at long leads in some years, catches outbreaks on Watch but rarely on Warning

**Results.**
- Best in Regions + QC 2019 at 6–8 weeks and in 2025 at 4–8 weeks.
- Watch caught 1,102 of 1,260 outbreak starts, the most of the four models.
- Outbreak warning caught only 218: 20% at 2 weeks, falling to 13% at 8 weeks. LightGBM caught 40% and 30%.

**Why.** A *hypothesis*, consistent with Person A's finding that SARIMAX's median is not biased low overall:
- SARIMAX is a stationary ARMA model around a seasonal mean, so its multi-step forecast pulls back toward that mean as the lead grows. In an outbreak, its median therefore stays under the epidemic line.
- Its range widens with the lead, so the q90 crosses the line, which triggers Watch.
- Supporting evidence: Warning catches fall with lead time (63, 62, 53, 40 of 315), while Watch catches don't (262–283).
- The same pull toward the seasonal mean suits years whose total stays close to the usual (2025, `out/f1_region_year_shape.csv`).

### Random forest: never best, always close

**Results.**
- Median error 2.6% above LightGBM, ranging from 3% below to 9% above.
- The most honest raw ranges: 81% median raw coverage (finding 5).

**Why.**
- It uses the same features and the same non-linear trees as LightGBM, without boosting. So it reaches nearly the same answer, slightly less sharply.
- Quantile regression forests take their ranges from real training outcomes in the same leaf, which gives wider and better-calibrated raw ranges.
- **Disagrees with carvajal2018**, where random forest was best in Metro Manila. That comparison used weather inputs only, with no lagged cases, and no boosted model with case history. With past cases available, boosting's sharper fit edges ahead.

### Average of the four methods (`blend_all4`)

An equal average of the four methods' calibrated forecasts, scored like any model (`model_comparison.csv`; `research/results/STATUS.md`).

**Results.**
- Smallest error in 11 of 24 checks against the four methods.
- Error below LightGBM's in 17 of 24, with a median of −2.6% (range −18% to +4%).
- Beat "same as this week" in 24 of 24, against 19 for LightGBM.
- Its trade-off: Outbreak warning caught 30% of outbreak starts, against 36% for LightGBM.

**Why it wins on error.** The methods fail in different years: negative binomial in 2024, LightGBM in 2019 and 2023, SARIMAX at short leads. Averaging cancels part of each one's misses.
- **Agrees with the literature.** colongonzalez2021's superensemble beat its component models, and johansson2019 (summary only) found ensembles beat single models.

**Why it loses on Outbreak warning.** A *hypothesis*: averaging pulls the median toward the methods whose medians stay low in an outbreak. SARIMAX is one of the four, and it catches only 17% on that rule (see above). Person A notes this is untested.

**Caveat.** Blending was chosen after seeing the test years, so the gain is optimistic.

## Variable groups: expectation against result

**Columns.**
- **Expectation** comes from `research/lit/feature_evidence.csv`.
- **Result** is the median `change_pct` from `feature_groups.csv`.
  - *Add* is the change from adding the group to cases + season (negative means it helped).
  - *Drop* is the change from removing the group from the full set (positive means removing it hurt, so the group helped).
  - Counts are the checks where the group helped.

| Group | Expectation | Regions + QC result | Provinces result | Verdict |
|---|---|---|---|---|
| cases | strong, positive | drop: +73% (16/16 helped; range +25% to +259%) | drop: +113% (8/8; +21% to +303%) | **agrees** |
| season | strong | drop: +0.3% (9/16) | drop: +3.3% (7/8) | **agrees for provinces; weak for regions** |
| rain | strong, lag 4–12 weeks | add: −1.6% (12/16); drop: 0.0% (8/16) | add: +0.7% (2/8); drop: −0.2% (2/8) | **agrees for regions; disagrees for provinces** |
| humidity | strong, lag 4–8 weeks | add: −3.5% (15/16); drop: 0.0% (8/16) | add: +0.1% (4/8); drop: 0.0% (4/8) | **agrees for regions; disagrees for provinces** |
| heat | strong, inverted U | add: −3.9% (14/16); drop: +0.5% (10/16) | add: +0.3% (3/8); drop: −0.2% (3/8) | **agrees for regions; disagrees for provinces** |
| enso | mixed (multi-year cycles) | add: −1.3% (8/16); drop: +0.1% (8/16) | add: +2.3% (2/8); drop: −1.6% (0/8: hurt every time) | **agrees (mixed)** |
| topography | mixed (linked to infection, not reported cases) | not tested | add: −1.9% (7/8); drop: −0.2% (3/8) | **partly disagrees**: helps alone, not in the full set |
| population | weak | add: −4.3% (15/16); drop: +0.9% (13/16) | add: +0.1% (4/8); drop: −0.4% (3/8) | **disagrees for regions** |

### Explaining each result

- **Cases.** As expected, recent cases are the backbone; removing them makes the error 21–303% worse. The forecasting studies that use case lags rely on them too [shi2016, colongonzalez2021].
- **Season.** In regions, rain, heat and humidity follow the same yearly cycle, so dropping week of year loses little. In the add test, season sits in the base.
- **Rain, humidity and heat in regions.** Each one alone improves on cases + season, most at 6–8 weeks (finding 3), as their literature lags predict. In the drop test, removing any one costs almost nothing. The three are seasonally correlated, so the others cover for a missing one. This is redundancy, not a lack of effect.
- **Rain, humidity and heat in provinces: disagrees.** Three likely causes, not separable with these data:
  1. The province test years are a record epidemic and a reporting collapse (finding 2), when recent cases dominate.
  2. Weather is one ERA5 point per province (README "Limits"), noisier than a population-weighted regional point.
  3. Province counts are smaller and noisier, so the weather signal is weaker against week-to-week noise.

  The literature's effects are at region or province level over many years [seposo2023: 10 years and 61 provinces; xu2020: 10 years]. EpiLag's provinces have 3 training years before 2019.
- **ENSO hurt provinces in every check.** This agrees with the "mixed" rating and with its mechanism: the ENSO evidence is about 2–5 year cycles [vanpanhuis2015], and the province data span 5 years (2016–2020), about one cycle. The model can use the index as a label for the year, and that fails on a new year (Person A's hypothesis 1). For regions it was neutral, helping in 8 of 16 checks.
- **Topography: a null result in the full model, a small gain alone.** sy2026 found elevation linked to infection but not to reported incidence. In a model that already knows each area's recent cases, a fixed per-area value has little to add, and the full-set result fits that.
  - Its gain when added alone (−1.9%, 7 of 8) likely comes from acting as a stand-in for climate (lowland = warmer) and urbanisation, which the weather groups carry in the full set. That is Person A's hypothesis 3, and is a *hypothesis*.
  - edillo2022 also found no altitude effect on mosquito egg traits.
- **Population helped regions more than expected.** With 18 areas, a fixed value per area works as an area label (`research/results/METHODS.md`), which lets the pooled model learn each region's own level. That is a modelling effect, not evidence that population drives dengue.

## Proposed variables (from `feature_evidence.csv`, tested by Person A)

**Results** (`research/results/proposed_features.csv`; counts are checks where the group cut the error, medians as given in `research/results/STATUS.md`):

| Variable | Expectation (evidence) | Regions + QC: added to cases + season / to the research set | Provinces: added to cases + season / to the research set | Verdict |
|---|---|---|---|---|
| Neighbours' cases | positive, lag 1–4 weeks (weak) [buczak2014, vanpanhuis2015] | 11 of 16, −1.8% / 9 of 16, −0.1% | 6 of 8, −1.4% / **8 of 8, −2.8%** | **agrees, more strongly than the evidence suggested (provinces)** |
| Heatwave days | rises up to about 7 days a month, then falls; about 2-month lag (mixed) [ith2025] | 9 of 16, −0.8% / 9 of 16, −0.1% | 3 of 8, +1.2% / 5 of 8, −0.2% | **agrees (mixed): no gain beyond heat** |
| Rain anomaly (stand-in for drought) | positive in drought (mixed) [ith2025] | 10 of 16, −1.3% / 7 of 16, +0.6% | 1 of 8, +2.2% / 3 of 8, +0.6% | **disagrees for provinces** |
| Rain 12–23 weeks back | positive, lag 12–20 weeks (mixed) [tuan2024, seposo2023, shi2016] | 6 of 16, +0.9% (`rain_lags.csv`) | 3 of 8, +0.1% | **disagrees: attention without gain** |

### Explaining each result

- **Neighbours' cases help provinces.**
  - Dengue moves between nearby areas: buczak2014 used adjacent-province cases, and vanpanhuis2015 found travelling waves between provinces.
  - A province's neighbours often rise before it does, so their reports this week act as an early signal that the province's own lags don't yet show.
  - For regions there are only 17 large units. Neighbours are far apart and already summed within each region, so there is little to add.
  - This was carried forward after seeing the test years, so the gain is optimistic.
- **Heatwave days add nothing beyond the heat group.** The heat group already carries the 4-week maximum and the days in the 26–29 °C band. ith2025's effect is monthly and over 291 locations; at weekly scale in 18 regions, it overlaps with the temperature lags.
- **The rain anomaly hurt provinces, mainly in 2020** (+2% to +12% when added to cases + season, per `STATUS.md`).
  - In 2020, reported cases collapsed for non-weather reasons (finding 2). A weather anomaly then points the wrong way: rain may say "risk", while reports say "low".
  - It is also a stand-in for the drought index ith2025 used (scPDSI), which is not available per area.
- **Longer rain lags draw SHAP attention but don't cut the error.**
  - SHAP: rain 12–15 weeks back gets the most attention of any 4-week rain block at 6–8 weeks ahead for Regions + QC: 3.5% and 4.3% of all attention (`rain_lag_shap.csv`, via `STATUS.md`).
  - Error: better in only 9 of 24 checks, median +0.3% (`rain_lags.csv`).
  - Person A's hypothesis 4 asks whether the literature reports a 3–5 month rain-to-dengue lag.
    - Some studies tested lags that long: tuan2024 lagged climate up to 20 weeks, shi2016 up to 20, and seposo2023 (temperature) up to 18.
    - But the reported rain effects are shorter: 6–7 weeks [sumi2017], cross-correlation peaking at 5 weeks [carvajal2018], and up to 12 weeks tested [iguchi2018].
    - So the long-lag attention more likely marks where the year is in the rainy season (timing), which week of year and the 0–11-week rain lags already carry. **Verdict: supported** as the likelier reading.
- **Not tested:** minimum temperature and daily temperature range, because the cached daily weather has no minimum. Their `feature_evidence.csv` rows stay `candidate`, marked untested.

## Candidate sets and the final variables

**Final choice** (`research/results/STATUS.md`, "Final variables"; scores in `candidates.csv`):
- **Provinces:** the live features plus neighbours' cases.
- **Regions + QC:** the live features plus heat and humidity, without ENSO.

**Against the live model, over 24 checks:**
- Error better in 21, median −1.4% (range −6.1% to +2.1%).
- Beat "same as this week" in 21, against 19.
- Range held 80% on average.
- Watch caught 1,050 outbreak starts against 1,049. Outbreak warning caught 473 against 458.

### Why these won

- **Provinces + neighbours'** is the only province set better in all 8 checks, and it catches more outbreak starts on both rules (`STATUS.md` candidate table: Watch 786 against 779, Outbreak warning 374 against 357). The reasons are above.
- **Regions + QC + heat and humidity** has the strongest literature support of all candidates:
  - humidity was the top weather factor in Metro Manila [carvajal2018] and drove the second seasonal peak [xu2020]
  - temperature risk is an inverted U peaking near 27.5 °C [seposo2023]

  Each helped on its own in 14–15 of 16 checks (`feature_groups.csv`).
- **ENSO was left out.**
  - Its extra gain sits mostly in 2023 (−5% to −14%).
  - It costs 10 Outbreak-warning catches (89 against 99).
  - The literature supports it for 2–5 year cycles [vanpanhuis2015], which these data can't learn from about one cycle (step 5, ENSO).

### What they cost

- **Error.** Three checks got worse: Regions + QC 2019 at 2 and 4 weeks (+2.1%, +0.4%), and 2025 at 6 weeks (+1.6%). 2019 is the record year, where every tree-based set is capped (step 5, LightGBM).
- **Gain left on the table.** The research set with ENSO and the average of the four methods cut the regional error more (−2.4% and −3.4% median), at the cost of Outbreak-warning catches.
- **Optimism.** The choices were made after seeing the test years, and no unseen year is left to score them (province data end in January 2021). Treat the −1.4% as an upper estimate until a new season is scored.
- **Not yet live.** `src/` and `reports/` still hold the submitted model. The write-up reports the submitted model as the main result, and the final variables as what the research found.
