"""The same test for every model (research only; the live model stays in src/).

For each test year Y and horizon h: train on rows whose target week falls before Y, forecast every
week of Y, widen the 10-90% range by a conformal margin measured on the last training year (the rule
src/backtest.py uses), then score error, range coverage and the two alert rules.

A model is predict(train, test, ctx) -> DataFrame[q10, q50, q90] of log1p(cases), indexed like test.

Usage: python research/models/harness.py region_qc lightgbm negbin random_forest sarimax
Writes data/processed/research/<panel>_<model>.parquet and research/results/model_comparison.csv
"""
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from alerts import evaluate as alert_scores  # noqa: E402
from backtest import QUANTILES, TEST_YEARS  # noqa: E402
from features import HORIZONS, PROC, feature_columns  # noqa: E402

OUT = PROC / "research"
RESULTS = ROOT / "research" / "results"
BASELINES = ("persistence", "seasonal_naive")


@dataclass
class Ctx:
    panel: str
    features: list[str]
    target: str
    h: int
    table: pd.DataFrame  # the whole model table, for models that need each area's series


def _predict(predict, train, test, ctx) -> pd.DataFrame:
    q = predict(train, test, ctx)[list(QUANTILES)]
    q[:] = np.sort(q.values, axis=1)  # keep q10 <= q50 <= q90
    return q


def conformal_margin(predict, train: pd.DataFrame, target_week: pd.Series, start: pd.Timestamp, ctx) -> float:
    """Same rule as src/backtest.conformal_margin, for any model."""
    tw = target_week[train.index]
    fit, cal = train[tw < start - pd.Timedelta(weeks=52)], train[tw >= start - pd.Timedelta(weeks=52)]
    if len(cal) < 50 or len(fit) < 200:
        return 0.0
    q = _predict(predict, fit, cal, ctx)
    miss = np.maximum(q.q10 - cal[ctx.target], cal[ctx.target] - q.q90)
    n = len(miss)
    return float(np.quantile(miss, min(1.0, np.ceil((n + 1) * 0.8) / n)))


def run(panel: str, predict, features: list[str] | None = None, table: pd.DataFrame | None = None) -> pd.DataFrame:
    df = pd.read_parquet(PROC / f"model_table_{panel}.parquet") if table is None else table
    features = features or feature_columns(df)
    rows = []
    for year in TEST_YEARS[panel]:
        start = pd.Timestamp(f"{year}-01-01")
        for h in HORIZONS:
            t0 = time.time()
            ctx = Ctx(panel, features, f"target_h{h}", h, df)
            target_week = df.week + pd.Timedelta(weeks=h)
            usable = df[ctx.target].notna() & df.y_lag0.notna()
            train = df[usable & (target_week < start)]
            test = df[usable & (target_week.dt.year == year)].copy()
            q = _predict(predict, train, test, ctx)
            margin = conformal_margin(predict, train, target_week, start, ctx)
            test["q10_raw"], test["q90_raw"] = np.expm1(q.q10.clip(lower=0)), np.expm1(q.q90.clip(lower=0))
            q["q10"], q["q90"] = q.q10 - margin, q.q90 + margin
            test[list(QUANTILES)] = np.expm1(q.clip(lower=0))
            test["margin"], test["horizon"], test["test_year"] = margin, h, year
            test["target_week"] = test.week + pd.Timedelta(weeks=h)
            test["actual"] = np.expm1(test[ctx.target])
            test["persistence"] = test.cases
            test["seasonal_naive"] = np.expm1(test[f"seasonal_naive_h{h}"])
            rows.append(test[["unit_id", "unit_name", "week", "target_week", "horizon", "test_year", "actual",
                              *QUANTILES, "q10_raw", "q90_raw", "margin", "persistence", "seasonal_naive"]])
            print(f"  {year} h={h}: train {len(train):,}, test {len(test):,}, margin {margin:.3f}, "
                  f"{time.time() - t0:.0f}s", flush=True)
    return pd.concat(rows, ignore_index=True)


def baseline_preds(preds: pd.DataFrame, name: str) -> pd.DataFrame:
    """A baseline as a forecast with no range: its single number is the middle."""
    b = preds.copy()
    b["q50"] = b[name]
    b[["q10", "q90", "q10_raw", "q90_raw"]] = np.nan
    return b


def score(preds: pd.DataFrame, panel: str, model: str) -> pd.DataFrame:
    rows = []
    for (year, h), g in preds.groupby(["test_year", "horizon"]):
        g = g.dropna(subset=["actual", *BASELINES])  # the same weeks for every model
        err = lambda col: (g[col] - g.actual).abs().mean()  # noqa: E731
        inside = lambda lo, hi: ((g.actual >= g[lo]) & (g.actual <= g[hi])).mean()  # noqa: E731
        rows.append({"panel": panel, "test_year": year, "horizon": h, "model": model, "n": len(g),
                     "mae": err("q50"), "rel_mae_vs_persistence": err("q50") / err("persistence"),
                     "rel_mae_vs_seasonal": err("q50") / err("seasonal_naive"),
                     "coverage_10_90": inside("q10", "q90"), "coverage_raw": inside("q10_raw", "q90_raw")})
    s = pd.DataFrame(rows)
    a = alert_scores(panel, preds).set_index(["test_year", "horizon", "rule"])
    for rule, name in (("warn_upper", "watch"), ("warn_median", "warning")):
        r = a.xs(rule, level="rule")
        s = s.join(r[["onsets_warned", "false_alarm_share"]].rename(
            columns={"onsets_warned": f"caught_{name}", "false_alarm_share": f"false_share_{name}"}),
            on=["test_year", "horizon"])
    s = s.join(a.xs("warn_median", level="rule")[["onsets"]], on=["test_year", "horizon"])
    if model in BASELINES:
        s[["coverage_10_90", "coverage_raw", "caught_watch", "false_share_watch"]] = np.nan
    cols = ["panel", "test_year", "horizon", "model", "n", "mae", "rel_mae_vs_persistence", "rel_mae_vs_seasonal",
            "coverage_10_90", "coverage_raw", "onsets", "caught_watch", "false_share_watch",
            "caught_warning", "false_share_warning"]
    return s[cols]


def upsert(path: Path, new: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Replace the rows of `new`'s keys in a results CSV, keep the rest."""
    if path.exists():
        old = pd.read_csv(path)
        drop = old.set_index(keys).index.isin(new.set_index(keys).index)
        new = pd.concat([old[~drop], new], ignore_index=True)
    new = new.sort_values(keys).reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False)
    return new


if __name__ == "__main__":
    from models import MODELS

    panel, names = sys.argv[1], sys.argv[2:] or list(MODELS)
    OUT.mkdir(parents=True, exist_ok=True)
    scores = []
    for name in names:
        print(f"{panel} / {name}", flush=True)
        preds = run(panel, MODELS[name])
        preds.to_parquet(OUT / f"{panel}_{name}.parquet", index=False)
        scores.append(score(preds, panel, name))
    for b in BASELINES:
        scores.append(score(baseline_preds(preds, b), panel, b))
    table = upsert(RESULTS / "model_comparison.csv", pd.concat(scores), ["panel", "model", "test_year", "horizon"])
    show = table[(table.panel == panel) & (table.horizon == 4)]
    print(show[["test_year", "model", "mae", "coverage_10_90", "caught_watch", "onsets"]].round(3).to_string(index=False))
