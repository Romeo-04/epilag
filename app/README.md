# Original Streamlit app (`app/`)

The first version of EpiLag-PH, kept for local use and as the Python reference for the web app's rules.
The live app is the JavaScript one in [`site/`](../site/README.md); [`tests/test_web_logic.py`](../tests/README.md)
checks that the two give the same alert levels, thresholds and replays.

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

It runs without the raw data: `data/` holds the small files it reads, written by the pipeline and committed.

| File | Written by | What it holds |
| --- | --- | --- |
| `<panel>_forecast.parquet` | `src/train_final.py` | The latest forecasts (low, middle, high) for each area and lead time |
| `<panel>_drivers.parquet` | `src/train_final.py` | Why each area is forecast that way: the SHAP contribution of each input group |
| `<panel>_thresholds.parquet` | `src/train_final.py` | Each area's usual level and epidemic line by week of the year |
| `<panel>_history.parquet` | `src/export_app_data.py` | Weekly reported cases |
| `<panel>_backtest.parquet` | `src/export_app_data.py` | The out-of-sample forecasts made 4 weeks ahead, for replays and the track record |
| `province.geojson`, `region.geojson` | `src/export_app_data.py` | Map boundaries (faeldon/philippines-json-maps, MIT) |
| `qc_barangays.csv`, `qc_barangays.geojson` | `src/export_app_data.py` | Quezon City's 142 barangays: yearly cases and boundaries |

`<panel>` is `province` or `region_qc`. Settings for the app are in [`.streamlit/config.toml`](../.streamlit/config.toml).
