"""Exploratory: does an equal average of the methods' middle forecasts beat LightGBM alone?

Uses the saved harness forecasts (data/processed/research/<panel>_<model>.parquet), so nothing is refit
and no weight is tuned on the test years. Scores the middle forecast only; the blend's 10-90% range and
alerts are not calibrated here. Writes research/results/blend_check.csv.

Usage: python research/models/blend.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import OUT, RESULTS  # noqa: E402

MODELS = ["lightgbm", "negbin", "random_forest", "sarimax"]
KEY = ["unit_id", "target_week", "horizon", "test_year"]
BLENDS = {"lightgbm": ["lightgbm"], "negbin": ["negbin"], "lightgbm+negbin": ["lightgbm", "negbin"], "all_four": MODELS}

rows = []
for panel in ["province", "region_qc"]:
    d = None
    for m in MODELS:
        p = pd.read_parquet(OUT / f"{panel}_{m}.parquet")
        keep = KEY + (["actual", "persistence", "seasonal_naive"] if d is None else []) + ["q50"]
        p = p[keep].rename(columns={"q50": m})
        d = p if d is None else d.merge(p, on=KEY)
    d = d.dropna(subset=["actual", "persistence", "seasonal_naive"])  # same rows the harness scores
    for name, ms in BLENDS.items():
        q50 = np.expm1(np.log1p(d[ms]).mean(axis=1))  # average in log space, like the models' own output
        err = (q50 - d.actual).abs().groupby([d.test_year, d.horizon]).mean()
        pers = (d.persistence - d.actual).abs().groupby([d.test_year, d.horizon]).mean()
        rows += [{"panel": panel, "test_year": y, "horizon": h, "blend": name, "mae": v,
                  "rel_mae_vs_persistence": v / pers[(y, h)]} for (y, h), v in err.items()]

out = pd.DataFrame(rows)
out.to_csv(RESULTS / "blend_check.csv", index=False)
t = out.pivot_table(index=["panel", "test_year", "horizon"], columns="blend", values="mae")
print(t.round(1).to_string())
print("smallest miss:", t.idxmin(axis=1).value_counts().to_dict())
print("median change vs lightgbm:", (t.div(t.lightgbm, axis=0) - 1).median().round(3).to_dict())
