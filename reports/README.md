# Results (`reports/`)

The submitted model's out-of-sample test results. Every file is written by the pipeline in [`src/`](../src/README.md);
the numbers in the main README, the app's *Did it work?* page and the deck come from these files.
`<panel>` is `province` (86 areas, test years 2019–2020) or `region_qc` (17 regions and Quezon City, test years
2019 and 2023–2025).

| File | Written by | One row per | Columns |
| --- | --- | --- | --- |
| `backtest_<panel>.csv` | `src/backtest.py` | test year × lead time | `n` area-weeks; average error (MAE) of EpiLag-PH and of the two baselines ("same week last year", "same as this week"); `skill_vs_*` (error change against each baseline, negative is better); `coverage_10_90` (share of weeks inside the range) |
| `backtest_<panel>_noweather.csv` | `src/backtest.py --no-weather` | test year × lead time | The same, for the model without weather inputs (the weather test) |
| `alerts_<panel>.csv` | `src/alerts.py` | test year × lead time × alert rule | `onsets` (outbreak starts), `onsets_warned` and `share_warned` (caught in time), `warnings` (alert weeks), `false_alarm_share` |
| `shap_<panel>.csv` | `src/train_final.py` | lead time × input | `mean_abs_shap` (how much the input moved the forecast) and its `group` (recent cases, season, rain by week, rain totals and, for provinces, heavy rain, temperature and humidity) |

The deeper experiments after the first round (other methods, new inputs, causes of each loss) are in
[`research/results/`](../research/results/README.md).
