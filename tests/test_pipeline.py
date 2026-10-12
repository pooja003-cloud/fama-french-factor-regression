"""Tests run fully offline on simulated data with known true parameters."""
import numpy as np
import pandas as pd
import pytest

from ff_alpha import config, data, models, rolling


@pytest.fixture(scope="module")
def synth():
    return data.synthetic_data()


def test_recovers_known_loadings(synth):
    factors, rets = synth
    ex = models.excess_returns(data.fund_sample(rets["IWD"], config.ORIGINAL_START, config.ORIGINAL_END), factors)
    r = models.regress(ex, factors, config.MODELS["FF5+MOM"], nw_lags=6)
    assert r["b_Mkt-RF"] == pytest.approx(0.95, abs=0.05)
    assert r["b_HML"] == pytest.approx(0.45, abs=0.07)
    assert r["b_MOM"] == pytest.approx(-0.05, abs=0.06)
    assert abs(r["alpha_t"]) < 3


def test_spy_sanity(synth):
    factors, rets = synth
    ex = models.excess_returns(rets["SPY"], factors)
    r = models.regress(ex, factors, ["Mkt-RF"], nw_lags=6)
    assert r["b_Mkt-RF"] == pytest.approx(1.0, abs=0.05)
    assert abs(r["alpha_ann"]) < 0.01


def test_first_full_month_and_min_months(synth):
    factors, rets = synth
    assert data.first_full_month(rets["AIQ"]) == pd.Period("2018-06", "M")
    res, skipped = models.run_period(rets, factors, config.ORIGINAL_START, config.ORIGINAL_END,
                                     config.MIN_MONTHS, "orig", (6,))
    assert set(res.ticker) == set(rets.columns)  # all funds have >= 60 months
    assert skipped.empty
    aiq = res[(res.ticker == "AIQ")].iloc[0]
    assert aiq.start == "2018-06" and aiq.nobs == 67


def test_bonferroni():
    df = pd.DataFrame({"period": ["a"] * 4, "nw_lags": [6] * 4, "model": ["m1", "m1", "m2", "m2"],
                       "alpha_p": [0.001, 0.02, 0.3, 0.9]})
    out = models.bonferroni(df)
    assert list(out.alpha_p_bonf) == pytest.approx([0.004, 0.08, 1.0, 1.0])
    assert list(out.sig_bonf) == [True, False, False, False]
    assert list(out.sig_raw) == [True, True, False, False]
    # Holm: sorted p x (m, m-1, ...), made monotone -> never above Bonferroni
    assert list(out.alpha_p_holm) == pytest.approx([0.004, 0.06, 0.6, 0.9])
    assert (out.alpha_p_holm <= out.alpha_p_bonf + 1e-12).all()
    # Benjamini-Hochberg: p x m / rank, made monotone
    assert list(out.alpha_p_bh) == pytest.approx([0.004, 0.04, 0.4, 0.9])
    # per-model family: 2 tests per model
    assert list(out.alpha_p_bonf_model) == pytest.approx([0.002, 0.04, 0.6, 1.0])
    assert list(out.sig_holm_model) == [True, True, False, False]


def test_structural_change_detects_momentum_shift(synth):
    factors, rets = synth
    chg = models.structural_change(rets[["SPY", "AIQ"]], factors)
    aiq = chg.set_index("ticker").loc["AIQ"]
    assert aiq["d_MOM"] == pytest.approx(0.35, abs=0.15)  # true change 0.05 -> 0.40
    assert aiq["dt_MOM"] > 2


def test_rolling_window(synth):
    factors, rets = synth
    roll = rolling.rolling_loadings(rets[["SPY"]], factors)
    assert roll.month.min() == pd.Period("2012-12", "M")  # first 36-month window from 2010-01
    assert roll["Mkt-RF"].between(0.9, 1.1).all()


def test_parse_french_csv():
    text = (
        "This file was created by CMPT_ME_BEME_OP_INV_RETS using the 202608 CRSP database.\n"
        "The 1-month TBill return is from Ibbotson and Associates Inc.\n\n"
        ",Mkt-RF,SMB,HML,RMW,CMA,RF\n"
        "196307,  -0.39,  -0.48,  -0.81,   0.64,  -1.15,   0.27\n"
        "196308,   5.07,  -0.80,   1.70,   0.40,  -0.38,   0.25\n\n"
        "  Annual Factors: January-December \n"
        ",Mkt-RF,SMB,HML,RMW,CMA,RF\n"
        "1964,  12.0,  1.0,  2.0,  3.0,  4.0,  3.5\n"
    )
    df = data.parse_french_csv(text)
    assert list(df.columns) == ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]
    assert len(df) == 2
    assert df.loc[pd.Period("1963-08", "M"), "Mkt-RF"] == pytest.approx(5.07)


def test_monthly_returns_first_month_is_nan():
    idx = pd.bdate_range("2020-01-15", "2020-04-30")
    prices = pd.DataFrame({"X": np.linspace(100, 110, len(idx))}, index=idx)
    r = data.prices_to_monthly_returns(prices)["X"]
    assert np.isnan(r.loc[pd.Period("2020-01", "M")])  # partial launch month excluded
    assert data.first_full_month(r) == pd.Period("2020-02", "M")
