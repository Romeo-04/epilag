"""Write the Dengue Drill's Quezon City mission: the 2024-25 season, barangay by barangay.

Quezon City is the most specific area with the latest data (weekly cases to December 2025; barangay counts by year).
Weekly reports exist only for the whole city, so the barangay numbers are estimates, and the game says so:
  - reported cases per barangay = the city's weekly cases x the barangay's share of the city's 2025 cases
    (what actually happened, by barangay, as far as the yearly data shows)
  - epidemic line and usual level per barangay = the city's (from years before 2024) x the barangay's 2022-2025 share
    (so barangays whose share grew in 2025 run hotter than their usual)
  - population per barangay = the city's population x its 2022-2025 share (assumes equal attack rates over the years)
  - EpiLag-PH intel at each turn = the real out-of-sample city forecast made that week (4 weeks ahead), shared out
    by the 2022-2025 share (what could be known at the time)
  - no rain: there is no weather series for the city in the app data, so the game shows none
The board is the city's 142 barangays (app/data/qc_barangays.geojson, faeldon/philippines-json-maps 2023, MIT),
rasterised like the other boards. Outputs site/public/drill/qc.json and site/public/geo/voxel_qc.json.
Usage: python scripts/qc_drill_data.py
"""
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "data"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from thresholds import thresholds  # noqa: E402
from voxel_data import pack, rings_of  # noqa: E402

SEASON = pd.date_range("2024-09-01", "2025-06-29", freq="W-SUN")
TURNS = pd.date_range("2024-11-10", periods=8, freq="2W-SUN")  # 8 turns, 2 weeks apart, before the Feb 2025 peak
HORIZON = 4
KIT = {"pesos": 500_000, "per_person": 15.0, "kits": 10, "max_share": 0.30, "effect": [0.10, 0.30, 0.50]}


def norm(name: str) -> str:
    """Barangay names as keys: no accents, no parenthetical alternate names, letters and digits only."""
    try:  # the CSV has a few UTF-8 names read as Latin-1 ("DoÃ±a" for "Doña")
        name = name.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"\(.*?\)", "", name).lower()
    return re.sub(r"[^a-z0-9]", "", name)


def level(q50, q90, alert, epidemic):
    return "warning" if q50 > epidemic else "watch" if q90 > epidemic else "above" if q50 > alert else "normal"


def main() -> None:
    geo = json.loads((DATA / "qc_barangays.geojson").read_text(encoding="utf-8"))
    brgy = pd.read_csv(DATA / "qc_barangays.csv")
    brgy["key"] = brgy.Barangay.map(norm)
    brgy["share_long"] = brgy.cases_2022_2025 / brgy.cases_2022_2025.sum()
    brgy["share_2025"] = brgy.cases_2025 / brgy.cases_2025.sum()
    by_key = {norm(f["properties"]["adm4_en"]): f for f in geo["features"]}
    missing = [b for b in brgy.key if b not in by_key]
    if missing:
        raise SystemExit(f"barangays without a boundary: {missing}")

    hist = pd.read_parquet(DATA / "region_qc_history.parquet")
    qc = hist[hist.unit_id == "QC"].set_index("week").cases
    pop = int(pd.read_parquet(DATA / "region_qc_forecast.parquet").query("unit_id == 'QC'").population.iloc[0])
    thr = thresholds(hist[(hist.unit_id == "QC") & (hist.week < "2024-01-01")]).set_index("woy")
    woy = pd.Series(SEASON.isocalendar().week.astype(int).clip(upper=52).values, index=SEASON)
    epi, usual = woy.map(thr.epidemic), woy.map(thr.alert)
    city = qc.reindex(SEASON)

    bt = pd.read_parquet(DATA / "region_qc_backtest.parquet")
    bt = bt[(bt.unit_id == "QC") & (bt.horizon == HORIZON)].assign(origin=lambda d: d.target_week - pd.Timedelta(weeks=HORIZON))
    fc_city = {}
    for origin in TURNS:
        r = bt[bt.origin == origin]
        if r.empty:
            continue
        r = r.iloc[0]
        w = int(min(52, r.target_week.isocalendar().week))
        fc_city[origin.strftime("%Y-%m-%d")] = (level(r.q50, r.q90, thr.alert.get(w, np.inf), thr.epidemic.get(w, np.inf)), r.q10, r.q50, r.q90)

    feats, provs = [], []
    for b in brgy.sort_values("cases_2022_2025", ascending=False).itertuples():
        f = by_key[b.key]
        uid = f"Q{f['properties']['adm4_psgc']}"
        feats.append({**f, "properties": {"unit_id": uid}})
        sl, s25 = b.share_long, b.share_2025
        provs.append({
            "id": uid, "name": b.Barangay, "pop": max(1, round(pop * sl)),
            "cases": [None if pd.isna(c) else round(float(c) * s25, 1) for c in city],
            "rain": [None] * len(SEASON),
            "epi": [None if pd.isna(e) else round(float(e) * sl, 2) for e in epi],
            "usual": [None if pd.isna(u) else round(float(u) * sl, 2) for u in usual],
            "fc": {k: [lv, round(q10 * sl, 1), round(q50 * sl, 1), round(q90 * sl, 1)] for k, (lv, q10, q50, q90) in fc_city.items()},
        })

    data = {"weeks": [d.strftime("%Y-%m-%d") for d in SEASON], "turns": [d.strftime("%Y-%m-%d") for d in TURNS],
            "kit": KIT, "estimated": True,
            "regions": [{"id": "QC", "name": "Quezon City", "year": 2025, "provinces": provs}]}
    out = ROOT / "site" / "public" / "drill" / "qc.json"
    out.write_text(json.dumps(data, separators=(",", ":")))

    feats = [f for f in feats if f.get("geometry")]  # one barangay (Capri) has no shape in the source: listed, not drawn
    pts = np.concatenate([r for f in feats for r in rings_of(f)])
    kx = math.cos(math.radians(pts[:, 1].mean()))
    span = max((pts[:, 0].max() - pts[:, 0].min()) * kx, pts[:, 1].max() - pts[:, 1].min())
    grid, _ = pack(feats, span / 96)
    (ROOT / "site" / "public" / "geo" / "voxel_qc.json").write_text(json.dumps({"QC": grid}, separators=(",", ":")))
    peak = city.idxmax()
    print(f"{out.relative_to(ROOT)}: {out.stat().st_size / 1e3:.0f} kB, {len(provs)} barangays, "
          f"{len(fc_city)} of {len(TURNS)} turns with a forecast; city peak {city.max():.0f} on {peak.date()}")
    print("city forecasts by turn:", {k: v[0] for k, v in fc_city.items()})


if __name__ == "__main__":
    main()
