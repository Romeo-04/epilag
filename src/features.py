"""Model features for any unit-week panel.

Input panel columns: unit_id, week (Sunday), cases, population, and any of the WEATHER columns.
One row per (unit, week t): features use data up to t only; targets are log1p(cases) at t+h.
So a model trained on these rows can be run on the latest week to forecast h weeks ahead.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"

HORIZONS = [2, 4, 6, 8]
WEATHER = ["rain_mm", "rain_heavy_days", "temp_mean", "temp_max", "rh_mean"]


def complete_weeks(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex each unit to a gap-free weekly calendar, so shift(k) always means k weeks."""
    weeks = pd.date_range(df.week.min(), df.week.max(), freq="W-SUN")
    idx = pd.MultiIndex.from_product([df.unit_id.unique(), weeks], names=["unit_id", "week"])
    static = df.drop_duplicates("unit_id").set_index("unit_id").drop(columns=["week"], errors="ignore")
    static = static[[c for c in static.columns if c not in ["cases", "deaths", *WEATHER]]]
    full = df.set_index(["unit_id", "week"]).reindex(idx).reset_index()
    full = full.drop(columns=static.columns, errors="ignore").merge(static, left_on="unit_id", right_index=True)
    return full.sort_values(["unit_id", "week"]).reset_index(drop=True)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = complete_weeks(df)
    g = df.groupby("unit_id", group_keys=False)
    roll = lambda col, n, fn="mean", mp=None: g[col].transform(lambda s: getattr(s.rolling(n, min_periods=mp or n), fn)())
    df["y"] = np.log1p(df.cases)

    # Recent cases (known at t).
    for k in range(4):
        df[f"y_lag{k}"] = g.y.shift(k)
    df["y_mean4"] = roll("y", 4, mp=2)
    df["y_mean12"] = roll("y", 12, mp=6)
    df["y_trend"] = df.y_lag0 - df.y_lag3
    df["y_lastyear"] = g.y.shift(52)

    # Weather: this week and the past 11 weeks, plus rolling totals (only for columns present).
    if "rain_mm" in df:
        for k in range(12):
            df[f"rain_lag{k}"] = g.rain_mm.shift(k)
        for n in (4, 8, 12):
            df[f"rain_sum{n}"] = roll("rain_mm", n, "sum")
    if "rain_heavy_days" in df:
        df["heavy_days8"] = roll("rain_heavy_days", 8, "sum")
    for col, short in (("rh_mean", "rh"), ("temp_mean", "temp")):
        if col in df:
            for k in (0, 2, 4, 6, 8):
                df[f"{short}_lag{k}"] = g[col].shift(k)
    if "temp_max" in df:
        df["tmax_max4"] = roll("temp_max", 4, "max")

    # Season and size.
    woy = df.week.dt.isocalendar().week.astype(int)
    df["woy_sin"], df["woy_cos"] = np.sin(2 * np.pi * woy / 52.18), np.cos(2 * np.pi * woy / 52.18)
    df["log_pop"] = np.log(df.population)

    for h in HORIZONS:
        df[f"target_h{h}"] = g.y.shift(-h)
        df[f"seasonal_naive_h{h}"] = g.y.shift(52 - h)  # cases in the target week, last year
    return df


def feature_columns(df: pd.DataFrame) -> list[str]:
    skip = {"y", "cases", "deaths", "population", *WEATHER}
    prefixes = ("y_", "rain_", "rh_", "temp_", "heavy_", "tmax_", "woy_", "log_pop")
    return [c for c in df.columns if c.startswith(prefixes) and c not in skip
            and not c.startswith(("target_", "seasonal_naive_"))]


# ---------------------------------------------------------------- panels

def province_panel() -> pd.DataFrame:
    d = pd.read_parquet(PROC / "dengue_unit_week.parquet")
    w = pd.read_parquet(PROC / "weather_unit_week.parquet")
    return d.merge(w, on=["unit_id", "week"], how="left")


def epiweek_to_sunday(year: pd.Series, week: pd.Series) -> pd.Series:
    # Epi week w of year y, labelled by its last day (Sunday), matching the HDX weeks.
    jan4 = pd.to_datetime(year.astype(str) + "-01-04")
    week1_sunday = jan4 + pd.to_timedelta(6 - jan4.dt.dayofweek, unit="D")
    return week1_sunday + pd.to_timedelta((week - 1) * 7, unit="D")


def region_qc_panel() -> pd.DataFrame:
    """17 regions (2016-2019, 2022-2025) + Quezon City (2010-2025), weekly cases + rainfall."""
    xlsx = ROOT / "data" / "raw" / "upri_noah" / "Dengue-Rainfall_Dataset.xlsx"
    units = pd.read_csv(PROC / "units.csv")
    region_pop = units.assign(r=units.region_name.map(_region_code)).groupby("r").population.sum()

    r = pd.read_excel(xlsx, sheet_name="Regional Data")
    r = pd.DataFrame({"unit_id": "R_" + r.REGION.str.replace(" ", "_"), "unit_name": r.REGION,
                      "week": epiweek_to_sunday(r.YR, r.WN), "cases": r.DC_HDX, "rain_mm": r.RF_HDX,
                      "population": r.REGION.map(region_pop)})
    q = pd.read_excel(xlsx, sheet_name="QC Data")
    q = pd.DataFrame({"unit_id": "QC", "unit_name": "Quezon City", "week": epiweek_to_sunday(q.YR, q.WN),
                      "cases": q.DC_QC, "rain_mm": q.RF_NASA, "population": 2_960_048})  # PSA 2020 CPH
    out = pd.concat([r, q], ignore_index=True)
    if out.population.isna().any():
        raise ValueError(f"no population for: {out[out.population.isna()].unit_name.unique()}")
    return out


def _region_code(name: str) -> str:
    """Map COD-AB region names to the region labels used in the UPRI-NOAH file."""
    special = {"National Capital Region": "NCR", "Cordillera": "CAR", "Mimaropa": "MIMAROPA",
               "Bangsamoro": "BARMM", "Caraga": "REGION XIII"}
    for key, code in special.items():
        if key.lower() in name.lower():
            return code
    return "REGION " + name.split("(")[0].replace("Region", "").strip()


PANELS = {"province": province_panel, "region_qc": region_qc_panel}


def build(panel: str) -> pd.DataFrame:
    df = add_features(PANELS[panel]())
    df.to_parquet(PROC / f"model_table_{panel}.parquet", index=False)
    return df


if __name__ == "__main__":
    import sys
    for name in sys.argv[1:] or PANELS:
        t = build(name)
        print(name, t.shape, t.week.min().date(), t.week.max().date(), len(feature_columns(t)), "features")
