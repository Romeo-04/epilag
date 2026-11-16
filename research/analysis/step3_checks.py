"""Step 3 checks: numbers for the five findings in causes.md.

Inputs, all in the repo (data/processed/ is not needed):
  site/public/web/data/{panel}_history.json   weekly reported cases per area (built by scripts/build_web.py)
  site/public/web/data/{panel}_backtest.json  out-of-sample 4-week forecasts q10/q50/q90, calibrated
  reports/backtest_{panel}.csv, reports/backtest_{panel}_noweather.csv
  research/results/model_comparison.csv, research/results/shap_groups.csv, research/results/feature_groups.csv
Outputs: research/analysis/out/*.csv and research/analysis/figures/*.png

Run: python research/analysis/step3_checks.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "site" / "public" / "web" / "data"
OUT = Path(__file__).with_name("out")
FIG = Path(__file__).with_name("figures")
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)
WEATHER_GROUPS = ["rain", "heat", "humidity"]


def load(panel: str, kind: str) -> pd.DataFrame:
    d = json.load(open(WEB / f"{panel}_{kind}.json"))
    units = json.load(open(WEB / "meta.json"))["panels"][panel]["units"]
    df = pd.DataFrame(d["cols"])
    df["unit_id"] = df.u.map(dict(enumerate(units)))
    for c in ("week", "target_week"):
        if c in df:
            df[c] = pd.to_datetime(df[c], unit="D")
    return df


def with_persistence(bt: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
    h = hist.set_index(["unit_id", "week"]).cases
    key = list(zip(bt.unit_id, bt.target_week - pd.to_timedelta(7 * bt.horizon, unit="D")))
    bt = bt.assign(persistence=h.reindex(key).values)
    key52 = list(zip(bt.unit_id, bt.target_week - pd.Timedelta(weeks=52)))
    return bt.assign(seasonal_naive=h.reindex(key52).values)


def finding1(hist: pd.DataFrame, bt: pd.DataFrame) -> pd.DataFrame:
    """Regions + QC: was 2023 a flat year, and how unusual was the calibration year (2022)?"""
    s = bt[bt.horizon == 4].dropna(subset=["actual", "persistence", "seasonal_naive"])
    by_year = s.groupby("test_year").apply(lambda g: pd.Series({
        "n": len(g),
        "mae_lightgbm": (g.q50 - g.actual).abs().mean(),
        "mae_persistence": (g.persistence - g.actual).abs().mean(),
        "coverage_10_90": ((g.actual >= g.q10) & (g.actual <= g.q90)).mean(),
        "median_range_width_ratio": (np.log1p(g.q90) - np.log1p(g.q10)).median(),
    }), include_groups=False)

    h = hist.copy()
    h["year"] = h.week.dt.year
    h["y"] = np.log1p(h.cases)
    h = h.sort_values(["unit_id", "week"])
    h["dy4"] = h.groupby("unit_id").y.diff(4)  # 4-week change in log cases
    yr = h.groupby(["unit_id", "year"]).agg(total=("cases", "sum"), weeks=("cases", "count"),
                                           peak=("cases", "max"), mean=("cases", "mean"),
                                           sd_dy4=("dy4", "std")).reset_index()
    yr["peak_to_mean"] = yr.peak / yr["mean"]
    regions = yr[yr.unit_id.str.startswith("R_")]
    shape = regions.groupby("year").agg(units=("unit_id", "nunique"), total=("total", "sum"),
                                        median_peak_to_mean=("peak_to_mean", "median"),
                                        median_sd_4wk_change=("sd_dy4", "median"),
                                        median_weeks=("weeks", "median"))
    # How far each year's level sits from the mean of all earlier years (per area, log scale).
    lvl = regions.assign(lt=np.log1p(regions["mean"])).pivot(index="year", columns="unit_id", values="lt")
    shift = {y: float((lvl.loc[y] - lvl.loc[lvl.index < y].mean()).abs().median())
             for y in lvl.index if (lvl.index < y).sum() >= 2}
    shape["median_abs_level_shift_vs_earlier_years"] = pd.Series(shift)
    by_year.to_csv(OUT / "f1_region_qc_h4_by_year.csv")
    shape.to_csv(OUT / "f1_region_year_shape.csv")

    fig, ax = plt.subplots(figsize=(8, 3.6))
    nat = hist[hist.unit_id.str.startswith("R_")].groupby("week").cases.sum()
    ax.plot(nat.index, nat.values, lw=1, color="#3b6ea5")
    for y in (2022, 2023):
        ax.axvspan(pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31"), alpha=.12,
                   color="#c0504d" if y == 2022 else "#9bbb59")
    ax.set_title("Weekly cases, 17 regions summed (2022 = calibration year, 2023 = test year)", fontsize=9)
    ax.set_ylabel("cases per week")
    fig.tight_layout()
    fig.savefig(FIG / "f1_regions_weekly_total.png", dpi=150)
    plt.close(fig)
    return by_year, shape


def finding2(hist: pd.DataFrame) -> pd.DataFrame:
    """Provinces: national totals 2016-2020 and how much 2020 fell from 2019, by week."""
    h = hist.assign(year=hist.week.dt.year)
    tot = h.groupby("year").cases.sum().rename("national_total").to_frame()
    tot["weeks"] = h.groupby("year").week.nunique()
    per_unit = h[h.year.isin([2019, 2020])].groupby(["unit_id", "year"]).cases.sum().unstack()
    tot.loc[2020, "provinces_lower_than_2019"] = int((per_unit[2020] < per_unit[2019]).sum())
    tot.loc[2020, "provinces"] = len(per_unit)
    tot.to_csv(OUT / "f2_province_national_totals.csv")

    # When did 2020 fall? Weekly national total against the 2016-2018 mean for the same week of year.
    h["woy"] = h.week.dt.isocalendar().week.astype(int)
    base = h[h.year.isin([2016, 2017, 2018])].groupby("woy").cases.sum() / 3
    ratio = (h[h.year == 2020].groupby("woy").cases.sum() / base).rename("ratio_2020_to_2016_18")
    ratio.to_frame().to_csv(OUT / "f2_2020_weekly_ratio.csv")

    wk = h.groupby("week").cases.sum()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for y, c in ((2019, "#c0504d"), (2020, "#3b6ea5"), (2018, "#999999")):
        s = wk[wk.index.year == y]
        ax.plot(s.index.isocalendar().week.values, s.values, label=str(y), color=c, lw=1.4)
    ax.set_xlabel("week of year")
    ax.set_ylabel("cases per week, 86 provinces")
    ax.set_title("'Same week last year' for 2020 copies the 2019 curve", fontsize=9)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "f2_province_2019_vs_2020.png", dpi=150)
    plt.close(fig)
    return tot


def finding3_4() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Weather gain by lead time and by year (live model, with vs without weather), plus SHAP weather share."""
    rows = []
    for panel in ("province", "region_qc"):
        w = pd.read_csv(ROOT / f"reports/backtest_{panel}.csv")
        nw = pd.read_csv(ROOT / f"reports/backtest_{panel}_noweather.csv")
        m = w.merge(nw, on=["test_year", "horizon"], suffixes=("", "_nw"))
        m["panel"] = panel
        m["weather_change_pct"] = 100 * (m.mae_epilag / m.mae_epilag_nw - 1)  # negative = weather helped
        rows.append(m[["panel", "test_year", "horizon", "mae_epilag", "mae_epilag_nw", "weather_change_pct"]])
    gain = pd.concat(rows)
    sg = pd.read_csv(ROOT / "research/results/shap_groups.csv")
    share = (sg[sg.group.isin(WEATHER_GROUPS)].groupby(["panel", "feature_set", "horizon"]).share.sum()
             .rename("weather_share").reset_index())
    by_h = gain.groupby(["panel", "horizon"]).weather_change_pct.agg(["median", "mean", "min", "max"]).reset_index()
    by_h = by_h.merge(share[share.feature_set == "current"].drop(columns="feature_set"), on=["panel", "horizon"])
    fg = pd.read_csv(ROOT / "research/results/feature_groups.csv")
    add = (fg[(fg["mode"] == "add") & fg.group.isin(WEATHER_GROUPS)]
           .groupby(["panel", "horizon", "group"]).change_pct.median().unstack().add_prefix("add_median_pct_"))
    by_h = by_h.merge(add.reset_index(), on=["panel", "horizon"], how="left")
    gain.to_csv(OUT / "f3_f4_weather_gain.csv", index=False)
    by_h.to_csv(OUT / "f3_weather_by_horizon.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.4))
    for ax, panel in zip(axes, ("region_qc", "province")):
        g = gain[gain.panel == panel]
        for y, s in g.groupby("test_year"):
            ax.plot(s.horizon, s.weather_change_pct, marker="o", label=str(y))
        ax.axhline(0, color="k", lw=.6)
        ax.set_title({"region_qc": "Regions + QC", "province": "Provinces"}[panel], fontsize=9)
        ax.set_xlabel("weeks ahead")
        ax.set_xticks([2, 4, 6, 8])
    axes[0].set_ylabel("error change from weather, % (below 0 = helped)")
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "f3_weather_gain_by_horizon.png", dpi=150)
    plt.close(fig)
    return gain, by_h


