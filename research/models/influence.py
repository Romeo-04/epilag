"""How much each variable group matters, on the table with the new candidate variables.

groups  Re-run the full test with LightGBM: drop one group from the full set, and add one group to a
        base of cases + season. Writes research/results/feature_groups.csv.
shap    Fit the median model on all usable rows (as src/train_final.py does) and measure each group's
        share of mean |SHAP|, and how it spreads over lag weeks. Writes shap_groups.csv and shap_lags.csv.

Usage: python research/models/influence.py groups|shap province|region_qc
Needs research/models/extra_features.py to have built the *_plus tables.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extra_features import OUT, PROC, group_of  # noqa: E402
from harness import RESULTS, run, score, upsert  # noqa: E402
from models import lightgbm  # noqa: E402

BASE = ("cases", "season")


def load(panel: str) -> tuple[pd.DataFrame, list[str]]:
    return (pd.read_parquet(OUT / f"model_table_{panel}_plus.parquet"),
            json.loads((OUT / f"features_{panel}_plus.json").read_text()))


def live_features(panel: str) -> list[str]:
    """The live model's features, read off the live table. src/features.feature_columns() picks columns by
    name prefix, so on a research table it would also take the research weather (temp_lag*, rh_lag*,
    tmax_max4) and any new rain_* column."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from features import feature_columns
    return feature_columns(pd.read_parquet(PROC / f"model_table_{panel}.parquet"))


def groups(panel: str) -> pd.DataFrame:
    table, feats = load(panel)
    by_group = pd.Series(feats).groupby([group_of(f) for f in feats]).apply(list).to_dict()
    base = [f for g in BASE for f in by_group[g]]
    runs = [("full", "all", feats), ("base", "+".join(BASE), base)]
    runs += [("drop", g, [f for f in feats if f not in fs]) for g, fs in by_group.items()]
    runs += [("add", g, base + fs) for g, fs in by_group.items() if g not in BASE]
    scored = []
    for mode, group, fs in runs:
        print(f"{panel} {mode} {group} ({len(fs)} features)", flush=True)
        s = score(run(panel, lightgbm, features=fs, table=table), panel, "lightgbm")
        scored.append(s.assign(mode=mode, group=group, n_features=len(fs)))
    s = pd.concat(scored, ignore_index=True)
    ref = s[s["mode"].isin(["full", "base"])].set_index(["mode", "test_year", "horizon"]).mae
    ref_mode = s["mode"].map({"drop": "full", "add": "base", "full": "full", "base": "base"})
    s["mae_reference"] = [ref[(m, y, h)] for m, y, h in zip(ref_mode, s.test_year, s.horizon)]
    s["change_pct"] = (s.mae / s.mae_reference - 1) * 100
    cols = ["panel", "test_year", "horizon", "mode", "group", "n_features", "mae", "mae_reference", "change_pct",
            "coverage_10_90", "caught_watch", "false_share_watch", "onsets"]
    return upsert(RESULTS / "feature_groups.csv", s[cols], ["panel", "mode", "group", "test_year", "horizon"])


def shap_shares(panel: str) -> None:
    import lightgbm as lgb
    import shap

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from backtest import PARAMS
    from features import HORIZONS

    table, plus = load(panel)
    g_rows, l_rows = [], []
    for name, feats in (("current", live_features(panel)), ("plus", plus)):
        for h in HORIZONS:
            target = f"target_h{h}"
            train = table[table[target].notna() & table.y_lag0.notna()]
            m = lgb.LGBMRegressor(objective="quantile", alpha=0.5, **PARAMS).fit(train[feats], train[target])
            sample = train.sample(min(4000, len(train)), random_state=0)
            sv = np.abs(shap.TreeExplainer(m.booster_).shap_values(sample[feats])).mean(axis=0)
            imp = pd.Series(sv, index=feats)
            share = imp.groupby([group_of(f) for f in feats]).sum() / imp.sum()
            g_rows += [{"panel": panel, "feature_set": name, "horizon": h, "group": g, "share": v}
                       for g, v in share.items()]
            for f, v in imp.items():
                m_ = re.fullmatch(r"(rain|temp|rh)_lag(\d+)", f)
                if m_:
                    l_rows.append({"panel": panel, "feature_set": name, "horizon": h, "variable": m_[1],
                                   "lag_weeks": int(m_[2]), "mean_abs_shap": v})
            print(f"{panel} {name} h={h}: " + ", ".join(f"{g} {v:.0%}" for g, v in share.sort_values(
                ascending=False).items()), flush=True)
    for name, rows, keys in (("shap_groups.csv", g_rows, ["panel", "feature_set", "horizon", "group"]),
                             ("shap_lags.csv", l_rows, ["panel", "feature_set", "horizon", "variable", "lag_weeks"])):
        if (RESULTS / name).exists():  # replace the panel's rows whole, so no group from an older run lingers
            old = pd.read_csv(RESULTS / name)
            old[old.panel != panel].to_csv(RESULTS / name, index=False)
        upsert(RESULTS / name, pd.DataFrame(rows), keys)


if __name__ == "__main__":
    what, panel = sys.argv[1], sys.argv[2]
    if what == "groups":
        out = groups(panel)
        show = out[(out.panel == panel) & (out.horizon == 4)]
        print(show.pivot_table(index=["mode", "group"], columns="test_year", values="change_pct").round(1).to_string())
    else:
        shap_shares(panel)
