"""Models for the comparison. Each takes (train, test, ctx) and returns q10/q50/q90 of log1p(cases).

lightgbm       EpiLag-PH as it runs today: gradient-boosted trees, one quantile model per quantile.
negbin         Negative binomial regression (NB2), the standard count model in epidemiology.
random_forest  Quantile regression forest (Meinshausen 2006): bagged trees instead of boosted.
sarimax        One seasonal time-series model per area, weather as lagged inputs.

The first three share the same inputs; SARIMAX sees only each area's own series and its weather.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import nbinom, norm

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from backtest import QUANTILES, fit_quantiles, predict_log  # noqa: E402

LEVELS = list(QUANTILES.values())


def lightgbm(train: pd.DataFrame, test: pd.DataFrame, ctx) -> pd.DataFrame:
    return predict_log(fit_quantiles(train, ctx.features, ctx.target), test[ctx.features])


# ---------------------------------------------------------------- negative binomial

def _design(train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Regression can't take gaps: fill with the training median, flag a missing last-year value, standardise."""
    tr, te = train[features].astype(float), test[features].astype(float)
    if "y_lastyear" in features:
        tr, te = tr.assign(lastyear_missing=tr.y_lastyear.isna() * 1.0), te.assign(lastyear_missing=te.y_lastyear.isna() * 1.0)
    med = tr.median().fillna(0)
    tr, te = tr.fillna(med), te.fillna(med)
    mean, sd = tr.mean(), tr.std().replace(0, 1).fillna(1)
    tr, te = (tr - mean) / sd, (te - mean) / sd
    return tr.assign(const=1.0), te.assign(const=1.0)


def negbin(train: pd.DataFrame, test: pd.DataFrame, ctx) -> pd.DataFrame:
    import statsmodels.api as sm

    X, Xt = _design(train, test, ctx.features)
    y = np.rint(np.expm1(train[ctx.target])).clip(lower=0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mu = sm.GLM(y, X, family=sm.families.Poisson()).fit().mu
        # Dispersion by the Cameron-Trivedi auxiliary regression: var = mu + alpha * mu^2.
        alpha = float(max(1e-4, ((y - mu) ** 2 - y).sum() / (mu ** 2).sum()))
        fit = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=alpha)).fit()
    mu_t = np.exp(np.clip(Xt.values @ fit.params.values, -10, np.log(1e5)))
    n = 1 / alpha
    p = n / (n + mu_t)
    return pd.DataFrame({k: np.log1p(nbinom.ppf(a, n, p)) for k, a in QUANTILES.items()}, index=test.index)


# ---------------------------------------------------------------- random forest

def random_forest(train: pd.DataFrame, test: pd.DataFrame, ctx) -> pd.DataFrame:
    from quantile_forest import RandomForestQuantileRegressor

    m = RandomForestQuantileRegressor(n_estimators=300, min_samples_leaf=5, max_features=1 / 3,
                                      n_jobs=-1, random_state=0)
    m.fit(train[ctx.features], train[ctx.target])
    return pd.DataFrame(m.predict(test[ctx.features], quantiles=LEVELS), columns=list(QUANTILES), index=test.index)


# ---------------------------------------------------------------- SARIMAX

ORDER = (2, 0, 1)  # chosen by AIC, see research/results/README.md
WEATHER_ROLL = {"rain_mm": "sum", "temp_mean": "mean", "rh_mean": "mean"}


def _exog(s: pd.DataFrame, h: int) -> pd.DataFrame:
    """Inputs known h weeks ahead: a constant, two yearly Fourier pairs, and 4-week weather from h weeks back."""
    angle = 2 * np.pi * s.index.dayofyear.values / 365.25
    x = pd.DataFrame({"const": 1.0, "s1": np.sin(angle), "c1": np.cos(angle),
                      "s2": np.sin(2 * angle), "c2": np.cos(2 * angle)}, index=s.index)
    for col, how in WEATHER_ROLL.items():
        if col in s and s[col].notna().any():
            x[col] = getattr(s[col].rolling(4, min_periods=2), how)().shift(h)
    return x


def _one_area(s: pd.DataFrame, h: int, cutoff: pd.Timestamp, origins: pd.DatetimeIndex) -> pd.DataFrame:
    """Fit on the area's series up to `cutoff`, then forecast h weeks ahead from each origin week."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    end = origins.max() + pd.Timedelta(weeks=h)
    s = s[(s.index <= end) & (s.index >= s.y.first_valid_index())]
    y, x = s.y, _exog(s, h)
    fit_rows = s.index <= cutoff
    weather = [c for c in x if c in WEATHER_ROLL]
    m, sd = x.loc[fit_rows, weather].mean(), x.loc[fit_rows, weather].std().replace(0, 1).fillna(1)
    x[weather] = ((x[weather] - m) / sd).fillna(0)  # standardised; missing weather = average weather
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = SARIMAX(y[fit_rows], exog=x[fit_rows], order=ORDER, trend="n").fit(disp=False, maxiter=200)
        full = res.apply(y, exog=x, refit=False)  # same parameters, filtered over the whole series
    ssm = full.model.ssm
    mat = lambda name: ssm[name][..., 0] if ssm[name].ndim == 3 else ssm[name]  # noqa: E731 (time-invariant)
    Z, T, R = mat("design"), mat("transition"), mat("selection")
    RQR = R @ mat("state_cov") @ R.T
    Th, noise = np.eye(T.shape[0]), np.zeros_like(T)
    for _ in range(h):  # T^h and the error that builds up over h steps
        noise = T @ noise @ T.T + RQR
        Th = T @ Th
    pos = s.index.get_indexer(origins)
    a, P = full.filtered_state[:, pos], full.filtered_state_cov[:, :, pos]
    mean = ssm["obs_intercept"][0, pos + h] + (Z @ Th @ a)[0]
    A = Z @ Th
    var = np.einsum("ij,jkn,ik->n", A, P, A) + (Z @ noise @ Z.T)[0, 0] + mat("obs_cov")[0, 0]
    sd_ = np.sqrt(np.maximum(var, 1e-9))
    return pd.DataFrame({k: mean + norm.ppf(a_) * sd_ for k, a_ in QUANTILES.items()}, index=origins)


def sarimax(train: pd.DataFrame, test: pd.DataFrame, ctx) -> pd.DataFrame:
    table = ctx.table.set_index("week")
    cutoff = (train.week + pd.Timedelta(weeks=ctx.h)).max()  # last target week the model may learn from
    units = test.unit_id.unique()
    parts = Parallel(n_jobs=-1)(
        delayed(_one_area)(table[table.unit_id == u], ctx.h, cutoff, pd.DatetimeIndex(test.week[test.unit_id == u]))
        for u in units)
    out = []
    for u, p in zip(units, parts):
        rows = test[test.unit_id == u]
        out.append(pd.DataFrame(p.values, columns=p.columns, index=rows.index))
    return pd.concat(out).loc[test.index]


MODELS = {"lightgbm": lightgbm, "negbin": negbin, "random_forest": random_forest, "sarimax": sarimax}
