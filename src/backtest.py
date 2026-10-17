"""Out-of-sample test: for each test year Y, train only on targets before Y, forecast every week of Y.

Models per horizon h (weeks ahead):
  - persistence:     cases(t+h) = cases(t)
  - seasonal naive:  cases(t+h) = cases in the same week last year
  - EpiLag (LightGBM, quantile loss): median plus a 10-90% interval

Usage: python src/backtest.py province|region_qc
Outputs: data/processed/backtest_<panel>.parquet, reports/backtest_<panel>.csv
"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from features import HORIZONS, PROC, feature_columns

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TEST_YEARS = {"province": [2019, 2020], "region_qc": [2019, 2023, 2024, 2025]}
QUANTILES = {"q10": 0.1, "q50": 0.5, "q90": 0.9}
PARAMS = dict(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=30,
              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1)


def fit_quantiles(train: pd.DataFrame, features: list[str], target: str) -> dict:
    models = {}
    for name, alpha in QUANTILES.items():
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, **PARAMS)
        m.fit(train[features], train[target])
        models[name] = m
    return models


def predict_log(models: dict, X: pd.DataFrame) -> pd.DataFrame:
    q = pd.DataFrame({name: m.predict(X) for name, m in models.items()}, index=X.index)
    q[:] = np.sort(q.values, axis=1)  # quantiles are fitted separately; keep q10 <= q50 <= q90
    return q


def conformal_margin(train: pd.DataFrame, features: list[str], target: str, target_week: pd.Series,
                     start: pd.Timestamp) -> float:
    """Conformalized quantile regression: fit on all but the last training year, measure how far
    the 10-90% band misses on that held-out year, and return the widening (in log space) that
    makes it cover 80%. Raw quantile models are usually overconfident on new years."""
    cal_start = start - pd.Timedelta(weeks=52)
    fit, cal = train[target_week[train.index] < cal_start], train[target_week[train.index] >= cal_start]
    if len(cal) < 50 or len(fit) < 200:
        return 0.0
    q = predict_log(fit_quantiles(fit, features, target), cal[features])
    miss = np.maximum(q.q10 - cal[target], cal[target] - q.q90)
    n = len(miss)
    return float(np.quantile(miss, min(1.0, np.ceil((n + 1) * 0.8) / n)))


WEATHER_PREFIXES = ("rain_", "rh_", "temp_", "heavy_", "tmax_")


def run(panel: str, no_weather: bool = False) -> pd.DataFrame:
    df = pd.read_parquet(PROC / f"model_table_{panel}.parquet")
    features = feature_columns(df)
    if no_weather:  # ablation: does weather add anything beyond case history and season?
        features = [f for f in features if not f.startswith(WEATHER_PREFIXES)]
    suffix = "_noweather" if no_weather else ""
    rows = []
    for year in TEST_YEARS[panel]:
        start = pd.Timestamp(f"{year}-01-01")
        for h in HORIZONS:
            target = f"target_h{h}"
            target_week = df.week + pd.Timedelta(weeks=h)
            usable = df[target].notna() & df.y_lag0.notna()
            train = df[usable & (target_week < start)]
            test = df[usable & (target_week.dt.year == year)].copy()
            q = predict_log(fit_quantiles(train, features, target), test[features])
            margin = conformal_margin(train, features, target, target_week, start)
            q["q10"], q["q90"] = q.q10 - margin, q.q90 + margin
            test[list(QUANTILES)] = np.expm1(q.clip(lower=0))
            test["margin"] = margin
            test["horizon"], test["test_year"] = h, year
            test["target_week"] = test.week + pd.Timedelta(weeks=h)
            test["actual"] = np.expm1(test[target])
            test["persistence"] = test.cases
            test["seasonal_naive"] = np.expm1(test[f"seasonal_naive_h{h}"])
            rows.append(test[["unit_id", "unit_name", "week", "target_week", "horizon", "test_year",
                              "actual", *QUANTILES, "margin", "persistence", "seasonal_naive"]])
            print(f"{year} h={h}: train {len(train):,} rows, test {len(test):,}, margin {margin:.2f}", flush=True)
    preds = pd.concat(rows, ignore_index=True)
    preds.to_parquet(PROC / f"backtest_{panel}{suffix}.parquet", index=False)
    return preds


def score(preds: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    def one(g: pd.DataFrame) -> pd.Series:
        g = g.dropna(subset=["actual", "seasonal_naive", "persistence"])
        mae = {m: (g[m] - g.actual).abs().mean() for m in ("q50", "seasonal_naive", "persistence")}
        return pd.Series({
            "n": len(g),
            "mae_epilag": mae["q50"],
            "mae_seasonal_naive": mae["seasonal_naive"],
            "mae_persistence": mae["persistence"],
            "skill_vs_seasonal": 1 - mae["q50"] / mae["seasonal_naive"],
            "skill_vs_persistence": 1 - mae["q50"] / mae["persistence"],
            "coverage_10_90": ((g.actual >= g.q10) & (g.actual <= g.q90)).mean(),
        })
    return preds.groupby(by).apply(one, include_groups=False).reset_index()


if __name__ == "__main__":
    panel, no_weather = sys.argv[1], "--no-weather" in sys.argv
    REPORTS.mkdir(exist_ok=True)
    preds = run(panel, no_weather)
    scores = score(preds, ["test_year", "horizon"])
    scores.to_csv(REPORTS / f"backtest_{panel}{'_noweather' if no_weather else ''}.csv", index=False)
    print(scores.round(3).to_string(index=False))
    if "QC" in set(preds.unit_id):
        print("\nQuezon City only:")
        print(score(preds[preds.unit_id == "QC"], ["test_year", "horizon"]).round(3).to_string(index=False))
