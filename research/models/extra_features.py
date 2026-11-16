"""New candidate variables for the research comparison (the live model is unchanged).

heat        Days in the 26-29 C transmission band (Mordecai 2017), days at or above 34 C (top of the
            transmission range), and the heat index; each as a 4-week total or mean known at week t.
            Regions + QC also get the temperature and humidity lags the province model already has.
humidity    rh_lag* for Regions + QC (provinces already have them).
enso        Oceanic Nino Index (NOAA CPC) for the 3-month season centred 2 and 5 months before
            week t, so the value was already published at forecast time.
topography  Provinces only (18 regional units are too few for a fixed per-area value): mean elevation
            and the share of land below 100 m, from 42,048 barangay centroids (Copernicus DEM
            GLO-90 via the Open-Meteo elevation API), weighted by barangay area.
population  Log population density (people per km2), provinces only.

Weather for Regions + QC is ERA5 from Open-Meteo, one population-weighted point per region and the
Quezon City centre. Province weather reuses the cached daily ERA5 from src/fetch_weather.py.

Usage: python research/models/extra_features.py   (fetches what is missing, then builds both tables)
Output: data/processed/research/model_table_<panel>_plus.parquet
"""
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import fetch_weather  # noqa: E402
from features import PROC, _region_code, feature_columns  # noqa: E402

RAW = ROOT / "data" / "raw" / "research"
OUT = PROC / "research"
QC_POINT = (14.6760, 121.0437)
GROUPS = {"cases": ("y_",), "season": ("woy_",), "rain": ("rain_", "heavy_"), "heat": ("temp_", "tmax_", "heat_"),
          "humidity": ("rh_",), "enso": ("enso_",), "topography": ("topo_",), "population": ("log_pop", "pop_")}


def group_of(feature: str) -> str:
    return next(g for g, prefixes in GROUPS.items() if feature.startswith(prefixes))


def _get(url: str, params: dict) -> requests.Response:
    for _ in range(30):
        r = requests.get(url, params=params, timeout=300)
        if r.status_code == 429:  # Open-Meteo free tier: wait out the hourly limit
            print("  rate limited, waiting 5 min", flush=True)
            time.sleep(300)
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"gave up on {url}")


# ---------------------------------------------------------------- fetch

def region_points() -> pd.DataFrame:
    u = pd.read_csv(PROC / "units.csv")
    u["unit_id"] = "R_" + u.region_name.map(_region_code).str.replace(" ", "_")
    w = u.groupby("unit_id").apply(lambda g: pd.Series({
        "lat": np.average(g.center_lat, weights=g.population),
        "lon": np.average(g.center_lon, weights=g.population)}), include_groups=False).reset_index()
    w["start"] = "2015-07-01"
    qc = pd.DataFrame([{"unit_id": "QC", "lat": QC_POINT[0], "lon": QC_POINT[1], "start": "2009-07-01"}])
    return pd.concat([w, qc], ignore_index=True)


def fetch_region_weather() -> pd.DataFrame:
    """Daily ERA5 mean/max temperature and humidity per region point, cached one file per point."""
    cache = RAW / "weather_region"
    cache.mkdir(parents=True, exist_ok=True)
    frames = []
    for p in region_points().itertuples():
        path = cache / f"{p.unit_id}.json"
        if not path.exists():
            r = _get(fetch_weather.API, {"latitude": f"{p.lat:.4f}", "longitude": f"{p.lon:.4f}",
                                         "start_date": p.start, "end_date": "2025-12-31", "timezone": "Asia/Manila",
                                         "daily": "temperature_2m_mean,temperature_2m_max,relative_humidity_2m_mean"})
            path.write_text(r.text)
            print(f"  weather {p.unit_id}", flush=True)
        frames.append(fetch_weather.to_daily(p.unit_id, json.loads(path.read_text())))
    return pd.concat(frames, ignore_index=True)


