"""Budget allocation: where does each peso avert the most forecast dengue cases?

For each unit and action, expected cases averted = forecast cases in weeks 3-8 ahead
x share of the population covered x action effect. Cost = people covered x cost per person.
Weeks 1-2 are left out: people who fall ill in the next two weeks are mostly already infected,
so an action started now cannot prevent them.
Value per peso is constant within a (unit, action), so the best plan under a budget is a
fractional knapsack: fund the highest cases-averted-per-peso first, up to each action's max
coverage, until the money runs out. Effects are ranges (low/central/high), so the plan is
chosen on the central effect and reported with all three. budget_curve() gives the same plan
for every budget at once: cases averted rise in straight lines between the points where the next
(unit, action) starts, and flatten as the money reaches lower-risk areas.
Each action starts at an alert level (Action.min_level, the "When to act" table in the app). Given each unit's
current level, the plan only funds the actions that level calls for, so fogging goes only to areas at watch or higher.
With priority="level" (the default), the worst level is funded first and value per peso decides only within a level,
so an area at outbreak warning is never passed over for a normal one; priority="value" ranks on value per peso alone.

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
    min_level: str = "normal"  # the alert level the action starts at (one of LEVELS)


DEFAULT_ACTIONS = (
    Action("Clean-up drive + container covers", 15.0, 0.10, 0.30, 0.50, 0.30),
    Action("Targeted fogging", 25.0, 0.00, 0.05, 0.10, 0.10, "watch"),
)

LEVELS = ("normal", "above usual", "watch", "outbreak warning")


PREVENTABLE_WEEKS = range(3, 9)  # weeks ahead an action started now can still affect


def expected_cases_8wk(forecast: pd.DataFrame, weeks_ahead=range(1, 9)) -> pd.DataFrame:
    """Sum of weekly forecasts over the given weeks ahead (default 1-8), interpolated from the 2/4/6/8-week
    horizons."""
    rows = []
    for unit_id, f in forecast.groupby("unit_id"):
        f = f.set_index("horizon").sort_index()
        weeks = pd.Index(list(weeks_ahead), name="horizon")
        interp = f[["q10", "q50", "q90"]].reindex(f.index.union(weeks)).interpolate("index").bfill().loc[weeks]
        rows.append({"unit_id": unit_id, "unit_name": f.unit_name.iloc[0], "population": f.population.iloc[0],
                     "cases_low": interp.q10.sum(), "cases_mid": interp.q50.sum(), "cases_high": interp.q90.sum()})
    return pd.DataFrame(rows)


def _options(forecast: pd.DataFrame, actions, levels=None, priority="level") -> pd.DataFrame:
    """Every (unit, action) pair with its cost cap and cases averted per peso, in funding order. With `levels`
    (unit_id -> alert level; a unit not in it counts as normal), only the actions each unit's level has reached, and
    with priority="level" the worst level first, best value first within a level."""
    units = expected_cases_8wk(forecast, PREVENTABLE_WEEKS)
    options = []
    for a in actions:
        o = units.copy()
        o["level_rank"] = o.unit_id.map(levels or {}).fillna(LEVELS[0]).map(LEVELS.index)
        if levels is not None:
            o = o[o.level_rank >= LEVELS.index(a.min_level)].copy()
        o["action"] = a.name
        o["max_people"] = o.population * a.max_coverage
        o["max_cost"] = o.max_people * a.cost_per_person
        # cases averted per person covered, assuming cases are spread evenly over the population
        o["averted_per_peso"] = o.cases_mid / o.population * a.effect_central / a.cost_per_person
        o["effects"] = [(a.effect_low, a.effect_central, a.effect_high)] * len(o)
        o["cost_per_person"] = a.cost_per_person
        options.append(o)
    keys = ["level_rank", "averted_per_peso"] if priority == "level" else ["averted_per_peso"]
    return pd.concat(options, ignore_index=True).sort_values(keys, ascending=False, kind="stable")


def allocate(forecast: pd.DataFrame, budget: float, actions=DEFAULT_ACTIONS, levels=None,
             priority="level") -> pd.DataFrame:
    """Return the funded (unit, action) lines with spend and cases averted (low/central/high). With `levels`
    (unit_id -> alert level), each unit only gets the actions its level calls for, worst level first unless
    priority="value"."""
    plan, left = [], float(budget)
    for o in _options(forecast, actions, levels, priority).itertuples():
        if left <= 0:
            break
        if o.averted_per_peso <= 0:  # with priority="level" a better-ranked level can hold zero-value options
            continue
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


def budget_curve(forecast: pd.DataFrame, actions=DEFAULT_ACTIONS, levels=None, priority="level") -> pd.DataFrame:
    """Total cases averted (low/central/high) against budget, at each point where the plan starts funding the
    next (unit, action). Between two points the totals rise in a straight line, so interpolating this table
    gives allocate()'s totals for any budget. Starts at a zero budget and ends where everything is funded."""
    rows = [{"spend": 0.0, "averted_low": 0.0, "averted_mid": 0.0, "averted_high": 0.0}]
    for o in _options(forecast, actions, levels, priority).itertuples():
        if o.averted_per_peso <= 0:
            continue
        lo, mid, hi = o.effects
        last = rows[-1]
        rows.append({"spend": last["spend"] + o.max_cost,
                     "averted_low": last["averted_low"] + o.cases_low * o.max_people / o.population * lo,
                     "averted_mid": last["averted_mid"] + o.cases_mid * o.max_people / o.population * mid,
                     "averted_high": last["averted_high"] + o.cases_high * o.max_people / o.population * hi})
    return pd.DataFrame(rows)
