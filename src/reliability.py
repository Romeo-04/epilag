"""Alert track record per area: how often its past watch / outbreak-warning alerts were right.

From the out-of-sample backtest forecasts at one horizon (pandas only, so the web app's JavaScript can mirror it;
see trackRecord() in site/src/app/logic.js and tests/test_web_logic.py):

  For each test year, thresholds come from the history before 1 January of that year (as src/alerts.py does).
  An alert week is a forecast at watch or outbreak warning (q50 or q90 above the epidemic line).
  It was right if the reported cases for that week were above the epidemic line.
  An outbreak onset is the first week of a run of >= 2 weeks above the line (src/alerts.py onsets());
  it was caught if the forecast for the onset week was an alert.

Reliability is the share of alert weeks that were right, graded high (>= 60%), medium (40-60%) or low (< 40%).
With fewer than MIN_ALERTS alert weeks there is too little history to grade.
"""
from __future__ import annotations

import pandas as pd

from thresholds import thresholds

MIN_ALERTS = 4
HIGH, MEDIUM = 0.6, 0.4


def grade(alert_weeks: int, right: int) -> str:
    if alert_weeks < MIN_ALERTS:
        return "too few"
    share = right / alert_weeks
    return "high" if share >= HIGH else "medium" if share >= MEDIUM else "low"


def track_record(history: pd.DataFrame, backtest: pd.DataFrame, horizon: int = 4,
                 before_year: int | None = None) -> pd.DataFrame:
    """history: unit_id, week, cases; backtest: unit_id, target_week, horizon, test_year, actual, q50, q90.
    Only test years before `before_year` count (a replay must not use what came after it).
    Returns one row per unit: alert_weeks, alert_weeks_right, onsets, onsets_caught, reliability, grade, years."""
    b = backtest[backtest.horizon == horizon]
    if before_year is not None:
        b = b[b.test_year < before_year]
    rows = []
    for year in sorted(b.test_year.unique()):
        thr = thresholds(history[history.week < f"{year}-01-01"])
        p = b[b.test_year == year].copy()
        p["woy"] = p.target_week.dt.isocalendar().week.astype(int).clip(upper=52)
        p = p.merge(thr, on=["unit_id", "woy"], how="inner")
        p["alert"] = (p.q50 > p.epidemic) | (p.q90 > p.epidemic)
        p["right"] = p.alert & (p.actual > p.epidemic)

        a = history[history.week.dt.year == year].dropna(subset=["cases"]).copy()
        a["woy"] = a.week.dt.isocalendar().week.astype(int).clip(upper=52)
        a = a.merge(thr, on=["unit_id", "woy"], how="inner").sort_values(["unit_id", "week"])
        a["above"] = a.cases > a.epidemic
        g = a.groupby("unit_id").above
        a["start"] = a.above & ~g.shift(1, fill_value=False) & g.shift(-1, fill_value=False)
        ons = a[a.start][["unit_id", "week"]].merge(p[["unit_id", "target_week", "alert"]],
                                                    left_on=["unit_id", "week"], right_on=["unit_id", "target_week"])
        for u, pu in p.groupby("unit_id"):
            ou = ons[ons.unit_id == u]
            rows.append({"unit_id": u, "test_year": year, "alert_weeks": int(pu.alert.sum()),
                         "alert_weeks_right": int(pu.right.sum()), "onsets": len(ou), "onsets_caught": int(ou.alert.sum())})
    cols = ["alert_weeks", "alert_weeks_right", "onsets", "onsets_caught"]
    if not rows:
        return pd.DataFrame(columns=["unit_id", *cols, "reliability", "grade", "years"])
    df = pd.DataFrame(rows)
    out = df.groupby("unit_id")[cols].sum().reset_index()
    out["years"] = df.groupby("unit_id").test_year.apply(lambda s: ",".join(map(str, sorted(s)))).values
    out["reliability"] = (out.alert_weeks_right / out.alert_weeks).where(out.alert_weeks > 0)
    out["grade"] = [grade(n, r) for n, r in zip(out.alert_weeks, out.alert_weeks_right)]
    return out
