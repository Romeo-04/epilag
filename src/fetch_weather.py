"""Daily rain, temperature and humidity per unit, aggregated to dengue weeks.

Source: Open-Meteo historical archive (ERA5 reanalysis), free, no key.
One point per unit centroid (a simplification: large provinces get one point).
Raw responses are cached in data/raw/weather/ so re-runs are free.

Output: data/processed/weather_unit_week.parquet
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE, OUT = ROOT / "data" / "raw" / "weather", ROOT / "data" / "processed"

API = "https://archive-api.open-meteo.com/v1/archive"
DAILY = "precipitation_sum,temperature_2m_mean,temperature_2m_max,relative_humidity_2m_mean"
# 26 weeks of lead-in before the first dengue week, to the last week of the HDX province data.
# (Region and Quezon City weekly data after 2021 come with their own rainfall.)
START, END = "2015-07-01", "2021-01-31"
BATCH = 5  # locations per request


def fetch_batch(i: int, units: pd.DataFrame) -> list[dict]:
    path = CACHE / f"batch_{i:03d}.json"
    if path.exists():
        return json.loads(path.read_text())
    params = {
        "latitude": ",".join(f"{v:.4f}" for v in units.center_lat),
        "longitude": ",".join(f"{v:.4f}" for v in units.center_lon),
        "start_date": START, "end_date": END, "daily": DAILY, "timezone": "Asia/Manila",
    }
    for attempt in range(20):
        r = requests.get(API, params=params, timeout=180)
        if r.status_code == 429:  # free tier is limited per hour: wait it out
            print(f"  rate limited on batch {i}, waiting 5 min", flush=True)
            time.sleep(300)
            continue
        r.raise_for_status()
        data = r.json()
        data = data if isinstance(data, list) else [data]
        path.write_text(json.dumps(data))
        return data
    raise RuntimeError(f"batch {i} failed")


def to_daily(unit_id: str, payload: dict) -> pd.DataFrame:
    df = pd.DataFrame(payload["daily"]).rename(columns={
        "time": "date", "precipitation_sum": "rain", "temperature_2m_mean": "temp",
        "temperature_2m_max": "tmax", "relative_humidity_2m_mean": "rh"})
    df["date"] = pd.to_datetime(df.date)
    df["unit_id"] = unit_id
    return df


def to_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    # Dengue weeks are labelled by their Sunday; W-SUN bins Mon..Sun and labels the Sunday.
    g = daily.set_index("date").groupby("unit_id").resample("W-SUN")
    weekly = pd.DataFrame({
        "rain_mm": g.rain.sum(min_count=7),
        "rain_heavy_days": g.rain.apply(lambda s: (s >= 50).sum()),
        "temp_mean": g.temp.mean(),
        "temp_max": g.tmax.max(),
        "rh_mean": g.rh.mean(),
    })
    return weekly.reset_index().rename(columns={"date": "week"})


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    units = pd.read_csv(OUT / "units.csv")
    frames = []
    for i, start in enumerate(range(0, len(units), BATCH)):
        chunk = units.iloc[start:start + BATCH]
        for unit_id, payload in zip(chunk.unit_id, fetch_batch(i, chunk)):
            frames.append(to_daily(unit_id, payload))
        print(f"batch {i + 1}/{-(-len(units) // BATCH)}", flush=True)
    daily = pd.concat(frames, ignore_index=True)
    daily = daily[daily.date <= END]  # early batches were fetched with a longer range
    weekly = to_weekly(daily)
    weekly.to_parquet(OUT / "weather_unit_week.parquet", index=False)
    print(weekly.describe().round(1).to_string())


if __name__ == "__main__":
    main()
