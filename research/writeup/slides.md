# Slide drafts (2–3 slides)

These go into `docs/deck/deck.html` only after Kish approves.

## Slide 1: Where EpiLag-PH sits in the literature

**Title:** Built on 19 dengue studies, filling a gap in the Philippine work

**Text:**
- **Features from the literature.**
  - Rain matters 5–7 weeks before cases [sumi2017, carvajal2018].
  - Humidity matters about 4 weeks before; it was Metro Manila's top weather factor [carvajal2018, xu2020].
  - Temperature risk peaks near 27.5 °C [seposo2023, mordecai2017].
- **Philippine forecasts so far.** They cover the national total by month [olana2025], one metro area [carvajal2018], one city [eligado2026], or high/low classes by province [buczak2014].
- **EpiLag-PH.** It gives weekly forecasts for 104 areas, 2–8 weeks ahead, with calibrated ranges. Its alerts are scored for both hits and false alarms, and it is tested on 5 unseen years (6 panel-years).

**Visual:** the comparison table from `research/lit/positioning.md`, cut to 5 rows: EpiLag, olana2025, carvajal2018, buczak2014, colongonzalez2021. Columns: lead time, ranges, alerts tested, unseen years.

## Slide 2: How it compares with other methods

**Title:** No method wins everywhere; LightGBM wins most

**Text:**
- **Same test for every method:** 6 test years × 4 lead times.
- **Lowest error:** LightGBM 12 of 24 checks, negative binomial 7, SARIMAX 5, random forest 0.
- **LightGBM** beats "same as this week" in 5 of 6 years at 4 weeks (18–32% lower error).
- **Why it loses sometimes:**
  - In the record 2019 epidemic, cases rose beyond the training range, which trees can't forecast past.
  - In flat 2023, "same as this week" was hard to beat.
- **An average of the four methods** had the lowest error in 11 of 24 checks and beat "same as this week" in all 24, but caught fewer outbreak starts on Outbreak warning (30% against 36%).
- **What the research changed:** adding neighbours' cases (provinces) and heat and humidity (regions) beat the submitted model in 21 of 24 checks, with no loss of outbreak catches. It was chosen after seeing the test years, so a new season is the real test.

**Chart:** a new bar chart of relative error against "same as this week", by method and test year, at 4 weeks, from `research/results/model_comparison.csv` (`rel_mae_vs_persistence`). Person A's validation page may already have one to reuse.

## Slide 3: What drives the forecast

**Title:** Recent cases lead; weather matters further ahead

**Text:**
- **Recent cases.** They carry 48–76% of the model's attention, and removing them makes the error 21–303% worse.
- **Weather (Regions + QC).** Its share grows from 11% at 2 weeks to 24% at 8 weeks. Each of heat, humidity and rain improves forecasts most at 6–8 weeks, which matches the mosquito-cycle lags in the literature.
- **Elevation and El Niño.** They added little. That is expected: elevation tracks infection, not reported cases [sy2026], and El Niño drives multi-year cycles [vanpanhuis2015] that 5 years of data can't learn.

**Chart:** `research/analysis/figures/f3_weather_gain_by_horizon.png`, alongside a small line of the SHAP weather share by lead time (`research/analysis/out/f3_weather_by_horizon.csv`; Regions + QC shares from Person A's rerun of 16 Nov).
