"""Proposed variables from the literature review (research/lit/feature_evidence.csv, status "proposed"), tested like the others.

neighbours  Dengue in the nearest areas (buczak2014; travelling waves, vanpanhuis2015). The k nearest
            areas by distance between centres (k = 4 for provinces, 3 for Regions + QC). Their pooled
            incidence this week (log cases per 100,000), its 4-week mean, and its 3-week change.
            Known at forecast time, like the area's own cases. Quezon City's nearest area is NCR,
            which contains it.
heatwave    Heatwave days (ith2025): days in a run of 2 or more with maximum temperature above the
            area's own 95th percentile. Counted over the last 4 weeks, and 4 and 8 weeks earlier
            (ith2025 found the effect after about 2 months).
drought     A rain anomaly standing in for ith2025's drought index (scPDSI is not available per area):
            the 12-week rain total as a z-score against the same time of year (within 4 weeks) in
            the area's own past (spread floored at a quarter of the area's overall spread). Now and
            8 weeks earlier. Negative = drier than usual.

Thresholds and baselines use data before 2019, the first test year, so no test year informs them.
Each group is added to cases + season ("add_to_base", reference: feature_groups.csv base) and to the
full research set ("add_to_plus", reference: its full rows). LightGBM, same harness.

Writes research/results/proposed_features.csv.
Usage: python research/models/proposed_features.py [province|region_qc ...]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extra_features import PROC, fetch_region_weather, group_of, province_daily, region_points  # noqa: E402
from harness import RESULTS, run, score, upsert  # noqa: E402
from influence import BASE, load  # noqa: E402
from models import lightgbm  # noqa: E402

CUTOFF = pd.Timestamp("2019-01-01")


def centres(panel: str) -> pd.DataFrame:
    if panel == "province":
        return pd.read_csv(PROC / "units.csv")[["unit_id", "center_lat", "center_lon"]].set_axis(["unit_id", "lat", "lon"], axis=1)
    return region_points()[["unit_id", "lat", "lon"]]


def neighbours(table: pd.DataFrame, panel: str) -> pd.DataFrame:
    k = 4 if panel == "province" else 3
    c = centres(panel).set_index("unit_id").loc[table.unit_id.unique()]
    lat, lon = np.radians(c.lat.values), np.radians(c.lon.values)
    d = np.arccos(np.clip(np.sin(lat[:, None]) * np.sin(lat) + np.cos(lat[:, None]) * np.cos(lat) * np.cos(lon[:, None] - lon), -1, 1))
    np.fill_diagonal(d, np.inf)
    nb = {u: list(c.index[np.argsort(row)[:k]]) for u, row in zip(c.index, d)}
    obs = table[["unit_id", "week", "cases", "population"]].dropna()
    pairs = pd.DataFrame([(u, v) for u, vs in nb.items() for v in vs], columns=["unit_id", "nb"])
    m = pairs.merge(obs.rename(columns={"unit_id": "nb"}), on="nb").groupby(["unit_id", "week"])[["cases", "population"]].sum()
    out = table[["unit_id", "week"]].merge(np.log1p(1e5 * m.cases / m.population).rename("nb_inc_log").reset_index(),
                                           on=["unit_id", "week"], how="left")
    g = out.groupby("unit_id").nb_inc_log
    out["nb_inc_log_mean4"] = g.transform(lambda s: s.rolling(4, min_periods=2).mean())
    out["nb_growth"] = out.nb_inc_log - g.shift(3)
    return out


def heatwaves(panel: str) -> pd.DataFrame:
    daily = province_daily() if panel == "province" else fetch_region_weather()
    daily = daily.sort_values(["unit_id", "date"])
    p95 = daily[daily.date < CUTOFF].groupby("unit_id").tmax.quantile(0.95)
    hot = daily.tmax > daily.unit_id.map(p95)
    run_id = (hot != hot.groupby(daily.unit_id).shift()).cumsum()
    run_len = hot.groupby(run_id).transform("size")
    daily = daily.assign(wave=hot & (run_len >= 2))
    wk = daily.set_index("date").groupby("unit_id").wave.resample("W-SUN").sum().rename("wave_days").reset_index()
    wk = wk.rename(columns={"date": "week"})
    g = wk.groupby("unit_id").wave_days
    wk["heat_wave4"] = g.transform(lambda s: s.rolling(4, min_periods=4).sum())
    g = wk.groupby("unit_id").heat_wave4
    wk["heat_wave4_lag4"], wk["heat_wave4_lag8"] = g.shift(4), g.shift(8)
    return wk.drop(columns="wave_days")


def rain_anomaly(table: pd.DataFrame) -> pd.DataFrame:
    t = table[["unit_id", "week", "rain_sum12"]].copy()
    t["woy"] = t.week.dt.isocalendar().week.astype(int).clip(upper=52)
    base = t[(t.week < CUTOFF) & t.rain_sum12.notna()]
    rows = []
    for u, b in base.groupby("unit_id"):
        for w in range(1, 53):
            dist = np.minimum(abs(b.woy - w), 52 - abs(b.woy - w))
            x = b.rain_sum12[dist <= 4]
            rows.append((u, w, x.mean(), x.std()))
    ref = pd.DataFrame(rows, columns=["unit_id", "woy", "mu", "sd"])
    # A dry-season window with almost no spread would blow the z-score up: floor the spread at a quarter
    # of the area's overall spread.
    ref["sd"] = np.maximum(ref.sd, 0.25 * ref.unit_id.map(base.groupby("unit_id").rain_sum12.std()))
    t = t.merge(ref, on=["unit_id", "woy"], how="left")
    t["rain_anom12"] = (t.rain_sum12 - t.mu) / t.sd
    t["rain_anom12_lag8"] = t.groupby("unit_id").rain_anom12.shift(8)
    return t[["unit_id", "week", "rain_anom12", "rain_anom12_lag8"]]


def extend(panel: str) -> tuple[pd.DataFrame, list[str], dict[str, list[str]]]:
    table, plus = load(panel)
    table = (table.merge(neighbours(table, panel), on=["unit_id", "week"], how="left")
             .merge(heatwaves(panel), on=["unit_id", "week"], how="left")
             .merge(rain_anomaly(table), on=["unit_id", "week"], how="left")
             .sort_values(["unit_id", "week"]).reset_index(drop=True))
    new = {"neighbours": ["nb_inc_log", "nb_inc_log_mean4", "nb_growth"],
           "heatwave": ["heat_wave4", "heat_wave4_lag4", "heat_wave4_lag8"],
           "drought": ["rain_anom12", "rain_anom12_lag8"]}
    return table, plus, new


def with_reference(s: pd.DataFrame) -> pd.DataFrame:
    """Reference error: the base (cases + season) or full research-set rows of feature_groups.csv."""
    fg = pd.read_csv(RESULTS / "feature_groups.csv")
    ref = {(p, m, y, h): v for p, m, y, h, v in fg[["panel", "mode", "test_year", "horizon", "mae"]].itertuples(index=False)
           if m in ("base", "full")}
    to = {"add_to_base": "base", "add_to_plus": "full"}
    s["mae_reference"] = [ref[(p, to[m], y, h)] for p, m, y, h in zip(s.panel, s["mode"], s.test_year, s.horizon)]
    s["change_pct"] = (s.mae / s.mae_reference - 1) * 100
    return s


def test(panel: str) -> pd.DataFrame:
    table, plus, new = extend(panel)
    usable = table.target_h4.notna() & table.y_lag0.notna()
    print(panel, "missing share (usable rows):", table.loc[usable, sum(new.values(), [])].isna().mean().round(3).to_dict(), flush=True)
    base = [f for f in plus if group_of(f) in BASE]
    scored = []
    for group, fs in new.items():
        for mode, start in (("add_to_base", base), ("add_to_plus", plus)):
            print(f"{panel} {mode} {group}", flush=True)
            s = score(run(panel, lightgbm, features=start + fs, table=table), panel, "lightgbm")
            scored.append(s.assign(mode=mode, group=group, n_features=len(start + fs)))
    s = with_reference(pd.concat(scored, ignore_index=True))
    cols = ["panel", "test_year", "horizon", "mode", "group", "n_features", "mae", "mae_reference", "change_pct",
            "coverage_10_90", "caught_watch", "false_share_watch", "onsets"]
    return upsert(RESULTS / "proposed_features.csv", s[cols], ["panel", "mode", "group", "test_year", "horizon"])


if __name__ == "__main__":
    for panel in sys.argv[1:] or ["region_qc", "province"]:
        out = test(panel)
        out = out[out.panel == panel]
        print(out.pivot_table(index=["mode", "group"], columns=["test_year", "horizon"], values="change_pct").round(1).to_string(), flush=True)
