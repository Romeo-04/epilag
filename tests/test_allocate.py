import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from allocate import Action, allocate, expected_cases_8wk  # noqa: E402


def forecast(rows):
    out = []
    for unit_id, pop, weekly in rows:
        for h in (2, 4, 6, 8):
            out.append({"unit_id": unit_id, "unit_name": unit_id, "population": pop, "horizon": h,
                        "q10": weekly * 0.5, "q50": weekly, "q90": weekly * 2})
    return pd.DataFrame(out)


ONE_ACTION = (Action("clean-up", cost_per_person=10.0, effect_low=0.1, effect_central=0.3,
                     effect_high=0.5, max_coverage=0.5),)


def test_expected_cases_sums_eight_weeks():
    e = expected_cases_8wk(forecast([("A", 1000, 10.0)])).iloc[0]
    assert e.cases_mid == pytest.approx(80.0)
    assert e.cases_low == pytest.approx(40.0) and e.cases_high == pytest.approx(160.0)


def test_funds_highest_rate_unit_first():
    # Same population, B has 5x the forecast cases -> B is funded first.
    plan = allocate(forecast([("A", 1000, 10.0), ("B", 1000, 50.0)]), budget=1000, actions=ONE_ACTION)
    assert plan.unit_id.tolist() == ["B"]
    assert plan.spend.sum() == pytest.approx(1000)


def test_respects_budget_and_max_coverage():
    plan = allocate(forecast([("A", 1000, 10.0), ("B", 1000, 50.0)]), budget=1e9, actions=ONE_ACTION)
    # Max coverage 50% of 1000 people at 10 pesos = 5000 pesos per unit.
    assert plan.spend.tolist() == pytest.approx([5000, 5000])
    assert (plan.share_covered <= 0.5 + 1e-9).all()


def test_averted_cases_ranges_are_ordered_and_correct():
    plan = allocate(forecast([("B", 1000, 50.0)]), budget=5000, actions=ONE_ACTION).iloc[0]
    # 400 cases in 8 weeks, 50% covered, 30% effect -> 60 averted (central).
    assert plan.averted_mid == pytest.approx(60.0)
    assert plan.averted_low < plan.averted_mid < plan.averted_high


def test_zero_budget_gives_empty_plan():
    assert allocate(forecast([("A", 1000, 10.0)]), budget=0, actions=ONE_ACTION).empty
