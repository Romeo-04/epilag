# Person A status

How the experiments were run: `METHODS.md`.

- [x] Harness: every model takes the same test. LightGBM through the harness reproduces `reports/backtest_*.csv` and `reports/alerts_*.csv` exactly, for both panels.
- [x] `model_comparison.csv`: negbin, random_forest and sarimax against lightgbm and the two baselines, both panels.
- [x] Blends in `model_comparison.csv` (`blend_all4`, `blend_lgb_negbin`): equal average of the methods' calibrated forecasts, scored like any model (error, range, both alert rules).
- [x] New variables: heat, humidity and ENSO for Regions + QC; heat, ENSO, elevation and density for provinces (`METHODS.md`).
- [x] `feature_groups.csv`: each group removed from the full set, and added to cases + season. LightGBM, same test, both panels.
- [x] `shap_groups.csv`, `shap_lags.csv` (rows with `feature_set = plus` use the research table; `current` is the live feature set).
- [x] `rain_lags.csv`, `rain_lag_shap.csv`: rain totals 12–23 weeks back added to the research set.
- [x] `proposed_features.csv`: Person B's proposed variables (neighbours' cases, heatwave days, rain anomaly), tested like the other groups.
- [x] `candidates.csv`: candidate final sets, scored on every measure. `live` reproduces the live LightGBM exactly (largest difference 1e-14).
- [x] `extracts/`: the parts of `data/processed/` that Person B's analysis needs (`export_extracts.py`).
- [x] Validation page: new sections 4 (data groups) and 6 (other methods). The page lives outside the repo, in `pugad/finals/`.
- [x] Final variables chosen (below). Not applied to the live model yet.

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
- **Provinces without ENSO** (the research set minus ENSO, from the `drop` runs in `feature_groups.csv`): level with the live model, better in 4 of 8, median 0.0% (−0.7% to +1.6%). ENSO accounts for most of the province gap; the other new province variables (heat, elevation, density) add nothing measurable on top.
- **Regions + QC without ENSO:** better than the live model in 13 of 16, median −0.9%. Much of the 2023 gain further ahead comes from ENSO: at 6 and 8 weeks the set without ENSO is −4.8% and −1.5% against the live model, against −11.9% and −14.2% with it.
- **Overall:** better in 11 of 24 checks, median +0.5%. Watch caught 1,066 outbreak starts, against 1,049 for the live model (of 1,260 across lead times).

**SHAP (final model, research table).**
- Recent cases carry 48–76% of the model's attention, falling with lead time.
- Then come time of year (7–13%) and rain (Regions + QC 8–17%, provinces 5–8%).
- ENSO gets 4–11% of the provinces' attention, despite making their forecasts worse.
- **Lag profiles (`shap_lags.csv`):**
  - Rain's largest share is at the longest lag offered (10–11 weeks) in 3 of 4 lead times, for both panels. Tested below: longer windows do not help.
  - Temperature peaks 4–8 weeks back. Humidity: 8 weeks for provinces.

**Longer rain lags (`rain_lags.py`).** Three 4-week rain totals, 12–15, 16–19 and 20–23 weeks back, added to the research set. LightGBM, same test.
- **Error:** no gain. Better in 9 of 24 checks, median +0.3% (−2.7% to +4.8%). Regions + QC: 6 of 16, median +0.9% (better in all of 2019, worse in all of 2023 and 2024). Provinces: 3 of 8, median +0.1%.
- **Watch:** 2 fewer outbreak starts caught for Regions + QC (263 against 265 of 324), 8 fewer for provinces (793 against 801 of 936).
- **SHAP (`rain_lag_shap.csv`):** the model does use the new windows. Rain 12–15 weeks back gets more attention than any other 4-week block of rain at 6 and 8 weeks ahead for Regions + QC (3.5% and 4.3% of all attention), and at 4–8 weeks for provinces (1.6–2.7%). The share falls from 16 weeks back.
- **Likely reading (not tested):** rain 3–4 months before the forecast week marks where the year is in the rainy season, which the time-of-year features and the existing lags already carry. So it draws attention without improving forecasts. Keep the 0–11-week window.
- Caveat: these windows were chosen after seeing the SHAP lag profile on all data, so this is a check of one idea, not a search.

## Ready now: Person B's proposed variables

`proposed_features.py`, built as in `METHODS.md`. Each group was added to cases + time of year (`add_to_base`) and to the full research set (`add_to_plus`). Counts are checks where the group cut the miss. Watch is outbreak starts caught, pooled (cases + time of year alone: 270 of 324 for Regions + QC, 807 of 936 for provinces; full research set: 265 and 801).

