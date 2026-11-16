"""Every number on the Research page (site/research.html), recomputed from the committed result files.

The page is static HTML. Each number on it that comes from the research sits in an element with a `data-k` key;
numbers() returns the text each key must show, straight from research/results/ and research/analysis/out/.
tests/test_research_page.py compares the two, so the page cannot drift from the results.
Usage: python scripts/research_numbers.py     (prints every key and its value)
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS, ANALYSIS = ROOT / "research" / "results", ROOT / "research" / "analysis" / "out"
FOUR = ["lightgbm", "negbin", "random_forest", "sarimax"]
SETS = [("province", 2019), ("province", 2020), ("region_qc", 2019), ("region_qc", 2023), ("region_qc", 2024), ("region_qc", 2025)]
CHECK = ["panel", "test_year", "horizon"]


def signed(x: float, digits: int = 1) -> str:
    """A change in percent with a true minus sign: −2.2%, +0.5%, 0.0%."""
    v = round(x, digits)
    return f"{'−' if v < 0 else '+' if v > 0 else ''}{abs(v):.{digits}f}%"


def pct(x: float) -> str:
    """A share as a whole percent, halves rounded up (as the write-up rounds them)."""
    return f"{int(x * 100 + 0.5 + 1e-9)}%"


def numbers() -> dict[str, str]:
    n: dict[str, str] = {}
    mc = pd.read_csv(RESULTS / "model_comparison.csv")

    # four methods on the same test: lowest error of the four, per check (6 test sets x 4 lead times)
    four = mc[mc.model.isin(FOUR)]
    wins = four.loc[four.groupby(CHECK).mae.idxmin()].model.value_counts()
    five = mc[mc.model.isin(FOUR + ["blend_all4"])]
    n["blend-lowest"] = str((five.loc[five.groupby(CHECK).mae.idxmin()].model == "blend_all4").sum())
    pooled = mc.groupby("model")[["caught_watch", "caught_warning", "onsets"]].sum()
    for m in FOUR + ["blend_all4"]:
        if m in FOUR:
            n[f"wins-{m}"] = str(int(wins.get(m, 0)))
        n[f"beat-{m}"] = str(int((mc[mc.model == m].rel_mae_vs_persistence < 1).sum()))
        n[f"watch-{m}"] = pct(pooled.caught_watch[m] / pooled.onsets[m])
        n[f"warn-{m}"] = pct(pooled.caught_warning[m] / pooled.onsets[m])
        n[f"watch-n-{m}"] = f"{int(pooled.caught_watch[m]):,}"
        n[f"warn-n-{m}"] = f"{int(pooled.caught_warning[m]):,}"

    # 4 weeks ahead: each method's error as a share of "same as this week", and LightGBM's range before and after
    h4 = mc[mc.horizon == 4].set_index(["panel", "test_year", "model"])
    for panel, year in SETS:
        for m in FOUR + ["blend_all4"]:
            n[f"rel-{panel}-{year}-{m}"] = str(round(h4.rel_mae_vs_persistence[(panel, year, m)] * 100))
        n[f"cov-raw-{panel}-{year}"] = pct(h4.coverage_raw[(panel, year, "lightgbm")])
        n[f"cov-cal-{panel}-{year}"] = pct(h4.coverage_10_90[(panel, year, "lightgbm")])

    # where the submitted model lost to "same as this week"
    lgb = mc[mc.model == "lightgbm"].set_index(CHECK).rel_mae_vs_persistence
    n["lost-2019-2wk"] = pct(lgb[("region_qc", 2019, 2)] - 1)
    n["lost-2023-4wk"] = pct(lgb[("region_qc", 2023, 4)] - 1)
    shape = pd.read_csv(ANALYSIS / "f1_region_year_shape.csv").set_index("year")
    n["peak-to-mean-2023"] = f"{shape.median_peak_to_mean[2023]:.2f}"
    cal = pd.read_csv(RESULTS / "extracts" / "calibration.csv")
    cal = cal[(cal.panel == "region_qc") & (cal.horizon == 4)].set_index("test_year").margin
    for year in (2019, 2023, 2024, 2025):
        n[f"margin-{year}"] = f"{cal[year]:.3f}"

    # weather, Regions + QC, by weeks ahead: its share of SHAP attention and the effect of adding heat
    wx = pd.read_csv(ANALYSIS / "f3_weather_by_horizon.csv")
    wx = wx[wx.panel == "region_qc"].set_index("horizon")
    for h in (2, 4, 6, 8):
        n[f"wx-share-{h}"] = pct(wx.weather_share[h])
        n[f"heat-{h}"] = signed(wx.add_median_pct_heat[h])
    sg = pd.read_csv(RESULTS / "shap_groups.csv")
    cases = sg[(sg.group == "cases") & (sg.feature_set == "plus")].share
    n["cases-share"] = f"{round(cases.min() * 100)}–{round(cases.max() * 100)}%"

    # variable groups: checks where adding the group to cases + season cut the error
    fg = pd.read_csv(RESULTS / "feature_groups.csv")
    add = fg[fg["mode"] == "add"]
    for (panel, group), g in add.groupby(["panel", "group"]):
        n[f"add-{panel}-{group}"] = f"{int((g.change_pct < 0).sum())} of {len(g)}"
    enso = fg[(fg["mode"] == "drop") & (fg.panel == "province") & (fg.group == "enso")]
    n["enso-helped-province"] = f"{int((enso.change_pct > 0).sum())} of {len(enso)}"  # removing it made things worse = it helped
    pf = pd.read_csv(RESULTS / "proposed_features.csv")
    nb = pf[(pf["mode"] == "add_to_plus") & (pf.group == "neighbours")]
    for panel, g in nb.groupby("panel"):
        n[f"neighbours-{panel}"] = f"{int((g.change_pct < 0).sum())} of {len(g)}"
        n[f"neighbours-median-{panel}"] = signed(g.change_pct.median())

    # the variables the research chose, against the submitted model
    c = pd.read_csv(RESULTS / "candidates.csv")
    live = c[c.model == "live"].set_index(CHECK)
    final = pd.concat([c[(c.panel == "province") & (c.model == "live_neighbours")],
                       c[(c.panel == "region_qc") & (c.model == "research_no_enso")]]).set_index(CHECK)
    change = (final.mae / live.mae.reindex(final.index) - 1) * 100
    for (panel, year, h), v in change.items():
        n[f"final-{panel}-{year}-{h}"] = signed(v)
    n["final-better"] = str(int((change < 0).sum()))
    n["final-median"] = signed(change.median())
    n["final-beat"], n["live-beat"] = (str(int((d.rel_mae_vs_persistence < 1).sum())) for d in (final, live))
    n["final-watch"], n["live-watch"] = (f"{int(d.caught_watch.sum()):,}" for d in (final, live))
    n["final-warn"], n["live-warn"] = (f"{int(d.caught_warning.sum()):,}" for d in (final, live))
    n["starts"] = f"{int(live.onsets.sum()):,}"

    n["studies"] = str(len(pd.read_csv(ROOT / "research" / "lit" / "rrl_matrix.csv")))
    return n


if __name__ == "__main__":
    for k, v in numbers().items():
        print(f"{k:34s} {v}")
