"""Write site/public/drill/models.json: the forecasts of every model the player can pick in Dengue Drill's round 2.

The game's own files (data.json, qc.json; scripts/drill_data.py and scripts/qc_drill_data.py) carry the submitted
model's forecasts as each area's "fc". This adds, for both missions, the same entries for the four research models
(research/results/extracts/game_forecasts.json, written by research/models/game_forecasts.py) and for their average:

  missions.<2019|qc>.<model>.<area id>.<turn> = [alert level, q10, q50, q90]

**The average of the four is approximate.** The research blend (research/models/blend.py) averages the models'
unrounded forecasts in log(cases + 1) space, quantile by quantile. Those are not in the repository, so this averages
the rounded numbers in game_forecasts.json the same way, and sets the alert level from the thresholds in the game
files (for Quezon City, from the city totals: every barangay is the city forecast times its share). Rebuilding the
four models' own levels this way gets 2,742 of 2,752 province entries and every Quezon City entry right (check()).

Each model also gets two figures for its card, pooled over the research's 24 checks
(research/results/model_comparison.csv): checks where it beat "same as this week", and the share of outbreak starts
caught by Outbreak warning. Stops if the lightgbm entries differ from the game's current "fc".
Usage: python scripts/drill_models.py
"""
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "site" / "public" / "drill"
RESEARCH = ROOT / "research" / "results"
HORIZON_WEEKS = 4
# id, name on the card, short name in the top bar, one line on how it behaves (from research/results/README.md)
MODELS = [
    ("lightgbm", "EpiLag-PH (LightGBM)", "EpiLag-PH", "The submitted model. Boosted trees; lowest error most often."),
    ("negbin", "Negative binomial", "Neg. binomial", "A classic count model. Carries a rise forward; best in the flat year."),
    ("random_forest", "Random forest", "Random forest", "Bagged trees. Close to LightGBM, never the best."),
    ("sarimax", "SARIMAX", "SARIMAX", "One time-series model per area. Many Watches, few Outbreak warnings."),
    ("average", "Average of the four", "Average", "All four combined. Steady, but fewer Outbreak warnings."),
]
FOUR = [m[0] for m in MODELS[:4]]
CSV_NAME = {"average": "blend_all4"}


def level(q50, q90, alert, epidemic):  # as scripts/drill_data.py
    return "warning" if q50 > epidemic else "watch" if q90 > epidemic else "above" if q50 > alert else "normal"


def log_mean(values):
    return math.expm1(sum(math.log1p(v) for v in values) / len(values))


def thresholds_2019(game):
    """(area id, turn) -> (usual, epidemic) for the week the forecast is for."""
    out = {}
    for r in game["regions"]:
        for p in r["provinces"]:
            for t in game["turns"]:
                j = game["weeks"].index(t) + HORIZON_WEEKS
                out[p["id"], t] = tuple(math.inf if v is None else v for v in (p["usual"][j], p["epi"][j]))
    return out


def average_2019(fc, thr):
    out = {}
    for area in fc[FOUR[0]]:
        out[area] = {}
        for t in fc[FOUR[0]][area]:
            q10, q50, q90 = (round(log_mean([fc[m][area][t][k] for m in FOUR])) for k in (1, 2, 3))
            out[area][t] = [level(q50, q90, *thr[area, t]), q10, q50, q90]
    return out


def city_level(fc_model, game, turn):
    """Quezon City: the level of the city forecast, from the barangay numbers summed back to the city."""
    ps = game["regions"][0]["provinces"]
    j = game["weeks"].index(turn) + HORIZON_WEEKS
    total = lambda k: sum(fc_model[p["id"]][turn][k] for p in ps)  # noqa: E731
    return level(total(2), total(3), sum(p["usual"][j] for p in ps), sum(p["epi"][j] for p in ps))


def average_qc(fc, game):
    out = {p["id"]: {} for p in game["regions"][0]["provinces"]}
    for t in game["turns"]:
        for area in out:
            out[area][t] = [None] + [round(log_mean([fc[m][area][t][k] for m in FOUR]), 1) for k in (1, 2, 3)]
        lv = city_level(out, game, t)
        for area in out:
            out[area][t][0] = lv
    return out


def cards() -> list[dict]:
    mc = pd.read_csv(RESEARCH / "model_comparison.csv")
    out = []
    for mid, name, short, line in MODELS:
        g = mc[mc.model == CSV_NAME.get(mid, mid)]
        out.append({"id": mid, "name": name, "short": short, "line": line, "checks": len(g),
                    "beat_same_as_this_week": int((g.rel_mae_vs_persistence < 1).sum()),
                    "warning_caught_pct": int(g.caught_warning.sum() / g.onsets.sum() * 100 + 0.5)})
    return out


def check(gf, g19, gqc, thr) -> None:
    """The four models' own levels, rebuilt the way the average's are: how many come out the same."""
    same = total = 0
    for m in FOUR:
        for area, turns in gf["drill_2019"]["fc"][m].items():
            for t, (lv, _, q50, q90) in turns.items():
                total += 1
                same += level(q50, q90, *thr[area, t]) == lv
    print(f"levels rebuilt from the rounded numbers: {same:,} of {total:,} province entries")
    any_area = gqc["regions"][0]["provinces"][0]["id"]
    for m in FOUR:
        for t in gqc["turns"]:
            assert city_level(gf["drill_qc"]["fc"][m], gqc, t) == gf["drill_qc"]["fc"][m][any_area][t][0], (m, t)
    print("levels rebuilt from the city totals: every Quezon City entry")


def main() -> None:
    gf = json.loads((RESEARCH / "extracts" / "game_forecasts.json").read_text())
    g19, gqc = (json.loads((GAME / f).read_text()) for f in ("data.json", "qc.json"))
    for game, key in ((g19, "drill_2019"), (gqc, "drill_qc")):
        assert game["turns"] == gf[key]["turns"], f"{key}: turns differ from the game's"
        for r in game["regions"]:
            for p in r["provinces"]:
                if p["fc"] != gf[key]["fc"]["lightgbm"].get(p["id"]):
                    raise SystemExit(f"{key}: lightgbm differs from the game's forecast for {p['id']}")
    thr = thresholds_2019(g19)
    check(gf, g19, gqc, thr)
    missions = {"2019": {**{m: gf["drill_2019"]["fc"][m] for m in FOUR}, "average": average_2019(gf["drill_2019"]["fc"], thr)},
                "qc": {**{m: gf["drill_qc"]["fc"][m] for m in FOUR}, "average": average_qc(gf["drill_qc"]["fc"], gqc)}}
    data = {"default": "lightgbm", "models": cards(), "missions": missions,
            "note": "average: the four models' rounded forecasts averaged in log(cases + 1) space; approximate (scripts/drill_models.py)"}
    out = GAME / "models.json"
    out.write_text(json.dumps(data, separators=(",", ":")))
    print(out.relative_to(ROOT), f"{out.stat().st_size / 1e3:.0f} kB")
    for c in data["models"]:
        print(f"  {c['name']:24s} beat 'same as this week' {c['beat_same_as_this_week']:2d} of {c['checks']}, Outbreak warning {c['warning_caught_pct']}%")


if __name__ == "__main__":
    main()
