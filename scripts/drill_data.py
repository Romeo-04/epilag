"""Write site/public/drill/data.json for Dengue Drill (Vite copies it to docs/drill/): the 2019 season, province by
province, for each region.

For every province: weekly reported cases and rain (Apr-Nov 2019), the epidemic threshold for each week (from
2016-2018 only), and the forecast EpiLag-PH made 4 weeks ahead from each turn's week (models trained only on
earlier years). Also prints how two simple strategies would score, as a check on the game's story.
Needs data/processed (python src/fetch_weather.py and src/clean_dengue.py). Usage: python scripts/drill_data.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from thresholds import thresholds  # noqa: E402

SEASON = pd.date_range("2019-04-07", "2019-11-24", freq="W-SUN")
TURNS = pd.date_range("2019-05-05", periods=8, freq="2W-SUN")  # 8 turns, 2 weeks apart
HORIZON = 4
KIT_PESOS, PESOS_PER_PERSON, KITS, MAX_SHARE = 500_000, 15.0, 10, 0.30
EFFECT = (0.10, 0.30, 0.50)


def level(q50, q90, alert, epidemic):
    return "warning" if q50 > epidemic else "watch" if q90 > epidemic else "above" if q50 > alert else "normal"


def main() -> None:
    units = pd.read_csv(ROOT / "data" / "processed" / "units.csv")
    hist = pd.read_parquet(ROOT / "app" / "data" / "province_history.parquet")
    weather = pd.read_parquet(ROOT / "data" / "processed" / "weather_unit_week.parquet")
    bt = pd.read_parquet(ROOT / "app" / "data" / "province_backtest.parquet")
    bt = bt[bt.horizon == HORIZON].assign(origin=lambda d: d.target_week - pd.Timedelta(weeks=HORIZON))

    thr = thresholds(hist[hist.week < "2019-01-01"])
    woy = pd.Series(SEASON.isocalendar().week.astype(int).clip(upper=52).values, index=SEASON)
    regions = []
    for (rid, rname), g in units.groupby(["region_id", "region_name"]):
        provs = []
        for u in g.itertuples():
            h = hist[hist.unit_id == u.unit_id].set_index("week").cases.reindex(SEASON)
            if h.isna().mean() > 0.2:
                continue
            rain = weather[weather.unit_id == u.unit_id].set_index("week").rain_mm.reindex(SEASON)
            t = thr[thr.unit_id == u.unit_id].set_index("woy")
            epi, usual = woy.map(t.epidemic), woy.map(t.alert)
            fc = {}
            for origin in TURNS:
                r = bt[(bt.unit_id == u.unit_id) & (bt.origin == origin)]
                if r.empty:
                    continue
                r = r.iloc[0]
                w = int(min(52, r.target_week.isocalendar().week))
                lv = level(r.q50, r.q90, t.alert.get(w, np.inf), t.epidemic.get(w, np.inf))
                fc[origin.strftime("%Y-%m-%d")] = [lv, round(r.q10), round(r.q50), round(r.q90)]
            provs.append({"id": u.unit_id, "name": u.unit_name, "pop": int(u.population),
                          "cases": [None if pd.isna(v) else int(v) for v in h],
                          "rain": [None if pd.isna(v) else round(float(v)) for v in rain],
                          "epi": [None if pd.isna(v) else round(float(v), 1) for v in epi],
                          "usual": [None if pd.isna(v) else round(float(v), 1) for v in usual], "fc": fc})
        if len(provs) >= 3:  # the 3D board of each region comes from scripts/voxel_data.py
            regions.append({"id": rid, "name": rname, "provinces": provs})

    data = {"weeks": [d.strftime("%Y-%m-%d") for d in SEASON], "turns": [d.strftime("%Y-%m-%d") for d in TURNS],
            "kit": {"pesos": KIT_PESOS, "per_person": PESOS_PER_PERSON, "kits": KITS, "max_share": MAX_SHARE,
                    "effect": EFFECT}, "regions": regions}
    out = ROOT / "site" / "public" / "drill" / "data.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, separators=(",", ":")))
    print(out.relative_to(ROOT), f"{out.stat().st_size / 1e3:.0f} kB,", len(regions), "regions")
    check(data)


# ------------------------------------------------------------------ the same scoring the game uses

def averted(prov, weeks, turn, n_kits):
    i = weeks.index(turn)
    window = [c or 0 for c in prov["cases"][i + 2:i + 10]]  # people infected before the clean-up still fall sick
    share = min(n_kits * KIT_PESOS / PESOS_PER_PERSON / prov["pop"], MAX_SHARE)
    return sum(window) * share * EFFECT[1]


def play(region, weeks, turns, pick):
    """pick(region, turn) -> list of province indices to send one kit each this turn."""
    left, total = KITS, 0.0
    for turn in turns:
        for p in pick(region, turn)[:left]:
            total += averted(region["provinces"][p], weeks, turn, 1)
            left -= 1
    return total


def reactive(region, turn):
    """Send kits where reported cases already passed the epidemic threshold this week (today's practice)."""
    out = []
    for k, p in enumerate(region["provinces"]):
        j = WEEKS.index(turn)
        if p["cases"][j] is not None and p["epi"][j] is not None and p["cases"][j] > p["epi"][j]:
            out.append(k)
    return out[:2]


def epilag(region, turn):
    """Send kits to areas EpiLag puts on watch or warning, highest forecast per 100,000 first."""
    rows = [(p["fc"][turn][2] / p["pop"], k) for k, p in enumerate(region["provinces"])
            if turn in p["fc"] and p["fc"][turn][0] in ("watch", "warning")]
    return [k for _, k in sorted(rows, reverse=True)][:2]


WEEKS: list = []


def check(data):
    global WEEKS
    WEEKS = data["weeks"]
    for r in data["regions"]:
        a, b = play(r, WEEKS, data["turns"], reactive), play(r, WEEKS, data["turns"], epilag)
        print(f"  {r['name'][:38]:38s} provinces={len(r['provinces']):2d}  reactive={a:6.0f}  epilag={b:6.0f}")


if __name__ == "__main__":
    main()
