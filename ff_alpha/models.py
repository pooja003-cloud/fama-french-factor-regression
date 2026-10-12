"""Factor regressions with Newey-West (HAC) standard errors.

    r_fund - RF = alpha + sum_k beta_k * factor_k + e

Point estimates are plain OLS; only the standard errors are HAC-adjusted,
which corrects t-stats for autocorrelation and heteroskedasticity in monthly
fund returns.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests

from . import config
from .data import fund_sample


def regress(excess: pd.Series, factors: pd.DataFrame, cols: list[str], nw_lags: int) -> dict:
    """One time-series regression. Returns a flat dict of results."""
    df = pd.concat([excess.rename("y"), factors[cols]], axis=1, join="inner").dropna()
    X = sm.add_constant(df[cols])
    fit = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags, "use_correction": True}, use_t=True)
    se = fit.bse.copy()
    # Short-sample guard: in small samples the HAC estimator can pick up
    # spurious negative autocorrelation and make SEs *smaller* than plain OLS,
    # inflating t-stats. Below MIN_MONTHS we never let NW shrink an SE.
    floored = len(df) < config.MIN_MONTHS
    if floored:
        se = np.maximum(se, sm.OLS(df["y"], X).fit().bse)
    tvals = fit.params / se
    dof = len(df) - X.shape[1]
    pvals = pd.Series(2 * stats.t.sf(np.abs(tvals), dof), index=tvals.index)
    out = {
        "alpha_m": fit.params["const"],
        "alpha_ann": fit.params["const"] * 12,
        "alpha_se": se["const"],
        "alpha_t": tvals["const"],
        "alpha_p": pvals["const"],
        "alpha_t_nw_raw": fit.tvalues["const"],
        "se_floor_applied": floored,
        "r2": fit.rsquared,
        "adj_r2": fit.rsquared_adj,
        "nobs": int(fit.nobs),
        "start": str(df.index.min()),
        "end": str(df.index.max()),
        "resid_vol_ann": float(np.std(fit.resid, ddof=len(cols) + 1) * np.sqrt(12)),
    }
    for c in cols:
        out[f"b_{c}"] = fit.params[c]
        out[f"t_{c}"] = tvals[c]
    return out


def excess_returns(fund_ret: pd.Series, factors: pd.DataFrame) -> pd.Series:
    """Fund return minus the French RF column (the same RF behind Mkt-RF)."""
    rf = factors["RF"].reindex(fund_ret.index)
    return (fund_ret - rf).dropna()


def run_period(returns: pd.DataFrame, factors: pd.DataFrame, start: pd.Period, end: pd.Period,
               min_months: int, period_name: str, lags: tuple[int, ...]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All funds x all models x all NW lag choices for one sample period.

    Returns (results, skipped) where skipped lists funds without enough data.
    """
    rows, skipped = [], []
    for ticker in returns.columns:
        r = fund_sample(returns[ticker], start, end)
        ex = excess_returns(r, factors)
        if len(ex) < min_months:
            skipped.append({"period": period_name, "ticker": ticker, "months": len(ex),
                            "reason": f"fewer than {min_months} months"})
            continue
        for model, cols in config.MODELS.items():
            for lag in lags:
                res = regress(ex, factors, cols, lag)
                rows.append({"period": period_name, "ticker": ticker, "model": model,
                             "nw_lags": lag, **res})
    return pd.DataFrame(rows), pd.DataFrame(skipped)


def bonferroni(results: pd.DataFrame, alpha_level: float = config.SIGNIFICANCE) -> pd.DataFrame:
    """Bonferroni-adjust alpha p-values across funds x models, per period and lag.

    m = number of (fund, model) alpha tests in that period. An alpha is called
    significant only if p * m < alpha_level.
    """
    out = results.copy()
    m = out.groupby(["period", "nw_lags"])["alpha_p"].transform("count")
    out["n_tests"] = m
    out["alpha_p_bonf"] = (out["alpha_p"] * m).clip(upper=1.0)
    out["sig_raw"] = out["alpha_p"] < alpha_level
    out["sig_bonf"] = out["alpha_p_bonf"] < alpha_level

    # Holm (step-down; controls the same family-wise error rate as Bonferroni
    # but is never less powerful) and Benjamini-Hochberg (controls the false
    # discovery rate instead: a looser, complementary standard).
    out["alpha_p_holm"] = np.nan
    out["alpha_p_bh"] = np.nan
    for _, idx in out.groupby(["period", "nw_lags"]).groups.items():
        p = out.loc[idx, "alpha_p"].to_numpy()
        out.loc[idx, "alpha_p_holm"] = multipletests(p, method="holm")[1]
        out.loc[idx, "alpha_p_bh"] = multipletests(p, method="fdr_bh")[1]
    out["sig_holm"] = out["alpha_p_holm"] < alpha_level
    out["sig_bh"] = out["alpha_p_bh"] < alpha_level
    return out


def structural_change(returns: pd.DataFrame, factors: pd.DataFrame, model: str = config.ROLLING_MODEL,
                      nw_lags: int = config.NW_LAGS_DEFAULT,
                      ext_end: pd.Period | None = None) -> pd.DataFrame:
    """Did alpha and loadings change after 2024-03?

    Pools the original and extension samples and estimates
        y = a + b'f + d*POST + g'(f*POST) + e
    where POST = 1 from EXTENSION_START. `d` is the change in monthly alpha,
    `g_k` the change in each loading; t-stats are Newey-West. (Jan-Feb 2024
    are excluded by design, so the HAC window spans a two-month gap: a
    negligible approximation.)
    """
    cols = config.MODELS[model]
    ext_end = ext_end or factors.index.max()
    rows = []
    for ticker in returns.columns:
        r = returns[ticker].dropna()
        pre = fund_sample(r, config.ORIGINAL_START, config.ORIGINAL_END)
        post = fund_sample(r, config.EXTENSION_START, ext_end)
        if len(pre) < config.MIN_MONTHS or len(post) < config.MIN_MONTHS_EXTENSION:
            continue
        ex = excess_returns(pd.concat([pre, post]), factors)
        df = pd.concat([ex.rename("y"), factors[cols]], axis=1, join="inner").dropna()
        df["POST"] = (df.index >= config.EXTENSION_START).astype(float)
        inter = [f"{c}xPOST" for c in cols]
        for c in cols:
            df[f"{c}xPOST"] = df[c] * df["POST"]
        X = sm.add_constant(df[cols + ["POST"] + inter])
        fit = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags, "use_correction": True}, use_t=True)
        row = {"ticker": ticker, "model": model, "nobs_pre": int((df.POST == 0).sum()),
               "nobs_post": int(df.POST.sum()),
               "d_alpha_ann": fit.params["POST"] * 12, "d_alpha_t": fit.tvalues["POST"]}
        for c in cols:
            row[f"d_{c}"] = fit.params[f"{c}xPOST"]
            row[f"dt_{c}"] = fit.tvalues[f"{c}xPOST"]
        # joint Wald test that every loading is unchanged
        names = list(X.columns)
        R = np.zeros((len(inter), len(names)))
        for i, name in enumerate(inter):
            R[i, names.index(name)] = 1.0
        w = fit.wald_test(R, scalar=True)
        row["loadings_changed_p"] = float(w.pvalue)
        rows.append(row)
    return pd.DataFrame(rows)
