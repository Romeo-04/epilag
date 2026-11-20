# Pipeline (`src/`)

The forecasting pipeline: from raw downloads to the forecasts, alerts and track records the app shows.
Every result in [`reports/`](../reports/) and [`app/data/`](../app/data/) comes from these files.

It runs on two **panels** (sets of areas observed every week):

| Panel | Areas | Weeks |
| --- | --- | --- |
| `province` | 86 province-level areas | 2016 to January 2021 (DOH via HDX) |
| `region_qc` | 17 regions and Quezon City | to December 2025 (UPRI-NOAH; Quezon City from 2010) |

## Steps, in order
Run from the repository root. The full command list is under *Rebuild everything from the raw data* in the
[main README](../README.md#run-it). `data/` is created by these steps and is not committed.

| Step | File | Reads | Writes |
| --- | --- | --- | --- |
| 1 | `fetch_data.py` | HDX dengue file, OCHA area codes and population, UPRI-NOAH dataset | `data/raw/` (skips files that already exist) |
| 2 | `clean_dengue.py` | `data/raw/` | `data/processed/dengue_unit_week.parquet`, `units.csv` |
| 3 | `fetch_weather.py` | Open-Meteo archive (ERA5), one point per area | `data/processed/weather_unit_week.parquet` (raw replies cached in `data/raw/weather/`) |
| 4 | `features.py` | the weekly case and weather panels | `data/processed/model_table_<panel>.parquet` |
| 5 | `backtest.py <panel> [--no-weather]` | the model table | `data/processed/backtest_<panel>.parquet`, `reports/backtest_<panel>.csv` |
| 6 | `alerts.py <panel>` | the backtest forecasts | `reports/alerts_<panel>.csv` |
| 7 | `train_final.py <panel>` | the model table | `app/data/<panel>_forecast.parquet`, `_drivers.parquet`, `_thresholds.parquet`, `reports/shap_<panel>.csv` |
| 8 | `export_app_data.py` | processed panels and backtests | `app/data/`: boundaries, weekly history, 4-week backtest, Quezon City barangay shares |

After step 8, [`scripts/build_web.py`](../scripts/README.md) turns `app/data/` into the JSON the web app loads.

## Shared modules
These hold rules that the web app mirrors in JavaScript, so they use pandas only.
[`tests/test_web_logic.py`](../tests/README.md) checks that both give the same answers.

| File | What it does |
| --- | --- |
| `thresholds.py` | The usual level (mean of the same week ±2 in earlier years) and the epidemic line (usual + 2 SD) per area and week of the year; `line_share` places a count on that scale (0 = usual, 1 = the epidemic line) for the web app's "Rising toward an outbreak" list |
| `reliability.py` | Each area's alert track record: how often its past *watch* and *outbreak warning* weeks were right, and how many outbreak starts were flagged |
| `allocate.py` | The budget plan: funds the actions that avert the most forecast cases per peso (fractional knapsack) |

## Rules every step follows
- **No peeking.** A forecast for week *t + h* uses only data known in week *t*. Thresholds for a test year use only the
  years before it.
- **Out of sample.** `backtest.py` retrains from scratch for each test year on data before 1 January of that year.
- **Blank is not zero.** A week with no report stays missing, so "4 weeks back" always means 4 calendar weeks.

The method is explained in plain words on the [methodology page](https://romeo-04.github.io/epilag/methodology.html).