| Group | Regions + QC, add to base | Regions + QC, add to research set | Provinces, add to base | Provinces, add to research set |
|---|---|---|---|---|
| Neighbours' cases | 11 of 16, median −1.8%; Watch 272 | 9 of 16, −0.1%; Watch 258 | 6 of 8, −1.4%; Watch 815 | **8 of 8, −2.8%** (−4.5% to −1.1%); Watch 804 |
| Heatwave days | 9 of 16, −0.8%; Watch 284 | 9 of 16, −0.1%; Watch 258 | 3 of 8, +1.2%; Watch 801 | 5 of 8, −0.2%; Watch 794 |
| Rain anomaly (drought) | 10 of 16, −1.3%; Watch 279 | 7 of 16, +0.6%; Watch 271 | 1 of 8, +2.2% (2020: +2% to +12%); Watch 809 | 3 of 8, +0.6%; Watch 797 |

- **Neighbours** is the one proposed group that adds to what the model already has, and only for provinces: better in all 8 checks on top of the research set. It goes into the candidate sets below.
- **Regions + QC:** each group helps a little on its own, but none adds anything on top of the research set. On their own they help less than humidity (15 of 16) or heat (14 of 16).
- **Heatwave days and the rain anomaly** hurt provinces in 2020 when added to cases + time of year. 2020 is the COVID year, so this may be a change in reporting rather than in weather.
- **Not built:** daily minimum temperature and daily temperature range (`candidate` rows in `feature_evidence.csv`). Neither cached daily weather set has a daily minimum; testing them means refetching all daily weather.
- Caveat: neighbours was carried forward after seeing these test years.

## Ready now: candidate final sets

`candidates.py`, LightGBM, same test. Change is the average miss against the live set; negative is better. Watch and Outbreak warning are outbreak starts caught, pooled over test years and lead times. The average of the four comes from `model_comparison.csv`.

**Regions + QC** (16 checks; 324 outbreak starts)

| Set | Better than live | Median change (worst) | Beat "same as this week" | Range held, mean (min–max) | Watch caught | Outbreak warning caught |
|---|---|---|---|---|---|---|
| Live | – | 0 | 11 of 16 | 81% (70–96%) | 270 | 101 |
| + heat, humidity, ENSO (research set) | 11 of 16 | −2.4% (+2.5%) | 15 | 79% (68–94%) | 265 | 89 |
| + heat, humidity (no ENSO) | 13 of 16 | −0.9% (+2.1%) | 13 | 81% (73–95%) | 264 | 99 |
| Average of the four methods | 13 of 16 | −3.4% (+4.4%) | 16 | 83% (75–97%) | 277 | 80 |

**Provinces** (8 checks; 936 outbreak starts)

| Set | Better than live | Median change (worst) | Beat "same as this week" | Range held, mean (min–max) | Watch caught | Outbreak warning caught |
|---|---|---|---|---|---|---|
| Live | – | 0 | 8 of 8 | 78% (76–80%) | 779 | 357 |
| + neighbours' cases | **8 of 8** | −2.4% (−0.5%) | 8 | 79% (76–80%) | 786 | 374 |
| + elevation, density | 3 of 8 | +0.1% (+0.6%) | 8 | 78% (76–80%) | 783 | 340 |
| Research set | 0 of 8 | +1.2% (+9.5%) | 8 | 79% (75–82%) | 801 | 337 |
| Research set, no ENSO | 4 of 8 | 0.0% (+1.6%) | 8 | 78% (74–79%) | 782 | 343 |
| Research set, no ENSO, + neighbours | 8 of 8 | −2.0% (−0.6%) | 8 | 79% (75–80%) | 789 | 355 |
| Average of the four methods | 4 of 8 | +0.4% (+4.2%) | 8 | 79% (73–85%) | 820 | 303 |

How to read it:
- **No set wins on every measure.** The sets that cut the miss most for Regions + QC (the research set, the average) catch fewer outbreak starts on Outbreak warning (89 and 80, against 101).
- **Provinces: live + neighbours** is better in every check and catches more starts on both rules (+7 on Watch, +17 on Outbreak warning). The neighbours' cases are this week's reports, known when the area's own are.
- **Regions + QC: heat and humidity without ENSO** is a small, steady gain (13 of 16, worst +2.1%) that keeps Outbreak warning nearly level (99 against 101). With ENSO the gain is bigger, mostly in 2023 (−5% to −14%), and hypothesis 1 says ENSO may be acting as a year label.
- **Caveats.** Neighbours, the blend and dropping ENSO were all chosen after seeing these test years, so every gain here is optimistic. Provinces have only two test years, 2019 and 2020, and both were unusual.

## Final variables (chosen 16 Nov)