def season_departure(hist: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Finding 4 proxy: how far a year's case curve departs from its usual seasonal shape.
    Per area: correlation between the year's weekly log cases and the mean of earlier years by week of year."""
    h = hist.assign(year=hist.week.dt.year, woy=hist.week.dt.isocalendar().week.clip(upper=52).astype(int),
                    y=np.log1p(hist.cases))
    out = []
    for y in years:
        for u, g in h.groupby("unit_id"):
            past = g[g.year < y].groupby("woy").y.mean()
            now = g[g.year == y].groupby("woy").y.mean()
            j = pd.concat([now, past], axis=1, keys=["now", "past"]).dropna()
            if len(j) >= 40 and (g.year < y).any():
                out.append({"test_year": y, "unit_id": u, "season_corr": j.now.corr(j.past)})
    d = pd.DataFrame(out)
    return d.groupby("test_year").season_corr.median().rename("median_season_corr").reset_index()


def finding5() -> pd.DataFrame:
    mc = pd.read_csv(ROOT / "research/results/model_comparison.csv")
    m = mc.dropna(subset=["coverage_raw"])
    t = m.pivot_table(index=["panel", "test_year", "horizon"], columns="model",
                      values=["coverage_raw", "coverage_10_90"]).round(3)
    t.to_csv(OUT / "f5_coverage_raw_vs_calibrated.csv")

    fig, ax = plt.subplots(figsize=(7, 3.6))
    models = ["lightgbm", "negbin", "random_forest", "sarimax"]
    for i, model in enumerate(models):
        g = m[m.model == model]
        ax.scatter(np.full(len(g), i) - .12, g.coverage_raw, s=12, color="#c0504d", label="before" if i == 0 else None)
        ax.scatter(np.full(len(g), i) + .12, g.coverage_10_90, s=12, color="#3b6ea5", label="after" if i == 0 else None)
    ax.axhline(.8, color="k", lw=.6, ls="--")
    ax.set_xticks(range(len(models)), models)
    ax.set_ylabel("share of real weeks inside 10-90% range")
    ax.set_title("Range coverage before and after calibration (target 80%), 24 checks per model", fontsize=9)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "f5_coverage_before_after.png", dpi=150)
    plt.close(fig)
    return m.groupby(["model"]).agg(raw_min=("coverage_raw", "min"), raw_max=("coverage_raw", "max"),
                                    raw_median=("coverage_raw", "median"),
                                    cal_min=("coverage_10_90", "min"), cal_max=("coverage_10_90", "max"),
                                    cal_median=("coverage_10_90", "median"))


