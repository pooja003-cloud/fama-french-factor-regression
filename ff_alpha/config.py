"""Study configuration: fund universe, sample periods and regression settings.

Everything a reader might want to change lives here, so the rest of the
pipeline never hard-codes a ticker or a date.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Fund:
    ticker: str
    name: str
    style: str   # short label used in tables and charts
    group: str   # "established" (full 2010 sample) or "young" (starts at inception)


# 9 funds: a market sanity check, size/style/momentum ETFs, two active funds
# and two AI / robotics thematic ETFs. Each fund's start date is not typed in
# by hand: data.first_full_month() derives it from the price history, and any
# fund with fewer than MIN_MONTHS observations in a period is dropped from it.
FUNDS = [
    Fund("SPY",   "SPDR S&P 500 ETF",                     "Market (sanity check)", "established"),
    Fund("IWM",   "iShares Russell 2000 ETF",             "Small-cap",             "established"),
    Fund("IWD",   "iShares Russell 1000 Value ETF",       "Large value",           "established"),
    Fund("IWF",   "iShares Russell 1000 Growth ETF",      "Large growth",          "established"),
    Fund("PDP",   "Invesco Dorsey Wright Momentum ETF",   "Momentum",              "established"),
    Fund("FCNTX", "Fidelity Contrafund (active)",         "Active large growth",   "established"),
    Fund("ARKK",  "ARK Innovation ETF (active)",          "Active thematic",       "young"),
    Fund("BOTZ",  "Global X Robotics & AI ETF",           "AI / robotics theme",   "young"),
    Fund("AIQ",   "Global X Artificial Intelligence & Technology ETF", "AI theme", "young"),
]

# Sample periods (inclusive, monthly)
ORIGINAL_START = pd.Period("2010-01", "M")
ORIGINAL_END = pd.Period("2023-12", "M")
EXTENSION_START = pd.Period("2024-03", "M")
EXTENSION_END = None  # None = latest month published in the Ken French library

MIN_MONTHS = 60          # minimum observations in the original period
MIN_MONTHS_EXTENSION = 24  # the extension is short by construction; flagged as low power

# Regression settings
NW_LAGS_DEFAULT = 6
NW_LAGS_ROBUSTNESS = (3, 12)
ROLLING_WINDOW = 36
SIGNIFICANCE = 0.05

MODELS = {
    "CAPM":    ["Mkt-RF"],
    "FF3":     ["Mkt-RF", "SMB", "HML"],
    "FF5":     ["Mkt-RF", "SMB", "HML", "RMW", "CMA"],
    "FF5+MOM": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM"],
}
ROLLING_MODEL = "FF5+MOM"

FACTOR_LABELS = {
    "Mkt-RF": "Market",
    "SMB": "Size (small minus big)",
    "HML": "Value (high minus low B/M)",
    "RMW": "Profitability (robust minus weak)",
    "CMA": "Investment (conservative minus aggressive)",
    "MOM": "Momentum",
}

# LLM add-on (Anthropic API). Override with the FF_LLM_MODEL env variable.
LLM_MODEL_DEFAULT = "claude-sonnet-5-5"