The human delegated the choice to Person A's recommendation:
- **Provinces:** the live features + neighbours' cases (`live_neighbours` in `candidates.csv`).
- **Regions + QC:** the live features + heat and humidity, without ENSO (`research_no_enso`).

Together, against the live model over the 24 checks:
- **Miss:** better in 21 of 24, median −1.4% (−6.1% to +2.1%); by lead time −1.8% / −2.6% / −0.9% / −1.1%. Worse in three: Regions + QC 2019 at 2 and 4 weeks (+2.1%, +0.4%) and 2025 at 6 weeks (+1.6%).
- **Beat "same as this week":** 21 of 24, against 19. The two new ones are Regions + QC 2023 at 2 and 4 weeks, the year the live model lost.
- **Range held:** mean 80% for both.
- **Alerts:** Watch caught 1,050 outbreak starts against 1,049 (of 1,260), false alarms 58% for both. Outbreak warning caught 473 against 458, false alarms 30% for both.

**Why these.** They cut the miss without losing outbreak starts on either rule. ENSO was left out: its extra gain is mostly Regions + QC 2023, it costs 10 Outbreak-warning catches (89 against 99), and it may be acting as a label for the year (hypothesis 1). The average of the four methods was not chosen because it catches the fewest starts on Outbreak warning.

**Not applied to the live model.** `src/` and `reports/` still hold the submitted model. Applying the choice (`HANDOFF.md`, open work 3) means:
- `src/`: neighbours' cases for provinces, and the research weather pipeline (region temperature and humidity from Open-Meteo) for Regions + QC.
- Rebuilding every output: README numbers, the Quezon City 2024–25 story, the "30 of 32" replay claim (checked in `tests/test_web_logic.py`), the app, the game and the open data.
- Then the validation page, the deck and the site.

**For the write-up:** report the submitted model as the main result, and the chosen sets as what the research found.

**Caveat.** Both choices were made after seeing the test years, and no year outside the tests is left to score them on: province data ends in January 2021, Regions + QC data in December 2025. Treat the gain as optimistic until a new season is scored.

## For Person B

**Get the files.** `git pull origin research-a`. The extracts in `research/results/extracts/` replace `data/processed/` for steps 3 and 5 (`HANDOFF-B.md`, "Data"). The zip is only needed to rerun the models.

**Inputs for step 5:**
- Models: `model_comparison.csv` (the four methods and both averages).
- Variables: `feature_groups.csv`, `proposed_features.csv`, `rain_lags.csv`.
- Attention: `shap_groups.csv`, `shap_lags.csv`, `rain_lag_shap.csv`.
- The final choice: `candidates.csv`, and "Final variables" above.
- Fix: the Regions + QC `current` rows of `shap_groups.csv` and `shap_lags.csv` were rerun on 16 Nov (`METHODS.md`). Re-read them if you used them before.

**Answers to your notes for Person A:**
- **Rain 12–20 weeks back:** tested, no gain (above, "Longer rain lags"). Better in 9 of 24 checks, median +0.3%. Update that `proposed` row.
- **Heatwave days, drought index, neighbours' cases:** tested (above, "Person B's proposed variables"). Drought is a rain anomaly standing in for scPDSI, which is not available per area. Only neighbours helps on top of the research set, and only for provinces.
- **Heat index:** built (`heat_hi4`, the 4-week mean of the daily heat index) but tested only inside the heat group, never on its own. So these results can't say whether it adds anything beyond its parts (temperature and humidity).
- **Minimum temperature and daily temperature range:** not built. Neither cached daily weather set has a daily minimum. Mark those `candidate` rows as untested.

**Hypotheses for Person B to check against the literature (not findings):**
1. ENSO hurts provinces because 5 years of province data (2016–2020) hold about one El Niño cycle. The model can use ENSO as a label for the year, and that pattern does not carry over to a new year. For Regions + QC it helped in 2023 and 2024 from 4 weeks ahead, not in 2019, and was mixed in 2025. QC alone has 16 years of data.
2. Weather groups help Regions + QC more than provinces. Region weather is one population-weighted point per region, while province weather is one point per province. Region counts are larger and smoother, too. Or the province test years (2019 record epidemic, 2020 COVID) are unusual.
3. Elevation helps provinces on its own but not inside the full set. It may stand in for something the other variables already carry (rain, temperature or urbanisation).
4. Rain's attention peaks 12–15 weeks before week t (14–23 weeks before the target week), but adding those weeks does not cut the miss. Compare with `expected_lag_weeks` in the literature: is a 3–5 month rain-to-dengue lag reported, or is this the rainy season's timing?

Waiting on: the human's word on applying the final variables to the live model (`HANDOFF.md`, open work 3).
