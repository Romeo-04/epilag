# EpiLag-PH open forecast data

The latest dengue forecasts from EpiLag-PH, free to reuse in research, news stories and other apps.

| File | Covers |
| --- | --- |
| `epilag_forecast_region_qc.csv` / `.json` | 17 regions and Quezon City, forecast from the week ending 28 Dec 2025 |
| `epilag_forecast_province.csv` / `.json` | 86 provinces, forecast from the week ending 10 Jan 2021 (the official province data ends there) |
| `index.json` | List of files with row counts and forecast dates |

Web addresses: `https://romeo-04.github.io/epilag/data/<file>`

## Columns
| Column | Meaning |
| --- | --- |
| `area_code`, `area_name` | PSGC-based area code and name (regions use `R_<name>`, Quezon City `QC`) |
| `forecast_made_week_ending` | Last week of data the forecast used (weeks end on Sunday) |
| `weeks_ahead`, `target_week_ending` | How far ahead, and the week being forecast |
| `cases_low`, `cases_middle`, `cases_high` | Likely range of reported cases that week (10th, 50th, 90th percentile, calibrated to cover 80%) |
| `cases_middle_per_100k` | Middle forecast per 100,000 people |
| `usual_level`, `epidemic_threshold` | Average for that week in earlier years, and that average + 2 standard deviations |
| `alert_level` | normal, above usual, watch (high forecast above the epidemic threshold), outbreak warning (middle forecast above it) |
| `population` | Population used (OCHA COD-PS, 2022) |

Forecasts are estimates of *reported* cases and carry uncertainty; use the range, not only the middle value.
How they are made: [methodology](https://romeo-04.github.io/epilag/methodology.html).
Regional and Quezon City forecasts build on the UPRI-NOAH Dengue–Rainfall Dataset (ODC-ODbL); please credit
EpiLag-PH and the original sources listed in the repository README.

Rebuild with `python scripts/export_open_data.py`.
