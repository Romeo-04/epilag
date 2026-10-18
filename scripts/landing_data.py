"""Write the landing page's replay data: the forecasts made in the week ending 2 Jun 2019 (site/public/data/).

Same method as the app's replay (app/streamlit_app.py replay_forecast/alert_level): out-of-sample backtest
forecasts at 4 and 8 weeks ahead, thresholds from years before 2019 only. Also recomputes the README claim
(provinces that crossed the epidemic threshold and how many were flagged watch or warning 4 weeks ahead),
so the landing page shows the number the data gives.
Usage: python scripts/landing_data.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from thresholds import thresholds  # noqa: E402

DATA = ROOT / "app" / "data"
OUT = ROOT / "site" / "public" / "data"
ORIGIN = pd.Timestamp("2019-06-02")
LEVEL = ["normal", "above", "watch", "warning"]


def level(q50, q90, alert, epidemic):
    lv = pd.Series(LEVEL[0], index=q50.index)
    lv[q50 > alert] = LEVEL[1]
    lv[q90 > epidemic] = LEVEL[2]
    lv[q50 > epidemic] = LEVEL[3]
    return lv


def main():
    bt = pd.read_parquet(DATA / "province_backtest.parquet")
    hist = pd.read_parquet(DATA / "province_history.parquet")
    static = pd.read_parquet(DATA / "province_forecast.parquet").drop_duplicates("unit_id")[["unit_id", "unit_name", "population"]]
    thr = thresholds(hist[hist.week < f"{ORIGIN.year}-01-01"])

    bt = bt.assign(origin=bt.target_week - pd.to_timedelta(bt.horizon * 7, unit="D"))
    f = bt[bt.origin == ORIGIN].merge(static, on="unit_id")
    f["woy"] = f.target_week.dt.isocalendar().week.astype(int).clip(upper=52)
    f = f.merge(thr, on=["unit_id", "woy"], how="left")
    f["level"] = level(f.q50, f.q90, f.alert, f.epidemic)
    f["actual_level"] = level(f.actual, f.actual, f.alert, f.epidemic)

    out = {"origin": ORIGIN.strftime("%Y-%m-%d"), "names": {}, "pop": {}, "horizons": {}, "claim": {}, "priority": []}
    for r in static.itertuples():
        out["names"][r.unit_id] = r.unit_name
        out["pop"][r.unit_id] = int(r.population)
    for h, g in f.groupby("horizon"):
        out["horizons"][str(h)] = {
            "target": g.target_week.iloc[0].strftime("%Y-%m-%d"),
            "units": {r.unit_id: [r.level, round(r.q10), round(r.q50), round(r.q90),
                                  None if pd.isna(r.actual) else int(r.actual), r.actual_level] for r in g.itertuples()},
        }
        crossed = g[g.actual_level == "warning"]
        out["claim"][str(h)] = {"crossed": int(len(crossed)), "flagged": int(crossed.level.isin(["watch", "warning"]).sum())}
    g4 = f[(f.horizon == 4) & f.level.isin(["watch", "warning"])].assign(per100k=lambda d: d.q50 / d.population * 1e5)
    out["priority"] = g4.sort_values("per100k", ascending=False).unit_id.head(5).tolist()

    # Dengue Drill teaser: Western Visayas at the turn of 2 Jun 2019 (from docs/drill/data.js)
    drill = json.loads((ROOT / "docs" / "drill" / "data.js").read_text().removeprefix("window.DRILL = ").rstrip().rstrip(";"))
    i = drill["weeks"].index(out["origin"])
    wv = next(r for r in drill["regions"] if r["id"] == "PH06")
    out["drill"] = {
        "region": wv["name"], "turn": drill["turns"].index(out["origin"]) + 1, "turns": len(drill["turns"]),
        "budget": drill["kit"]["pesos"] * drill["kit"]["kits"],
        "provinces": {p["id"]: {"name": p["name"], "cases": p["cases"][i], "before": p["cases"][i - 2], "fc": p["fc"].get(out["origin"])}
                      for p in wv["provinces"]},
    }

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"replay_{out['origin']}.json"
    path.write_text(json.dumps(out, separators=(",", ":")))
    print(path.relative_to(ROOT), f"{path.stat().st_size / 1e3:.0f} kB", "claim", out["claim"],
          "priority", [out["names"][u] for u in out["priority"]])


if __name__ == "__main__":
    main()
