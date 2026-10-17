"""Deck figures (SVG) from the committed reports and app data. Usage: python scripts/make_figures.py"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REP, APP, OUT = ROOT / "reports", ROOT / "app" / "data", ROOT / "docs" / "figures"
INK, MUTED, GRID, ACCENT, RED, AMBER = "#14211B", "#7E8C85", "#E2E8E4", "#12804A", "#D23B30", "#EE8A2A"

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"], "font.size": 13,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "axes.axisbelow": True, "svg.fonttype": "none",
})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    print("saved", name)


def national_weekly():
    h = pd.read_parquet(APP / "region_qc_history.parquet")
    h = h[h.unit_id.str.startswith("R_")].groupby("week").cases.sum()
    fig, ax = plt.subplots(figsize=(11, 4))
    for start in (h.index.min(), pd.Timestamp("2022-01-01")):
        seg = h[(h.index >= start) & (h.index < (pd.Timestamp("2020-01-01") if start.year < 2020 else h.index.max() + pd.Timedelta(days=1)))]
        ax.fill_between(seg.index, seg.values, color=ACCENT, alpha=0.18, lw=0)
        ax.plot(seg.index, seg.values, color=ACCENT, lw=1.8)
    ax.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2022-01-01"), color=GRID, alpha=0.6, lw=0)
    ax.text(pd.Timestamp("2021-01-01"), h.max() * 0.5, "no weekly\nregional data", ha="center", color=MUTED, fontsize=11)
    ax.annotate("2019 epidemic\n415,845 cases", xy=(pd.Timestamp("2019-08-01"), h["2019"].max()),
                xytext=(pd.Timestamp("2017-03-01"), h.max() * 0.9), color=INK, fontsize=12,
                arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.set_ylabel("Reported cases per week")
    ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    save(fig, "national_weekly")


def skill():
    rows = []
    for panel, label in (("province", "Provinces"), ("region_qc", "Regions + QC")):
        b = pd.read_csv(REP / f"backtest_{panel}.csv")
        b = b[b.horizon == 4]
        for r in b.itertuples():
            rows.append((f"{label}\n{r.test_year}", r.mae_epilag, r.mae_seasonal_naive, r.mae_persistence))
    d = pd.DataFrame(rows, columns=["set", "EpiLag", "Same week last year", "Same as this week"]).set_index("set")
    rel = d.div(d["Same week last year"], axis=0)  # error relative to the seasonal baseline
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = range(len(rel))
    w = 0.26
    for i, (col, color) in enumerate([("Same week last year", "#CBD2D9"), ("Same as this week", "#9AA5B1"), ("EpiLag", ACCENT)]):
        ax.bar([v + (i - 1) * w for v in x], rel[col], w, label=col, color=color)
    ax.set_xticks(list(x), rel.index, fontsize=11)
    ax.set_ylabel("Error, 4 weeks ahead\n(relative to 'same week last year')")
    ax.legend(frameon=False, ncol=3, loc="upper right")
    ax.set_ylim(0, 1.25)
    save(fig, "skill_h4")


def early_warning():
    rows = []
    for panel, label in (("province", "Provinces"), ("region_qc", "Regions + QC")):
        a = pd.read_csv(REP / f"alerts_{panel}.csv")
        a = a[a.horizon == 4]
        for year, g in a.groupby("test_year"):
            g = g.set_index("rule")
            rows.append((f"{label}\n{year}", g.loc["warn_upper", "share_warned"], g.loc["warn_upper", "false_alarm_share"],
                         g.loc["warn_median", "share_warned"], g.loc["warn_median", "false_alarm_share"],
                         int(g.loc["warn_upper", "onsets"])))
    d = pd.DataFrame(rows, columns=["set", "watch_hit", "watch_fa", "warn_hit", "warn_fa", "onsets"]).set_index("set")
    fig, ax = plt.subplots(figsize=(11, 4.4))
    x = list(range(len(d)))
    ax.bar([v - 0.2 for v in x], d.watch_hit, 0.38, color=AMBER, label="Watch: outbreak starts caught")
    ax.bar([v + 0.2 for v in x], d.warn_hit, 0.38, color=RED, label="Warning: outbreak starts caught")
    for v, hit in enumerate(d.watch_hit):
        ax.text(v - 0.2, hit + 0.02, f"{hit:.0%}", ha="center", fontsize=11, color=INK)
    ax.set_xticks(x, [f"{name}\n({n} starts)" for name, n in zip(d.index, d.onsets)], fontsize=11)
    ax.set_ylim(0, 1.12)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.28))
    ax.set_ylabel("Share warned 4 weeks ahead")
    save(fig, "early_warning_h4")


def weather_ablation():
    fig, ax = plt.subplots(figsize=(11, 4))
    for panel, label, color in (("province", "Provinces (rain, heat, humidity)", ACCENT), ("region_qc", "Regions + QC (rain)", AMBER)):
        a = pd.read_csv(REP / f"backtest_{panel}.csv").set_index(["test_year", "horizon"]).mae_epilag
        b = pd.read_csv(REP / f"backtest_{panel}_noweather.csv").set_index(["test_year", "horizon"]).mae_epilag
        gain = (1 - a / b).groupby("horizon").mean()
        ax.plot(gain.index, gain.values, marker="o", lw=2, color=color, label=label)
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks([2, 4, 6, 8])
    ax.set_xlabel("Weeks ahead")
    ax.set_ylabel("Error reduction from adding weather")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_ylim(-0.06, 0.06)
    ax.legend(frameon=False)
    save(fig, "weather_ablation")


def drivers():
    s = pd.read_csv(REP / "shap_province.csv")
    s = s[s.horizon == 4].copy()
    s["group"] = s.group.where(~s.group.str.startswith("rain "), "rain (weekly lags)")
    g = s.groupby("group").mean_abs_shap.sum().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.barh(g.index, g.values, color=[ACCENT if v == g.max() else "#9AA5B1" for v in g.values])
    ax.set_xlabel("Average influence on the 4-week forecast (mean |SHAP|)")
    ax.grid(axis="y", visible=False)
    save(fig, "drivers_province_h4")


if __name__ == "__main__":
    national_weekly()
    skill()
    early_warning()
    weather_ablation()
    drivers()
