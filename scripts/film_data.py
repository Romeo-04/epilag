"""Write docs/film/data.js for the motion-graphics film: province outlines as SVG paths, coloured by the
forecast EpiLag-PH made on 2 Jun 2019 (4 weeks ahead) and by what actually happened; and Quezon City's 2024-25
season, week by week, with the out-of-sample forecast made 4 weeks before each week.
Usage: python scripts/film_data.py"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from thresholds import thresholds  # noqa: E402

ORIGIN, HORIZON = pd.Timestamp("2019-06-02"), 4
QC_SEASON = pd.date_range("2024-09-01", "2025-06-29", freq="W-SUN")
W, H = 1000, 1400  # SVG viewBox
LON, LAT = (116.8, 127.0), (4.4, 21.2)


def level(q50, q90, alert, epidemic):
    return "warning" if q50 > epidemic else "watch" if q90 > epidemic else "above" if q50 > alert else "normal"


def xy(lon, lat):
    return (lon - LON[0]) / (LON[1] - LON[0]) * W, (LAT[1] - lat) / (LAT[1] - LAT[0]) * H


def ring_path(ring):
    pts, last = [], None
    for lon, lat in ring:
        p = tuple(round(v, 1) for v in xy(lon, lat))
        if p != last:
            pts.append(p)
            last = p
    if len(pts) < 3:
        return ""
    return "M" + "L".join(f"{x:g},{y:g}" for x, y in pts) + "Z"


def woy(d) -> int:
    return min(52, int(d.isocalendar().week))


def qc_season(data: Path) -> dict:
    """Quezon City's weekly cases, its epidemic line (from years before 2024), and the forecast for each week made
    4 weeks earlier, its level judged on the thresholds known at the time (years before the forecast's year)."""
    hist = pd.read_parquet(data / "region_qc_history.parquet").query("unit_id == 'QC'")
    bt = pd.read_parquet(data / "region_qc_backtest.parquet").query("unit_id == 'QC' and horizon == @HORIZON")
    thr = {y: thresholds(hist[hist.week < f"{y}-01-01"]).set_index("woy") for y in (2024, 2025)}
    cases = hist.set_index("week").cases.reindex(QC_SEASON)
    epi = [float(thr[2024].epidemic[woy(d)]) for d in QC_SEASON]
    fc = []
    for d in QC_SEASON:
        r = bt[bt.target_week == d]
        if r.empty:
            fc.append(None)
            continue
        r = r.iloc[0]
        t = thr[(d - pd.Timedelta(weeks=HORIZON)).year]
        fc.append([level(r.q50, r.q90, t.alert[woy(d)], t.epidemic[woy(d)]), round(r.q10), round(r.q50), round(r.q90)])
    above = [i for i, (c, e) in enumerate(zip(cases, epi)) if c > e]
    peak = int(cases.values.argmax())
    flagged = [i for i, f in enumerate(fc) if f and f[0] in ("watch", "warning")]
    stats = {"crossed": QC_SEASON[above[0]].strftime("%Y-%m-%d"), "weeks_above": len(above), "peak": int(cases.iloc[peak]),
             "peak_week": QC_SEASON[peak].strftime("%Y-%m-%d"), "peak_epi": round(epi[peak]), "peak_fc": fc[peak][1:],
             "first_flag": (QC_SEASON[flagged[0]] - pd.Timedelta(weeks=HORIZON)).strftime("%Y-%m-%d"),
             "season_cases": int(cases.sum())}
    return {"weeks": [d.strftime("%Y-%m-%d") for d in QC_SEASON], "cases": [int(c) for c in cases],
            "epi": [round(e, 1) for e in epi], "fc": fc, "stats": stats}


def main() -> None:
    data = ROOT / "app" / "data"
    bt = pd.read_parquet(data / "province_backtest.parquet")
    hist = pd.read_parquet(data / "province_history.parquet")
    f = bt[(bt.horizon == HORIZON) & (bt.target_week - pd.Timedelta(weeks=HORIZON) == ORIGIN)].copy()
    f["woy"] = f.target_week.dt.isocalendar().week.astype(int).clip(upper=52)
    f = f.merge(thresholds(hist[hist.week < f"{ORIGIN.year}-01-01"]), on=["unit_id", "woy"], how="left")
    f["fc"] = [level(*r) for r in f[["q50", "q90", "alert", "epidemic"]].itertuples(index=False)]
    f["act"] = [level(a, a, al, ep) for a, al, ep in f[["actual", "alert", "epidemic"]].itertuples(index=False)]
    lv = f.set_index("unit_id")[["fc", "act"]].to_dict("index")

    geo = json.loads((data / "province.geojson").read_text())
    shapes = []
    for feat in geo["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        d = "".join(ring_path(poly[0]) for poly in polys)
        c = feat["properties"].get("centroid") or None
        info = lv.get(feat["id"], {"fc": "normal", "act": "normal"})
        xs = [p for poly in polys for p in poly[0]]
        cx, cy = xy(sum(p[0] for p in xs) / len(xs), sum(p[1] for p in xs) / len(xs))
        shapes.append({"id": feat["id"], "d": d, "fc": info["fc"], "act": info["act"], "cx": round(cx), "cy": round(cy)})
    crossed = f[f.act == "warning"]
    stats = {"crossed": int(len(crossed)), "flagged": int(crossed.fc.isin(["watch", "warning"]).sum())}
    out = ROOT / "docs" / "film" / "data.js"
    qc = qc_season(data)
    out.write_text(f"window.PH = {json.dumps(shapes, separators=(',', ':'))};\nwindow.STATS = {json.dumps(stats)};\n"
                   f"window.QC = {json.dumps(qc, separators=(',', ':'))};\n", newline="\n")
    print(out.relative_to(ROOT), f"{out.stat().st_size / 1e3:.0f} kB", stats, qc["stats"])


if __name__ == "__main__":
    main()
