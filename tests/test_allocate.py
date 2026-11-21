import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from allocate import Action, allocate, budget_curve, expected_cases_8wk  # noqa: E402


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


def test_expected_cases_can_skip_the_first_weeks():
    e = expected_cases_8wk(forecast([("A", 1000, 10.0)]), weeks_ahead=range(3, 9)).iloc[0]
    assert e.cases_mid == pytest.approx(60.0)


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
    # 300 cases in weeks 3-8 (weeks 1-2 are already infected), 50% covered, 30% effect -> 45 averted.
    assert plan.averted_mid == pytest.approx(45.0)
    assert plan.averted_low < plan.averted_mid < plan.averted_high


def test_zero_budget_gives_empty_plan():
    assert allocate(forecast([("A", 1000, 10.0)]), budget=0, actions=ONE_ACTION).empty


def test_budget_curve_matches_allocate_at_any_budget():
    fc = forecast([("A", 1000, 10.0), ("B", 1000, 50.0), ("C", 4000, 20.0)])
    two = ONE_ACTION + (Action("fogging", 25.0, 0.0, 0.05, 0.1, 0.1),)
    curve = budget_curve(fc, two)
    assert curve.spend.iloc[0] == 0 and curve.averted_mid.iloc[0] == 0
    assert curve.spend.is_monotonic_increasing and curve.averted_mid.is_monotonic_increasing
    for budget in (0, 1000, 5000, 7300, 20000, 1e9):
        plan = allocate(fc, budget, two)
        for k in ("averted_low", "averted_mid", "averted_high"):
            assert plan[k].sum() == pytest.approx(np.interp(budget, curve.spend, curve[k]))


def test_budget_curve_flattens():
    # Each extra peso buys fewer cases: the slope never rises.
    curve = budget_curve(forecast([("A", 1000, 10.0), ("B", 1000, 50.0), ("C", 4000, 20.0)]), ONE_ACTION)
    slope = curve.averted_mid.diff().iloc[1:].to_numpy() / curve.spend.diff().iloc[1:].to_numpy()
    assert (np.diff(slope) <= 1e-12).all()


LEVELLED = ONE_ACTION + (Action("fogging", 25.0, 0.0, 0.05, 0.1, 0.1, min_level="watch"),)


def test_levels_decide_which_actions_an_area_gets():
    # B has the most cases, but is only above usual, so it gets clean-up and no fogging; C is at watch and gets both.
    fc = forecast([("A", 1000, 10.0), ("B", 1000, 50.0), ("C", 1000, 20.0)])
    plan = allocate(fc, 1e9, LEVELLED, levels={"A": "normal", "B": "above usual", "C": "watch"})
    assert sorted(zip(plan.unit_id, plan.action)) == [("A", "clean-up"), ("B", "clean-up"), ("C", "clean-up"), ("C", "fogging")]


def test_unlisted_area_counts_as_normal_and_no_levels_means_no_gate():
    fc = forecast([("A", 1000, 10.0)])
    assert set(allocate(fc, 1e9, LEVELLED, levels={}).action) == {"clean-up"}
    assert set(allocate(fc, 1e9, LEVELLED).action) == {"clean-up", "fogging"}


def test_budget_curve_follows_the_levels():
    fc = forecast([("A", 1000, 10.0), ("B", 1000, 50.0), ("C", 4000, 20.0)])
    levels = {"A": "watch", "B": "normal", "C": "outbreak warning"}
    curve = budget_curve(fc, LEVELLED, levels)
    for budget in (0, 3000, 9000, 1e9):
        plan = allocate(fc, budget, LEVELLED, levels)
        assert plan.averted_mid.sum() == pytest.approx(np.interp(budget, curve.spend, curve.averted_mid))
