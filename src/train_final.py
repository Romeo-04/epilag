"""Train final models on all data, forecast from the latest week, assign alert levels, explain.

For each horizon h: quantile LightGBM (q10/q50/q90) on every usable row, with a conformal margin
from the last year (same method as the backtest). Forecasts are made from each unit's latest week.

Alert levels for a forecast week (thresholds from all past years, same weeks +-2):
  outbreak warning : median forecast above the epidemic threshold (mean + 2 SD)
  watch            : upper end (q90) above the epidemic threshold
  above usual      : median forecast above the usual level (mean)
  normal           : otherwise

Usage: python src/train_final.py province|region_qc
Outputs (small, committed for the app): app/data/<panel>_forecast.parquet,
  app/data/<panel>_drivers.parquet, app/data/<panel>_thresholds.parquet, reports/shap_<panel>.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shap

from alerts import thresholds
from backtest import conformal_margin, fit_quantiles, predict_log
from features import HORIZONS, PROC, feature_columns

ROOT = Path(__file__).resolve().parents[1]
APP_DATA, REPORTS = ROOT / "app" / "data", ROOT / "reports"
LEVELS = ["normal", "above usual", "watch", "outbreak warning"]


def feature_group(name: str) -> str:
    if name.startswith("rain_lag"):
        return f"rain {name.removeprefix('rain_lag')} wk ago"
    for prefix, label in (("y_", "recent cases"), ("rain_sum", "rain totals"), ("heavy_", "heavy rain days"),
                          ("rh_", "humidity"), ("temp_", "temperature"), ("tmax_", "temperature"),
                          ("woy_", "season"), ("log_pop", "population")):
        if name.startswith(prefix):
            return label
    return name


def level(row: pd.Series) -> str:
    if row.q50 > row.epidemic:
        return LEVELS[3]
    if row.q90 > row.epidemic:
        return LEVELS[2]
    if row.q50 > row.alert:
        return LEVELS[1]
    return LEVELS[0]


def woy(s: pd.Series) -> pd.Series:
    return s.dt.isocalendar().week.astype(int).clip(upper=52)


def run(panel: str) -> None:
    df = pd.read_parquet(PROC / f"model_table_{panel}.parquet")
    features = feature_columns(df)
    latest = df[df.y_lag0.notna()].groupby("unit_id").week.max().rename("latest").reset_index()
    origin = df.merge(latest, on="unit_id")
    origin = origin[origin.week == origin.latest]

    thr = thresholds(df[["unit_id", "week", "cases"]])
    forecasts, drivers, shap_rows = [], [], []
    for h in HORIZONS:
        target = f"target_h{h}"
        train = df[df[target].notna() & df.y_lag0.notna()]
        target_week = df.week + pd.Timedelta(weeks=h)
        end = target_week[train.index].max() + pd.Timedelta(weeks=1)
        models = fit_quantiles(train, features, target)
        margin = conformal_margin(train, features, target, target_week, end)

        q = predict_log(models, origin[features])
        f = origin[["unit_id", "unit_name", "week", "population"]].copy()
        f["horizon"], f["target_week"] = h, f.week + pd.Timedelta(weeks=h)
        f["q10"] = np.expm1((q.q10 - margin).clip(lower=0))
        f["q50"] = np.expm1(q.q50.clip(lower=0))
        f["q90"] = np.expm1(q.q90 + margin)
        forecasts.append(f)

        # Why: SHAP on the median model, at the latest week (per unit) and over all rows (global).
        explainer = shap.TreeExplainer(models["q50"].booster_)
        sv = pd.DataFrame(explainer.shap_values(origin[features]), columns=features, index=origin.index)
        grouped = sv.T.groupby(feature_group).sum().T
        for unit_id, row in zip(origin.unit_id, grouped.itertuples(index=False)):
            for g, v in zip(grouped.columns, row):
                drivers.append({"unit_id": unit_id, "horizon": h, "driver": g, "shap": v})
        sample = train.sample(min(3000, len(train)), random_state=0)
        sv_all = pd.DataFrame(explainer.shap_values(sample[features]), columns=features)
        imp = sv_all.abs().mean()
        shap_rows.append(pd.DataFrame({"horizon": h, "feature": imp.index, "mean_abs_shap": imp.values}))
        print(f"h={h}: trained on {len(train):,} rows, margin {margin:.2f}", flush=True)

    fc = pd.concat(forecasts, ignore_index=True)
    fc["woy"] = woy(fc.target_week)
    fc = fc.merge(thr, on=["unit_id", "woy"], how="left")
    fc["level"] = fc.apply(level, axis=1)
    fc["q50_per100k"] = fc.q50 / fc.population * 1e5

    APP_DATA.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    fc.drop(columns=["woy", "count"]).to_parquet(APP_DATA / f"{panel}_forecast.parquet", index=False)
    pd.DataFrame(drivers).to_parquet(APP_DATA / f"{panel}_drivers.parquet", index=False)
    thr.to_parquet(APP_DATA / f"{panel}_thresholds.parquet", index=False)
    shap_all = pd.concat(shap_rows)
    shap_all["group"] = shap_all.feature.map(feature_group)
    shap_all.to_csv(REPORTS / f"shap_{panel}.csv", index=False)

    print(fc.groupby(["horizon", "level"]).size().unstack(fill_value=0).to_string())
    top = shap_all[shap_all.horizon == 4].groupby("group").mean_abs_shap.sum().sort_values(ascending=False)
    print("\nWhat drives the 4-week forecast (mean |SHAP|, log cases):")
    print(top.head(12).round(3).to_string())


if __name__ == "__main__":
    run(sys.argv[1])
