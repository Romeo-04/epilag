"""Budget allocation: where does each peso avert the most forecast dengue cases?

For each unit and action, expected cases averted = forecast cases in the next 8 weeks
x share of the population covered x action effect. Cost = people covered x cost per person.
Value per peso is constant within a (unit, action), so the best plan under a budget is a
fractional knapsack: fund the highest cases-averted-per-peso first, up to each action's max
coverage, until the money runs out. Effects are ranges (low/central/high), so the plan is
chosen on the central effect and reported with all three.

Effect sizes are deliberately cautious placeholders anchored to the evidence:
  community clean-up + container covers: Bowman et al. (2016) meta-analysis, OR 0.22
    (95% CI 0.15-0.32) for community environmental management with container covers;
    trials are few and small, so we use 10% / 30% / 50% fewer cases.
  fogging (space spraying): little evidence of effect on cases (same review); 0% / 5% / 10%.
Costs are example values only. Replace them with the LGU's own costs in the app.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Action:
    name: str
    cost_per_person: float  # pesos per person covered (example value)
    effect_low: float
    effect_central: float
    effect_high: float
    max_coverage: float  # max share of a unit's population this action can reach in 8 weeks


DEFAULT_ACTIONS = (
    Action("Clean-up drive + container covers", 15.0, 0.10, 0.30, 0.50, 0.30),
    Action("Targeted fogging", 25.0, 0.00, 0.05, 0.10, 0.10),
)


def expected_cases_8wk(forecast: pd.DataFrame) -> pd.DataFrame:
    """Sum of weekly forecasts over the next 8 weeks, interpolated from the 2/4/6/8-week horizons."""
    rows = []
    for unit_id, f in forecast.groupby("unit_id"):
        f = f.set_index("horizon").sort_index()
        weeks = pd.Index(range(1, 9), name="horizon")
        interp = f[["q10", "q50", "q90"]].reindex(f.index.union(weeks)).interpolate("index").bfill().loc[weeks]
        rows.append({"unit_id": unit_id, "unit_name": f.unit_name.iloc[0], "population": f.population.iloc[0],
                     "cases_low": interp.q10.sum(), "cases_mid": interp.q50.sum(), "cases_high": interp.q90.sum()})
    return pd.DataFrame(rows)


def allocate(forecast: pd.DataFrame, budget: float, actions=DEFAULT_ACTIONS) -> pd.DataFrame:
    """Return the funded (unit, action) lines with spend and cases averted (low/central/high)."""
    units = expected_cases_8wk(forecast)
    options = []
    for a in actions:
        o = units.copy()
        o["action"] = a.name
        o["max_people"] = o.population * a.max_coverage
        o["max_cost"] = o.max_people * a.cost_per_person
        # cases averted per person covered, assuming cases are spread evenly over the population
        o["averted_per_peso"] = o.cases_mid / o.population * a.effect_central / a.cost_per_person
        o["effects"] = [(a.effect_low, a.effect_central, a.effect_high)] * len(o)
        o["cost_per_person"] = a.cost_per_person
        options.append(o)
    opts = pd.concat(options, ignore_index=True).sort_values("averted_per_peso", ascending=False)

    plan, left = [], float(budget)
    for o in opts.itertuples():
        if left <= 0 or o.averted_per_peso <= 0:
            break
        spend = min(left, o.max_cost)
        share = spend / o.cost_per_person / o.population  # share of the unit's population covered
        lo, mid, hi = o.effects
        plan.append({
            "unit_id": o.unit_id, "unit_name": o.unit_name, "action": o.action, "spend": spend,
            "people_covered": spend / o.cost_per_person, "share_covered": share,
            # low uses the low forecast and low effect, high uses high and high
            "averted_low": o.cases_low * share * lo,
            "averted_mid": o.cases_mid * share * mid,
            "averted_high": o.cases_high * share * hi,
        })
        left -= spend
    cols = ["unit_id", "unit_name", "action", "spend", "people_covered", "share_covered",
            "averted_low", "averted_mid", "averted_high"]
    return pd.DataFrame(plan, columns=cols)