def province_daily() -> pd.DataFrame:
    """The cached daily ERA5 the province model was built from (no new download)."""
    units = pd.read_csv(PROC / "units.csv")
    frames = []
    for i, start in enumerate(range(0, len(units), fetch_weather.BATCH)):
        chunk = units.iloc[start:start + fetch_weather.BATCH]
        for unit_id, payload in zip(chunk.unit_id, fetch_weather.fetch_batch(i, chunk)):
            frames.append(fetch_weather.to_daily(unit_id, payload))
    return pd.concat(frames, ignore_index=True)


def fetch_oni() -> pd.DataFrame:
    path = RAW / "oni.ascii.txt"
    if not path.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        path.write_text(_get("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", {}).text)
    oni = pd.read_csv(io.StringIO(path.read_text()), sep=r"\s+")
    centre = {s: i + 1 for i, s in enumerate(["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
                                               "JJA", "JAS", "ASO", "SON", "OND", "NDJ"])}
    oni["month"] = pd.to_datetime(dict(year=oni.YR, month=oni.SEAS.map(centre), day=1))
    return oni[["month", "ANOM"]].rename(columns={"ANOM": "oni"})


def fetch_elevation() -> pd.DataFrame:
    """Elevation at every barangay centroid, 100 points per request, cached."""
    path = RAW / "elevation_barangay.parquet"
    if path.exists():
        return pd.read_parquet(path)
    b = pd.read_excel(ROOT / "data" / "raw" / "phl_admin_boundaries.xlsx", sheet_name="phl_admin4",
                      usecols=["adm4_pcode", "adm2_pcode", "area_sqkm", "center_lat", "center_lon"])
    elev = []
    for i in range(0, len(b), 100):
        c = b.iloc[i:i + 100]
        r = _get("https://api.open-meteo.com/v1/elevation",
                 {"latitude": ",".join(f"{v:.5f}" for v in c.center_lat),
                  "longitude": ",".join(f"{v:.5f}" for v in c.center_lon)})
        elev += r.json()["elevation"]
        if i % 5000 == 0:
            print(f"  elevation {i:,}/{len(b):,}", flush=True)
    b["elevation_m"] = elev
    RAW.mkdir(parents=True, exist_ok=True)
    b.to_parquet(path, index=False)
    return b


# ---------------------------------------------------------------- features

def heat_index_c(t: pd.Series, rh: pd.Series) -> pd.Series:
    """NWS heat index (Rothfusz) from daily mean temperature (C) and humidity (%); plain temperature below 27 C."""
    f = t * 9 / 5 + 32
    hi = (-42.379 + 2.04901523 * f + 10.14333127 * rh - 0.22475541 * f * rh - 6.83783e-3 * f ** 2
          - 5.481717e-2 * rh ** 2 + 1.22874e-3 * f ** 2 * rh + 8.5282e-4 * f * rh ** 2 - 1.99e-6 * f ** 2 * rh ** 2)
    return ((hi - 32) * 5 / 9).where(t >= 27, t)


def weekly_heat(daily: pd.DataFrame) -> pd.DataFrame:
    d = daily.assign(band=daily.temp.between(26, 29), hot=daily.tmax >= 34, hi=heat_index_c(daily.temp, daily.rh))
    g = d.set_index("date").groupby("unit_id").resample("W-SUN")
    return pd.DataFrame({"band_days": g.band.sum(), "hot_days": g.hot.sum(), "hi": g.hi.mean(),
                         "temp_mean_x": g.temp.mean(), "temp_max_x": g.tmax.max(), "rh_mean_x": g.rh.mean(),
                         }).reset_index().rename(columns={"date": "week"})


