"""The weekly data contract check and the model promotion gate (scripts/validate_cases.py, scripts/model_gate.py)."""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from model_gate import check  # noqa: E402
from validate_cases import validate  # noqa: E402

TODAY = date(2026, 11, 20)


def write(tmp_path, text):
    p = tmp_path / "w.csv"
    p.write_text(text)
    return p


def test_template_passes():
    errors, warnings = validate(ROOT / "data/contract/weekly_cases_template.csv", TODAY)
    assert errors == []
    assert any("not reported" in w for w in warnings)


def test_patient_columns_are_rejected(tmp_path):
    errors, _ = validate(write(tmp_path, "area_code,week_ending,cases,patient_name\nPH01028,2021-01-10,3,Juan\n"), TODAY)
    assert any("patient" in e for e in errors)


def test_bad_rows_are_rejected(tmp_path):
    text = ("area_code,week_ending,cases\n"
            "PH01028,2021-01-05,3\n"     # a Tuesday
            "PH01028,2021-01-10,-3\n"    # negative
            "PH01028,2021-01-17,2.5\n"   # fractional
            "PH01029,2021-01-10,4\n"
            "PH01029,2021-01-10,5\n"     # duplicate
            "PH01029,2027-01-03,5\n")    # future
    errors, _ = validate(write(tmp_path, text), TODAY)
    joined = " | ".join(errors)
    for needle in ("not a Sunday", "whole number", "more than once", "in the future"):
        assert needle in joined


def test_missing_column(tmp_path):
    errors, _ = validate(write(tmp_path, "area_code,cases\nPH01028,3\n"), TODAY)
    assert errors == ["missing column(s): week_ending"]


def test_spikes_new_codes_and_gaps_warn(tmp_path):
    text = ("area_code,week_ending,cases\n"
            "PH01028,2021-01-17,900\n"   # Ilocos Norte runs at about 2 a week
            "PH01028,2021-01-31,2\n"     # 24 Jan absent
            "PH99999,2021-01-17,1\n")
    errors, warnings = validate(write(tmp_path, text), TODAY)
    assert errors == []
    joined = " | ".join(warnings)
    assert "12-week median" in joined and "new area code" in joined and "absent" in joined


def test_gate_passes_on_committed_reports():
    assert all(passed for panel in ("province", "region_qc") for _, passed, _ in check(panel))


def test_gate_fails_a_drifted_model(tmp_path):
    for panel in ("province", "region_qc"):
        bt = pd.read_csv(ROOT / f"reports/backtest_{panel}.csv")
        bt["mae_epilag"] = bt.mae_seasonal_naive * 1.2  # worse than last year's cases
        bt.to_csv(tmp_path / f"backtest_{panel}.csv", index=False)
    results = check("region_qc", tmp_path)
    assert not results[0][1]
