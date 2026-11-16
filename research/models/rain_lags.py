"""Longer rain lags: does rain from 12-23 weeks back help?

SHAP put rain's largest share at the longest lag offered (11 weeks), so the window may be too short.
This adds three 4-week rain totals, 12-15, 16-19 and 20-23 weeks before week t, to the research
table (extra_features.py), re-runs the LightGBM test, and measures where rain's SHAP sits by weeks back.

Writes research/results/rain_lags.csv (error, range, Watch: research set vs research set + long rain)
and rain_lag_shap.csv (mean |SHAP| of rain features, by weeks back, for the extended set).
Usage: python research/models/rain_lags.py [province|region_qc ...]
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import RESULTS, run, score, upsert  # noqa: E402
from influence import load  # noqa: E402
from models import lightgbm  # noqa: E402

WINDOWS = [(12, 15), (16, 19), (20, 23)]


def extend(table: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Sum of weekly rain from a to b weeks before week t (all four weeks needed)."""
    table = table.sort_values(["unit_id", "week"]).reset_index(drop=True)
    g = table.groupby("unit_id").rain_mm
    new = []
    for a, b in WINDOWS:
        name = f"rain_win{a}_{b}"
        table[name] = g.transform(lambda s: s.shift(a).rolling(b - a + 1).sum())
        new.append(name)
    return table, new


def weeks_back(f: str) -> str | None:
    if m := re.fullmatch(r"rain_lag(\d+)", f):
        k = int(m[1]); return f"{k // 4 * 4}-{k // 4 * 4 + 3}"
    if m := re.fullmatch(r"rain_win(\d+)_(\d+)", f):
        return f"{m[1]}-{m[2]}"
    if m := re.fullmatch(r"rain_sum(\d+)", f):
        return f"0-{int(m[1]) - 1} (total)"
    return None


def compare(panel: str, table: pd.DataFrame, plus: list[str], new: list[str]) -> pd.DataFrame:
    s = pd.concat([score(run(panel, lightgbm, features=fs, table=table), panel, "lightgbm").assign(feature_set=name)
                   for name, fs in (("plus", plus), ("plus_long_rain", plus + new))], ignore_index=True)
    ref = s[s.feature_set == "plus"].set_index(["test_year", "horizon"]).mae
    s["change_pct_vs_plus"] = [(m / ref[(y, h)] - 1) * 100 for m, y, h in zip(s.mae, s.test_year, s.horizon)]
    cols = ["panel", "test_year", "horizon", "feature_set", "mae", "change_pct_vs_plus", "rel_mae_vs_persistence",
            "coverage_10_90", "caught_watch", "false_share_watch", "onsets"]
    return upsert(RESULTS / "rain_lags.csv", s[cols], ["panel", "feature_set", "test_year", "horizon"])


def shap_by_weeks(panel: str, table: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    import lightgbm as lgb
    import shap

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from backtest import PARAMS
    from features import HORIZONS

    rows = []
    for h in HORIZONS:
        target = f"target_h{h}"
        train = table[table[target].notna() & table.y_lag0.notna()]
        m = lgb.LGBMRegressor(objective="quantile", alpha=0.5, **PARAMS).fit(train[feats], train[target])
        sample = train.sample(min(4000, len(train)), random_state=0)
        imp = pd.Series(np.abs(shap.TreeExplainer(m.booster_).shap_values(sample[feats])).mean(axis=0), index=feats)
        total = imp.sum()
        for f, v in imp.items():
            if (w := weeks_back(f)) is not None:
                rows.append({"panel": panel, "horizon": h, "feature": f, "weeks_back": w,
                             "mean_abs_shap": v, "share_of_all": v / total})
    out = pd.DataFrame(rows)
    upsert(RESULTS / "rain_lag_shap.csv", out, ["panel", "horizon", "feature"])
    return out


if __name__ == "__main__":
    for panel in sys.argv[1:] or ["region_qc", "province"]:
        table, plus = load(panel)
        table, new = extend(table)
        print(panel, "missing share of new features (usable rows):",
              table.loc[table.target_h4.notna() & table.y_lag0.notna(), new].isna().mean().round(3).to_dict(), flush=True)
        c = compare(panel, table, plus, new)
        c = c[(c.panel == panel) & (c.feature_set == "plus_long_rain")]
        print(c.pivot_table(index="test_year", columns="horizon", values="change_pct_vs_plus").round(1).to_string(), flush=True)
        sh = shap_by_weeks(panel, table, plus + new)
        print(sh.pivot_table(index="weeks_back", columns="horizon", values="share_of_all", aggfunc="sum").mul(100).round(1).to_string(),
              flush=True)
