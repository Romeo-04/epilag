# Handoff: Person B, literature and analysis

You are Person B's agent on EpiLag-PH, a PJDSC 2026 top-10 finalist. The final round is judged as research. The mentor asked for:

- a literature review (RRL) behind every model feature
- a comparison with published models
- a test of heat, topography and other variables
- a conclusion that explains *why* the results came out as they did

Person A's agent is working at the same time. Person A builds the comparison models and runs the experiments. **You own the literature and the interpretation.**

## The project

EpiLag-PH forecasts weekly dengue cases 2, 4, 6 and 8 weeks ahead. It covers 86 provinces (data 2016 to Jan 2021) and 17 regions plus Quezon City (data to Dec 2025).

**Model**
- One LightGBM quantile model per lead time gives a low, middle and high forecast (q10/q50/q90).
- The range is widened by conformal calibration on the last training year.

**Alerts**
- **Watch:** the high end (q90) is above the epidemic line.
- **Outbreak warning:** the middle (q50) is above the epidemic line.

**Test design**
- Every test year is forecast by a model trained only on earlier years.
- Test years:
  - Provinces: 2019 and 2020.
  - Regions + QC: 2019, 2023, 2024 and 2025.
- Baselines:
  - persistence ("same as this week")
  - seasonal naive ("same week last year")

The code is the source of truth for the details: `src/features.py` (features), `src/backtest.py` (test design and calibration), `src/thresholds.py` (epidemic line), `src/alerts.py` (outbreak starts and false alarms), and the README section "Methods".

## Workspace

**Your checkout.** Work in your own checkout so Person A's stays put.
- Same machine: `git worktree add ../epilag-b -b research-b research-a` from inside `epilag/`.
- Another machine: a fresh clone, then `git switch -c research-b`.

**Python.** Use Person A's venv (`../epilag/.venv/Scripts/python`) or make your own from `requirements.txt`.

**Data.** `data/processed/` is gitignored.
- Same machine: copy it from `../epilag/data/processed`.
- Otherwise: ask your human for the files, or rebuild them with the steps in README "Run it". The weather download waits out a free-tier limit, so expect an hour or more.

**File ownership.**
- **You write:** `research/lit/`, `research/analysis/`, `research/writeup/`.
- **Person A writes:** `src/`, `research/models/`, `research/results/`.
- You read everything.

**Commits.** Commit locally on `research-b`, in small commits with plain messages and no AI attribution lines. Push only when your human says so.

**Getting Person A's results.** Run `git merge research-a` whenever `research/results/STATUS.md` reports new files.

**Your status.** Keep `research/lit/STATUS.md` current with what is done, what is next, and anything Person A needs to know.

## Three words that govern the work

- **verified**: you opened the source (DOI, PubMed Central or publisher page) and saw the claim there yourself. Only verified citations enter the tables; every other row says `unverified` in its status column.
- **traceable**: every number you write names the file and filter it came from, or the script in `research/analysis/` that computes it.
- **hypothesis**: a cause stays labelled a hypothesis until a check with numbers backs it; then it becomes *supported*, *not supported* or *can't tell from this data*.

## Steps

Do steps 1 and 2 first. Then step 3, which can start right away because it uses existing outputs. Steps 4 and 5 follow. Step 6 comes last.

### 1. Feature evidence table (Person A is waiting on this)

**Output:** `research/lit/feature_evidence.csv` with one row per feature and these columns:
`group, feature, status, mechanism, expected_lag_weeks, expected_direction, evidence_strength, citations, notes`

- **status:** `current`, `candidate` or `proposed`.
- **evidence_strength:** `strong`, `mixed`, `weak` or `none`.
- **citations:** keys from `references.md`.

Cover every current feature in `feature_columns()` in `src/features.py`:
- recent cases and trend
- cases in the same week last year
- rain this week and 1 to 11 weeks back
- 4, 8 and 12-week rain totals
- heavy-rain days
- humidity
- mean and maximum temperature
- season (week of year)
- population

Cover every candidate Person A is building:
- **heat:** minimum temperature, daily temperature range, days inside the 26–29 °C transmission band, heat index
- humidity and temperature for Regions + QC
- **ENSO:** the Oceanic Niño Index
- **topography:** mean elevation, and the share of land below 100 m
- population density

If you find strong evidence for something else, add it as `proposed`.

Where the evidence is mixed, record both sides. Elevation is mixed for the Philippines, for example.

**Done when:**
- Every row has a mechanism, an expected lag and direction, and either at least one verified citation or `evidence_strength=none`.
- The file is committed.
- `STATUS.md` says it is ready.

