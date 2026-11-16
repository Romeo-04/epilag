"""Every model's forecasts in Dengue Drill's own format, so the game can show how the four models differ.

The game (site/public/drill/data.json and qc.json) shows, at each turn, the forecast EpiLag-PH made 4 weeks ahead:
[alert level, q10, q50, q90]. scripts/drill_data.py and scripts/qc_drill_data.py take it from the submitted model only
(app/data/*_backtest.parquet). This script builds the same entries from the research backtests of all four models
(data/processed/research/<panel>_<model>.parquet, written by harness.py), with the same thresholds, turns and rounding:

  drill_2019.fc[model][province id][turn]  = [level, q10, q50, q90]     2019 mission, per province
  drill_qc.fc[model][barangay id][turn]     = [level, q10, q50, q90]     Quezon City 2024-25 mission, per barangay
                                                                         (the city forecast x the barangay's share)

To use a model in the game, put its entry in place of each area's "fc". The lightgbm entries equal the game's current
"fc" exactly; the script stops if they do not. It also prints how the build scripts' two strategies score on the 2019
mission with each model, and each model's Quezon City alert level by turn.
Output: research/results/extracts/game_forecasts.json. Needs data/processed/ (harness.py run for all four models).
Usage: python research/models/game_forecasts.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import drill_data  # noqa: E402
import qc_drill_data  # noqa: E402
from thresholds import thresholds  # noqa: E402

APP, RESEARCH = ROOT / "app" / "data", ROOT / "data" / "processed" / "research"
GAME = ROOT / "site" / "public" / "drill"
OUT = ROOT / "research" / "results" / "extracts" / "game_forecasts.json"
MODELS = {"lightgbm": "LightGBM (the submitted model)", "negbin": "Negative binomial",
          "random_forest": "Random forest", "sarimax": "SARIMAX"}


def turn_rows(panel: str, model: str, turns: pd.DatetimeIndex, horizon: int) -> pd.DataFrame:
    bt = pd.read_parquet(RESEARCH / f"{panel}_{model}.parquet")
    bt = bt[bt.horizon == horizon].assign(origin=lambda d: d.target_week - pd.Timedelta(weeks=horizon))
    return bt[bt.origin.isin(turns)]


def woy(week) -> int:
    return int(min(52, week.isocalendar().week))


def province_2019(model: str) -> dict:
    """As scripts/drill_data.py: thresholds from 2016-2018, whole-number q10/q50/q90."""
    hist = pd.read_parquet(APP / "province_history.parquet")
    thr = thresholds(hist[hist.week < "2019-01-01"])
    thr = {u: g.set_index("woy") for u, g in thr.groupby("unit_id")}
    fc: dict = {}
    for r in turn_rows("province", model, drill_data.TURNS, drill_data.HORIZON).itertuples():
        t = thr.get(r.unit_id)
        if t is None:
            continue
        w = woy(r.target_week)
        lv = drill_data.level(r.q50, r.q90, t.alert.get(w, np.inf), t.epidemic.get(w, np.inf))
        fc.setdefault(r.unit_id, {})[r.origin.strftime("%Y-%m-%d")] = [lv, int(round(r.q10)), int(round(r.q50)), int(round(r.q90))]
    return fc


def qc_shares() -> dict:
    """Barangay id -> 2022-2025 share of the city's cases, keyed as scripts/qc_drill_data.py keys them."""
    geo = json.loads((APP / "qc_barangays.geojson").read_text(encoding="utf-8"))
    by_key = {qc_drill_data.norm(f["properties"]["adm4_en"]): f["properties"]["adm4_psgc"] for f in geo["features"]}
    b = pd.read_csv(APP / "qc_barangays.csv")
    share = b.cases_2022_2025 / b.cases_2022_2025.sum()
    return {f"Q{by_key[qc_drill_data.norm(n)]}": s for n, s in zip(b.Barangay, share)}


def qc_2024_25(model: str, shares: dict) -> dict:
    """As scripts/qc_drill_data.py: the city's 4-week forecast, its level from city thresholds before 2024, shared out."""
    hist = pd.read_parquet(APP / "region_qc_history.parquet")
    thr = thresholds(hist[(hist.unit_id == "QC") & (hist.week < "2024-01-01")]).set_index("woy")
    city = {}
    for r in turn_rows("region_qc", model, qc_drill_data.TURNS, qc_drill_data.HORIZON).query("unit_id == 'QC'").itertuples():
        w = woy(r.target_week)
        lv = qc_drill_data.level(r.q50, r.q90, thr.alert.get(w, np.inf), thr.epidemic.get(w, np.inf))
        city[r.origin.strftime("%Y-%m-%d")] = (lv, r.q10, r.q50, r.q90)
    return {uid: {k: [lv, round(q10 * s, 1), round(q50 * s, 1), round(q90 * s, 1)] for k, (lv, q10, q50, q90) in city.items()}
            for uid, s in shares.items()}


def same_as_game(game: dict, fc: dict, name: str) -> None:
    """The lightgbm entries must equal the game's current fc, area by area."""
    areas = [p for r in game["regions"] for p in r["provinces"]]
    bad = [p["id"] for p in areas if p["fc"] != fc.get(p["id"], {})]
    if bad:
        raise SystemExit(f"{name}: lightgbm differs from the game's forecasts for {len(bad)} areas, e.g. {bad[:3]}")
    print(f"{name}: lightgbm matches the game's forecasts for all {len(areas)} areas")


def scores(game: dict, fcs: dict) -> None:
    """Cases averted over the mission by the build scripts' two strategies (scripts/drill_data.py), per model."""
    drill_data.WEEKS = game["weeks"]
    base = sum(drill_data.play(r, game["weeks"], game["turns"], drill_data.reactive) for r in game["regions"])
    print(f"  {'reactive (no forecast)':32s} {base:8.0f}")
    for m, fc in fcs.items():
        total = 0.0
        for r in game["regions"]:
            swapped = {**r, "provinces": [{**p, "fc": fc.get(p["id"], {})} for p in r["provinces"]]}
            total += drill_data.play(swapped, game["weeks"], game["turns"], drill_data.epilag)
        print(f"  {'forecast: ' + m:32s} {total:8.0f}")


def main() -> None:
    shares = qc_shares()
    p19 = {m: province_2019(m) for m in MODELS}
    pqc = {m: qc_2024_25(m, shares) for m in MODELS}
    g19 = json.loads((GAME / "data.json").read_text())
    gqc = json.loads((GAME / "qc.json").read_text())
    same_as_game(g19, p19["lightgbm"], "2019 mission")
    same_as_game(gqc, pqc["lightgbm"], "Quezon City mission")

    data = {"about": __doc__.split("\n\n")[0], "horizon": drill_data.HORIZON, "models": MODELS,
            "drill_2019": {"turns": g19["turns"], "fc": p19}, "drill_qc": {"turns": gqc["turns"], "fc": pqc}}
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(OUT.relative_to(ROOT), f"{OUT.stat().st_size / 1e3:.0f} kB")

    print("Cases averted, 2019 mission (all regions):")
    scores(g19, p19)
    # No score for Quezon City: every barangay gets the same city forecast x its share, so the build scripts' strategy
    # (highest forecast per person) has nothing to rank by. There the models differ only in the level at each turn.
    print("Quezon City alert level by turn (the same for every barangay):")
    any_brgy = next(iter(shares))
    for m in MODELS:
        print(f"  {m:14s}", " ".join(f"{pqc[m][any_brgy][t][0]:8s}" for t in gqc["turns"]))


if __name__ == "__main__":
    main()
