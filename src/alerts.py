"""Alert levels and the early-warning test.

Thresholds (src/thresholds.py) come from earlier years only (no peeking at the test year).

Early-warning test on the backtest forecasts:
  An outbreak onset is the first week of a run of >= 2 weeks above the epidemic threshold.
  A forecast issued h weeks before the onset "warned" if its forecast for the onset week was
  above the threshold. We report how many onsets were warned, and how often warnings were false.

Usage: python src/alerts.py region_qc
"""
import sys

import numpy as np
import pandas as pd

from features import PROC
from backtest import REPORTS
from thresholds import thresholds

def onsets(actual: pd.DataFrame) -> pd.DataFrame:
    """First week of each run of >= 2 consecutive weeks above the epidemic threshold."""
    a = actual.sort_values(["unit_id", "week"]).copy()
    a["above"] = a.cases > a.epidemic
    g = a.groupby("unit_id").above
    a["start"] = a.above & ~g.shift(1, fill_value=False) & g.shift(-1, fill_value=False)
    return a[a.start][["unit_id", "week"]].rename(columns={"week": "onset_week"})


def evaluate(panel: str) -> pd.DataFrame:
    table = pd.read_parquet(PROC / f"model_table_{panel}.parquet")[["unit_id", "week", "cases"]]
    preds = pd.read_parquet(PROC / f"backtest_{panel}.parquet")
    results = []
    for year in sorted(preds.test_year.unique()):
        thr = thresholds(table[table.week < f"{year}-01-01"])
        actual = table[table.week.dt.year == year].copy()
        actual["woy"] = actual.week.dt.isocalendar().week.astype(int).clip(upper=52)
        actual = actual.merge(thr, on=["unit_id", "woy"], how="inner")
        events = onsets(actual)

        p = preds[preds.test_year == year].copy()
        p["woy"] = p.target_week.dt.isocalendar().week.astype(int).clip(upper=52)
        p = p.merge(thr, on=["unit_id", "woy"], how="inner")
        p["warn_median"] = p.q50 > p.epidemic
        p["warn_upper"] = p.q90 > p.epidemic  # "possible outbreak": upper end of the range
        p["truly_above"] = p.actual > p.epidemic

        for h, ph in p.groupby("horizon"):
            hit = events.merge(ph, left_on=["unit_id", "onset_week"], right_on=["unit_id", "target_week"])
            for rule in ("warn_median", "warn_upper"):
                warned = ph[ph[rule]]
                results.append({
                    "test_year": year, "horizon": h, "rule": rule, "onsets": len(events),
                    "onsets_warned": int(hit[rule].sum()),
                    "share_warned": hit[rule].mean() if len(hit) else np.nan,
                    "warnings": len(warned),
                    "false_alarm_share": 1 - warned.truly_above.mean() if len(warned) else np.nan,
                })
    return pd.DataFrame(results)


if __name__ == "__main__":
    panel = sys.argv[1]
    r = evaluate(panel)
    r.to_csv(REPORTS / f"alerts_{panel}.csv", index=False)
    print(r.round(2).to_string(index=False))
