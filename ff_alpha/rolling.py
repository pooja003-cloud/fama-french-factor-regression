"""Rolling 36-month factor regressions: how exposures drift over time."""
from __future__ import annotations

import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS

from . import config
from .data import fund_sample
from .models import excess_returns


def rolling_loadings(returns: pd.DataFrame, factors: pd.DataFrame,
                     model: str = config.ROLLING_MODEL, window: int = config.ROLLING_WINDOW,
                     start: pd.Period = config.ORIGINAL_START,
                     end: pd.Period | None = None) -> pd.DataFrame:
    """Long table: one row per (fund, window end month) with alpha and loadings.

    Each row uses the `window` months ending at `month`. Point estimates only
    (rolling t-stats on overlapping windows are not independent tests).
    """
    cols = config.MODELS[model]
    end = end or factors.index.max()
    frames = []
    for ticker in returns.columns:
        ex = excess_returns(fund_sample(returns[ticker], start, end), factors)
        df = pd.concat([ex.rename("y"), factors[cols]], axis=1, join="inner").dropna()
        if len(df) < window:
            continue
        fit = RollingOLS(df["y"], sm.add_constant(df[cols]), window=window).fit()
        p = fit.params.dropna().rename(columns={"const": "alpha_m"})
        p["alpha_ann"] = p["alpha_m"] * 12
        p["r2"] = fit.rsquared.reindex(p.index)
        p["ticker"] = ticker
        p.index.name = "month"
        frames.append(p.reset_index())
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
