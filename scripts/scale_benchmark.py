"""How long does a full weekly retrain take, and how does it grow with the number of areas?

Runs the production training code (src/features.add_features, src/backtest.fit_quantiles and
conformal_margin: 3 quantile models with conformal calibration for each of 4 horizons) on the real weekly
case histories in app/data, then on the same histories copied out to about 1,600 areas, the number of
Philippine cities and municipalities. Weather columns are random numbers of the right shape: the timing
depends on rows and columns, not on the values. The raw weather is not in the repository.

    python scripts/scale_benchmark.py            # prints a table, writes reports/scale_benchmark.csv
"""
from __future__ import annotations

import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from backtest import conformal_margin, fit_quantiles  # noqa: E402
from features import HORIZONS, add_features, feature_columns  # noqa: E402

RNG = np.random.default_rng(7)
SIZES = [86, 400, 1600]  # provinces today; a mid step; about every city and municipality


def panel(n_units: int) -> pd.DataFrame:
    """Real province case histories, copied (with a little noise) until there are n_units areas."""
    base = pd.read_parquet(ROOT / "app/data/province_history.parquet")[["unit_id", "week", "cases"]]
    base["week"] = pd.to_datetime(base.week)
    ids = base.unit_id.unique()
    parts = []
    for i in range(n_units):
        src = base[base.unit_id == ids[i % len(ids)]].copy()
        src["unit_id"] = f"u{i:05d}"
        if i >= len(ids):
            src["cases"] = np.maximum(0, np.round(src.cases * RNG.uniform(0.3, 1.5)))
        parts.append(src)
    df = pd.concat(parts, ignore_index=True)
    n = len(df)
    df["population"] = df.groupby("unit_id").unit_id.transform(lambda s: RNG.integers(20_000, 3_000_000))
    df["rain_mm"] = RNG.gamma(2, 25, n)
    df["rain_heavy_days"] = RNG.integers(0, 4, n)
    df["temp_mean"] = RNG.normal(28, 1.5, n)
    df["temp_max"] = df.temp_mean + RNG.uniform(2, 6, n)
    df["rh_mean"] = RNG.uniform(65, 90, n)
    return df


def retrain(df: pd.DataFrame) -> dict:
    t0 = time.perf_counter()
    feats = add_features(df)
    t1 = time.perf_counter()
    cols = feature_columns(feats)
    end = feats.week.max() - pd.Timedelta(weeks=8)
    rows = 0
    for h in HORIZONS:
        target = f"target_h{h}"
        target_week = feats.week + pd.Timedelta(weeks=h)
        train = feats[(target_week <= end) & feats[target].notna() & feats.y_lastyear.notna()]
        fit_quantiles(train, cols, target)
        conformal_margin(train, cols, target, target_week, end)
        rows = max(rows, len(train))
    t2 = time.perf_counter()
    return {"features_s": t1 - t0, "train_s": t2 - t1, "total_s": t2 - t0, "train_rows": rows, "n_features": len(cols)}


def main() -> None:
    out = []
    for n in SIZES:
        r = {"areas": n, **retrain(panel(n))}
        out.append(r)
        print(f"{n:>5} areas  {r['train_rows']:>8,} rows x {r['n_features']} features  "
              f"features {r['features_s']:6.1f}s  train {r['train_s']:6.1f}s  total {r['total_s'] / 60:5.1f} min", flush=True)
    res = pd.DataFrame(out).round(1)
    res["machine"] = f"{platform.machine()} {platform.system()}, {os.cpu_count()} CPU threads, no GPU"
    res.to_csv(ROOT / "reports/scale_benchmark.csv", index=False)
    print("wrote reports/scale_benchmark.csv")


if __name__ == "__main__":
    main()