### 2. Literature matrix (RRL)

**Outputs:**
- `research/lit/rrl_matrix.csv`
- `research/lit/references.md` (full citations with DOI or URL, each with a short key)

**Selection:** 15–25 papers.
- At least 8 from the Philippines.
- The rest from Southeast Asia, or landmark dengue forecasting and early-warning work.
- Prefer weekly forecasting, papers that compare models, and papers that test on held-out years.

**Columns:**
`key, place, years, area_level, horizon, models_compared, features, lags_that_mattered, metric, best_model, beat_simple_baseline, ranges_given, alerts_tested, held_out_years, status`

**Done when:**
- At least 15 verified rows.
- Every column is filled, or says `not reported`.

### 3. Explain the current results

**Outputs:**
- `research/analysis/causes.md`
- analysis scripts in `research/analysis/`
- charts as PNG in `research/analysis/figures/`

For each finding below, write the **hypothesis**, run a **check** that produces numbers, and give a **conclusion**.

The sources are `reports/backtest_<panel>.csv`, `reports/backtest_<panel>_noweather.csv`, `reports/alerts_<panel>.csv` and `reports/shap_<panel>.csv`. Per-week predictions, including the calibration margin, are in `data/processed/backtest_<panel>.parquet`. All numbers are at 4 weeks ahead unless stated.

**1. Regions + QC 2023.** EpiLag lost to "same as this week" (error 58.0 vs 55.6). Its range was also too wide: 92% of weeks fell inside, against an 80% target.
- *Hypothesis:* the calibration year, 2022, was an unusual post-pandemic year. Its margin of 0.227 is the largest of the six tests. In 2024 and 2025 the margins were about 0.09 and coverage landed near 80%.
- Also check whether 2023 was a flat year, where "same as this week" is hard to beat.

**2. Provinces 2020.** "Same week last year" scored an error of 85.5, against EpiLag's 9.7.
- *Hypothesis:* it copied the 2019 national epidemic into a year of COVID lockdowns and lower reporting.
- Check against national totals for 2019 and 2020, and cite the 2019 epidemic declaration.

**3. Weather helps little at 2 weeks and more at 8.** Compare the backtest with and without weather at each lead time, and the SHAP weather share at each lead time.
- *Hypothesis:* at short range, recent cases already carry the weather signal, and weather acts through the mosquito life cycle over several weeks.

**4. Weather helped in Regions + QC 2024** (error 101.2 vs 111.3 without weather) **but not in 2019, 2023 or 2025.**
- *Hypothesis:* weather adds the most when a year departs from its usual season.
- Check each year's rain anomaly against the gain from weather.

**5. Before calibration, the 10–90% ranges caught only 48–69% of real weeks.**
- *Hypothesis:* each new year differs from the training years, so the raw model is overconfident.
- `../finals/validation_data.py` shows how the raw coverage is computed, if that folder is on your machine.

**Done when:**
- Every finding has a check that was run, with numbers, a chart where it helps, and a verdict.
- Each verdict names its sources.

### 4. Place EpiLag among published work

**Output:** `research/lit/positioning.md`

Build a table of EpiLag against the papers in your matrix. Columns:
- methods
- area level
- lead times
- whether ranges are given
- whether alerts were tested
- whether testing used unseen years
- skill against a simple baseline

Raw error can't be compared across papers, because places and case counts differ. Compare **relative** error against a baseline wherever a paper reports one.

Then write the gap EpiLag fills. Claim only what the matrix supports, and cite the rows.

**Done when:** every claim about other work points to a row in the matrix.

### 5. Explain Person A's results

When `research/results/` holds the model comparison and feature-group files (formats below), extend `causes.md`:

- **Models:** why each one won or lost, by test year and lead time.
- **Variables:** a table of expectation against result for each variable group.
  - The expectation comes from your step 1 table; the result comes from Person A's numbers.
  - Mark each row *agrees* or *disagrees*, and explain each disagreement.
- **Null results:** a group that adds nothing is a finding too. For example, past cases may already reflect an area's level, which would leave static topography nothing to add. Explain why.

**Done when:** every model and every variable group has a sentence explaining its result, with numbers.

### 6. Write-up drafts

**Outputs:**
- `research/writeup/discussion.md`: results, discussion, limitations and conclusion, all traceable.
- `research/writeup/slides.md`: 2–3 slides covering where EpiLag sits in the literature, the model comparison, and what drives the forecast. For each slide give the text and which chart it uses.
- `research/writeup/qa.md`: likely judge questions with short answers. Include "why LightGBM", "why not LSTM", "why didn't topography help" and "what went wrong in 2023".