def add_weather(df: pd.DataFrame, weekly: pd.DataFrame, with_lags: bool) -> pd.DataFrame:
    df = df.merge(weekly, on=["unit_id", "week"], how="left").sort_values(["unit_id", "week"])
    g = df.groupby("unit_id", group_keys=False)
    roll = lambda col, n, fn: g[col].transform(lambda s: getattr(s.rolling(n, min_periods=2), fn)())  # noqa: E731
    df["heat_band4"] = roll("band_days", 4, "sum")
    df["heat_band4_lag4"] = g.heat_band4.shift(4)
    df["heat_hot4"] = roll("hot_days", 4, "sum")
    df["heat_hi4"] = roll("hi", 4, "mean")
    if with_lags:  # Regions + QC: the same temperature and humidity inputs the province model has
        for k in (0, 2, 4, 6, 8):
            df[f"temp_lag{k}"] = g.temp_mean_x.shift(k)
            df[f"rh_lag{k}"] = g.rh_mean_x.shift(k)
        df["tmax_max4"] = roll("temp_max_x", 4, "max")
    return df.drop(columns=["band_days", "hot_days", "hi", "temp_mean_x", "temp_max_x", "rh_mean_x"])


def add_enso(df: pd.DataFrame, oni: pd.DataFrame) -> pd.DataFrame:
    month = df.week.dt.to_period("M").dt.to_timestamp()
    s = oni.set_index("month").oni
    df["enso_oni"] = (month - pd.DateOffset(months=2)).map(s).values
    df["enso_oni_lag3"] = (month - pd.DateOffset(months=5)).map(s).values
    return df


def province_static() -> pd.DataFrame:
    u = pd.read_csv(PROC / "units.csv")
    b = fetch_elevation()
    cot = u.loc[u.unit_name.str.fullmatch("Cotabato"), "unit_id"].iloc[0]
    # Maguindanao was split in 2022 (the data keep it whole); the Special Geographic Area left Cotabato in 2019.
    b["unit_id"] = b.adm2_pcode.replace({"PH19087": "MAG", "PH19088": "MAG", "PH19099": cot})
    b = b[b.unit_id.isin(u.unit_id)]
    topo = b.groupby("unit_id").apply(lambda g: pd.Series({
        "topo_elev_mean": np.average(g.elevation_m, weights=g.area_sqkm),
        "topo_low_share": np.average(g.elevation_m < 100, weights=g.area_sqkm)}), include_groups=False)
    u = u.set_index("unit_id").join(topo)
    u["pop_density_log"] = np.log(u.population / u.area_sqkm)
    return u[["topo_elev_mean", "topo_low_share", "pop_density_log"]].reset_index()


def build(panel: str) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_parquet(PROC / f"model_table_{panel}.parquet")
    base = feature_columns(df)
    oni = fetch_oni()
    if panel == "province":
        df = add_weather(df, weekly_heat(province_daily()), with_lags=False)
        df = df.merge(province_static(), on="unit_id", how="left")
    else:
        df = add_weather(df, weekly_heat(fetch_region_weather()), with_lags=True)
    df = add_enso(df, oni).sort_values(["unit_id", "week"]).reset_index(drop=True)
    new = [c for c in df.columns if c.startswith(("heat_", "enso_", "topo_", "pop_", "temp_lag", "rh_lag", "tmax_"))
           and c not in base]
    return df, base + new


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for panel in sys.argv[1:] or ["region_qc", "province"]:
        df, feats = build(panel)
        df.to_parquet(OUT / f"model_table_{panel}_plus.parquet", index=False)
        (OUT / f"features_{panel}_plus.json").write_text(json.dumps(feats))
        miss = df.loc[df.target_h4.notna() & df.y_lag0.notna(), feats].isna().mean()
        print(panel, df.shape, len(feats), "features; by group:",
              pd.Series([group_of(f) for f in feats]).value_counts().to_dict())
        print("  share missing (usable rows), new features:", miss[[f for f in feats if f in miss.index]].loc[
            lambda s: s.index.str.startswith(("heat_", "enso_", "topo_", "pop_", "temp_lag", "rh_lag", "tmax_"))].round(3).to_dict())
