"""Publish the latest forecasts as open data in docs/data/ (CSV and JSON), for researchers, newsrooms and other apps.
Usage: python scripts/export_open_data.py"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "data"
COLUMNS = {
    "unit_id": "area_code", "unit_name": "area_name", "week": "forecast_made_week_ending", "horizon": "weeks_ahead",
    "target_week": "target_week_ending", "q10": "cases_low", "q50": "cases_middle", "q90": "cases_high",
    "q50_per100k": "cases_middle_per_100k", "alert": "usual_level", "epidemic": "epidemic_threshold", "level": "alert_level",
    "population": "population",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"source": "EpiLag-PH, https://github.com/Romeo-04/epilag", "files": {}}
    for panel, label in [("region_qc", "17 regions and Quezon City"), ("province", "86 provinces (data ends Jan 2021)")]:
        f = pd.read_parquet(ROOT / "app" / "data" / f"{panel}_forecast.parquet")[list(COLUMNS)].rename(columns=COLUMNS)
        for col in ("forecast_made_week_ending", "target_week_ending"):
            f[col] = f[col].dt.strftime("%Y-%m-%d")
        for col in ("cases_low", "cases_middle", "cases_high", "usual_level", "epidemic_threshold"):
            f[col] = f[col].round(1)
        f["cases_middle_per_100k"] = f["cases_middle_per_100k"].round(2)
        f = f.sort_values(["weeks_ahead", "area_name"])
        name = f"epilag_forecast_{panel}"
        f.to_csv(OUT / f"{name}.csv", index=False)
        (OUT / f"{name}.json").write_text(json.dumps(f.to_dict("records"), indent=1))
        meta["files"][name] = {"covers": label, "rows": len(f), "forecast_made_week_ending": f.forecast_made_week_ending.max()}
        print(name, len(f), "rows")
    (OUT / "index.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
