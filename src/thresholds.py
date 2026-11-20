"""Alert thresholds per unit and week of year (pandas only, so the in-browser app can import it).

From earlier years only (the caller passes the history it is allowed to see):
  alert     = mean of the same weeks (+-2) in earlier years      (cases above usual)
  epidemic  = mean + 2 SD of the same weeks in earlier years     (common surveillance rule)
"""
import numpy as np
import pandas as pd

WINDOW = 2  # +-weeks around the week of year


def thresholds(history: pd.DataFrame) -> pd.DataFrame:
    """history: unit_id, week, cases -> unit_id, woy, alert, epidemic, count."""
    h = history.dropna(subset=["cases"]).assign(woy=lambda d: d.week.dt.isocalendar().week.astype(int).clip(upper=52))
    rows = [h.assign(woy=((h.woy - 1 + shift) % 52) + 1) for shift in range(-WINDOW, WINDOW + 1)]
    s = pd.concat(rows).groupby(["unit_id", "woy"]).cases.agg(["mean", "std", "count"]).reset_index()
    s["alert"] = s["mean"]
    s["epidemic"] = s["mean"] + 2 * s["std"].fillna(0)
    return s[["unit_id", "woy", "alert", "epidemic", "count"]]


def line_share(cases, alert, epidemic):
    """Where a weekly count sits between its area's usual level (0) and its epidemic line (1) for that week of year.

    Compares each area with its own past, so population, how much dengue it usually has, the season and how completely
    it reports all cancel out. The gap is at least the Poisson spread (2 x sqrt(usual), and 2 cases), so an area with
    a flat history does not swing wildly. The web app's "Rising toward an outbreak" list ranks areas on this.
    """
    gap = np.maximum(np.asarray(epidemic, float) - alert, 2 * np.sqrt(np.maximum(np.asarray(alert, float), 1)))
    return (np.asarray(cases, float) - alert) / gap