Edit the deck and the site only after your human approves these drafts. The deck is `docs/deck/deck.html` and the methodology page is `site/methodology.html`.

**Done when:** all three drafts exist, and every number in them is traceable.

## What Person A delivers

All of this lands in `research/results/`, with `STATUS.md` noting what changed. You can write your analysis scripts against these formats before the files exist.

**Variable groups (shared names):**

| Group | Features |
|---|---|
| `cases` | recent cases, trend, same week last year |
| `season` | week of year |
| `rain` | rain lags, rain totals, heavy-rain days |
| `heat` | temperature features, plus the new heat features |
| `humidity` | humidity |
| `enso` | Oceanic Niño Index |
| `topography` | elevation, share of land below 100 m |
| `population` | population, density |

**`model_comparison.csv`**: one row per panel, test year, lead time and model.

`panel, test_year, horizon, model, n, mae, rel_mae_vs_persistence, rel_mae_vs_seasonal, coverage_10_90, coverage_raw, onsets, caught_watch, false_share_watch, caught_warning, false_share_warning`

- **Models:** `lightgbm`, `negbin` (negative binomial regression), `sarimax`, `random_forest`, `persistence`, `seasonal_naive`.
- **Baselines** have no range, so their coverage and Watch columns are blank. Their Outbreak warning uses the single forecast against the epidemic line.

**`feature_groups.csv`**: one row per panel, test year, lead time, mode and group.

`panel, test_year, horizon, mode, group, n_features, mae, mae_reference, change_pct, coverage_10_90, caught_watch, false_share_watch`

- `mode=drop` removes one group from the full model; its reference is the full model.
- `mode=add` adds one group to a base of `cases` + `season`; its reference is that base.

**`shap_groups.csv`**: each group's share of the model's attention.

`panel, horizon, group, share`

**`shap_lags.csv`**: which weeks back matter, for rain, temperature and humidity.

`panel, horizon, variable, lag_weeks, mean_abs_shap`

## Starting papers (verified 2026-11-16, add to `references.md`)

- **Carvajal et al. 2018**, *BMC Infectious Diseases* 18:183, Metro Manila. DOI 10.1186/s12879-018-3066-0. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5905126/
  - Compared GAM, SARIMAX, random forest and gradient boosting; random forest was best.
  - Lagged weather worked best, and humidity was the top weather factor.
- **Olana et al. 2025**, *Transboundary and Emerging Diseases*, Philippines at national scale. DOI 10.1155/tbed/7480710. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12543447/
  - Compared SARIMA, NNAR, random forest, LSTM, TBATS and Prophet.
- **Ba Ria–Vung Tau, Vietnam, 2024**, *Tropical Medicine and Infectious Disease* 9(10):250. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11511084/
  - Negative binomial regression had the lowest error, beating SARIMAX, XGBoost and LSTM.
  - Climate lagged 2–20 weeks helped.
- **Iguchi, Seposo & Honda 2018**, *BMC Public Health*, Davao. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5952851/
  - Distributed-lag model; rain and dew point effects.
- **Seposo, Valenzuela & Apostol 2023**, *PLOS NTD*, 61 provinces. https://doaj.org/article/6985f15756784f108b9d30679808c2c5
  - Dengue risk rises with temperature to 27.5 °C, then falls.
- **Mordecai et al. 2017**, *PLOS NTD* 11(4):e0005568. https://doaj.org/article/c4e055a826b840dda8e8bba1eab01241
  - Transmission happens at 18–34 °C and peaks at 26–29 °C.
- **van Panhuis et al. 2015**, *PNAS* 112(42):13069. DOI 10.1073/pnas.1501375112
  - Dengue cycles across Southeast Asia move with the Oceanic Niño Index and high temperatures.
- **Lowe et al. 2014**, *Lancet Infectious Diseases* 14(7):619. DOI 10.1016/S1473-3099(14)70781-9
  - A Bayesian early-warning system for Brazil, up to 3 months ahead.
- **Elevation in the Philippines** (mixed evidence):
  - A nationwide study links low elevation and density to infection, but not to reported cases: https://pmc.ncbi.nlm.nih.gov/articles/PMC8898531
  - A Mandaue City study found weak links with elevation and slope: https://publish.mersin.edu.tr/index.php/igd/article/view/1262
- **Already cited in the README:** Romano et al. 2019 (conformalized quantile regression), Undurraga et al. 2017, Bowman et al. 2016, and Pelitro et al. 2026 (the UPRI-NOAH dataset).