EXTRACTS = ROOT / "research" / "results" / "extracts"


def finding1_margins() -> pd.DataFrame:
    """Calibration margin and coverage per test year (research/results/extracts/calibration.csv)."""
    c = pd.read_csv(EXTRACTS / "calibration.csv")
    c.to_csv(OUT / "f1_calibration_margins.csv", index=False)
    return c.pivot(index=["panel", "test_year"], columns="horizon", values="margin")


def finding4_rain(gain: pd.DataFrame) -> pd.DataFrame:
    """Each Regions + QC year's rain anomaly (median over areas) against the gain from weather."""
    r = pd.read_csv(EXTRACTS / "rain_by_year.csv")
    r = r[r.panel == "region_qc"]
    anom = r.groupby("year").agg(
        rain_total_vs_other_years_pct=("rain_total_vs_other_years_pct", "median"),
        wet_season_vs_other_years_pct=("rain_wet_season_vs_other_years_pct", "median"),
        abs_wet_season_pct=("rain_wet_season_vs_other_years_pct", lambda s: s.abs().median()))
    g = gain[gain.panel == "region_qc"].pivot(index="test_year", columns="horizon", values="weather_change_pct")
    g.columns = [f"weather_change_h{h}" for h in g.columns]
    out = anom.join(g, how="inner")
    out.index.name = "test_year"
    out.to_csv(OUT / "f4_rain_anomaly_vs_weather_gain.csv")
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    rh, rb = load("region_qc", "history"), load("region_qc", "backtest")
    ph = load("province", "history")
    rb = with_persistence(rb, rh)
    print("Backtest JSON horizons:", sorted(rb.horizon.unique()))
    f1, shape = finding1(rh, rb)
    print("\nF1 Regions+QC, 4 weeks ahead, by test year (should match reports/backtest_region_qc.csv)\n", f1.round(3))
    print("\nF1 shape of each year, 17 regions\n", shape.round(3))
    print("\nF2 province national totals\n", finding2(ph))
    gain, by_h = finding3_4()
    print("\nF3 weather effect by lead time (% change in error; negative = weather helped) and SHAP weather share\n",
          by_h.round(3))
    print("\nF4 weather effect by year, Regions+QC\n",
          gain[gain.panel == "region_qc"].pivot(index="test_year", columns="horizon", values="weather_change_pct").round(1))
    sd = season_departure(rh[rh.unit_id.str.startswith("R_") | (rh.unit_id == "QC")], [2019, 2023, 2024, 2025])
    sd.to_csv(OUT / "f4_season_departure.csv", index=False)
    print("\nF4 proxy: median correlation of each year's curve with the usual season (lower = more unusual)\n", sd.round(3))
    print("\nF1 calibration margin (log scale) by test year and lead time\n", finding1_margins().round(3))
    print("\nF4 rain anomaly (median over areas, %) against weather gain (%)\n", finding4_rain(gain).round(1))
    print("\nF5 coverage before (raw) and after calibration, across panels, years and lead times\n", finding5().round(3))
