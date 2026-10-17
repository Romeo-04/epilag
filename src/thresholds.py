"""Alert thresholds per unit and week of year (pandas only, so the in-browser app can import it).

From earlier years only (the caller passes the history it is allowed to see):
  alert     = mean of the same weeks (+-2) in earlier years      (cases above usual)
  epidemic  = mean + 2 SD of the same weeks in earlier years     (common surveillance rule)
"""
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
