"""Data loading: Ken French factors and monthly fund returns.

All returns are monthly, in decimals (0.01 = 1%), indexed by pandas monthly
Periods so fund and factor data align exactly on calendar month.

Downloads are cached in data/raw/ so a run can be reproduced offline. The Ken
French library is revised occasionally; delete the cache to refresh it.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

FRENCH_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip"
FF5_NAME = "F-F_Research_Data_5_Factors_2x3"
MOM_NAME = "F-F_Momentum_Factor"


# --------------------------------------------------------------------------
# Ken French factors
# --------------------------------------------------------------------------
def parse_french_csv(text: str) -> pd.DataFrame:
    """Parse the *monthly* table from a Ken French CSV.

    The files have a free-text preamble, then a monthly table whose rows start
    with a YYYYMM date, then an annual table (YYYY dates). We keep only the
    first contiguous block of YYYYMM rows. Values are in percent.
    """
    lines = text.splitlines()
    header, rows, started = None, [], False
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.split(",")]
        if re.fullmatch(r"\d{6}", cells[0] or ""):
            if header is None:
                prev = [c.strip() for c in lines[i - 1].split(",")]
                header = [c for c in prev[1:] if c]
            started = True
            rows.append(cells[: len(header) + 1])
        elif started:
            break  # end of the monthly block
    if not rows:
        raise ValueError("No monthly rows found in Ken French file")
    df = pd.DataFrame(rows, columns=["date"] + header)
    df.index = pd.PeriodIndex(df.pop("date"), freq="M")
    df = df.apply(pd.to_numeric, errors="coerce")
    df.columns = [c.strip() for c in df.columns]
    return df


def _download_french(name: str) -> pd.DataFrame:
    """Fetch one dataset: pandas-datareader first, direct zip as fallback."""
    try:
        from pandas_datareader import data as pdr  # noqa: WPS433

        tables = pdr.DataReader(name, "famafrench", start="1960-01-01")
        df = tables[0].copy()  # table 0 is always the monthly series
        df.index = pd.PeriodIndex(df.index, freq="M")
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as exc:  # datareader breaks with some pandas versions
        print(f"  pandas-datareader failed for {name} ({exc!r}); downloading zip directly")
    import requests

    resp = requests.get(FRENCH_URL.format(name=name), timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        member = zf.namelist()[0]
        text = zf.read(member).decode("latin-1")
    return parse_french_csv(text)


def load_factors(cache_dir: Path, refresh: bool = False) -> pd.DataFrame:
    """Monthly Mkt-RF, SMB, HML, RMW, CMA, MOM and RF in decimals."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "french_factors_monthly.csv"
    if cache.exists() and not refresh:
        df = pd.read_csv(cache, index_col=0)
        df.index = pd.PeriodIndex(df.index, freq="M")
        return df

    ff5 = _download_french(FF5_NAME)
    mom = _download_french(MOM_NAME)
    mom.columns = ["MOM"]  # file calls it "Mom" (older versions "Mom   ")
    df = ff5.join(mom, how="inner")
    df = df[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM", "RF"]] / 100.0
    df = df.dropna()
    df.to_csv(cache)
    return df


# --------------------------------------------------------------------------
# Fund returns
# --------------------------------------------------------------------------
def prices_to_monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily total-return prices -> calendar-month simple returns.

    The month in which a fund launches has no prior month-end price, so its
    return is NaN; the first non-NaN value is therefore the first *full* month.
    The current, incomplete month is dropped.
    """
    month_end = prices.resample("ME").last()
    month_end.index = month_end.index.to_period("M")
    rets = month_end.pct_change(fill_method=None)
    current = pd.Timestamp.today().to_period("M")
    return rets[rets.index < current]


def load_fund_returns(tickers: list[str], cache_dir: Path, refresh: bool = False) -> pd.DataFrame:
    """Monthly total returns (dividends reinvested) from Yahoo Finance."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "fund_returns_monthly.csv"
    if cache.exists() and not refresh:
        df = pd.read_csv(cache, index_col=0)
        df.index = pd.PeriodIndex(df.index, freq="M")
        if set(tickers) <= set(df.columns):
            return df[tickers]

    import yfinance as yf

    raw = yf.download(tickers, start="2000-01-01", auto_adjust=True,
                      progress=False, group_by="column")
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if not isinstance(prices, pd.DataFrame):
        prices = prices.to_frame(tickers[0])
    if prices.shape[1] == 1 and len(tickers) == 1:
        prices.columns = tickers
    missing = [t for t in tickers if t not in prices.columns or prices[t].dropna().empty]
    if missing:
        raise RuntimeError(f"No price data returned for: {missing}")
    rets = prices_to_monthly_returns(prices[tickers])
    rets.to_csv(cache)
    return rets


def first_full_month(returns: pd.Series) -> pd.Period:
    return returns.dropna().index.min()


def fund_sample(returns: pd.Series, start: pd.Period, end: pd.Period) -> pd.Series:
    """Fund returns clipped to [max(start, first full month), end]."""
    r = returns.dropna()
    begin = max(start, first_full_month(r))
    return r.loc[begin:end]


# --------------------------------------------------------------------------
# Synthetic data for offline testing (never mixed with real results)
# --------------------------------------------------------------------------
def synthetic_data(seed: int = 7, end: str = "2026-07") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulated factors + fund returns with *known* alphas and loadings.

    Used by the test suite and `run.py --demo` to check that the pipeline
    recovers the true parameters. Outputs are labelled SYNTHETIC.
    """
    rng = np.random.default_rng(seed)
    idx = pd.period_range("2005-01", end, freq="M")
    n = len(idx)
    means = np.array([0.007, 0.001, 0.000, 0.003, 0.002, 0.004])
    vols = np.array([0.044, 0.025, 0.030, 0.020, 0.018, 0.040])
    f = rng.normal(means, vols, size=(n, 6))
    factors = pd.DataFrame(f, index=idx, columns=["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM"])
    factors["RF"] = np.clip(rng.normal(0.001, 0.0005, n), 0, None)

    # true monthly alpha and FF5+MOM loadings, regime switch at 2024-03 for AI funds
    truth = {
        "SPY":   (0.0000, [1.00, 0.00, 0.00, 0.00, 0.00, 0.00], None),
        "IWM":   (0.0000, [1.05, 0.90, 0.15, -0.20, 0.00, -0.05], None),
        "IWD":   (0.0000, [0.95, -0.10, 0.45, 0.10, 0.20, -0.05], None),
        "IWF":   (0.0000, [1.02, -0.15, -0.35, 0.10, -0.25, 0.05], None),
        "PDP":   (0.0000, [1.05, 0.20, -0.05, -0.05, 0.00, 0.45], None),
        "FCNTX": (0.0010, [0.95, -0.15, -0.20, 0.15, -0.10, 0.10], None),
        "ARKK":  (0.0000, [1.50, 0.60, -0.70, -0.80, -0.50, 0.20], None),
        "BOTZ":  (0.0020, [1.20, 0.10, -0.40, -0.20, -0.30, 0.10],
                  (0.0000, [1.35, 0.00, -0.60, 0.00, -0.40, 0.45])),
        "AIQ":   (0.0030, [1.15, -0.05, -0.45, 0.00, -0.30, 0.05],
                  (0.0000, [1.25, -0.10, -0.60, 0.10, -0.40, 0.40])),
    }
    starts = {"ARKK": "2014-11", "BOTZ": "2016-10", "AIQ": "2018-06"}
    rets = {}
    post = idx >= pd.Period("2024-03", "M")
    for t, (a, b, regime2) in truth.items():
        b = np.array(b)
        r = a + f @ b + rng.normal(0, 0.012 if t != "SPY" else 0.002, n)
        if regime2 is not None:
            a2, b2 = regime2
            r2 = a2 + f @ np.array(b2) + rng.normal(0, 0.012, n)
            r = np.where(post, r2, r)
        s = pd.Series(r + factors["RF"].values, index=idx)
        if t in starts:
            s[s.index < pd.Period(starts[t], "M")] = np.nan
        rets[t] = s
    return factors, pd.DataFrame(rets)
