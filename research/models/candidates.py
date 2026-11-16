"""Candidate final variable sets, scored on every measure against the live model, so the choice of final
variables can be made from one table. LightGBM, same harness; the average of the four methods comes from
model_comparison.csv (blend.py).

Writes research/results/candidates.csv (all score columns; `model` holds the set name) and prints, per panel:
checks better than the live set, median and worst change in miss, range held, and both alert rules.
Usage: python research/models/candidates.py [province|region_qc ...]
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extra_features import group_of  # noqa: E402
from harness import RESULTS, run, score, upsert  # noqa: E402
from models import lightgbm  # noqa: E402
from influence import live_features  # noqa: E402
from proposed_features import extend  # noqa: E402

# Proposed groups worth carrying into a candidate set, per panel: those that cut the miss when added to the
# full research set (proposed_features.csv, add_to_plus). Neighbours for provinces: 8 of 8 checks better.
PROPOSED = {"region_qc": [], "province": ["neighbours"]}


def sets(panel: str, plus: list[str], new: dict[str, list[str]]) -> dict[str, list[str]]:
    live = live_features(panel)
    assert plus[:len(live)] == live, "the research list should start with the live features"
    by = lambda *gs: [f for f in plus if group_of(f) in gs]  # noqa: E731
    out = {"live": live,
           "research": plus,
           "research_no_enso": [f for f in plus if group_of(f) != "enso"]}
    if panel == "province":
        out["live_topography"] = live + by("topography")
    for g in PROPOSED[panel]:
        out[f"live_{g}"] = live + new[g]
        out[f"research_no_enso_{g}"] = out["research_no_enso"] + new[g]
    return out


def summary(t: pd.DataFrame) -> pd.DataFrame:
    live = t[t.model == "live"].set_index(["test_year", "horizon"]).mae
    rows = []
    for m, g in t.groupby("model", sort=False):
        ch = (g.set_index(["test_year", "horizon"]).mae / live - 1) * 100
        rows.append({"set": m, "better_than_live": f"{(ch < -1e-9).sum()}/{len(ch)}", "median_%": ch.median(),
                     "worst_%": ch.max(), "best_%": ch.min(), "beat_persistence": int((g.rel_mae_vs_persistence < 1).sum()),
                     "range_held": g.coverage_10_90.mean(), "watch": g.caught_watch.sum() / g.onsets.sum(),
                     "watch_false": g.false_share_watch.mean(), "warning": g.caught_warning.sum() / g.onsets.sum(),
                     "warning_false": g.false_share_warning.mean()})
    return pd.DataFrame(rows).round(3)


if __name__ == "__main__":
    for panel in sys.argv[1:] or ["region_qc", "province"]:
        table, plus, new = extend(panel)
        scored = [score(run(panel, lightgbm, features=fs, table=table), panel, name)
                  for name, fs in sets(panel, plus, new).items()]
        out = upsert(RESULTS / "candidates.csv", pd.concat(scored), ["panel", "model", "test_year", "horizon"])
        mc = pd.read_csv(RESULTS / "model_comparison.csv")
        drift = (out[(out.panel == panel) & (out.model == "live")].set_index(["test_year", "horizon"]).mae
                 - mc[(mc.panel == panel) & (mc.model == "lightgbm")].set_index(["test_year", "horizon"]).mae).abs().max()
        print(panel, "live set vs model_comparison lightgbm, max mae diff:", drift)
        t = pd.concat([out[out.panel == panel], mc[(mc.panel == panel) & (mc.model == "blend_all4")]])
        print(panel); print(summary(t).to_string(index=False), flush=True)
