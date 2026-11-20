"""Check a weekly case file against the data contract (data/contract/README.md) before it enters the pipeline.

    python scripts/validate_cases.py data/contract/weekly_cases_template.csv
    python scripts/validate_cases.py incoming/*.csv

Prints every error and warning. Exits 1 if any file has an error, so a scheduled job stops instead of forecasting
from a bad file.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["area_code", "week_ending", "cases"]
OPTIONAL = ["area_name"]
SPIKE = 10  # times the previous 12-week median


def known_history() -> pd.DataFrame:
    parts = [pd.read_parquet(ROOT / f"app/data/{p}_history.parquet") for p in ("province", "region_qc")]
    h = pd.concat(parts, ignore_index=True)[["unit_id", "week", "cases"]]
    h["week"] = pd.to_datetime(h.week)
    return h.rename(columns={"unit_id": "area_code", "week": "week_ending"})


def validate(path: Path, today: date | None = None) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    try:
        df = pd.read_csv(path, dtype={"area_code": str, "area_name": str, "week_ending": str})
    except Exception as e:  # noqa: BLE001 - any unreadable file is one error
        return [f"cannot read the file: {e}"], []

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return [f"missing column(s): {', '.join(missing)}"], []
    extra = [c for c in df.columns if c not in REQUIRED + OPTIONAL]
    if extra:
        errors.append(f"unknown column(s) {', '.join(extra)}: the file must hold weekly counts only, no patient details")

    line = lambda i: i + 2  # noqa: E731 - row 0 is line 2 under the header
    df["area_code"] = df.area_code.str.strip()
    for i in df.index[df.area_code.isna() | (df.area_code == "")]:
        errors.append(f"line {line(i)}: empty area_code")

    weeks = pd.to_datetime(df.week_ending, format="%Y-%m-%d", errors="coerce")
    for i in df.index[weeks.isna()]:
        errors.append(f"line {line(i)}: week_ending {df.week_ending[i]!r} is not a YYYY-MM-DD date")
    for i in df.index[weeks.notna() & (weeks.dt.dayofweek != 6)]:
        errors.append(f"line {line(i)}: week_ending {df.week_ending[i]} is a {weeks[i]:%A}, not a Sunday")
    limit = pd.Timestamp(today or date.today())
    for i in df.index[weeks > limit]:
        errors.append(f"line {line(i)}: week_ending {df.week_ending[i]} is in the future")

    cases = pd.to_numeric(df.cases, errors="coerce")
    for i in df.index[df.cases.notna() & cases.isna()]:
        errors.append(f"line {line(i)}: cases {df.cases[i]!r} is not a number")
    for i in df.index[(cases < 0) | (cases.notna() & (cases % 1 != 0))]:
        errors.append(f"line {line(i)}: cases {df.cases[i]} must be a whole number, 0 or more")

    df["week_ending"], df["cases"] = weeks, cases
    dup = df[df.duplicated(["area_code", "week_ending"], keep=False) & weeks.notna()]
    for (code, wk), _ in dup.groupby(["area_code", "week_ending"]):
        errors.append(f"{code} {wk:%Y-%m-%d} appears more than once")
    if errors:
        return errors, warnings

    hist = known_history()
    for code in sorted(set(df.area_code) - set(hist.area_code)):
        warnings.append(f"{code} is a new area code: it will start a new area with no history")

    n_missing = int(df.cases.isna().sum())
    if n_missing:
        warnings.append(f"{n_missing} week(s) marked as not reported (empty cases); they stay missing, never 0")

    both = pd.concat([hist, df[["area_code", "week_ending", "cases"]]]).drop_duplicates(["area_code", "week_ending"], keep="last")
    both = both.sort_values(["area_code", "week_ending"])
    both["median12"] = both.groupby("area_code").cases.transform(lambda s: s.shift(1).rolling(12, min_periods=6).median())
    new = both.merge(df[["area_code", "week_ending"]], on=["area_code", "week_ending"])
    for r in new[(new.cases > SPIKE * new.median12.clip(lower=1))].itertuples():
        warnings.append(f"{r.area_code} {r.week_ending:%Y-%m-%d}: {r.cases:.0f} cases, over {SPIKE}x the previous "
                        f"12-week median ({r.median12:.0f}); check for a typing slip or a backlog of late reports")

    for code, g in df.dropna(subset=["week_ending"]).groupby("area_code"):
        span = (g.week_ending.max() - g.week_ending.min()).days // 7 + 1
        if span > len(g):
            warnings.append(f"{code}: {span - len(g)} week(s) absent between {g.week_ending.min():%Y-%m-%d} and "
                            f"{g.week_ending.max():%Y-%m-%d}; send them as empty rows if they were not reported")
    return errors, warnings


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__)
        return 2
    bad = 0
    for p in paths:
        errors, warnings = validate(Path(p))
        status = "REJECTED" if errors else "OK"
        print(f"{p}: {status} ({len(errors)} error(s), {len(warnings)} warning(s))")
        for e in errors:
            print(f"  error   {e}")
        for w in warnings:
            print(f"  warning {w}")
        bad += bool(errors)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
