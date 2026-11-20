"""The promotion gate: a retrained model replaces the live one only if it still earns its place.

Reads the out-of-sample backtests in reports/ (written by src/backtest.py) and checks, for the most recent test
year of each panel, 4 weeks ahead:

  1. its error is lower than "same week last year" (seasonal naive);
  2. its error is no more than 5% above "same as this week" (persistence);
  3. its 10-90% range covers between 70% and 90% of real values (target 80%).

    python scripts/model_gate.py        # exits 1 if any panel fails, so a scheduled retrain stops

A failing gate keeps the last good forecasts online and tells the maintainers, instead of publishing a model that
has drifted. Rule 2 allows 5% because a quiet year can favour persistence (regions and Quezon City, 2023: 4%).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HORIZON = 4
PERSISTENCE_SLACK = 1.05
COVERAGE = (0.70, 0.90)


def check(panel: str, reports: Path = ROOT / "reports") -> list[tuple[str, bool, str]]:
    bt = pd.read_csv(reports / f"backtest_{panel}.csv")
    row = bt[bt.horizon == HORIZON].sort_values("test_year").iloc[-1]
    year = int(row.test_year)
    return [
        (f"{panel} {year}: beats same week last year", row.mae_epilag < row.mae_seasonal_naive,
         f"error {row.mae_epilag:.1f} vs {row.mae_seasonal_naive:.1f}"),
        (f"{panel} {year}: within 5% of same as this week", row.mae_epilag <= PERSISTENCE_SLACK * row.mae_persistence,
         f"error {row.mae_epilag:.1f} vs {row.mae_persistence:.1f}"),
        (f"{panel} {year}: range coverage 70-90%", COVERAGE[0] <= row.coverage_10_90 <= COVERAGE[1],
         f"{row.coverage_10_90:.0%}"),
    ]


def main() -> int:
    ok = True
    for panel in ("province", "region_qc"):
        for name, passed, detail in check(panel):
            print(f"{'PASS' if passed else 'FAIL'}  {name} ({detail})")
            ok &= passed
    print("gate passed: the model may be promoted" if ok else "gate FAILED: keep the last good forecasts online")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
