"""Person B's question: is the wide 2023 range for Regions + QC caused by `y_lastyear` missing in the
calibration year?

The regions have no data for 2020-2021. In 2022, the calibration year of the 2023 test, `y_lastyear`
(cases 52 weeks earlier) is missing for 17 of the 18 areas. The model learned what a missing value means
from 2016, the regions' first year. The 2023 margin is 0.227 at 4 weeks against about 0.09 in 2024 and
2025, and 2023's range held 92% of weeks against an 80% target.

Three versions of the live backtest (LightGBM, live features, src/backtest.py's rule), every Regions + QC
test year, so 2019, 2024 and 2025 act as controls:
  live         as src/backtest.py; must reproduce reports/backtest_region_qc.csv
  fill_gap     a missing y_lastyear filled with the same week 3 years earlier (2022 <- 2019), the latest
               year before the gap; train, calibration and test all use the filled column
  no_lastyear  y_lastyear dropped from the features

Writes research/results/margin_check.csv: margin, range coverage and error per version, year and lead time.

Also, for the live version, how the calibration step misses on its held-out year (the year before each test
year): the median log error of the 50% forecast (negative = too low), and the share of weeks above the 90%
forecast and below the 10% forecast. Lopsided misses mean a shift in level; even misses mean a too-narrow
range. It also gives the margin again over only the weeks that have the 4- and 12-week averages, which
are missing in early 2022, after the gap. Writes research/results/margin_check_calibration_year.csv.
Usage: python research/models/margin_check.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from backtest import QUANTILES, TEST_YEARS, conformal_margin, fit_quantiles, predict_log  # noqa: E402
from features import HORIZONS, PROC, feature_columns  # noqa: E402

PANEL = "region_qc"
OUT = ROOT / "research" / "results" / "margin_check.csv"


def versions(df: pd.DataFrame) -> dict[str, tuple[pd.DataFrame, list[str]]]:
    feats = feature_columns(df)
    filled = df.copy()
    three_back = filled.groupby("unit_id").y.shift(156)
    filled["y_lastyear"] = filled.y_lastyear.fillna(three_back)
    return {"live": (df, feats),
            "fill_gap": (filled, feats),
            "no_lastyear": (df, [f for f in feats if f != "y_lastyear"])}


def backtest(df: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    rows = []
    for year in TEST_YEARS[PANEL]:
        start = pd.Timestamp(f"{year}-01-01")
        for h in HORIZONS:
            target = f"target_h{h}"
            target_week = df.week + pd.Timedelta(weeks=h)
            usable = df[target].notna() & df.y_lag0.notna()
            train = df[usable & (target_week < start)]
            test = df[usable & (target_week.dt.year == year)].copy()
            q = predict_log(fit_quantiles(train, feats, target), test[feats])
            margin = conformal_margin(train, feats, target, target_week, start)
            raw = np.expm1(q.clip(lower=0))
            q["q10"], q["q90"] = q.q10 - margin, q.q90 + margin
            test[list(QUANTILES)] = np.expm1(q.clip(lower=0))
            test["actual"] = np.expm1(test[target])
            test["seasonal_naive"] = np.expm1(test[f"seasonal_naive_h{h}"])
            keep = test.actual.notna() & test.seasonal_naive.notna() & test.cases.notna()  # the rows backtest.score uses
            g, r = test[keep], raw[keep]
            rows.append({"test_year": year, "horizon": h, "n": len(g), "margin": margin,
                         "mae": (g.q50 - g.actual).abs().mean(),
                         "coverage_raw": ((g.actual >= r.q10) & (g.actual <= r.q90)).mean(),
                         "coverage_10_90": ((g.actual >= g.q10) & (g.actual <= g.q90)).mean()})
    return pd.DataFrame(rows)


def calibration_year(df: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    """The split conformal_margin makes: fit on targets before the last training year, predict that year."""
    rows = []
    for year in TEST_YEARS[PANEL]:
        start = pd.Timestamp(f"{year}-01-01")
        cal_start = start - pd.Timedelta(weeks=52)
        for h in HORIZONS:
            target = f"target_h{h}"
            target_week = df.week + pd.Timedelta(weeks=h)
            usable = df[target].notna() & df.y_lag0.notna()
            fit = df[usable & (target_week < cal_start)]
            cal = df[usable & (target_week >= cal_start) & (target_week < start)]
            q = predict_log(fit_quantiles(fit, feats, target), cal[feats])
            y = cal[target]
            miss = np.maximum(q.q10 - y, y - q.q90)
            averages = cal[["y_mean4", "y_mean12"]].notna().all(axis=1)  # missing in the weeks after a gap
            rows.append({"test_year": year, "calibration_year": year - 1, "horizon": h, "n": len(cal),
                         "median_log_error": (q.q50 - y).median(),
                         "above_q90": (y > q.q90).mean(), "below_q10": (y < q.q10).mean(),
                         "margin": margin_of(miss), "n_averages_present": int(averages.sum()),
                         "margin_averages_present": margin_of(miss[averages])})
    return pd.DataFrame(rows)


def margin_of(miss: pd.Series) -> float:
    """The 80% conformal quantile, as in src/backtest.conformal_margin."""
    n = len(miss)
    return float(np.quantile(miss, min(1.0, np.ceil((n + 1) * 0.8) / n)))


if __name__ == "__main__":
    df = pd.read_parquet(PROC / f"model_table_{PANEL}.parquet")
    cal = calibration_year(df, feature_columns(df))
    cal.to_csv(OUT.with_name("margin_check_calibration_year.csv"), index=False)
    print(cal.round(3).to_string(index=False), flush=True)
    out = []
    for name, (table, feats) in versions(df).items():
        print(name, flush=True)
        out.append(backtest(table, feats).assign(version=name))
    out = pd.concat(out, ignore_index=True)
    rep = pd.read_csv(ROOT / "reports" / f"backtest_{PANEL}.csv").set_index(["test_year", "horizon"])
    live = out[out.version == "live"].set_index(["test_year", "horizon"])
    print("live vs reports, max diff: mae", (live.mae - rep.mae_epilag).abs().max(),
          "coverage", (live.coverage_10_90 - rep.coverage_10_90).abs().max())
    out = out[["version", "test_year", "horizon", "n", "margin", "mae", "coverage_raw", "coverage_10_90"]]
    out.to_csv(OUT, index=False)
    for col in ("margin", "coverage_10_90", "mae"):
        print(col); print(out.pivot_table(index="version", columns=["test_year", "horizon"], values=col).round(3).to_string())
