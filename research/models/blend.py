"""Blends: an equal average of several methods' forecasts, scored like any other model.

Each method's saved, already calibrated q10/q50/q90 (data/processed/research/<panel>_<model>.parquet) are
averaged in log space, quantile by quantile ("quantile averaging", Lichtendahl, Grushka-Cockayne and
Winkler 2013). Nothing is refit, no weight is tuned, and the blend gets no calibration of its own: its
range is the average of ranges each calibrated on the last training year only. Scores (error, range,
both alert rules) go into research/results/model_comparison.csv as models blend_lgb_negbin and blend_all4.

Usage: python research/models/blend.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import OUT, RESULTS, score, upsert  # noqa: E402

KEY = ["unit_id", "target_week", "horizon", "test_year"]
QCOLS = ["q10", "q50", "q90", "q10_raw", "q90_raw"]
BLENDS = {"blend_lgb_negbin": ["lightgbm", "negbin"],
          "blend_all4": ["lightgbm", "negbin", "random_forest", "sarimax"]}


def blend(panel: str, models: list[str]) -> pd.DataFrame:
    frames = [pd.read_parquet(OUT / f"{panel}_{m}.parquet").sort_values(KEY).reset_index(drop=True) for m in models]
    for f in frames[1:]:
        assert f[KEY].equals(frames[0][KEY]), "methods must forecast the same rows"
    out = frames[0].drop(columns=QCOLS + ["margin"])
    for c in QCOLS:
        out[c] = np.expm1(np.mean([np.log1p(f[c].values) for f in frames], axis=0))
    return out


if __name__ == "__main__":
    scores = [score(blend(panel, ms), panel, name) for panel in ["province", "region_qc"] for name, ms in BLENDS.items()]
    table = upsert(RESULTS / "model_comparison.csv", pd.concat(scores), ["panel", "model", "test_year", "horizon"])
    keep = ["lightgbm", "negbin", "random_forest", "sarimax", *BLENDS]
    t = table[table.model.isin(keep)]
    for col in ["mae", "coverage_10_90", "caught_watch", "false_share_watch", "caught_warning"]:
        print(col); print(t.pivot_table(index=["panel", "test_year", "horizon"], columns="model", values=col).round(3).to_string())
