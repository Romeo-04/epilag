"""Small extracts of data/processed/ (gitignored) that Person B's analysis needs, so no one has to copy that folder.

research/results/extracts/
  backtest_predictions.csv.gz  Every test week of the live backtest, with and without weather (`weather` column):
                               actual, calibrated q10/q50/q90, the calibration margin, the raw (uncalibrated) q10/q90,
                               and both baselines. q10_raw is blank where the calibrated q10 was clipped at 0, so the
                               raw value can't be recovered.
  calibration.csv              Per panel, test year and lead time: the margin, coverage before calibration (a blank
                               raw q10 counted as missed / as covered) and after, on the weeks src/backtest.py scores
                               (both baselines present). Calibrated coverage matches reports/backtest_<panel>.csv.
  weekly_series.csv.gz         Every area-week in the model tables: cases, population, rain, and the weekly mean
                               temperature and humidity where the panel has them (Regions + QC: research weather).
  rain_by_year.csv             Per area and year: rain total and rainy-season (June-November) total, the weeks with
                               data, and each as a % difference from the area's mean over its other complete years.

Usage: python research/models/export_extracts.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extra_features import OUT as RESEARCH_PROC, PROC  # noqa: E402
from harness import RESULTS  # noqa: E402

DEST = RESULTS / "extracts"
PANELS = ["province", "region_qc"]


def predictions() -> pd.DataFrame:
    frames = []
    for panel in PANELS:
        for weather, suffix in ((True, ""), (False, "_noweather")):
            b = pd.read_parquet(PROC / f"backtest_{panel}{suffix}.parquet")
            b["q90_raw"] = np.expm1(np.log1p(b.q90) - b.margin)
            b["q10_raw"] = np.where(b.q10 > 0, np.expm1(np.log1p(b.q10) + b.margin), np.nan)
            frames.append(b.assign(panel=panel, weather=weather))
    cols = ["panel", "weather", "unit_id", "unit_name", "week", "target_week", "horizon", "test_year", "actual",
            "q10", "q50", "q90", "margin", "q10_raw", "q90_raw", "persistence", "seasonal_naive"]
    return pd.concat(frames, ignore_index=True)[cols]


def calibration(p: pd.DataFrame) -> pd.DataFrame:
    p = p[p.weather].dropna(subset=["actual", "seasonal_naive", "persistence"])  # the rows src/backtest.py scores
    rows = []
    for (panel, y, h), g in p.groupby(["panel", "test_year", "horizon"]):
        up = g.actual <= g.q90_raw
        unknown = g.q10_raw.isna()
        rows.append({"panel": panel, "test_year": y, "horizon": h, "margin": g.margin.iloc[0],
                     "coverage_raw_low": (up & ~unknown & (g.actual >= g.q10_raw)).mean(),
                     "coverage_raw_high": (up & (unknown | (g.actual >= g.q10_raw))).mean(),
                     "coverage_calibrated": ((g.actual >= g.q10) & (g.actual <= g.q90)).mean()})
    return pd.DataFrame(rows)


def series() -> pd.DataFrame:
    frames = []
    for panel in PANELS:
        t = pd.read_parquet(RESEARCH_PROC / f"model_table_{panel}_plus.parquet")
        temp = t.temp_mean if "temp_mean" in t else t.temp_lag0
        rh = t.rh_mean if "rh_mean" in t else t.rh_lag0
        frames.append(pd.DataFrame({"panel": panel, "unit_id": t.unit_id, "unit_name": t.unit_name, "week": t.week,
                                    "cases": t.cases, "population": t.population, "rain_mm": t.rain_mm,
                                    "temp_mean": temp, "rh_mean": rh}))
    return pd.concat(frames, ignore_index=True)


def rain_by_year(s: pd.DataFrame) -> pd.DataFrame:
    s = s.assign(year=s.week.dt.year, wet=s.week.dt.month.between(6, 11))
    g = s.groupby(["panel", "unit_id", "unit_name", "year"])
    y = pd.DataFrame({"rain_total": g.rain_mm.sum(min_count=1), "weeks_with_rain": g.rain_mm.count(),
                      "rain_wet_season": s[s.wet].groupby(["panel", "unit_id", "unit_name", "year"]).rain_mm.sum(min_count=1),
                      "wet_weeks_with_rain": s[s.wet].groupby(["panel", "unit_id", "unit_name", "year"]).rain_mm.count(),
                      }).reset_index()
    full = (y.weeks_with_rain >= 50) & (y.wet_weeks_with_rain >= 25)
    for col in ("rain_total", "rain_wet_season"):
        tot = y[full].groupby("unit_id")[col].agg(["sum", "count"])
        others = (y.unit_id.map(tot["sum"]) - y[col].where(full, 0)) / (y.unit_id.map(tot["count"]) - full.astype(int))
        y[f"{col}_vs_other_years_pct"] = ((y[col] / others - 1) * 100).where(full)
    return y


if __name__ == "__main__":
    DEST.mkdir(parents=True, exist_ok=True)
    p = predictions()
    p.to_csv(DEST / "backtest_predictions.csv.gz", index=False, float_format="%.4f")
    c = calibration(p)
    c.to_csv(DEST / "calibration.csv", index=False, float_format="%.4f")
    for panel in PANELS:  # check against the committed reports
        r = pd.read_csv(Path(__file__).resolve().parents[2] / "reports" / f"backtest_{panel}.csv")
        m = c[c.panel == panel].merge(r, on=["test_year", "horizon"])
        print(panel, "calibrated coverage vs reports, max diff:", (m.coverage_calibrated - m.coverage_10_90).abs().max())
    s = series()
    s.to_csv(DEST / "weekly_series.csv.gz", index=False, float_format="%.4f")
    rain_by_year(s).to_csv(DEST / "rain_by_year.csv", index=False, float_format="%.2f")
    for f in sorted(DEST.iterdir()):
        print(f"{f.name}: {f.stat().st_size / 1e3:,.0f} kB")
