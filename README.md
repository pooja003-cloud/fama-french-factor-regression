# Is it alpha, or just factors? A Fama-French regression study

_Based on my MS Quantitative Finance Empirical Methods coursework (2024); rebuilt and extended in Python in 2026._

Do well-known funds earn real alpha, or is their performance explained by exposure to common, cheaply available risk factors (market, size, value, profitability, investment, momentum)?

This project regresses the monthly excess returns of 9 funds and ETFs on the CAPM, the Fama-French 3- and 5-factor models, and the 5-factor model plus momentum, with Newey-West standard errors and Bonferroni, Holm and Benjamini-Hochberg multiple-testing corrections. Rolling 36-month regressions show how exposures drift, an out-of-sample extension asks whether the AI-themed funds' results held after 2024, and an LLM writes a plain-English summary of each fund for a non-quant reader.

> **Results:** see [`results/summary.md`](results/summary.md) for every table and figure, and [`results/explanations.md`](results/explanations.md) for the plain-English write-ups.

![Alpha by model](results/figures/alpha_by_model_main_period.png)

## Key findings

Data: Ken French factors through 2026-08, Newey-West lags = 6, alphas annualized. Full tables are in [`results/summary.md`](results/summary.md).

1. **No fund earns alpha that survives the multiple-testing correction.** That is 0 of 72 fund × model × period tests under Bonferroni, Holm *and* the looser Benjamini-Hochberg false-discovery-rate correction, and the verdict holds whether the Newey-West window is 3, 6 or 12 lags.
2. **Where CAPM alpha was positive, adding factors shrinks it.** Neither of these CAPM alphas was statistically significant to begin with: the apparent outperformance was mostly growth and investment-style tilts, not skill.

   | Fund | CAPM alpha | FF5+MOM alpha | Main tilts |
   |---|---|---|---|
   | IWF (growth) | +1.71% | +0.75% | Value −0.21, investment −0.14 |
   | Fidelity Contrafund | +1.38% | +0.55% | Investment −0.24, value −0.12 |

3. **The factors explain almost everything for broad ETFs.** FF5+MOM R² is 0.97-1.00 for SPY, IWM, IWD and IWF, against 0.78-0.91 for the thematic funds (ARKK, BOTZ, AIQ), whose returns depend more on fund-specific bets.
4. **The strongest result is negative.** IWM (small caps) earned about −1.4% a year after factors (t ≈ −3.0). It is significant at 5% on its own but not after correction: adjusted p = 0.10 (Bonferroni), 0.10 (Holm) and 0.065 (Benjamini-Hochberg). Holm cannot help here, because for the single smallest p-value it is identical to Bonferroni. See [why IWM lags](#why-does-iwm-lag-its-factors) below.
5. **ARKK is mostly a bundle of factor bets.** It has market beta 1.55, a strong growth tilt (value −0.64) and a very negative profitability loading (−1.20), meaning it leaned toward unprofitable companies.
6. **Sanity check passes.** SPY has CAPM beta 0.96-1.00 and alpha under 0.5% a year in both periods. Its small negative size loading (−0.12) is expected, because the French market factor includes small caps.

### Does it still hold after 2024? (2024-03 to 2026-08, 30 months)

![Rolling exposures](results/figures/rolling_ai_vs_market.png)

_Rolling 36-month loadings; the shaded area marks windows ending in the post-2024 extension. ARKK's and BOTZ's market betas climb toward 1.6-1.9, while the AI funds' momentum loadings stay near or below zero._

- **The AI funds' post-2024 returns were driven mainly by market beta, not momentum.** AIQ's market beta rose from 1.06 to 1.39 and BOTZ's from 1.24 to 1.41. Their momentum loadings barely changed (BOTZ +0.28, t = 1.7; AIQ +0.14, t = 0.9).
- **No new alpha appeared.** BOTZ shows −16% a year of FF5+MOM alpha after 2024 (t = −2.0 under the small-sample guard), but it is not significant after Bonferroni over 30 months.
- **Exposures do drift.** For the pre/post-2024 change in loadings, the joint test rejects "unchanged" at 5% for 7 of 9 funds. ARKK (p = 0.09) and BOTZ (p = 0.18) are the exceptions, partly because their samples are short and noisy.

All post-2024 estimates rest on 30 months of data, so treat them as indicative.

### Why does IWM lag its factors?

IWM's −1.4% a year is the one result an interviewer will push on. These are candidate explanations, not tested in this project:

- **Reconstitution drag.** The Russell 2000 is rebuilt once a year on a published schedule, so traders can buy the stocks about to be added and sell the ones about to be dropped before index funds have to trade. Cai and Houge (*Financial Analysts Journal*, 2008) found that over 1979-2004, a buy-and-hold version of the index beat the annually rebalanced one by 2.2% in the following year. More recent work suggests the cost has shrunk as liquidity improved, so this probably explains part of the gap, not all of it.
- **The index holds what the five-factor model prices worst.** Fama and French (2015) note that their model's biggest failure is small stocks that invest heavily despite low profitability, which earn less than the model predicts. The Russell 2000 holds many of these, and a linear profitability loading (−0.10 here) does not fully capture them.
- **Construction mismatch.** SMB is built from equal-weighted averages across value and profitability groups using NYSE size cut-offs, while the Russell 2000 is cap-weighted with its own size cut-offs. A loading of 0.83 on SMB is a close but imperfect proxy for what IWM actually holds.
- **Fees are not the answer.** IWM's expense ratio of about 0.2% a year is far too small to explain a 1.4% gap.

A natural next step is to regress IWM on the S&P 600 small-cap index (which reconstitutes differently and screens for profitability) to separate these effects.

## Funds

| Ticker | Fund | Role | Sample |
|---|---|---|---|
| SPY | SPDR S&P 500 ETF | Sanity check (beta ≈ 1, alpha ≈ 0) | 2010-01 to 2023-12 |
| IWM | iShares Russell 2000 | Small-cap | 2010-01 to 2023-12 |
| IWD | iShares Russell 1000 Value | Value | 2010-01 to 2023-12 |
| IWF | iShares Russell 1000 Growth | Growth | 2010-01 to 2023-12 |
| PDP | Invesco DWA Momentum | Momentum | 2010-01 to 2023-12 |
| FCNTX | Fidelity Contrafund | Active, long history | 2010-01 to 2023-12 |
| ARKK | ARK Innovation | Active, thematic | first full month to 2023-12 |
| BOTZ | Global X Robotics & AI | AI / robotics theme | first full month to 2023-12 |
| AIQ | Global X AI & Technology | AI theme | first full month to 2023-12 |

PDP is used for momentum rather than MTUM because MTUM launched in 2013 and would not cover the full 2010 sample. Young funds start at their **first full month** of returns, derived from the price history (the launch month is partial and excluded), and are dropped if they have fewer than 60 months. The fund list lives in [`ff_alpha/config.py`](ff_alpha/config.py).

## Method

**Data.** Monthly total returns (dividends reinvested) from Yahoo Finance via `yfinance`; factors and the risk-free rate from the [Kenneth French data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) via `pandas-datareader` (with a direct-download fallback). Excess returns use the **French RF column**, the same T-bill series behind `Mkt-RF`, so fund and market excess returns are measured consistently.

**Models** (all on excess returns):

| Model | Factors |
|---|---|
| CAPM | Mkt-RF |
| FF3 | + SMB, HML |
| FF5 | + RMW, CMA |
| FF5+MOM | + MOM |

**Inference.** OLS point estimates with Newey-West (HAC) standard errors, 6 lags by default; every table is re-run with 3 and 12 lags and flags any fund whose verdict changes. p-values use the t-distribution. Alpha is reported annualized (monthly × 12).

**Multiple testing.** With 9 funds × 4 models = 36 alpha tests per period, about two "significant" alphas would appear at the 5% level by luck alone. Three corrections are reported side by side:

| Method | Controls | Strictness |
|---|---|---|
| Bonferroni | Chance of *any* false positive | Strictest: `p × 36 < 0.05` |
| Holm | Same as Bonferroni | Step-down version: never less powerful, identical for the smallest p-value |
| Benjamini-Hochberg | Expected *share* of false positives | Looser: a check that conclusions aren't driven by Bonferroni's strictness |

The headline verdict uses Bonferroni; it is the same under all three.

**Short-sample guard.** In samples under 60 months (the 2024+ extension), the Newey-West estimator can pick up spurious negative autocorrelation and produce standard errors *smaller* than plain OLS. On simulated data with zero true alpha this produced a t-stat of 3.9 from 29 months (plain OLS: 1.85). Below 60 months, standard errors are therefore floored at the OLS value; the raw NW t-stat is kept in `regressions.csv` as `alpha_t_nw_raw`.

**Rolling exposures.** 36-month rolling FF5+MOM regressions for every fund, from 2010 (or inception) through the latest factor month. Point estimates only: overlapping windows are not independent tests.

## Extension: does it still hold after 2024?

The main period covers January 2010 to December 2023 (168 months for established funds). The extension runs from March 2024 to the latest month in the French library (updated with a lag of a few months), and asks: **did the AI-themed funds' alpha and exposures persist, or were their returns mostly market, growth and momentum beta?**

Three pieces of evidence:
1. The same four models re-estimated on the extension sample alone.
2. A pooled regression across both periods with a post-2024 dummy interacted with every factor: `y = a + b'f + d·POST + g'(f·POST) + e`. `d` is the change in alpha, each `g` the change in a loading, plus a joint Wald test that no loading changed.
3. Rolling 36-month loadings with the extension period shaded.

The extension is short (around 2-2.5 years), so it has low statistical power; results are framed as indicative.

![Rolling exposures](results/figures/rolling_ai_vs_market.png)

## AI add-on

[`ff_alpha/explain.py`](ff_alpha/explain.py) sends each fund's computed numbers (as JSON) to an LLM with instructions to use only those numbers, explain the 2-3 exposures that matter in everyday terms, and treat the Bonferroni-adjusted result as the final verdict. Set `ANTHROPIC_API_KEY` to enable it (model configurable with `FF_LLM_MODEL`); without a key, a deterministic template writes the summaries so the pipeline always completes.

**Sample output (ARKK).** The project's own runs used the built-in template, because the LLM step needs a paid API key. The text below was generated with Claude (claude.ai) using the same system prompt and ARKK's computed numbers from `results/regressions.csv`:

> ARKK is best understood as a magnified bet on one kind of company rather than a source of independent skill. From November 2014 to December 2023 (110 months), it moved about 1.5 to 1.7 times as much as the overall stock market, so a 10% market rise typically meant a 15-17% move for ARKK, in either direction. On top of that, it leaned toward smaller, expensive "growth" companies and, most strongly, toward unprofitable ones (a profitability loading of −1.20). Against the market alone its alpha was −2.58% a year; after accounting for these tilts it was +4.20% a year. Neither figure is statistically reliable (t = −0.26 and 0.88), and neither survives the correction for testing many funds, so the honest verdict is no detectable alpha. The factors explain about 82% of its monthly ups and downs. In the 30 months after March 2024 the picture is similar: an even stronger growth tilt (−1.37) and still no reliable alpha, though a sample this short makes the comparison uncertain.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m pytest -q                 # 8 offline tests on simulated data
python run.py --demo --no-llm       # whole pipeline on simulated data -> results_demo/
python run.py                       # real data -> results/
export ANTHROPIC_API_KEY=...        # optional, for LLM explanations
```

Downloads are cached in `data/raw/`; use `--refresh` to re-download (the French library is revised occasionally, so note the download date when quoting numbers).

### Outputs

| File | Contents |
|---|---|
| `results/summary.md` | Sanity check, fund samples, alpha and loading tables, robustness, extension tests |
| `results/regressions.csv` | Every fund × model × period × lag: alpha, t, p, Bonferroni p, loadings, R² |
| `results/structural_change.csv` | Pre/post-2024 change in alpha and loadings |
| `results/rolling_loadings.csv` | Rolling 36-month estimates |
| `results/explanations.md` | Plain-English summary per fund |
| `results/figures/` | Alpha by model, loadings heatmap, R², rolling charts |

## Validation

The test suite simulates factor returns and funds with **known** alphas and loadings (including a momentum shift after 2024 for the AI funds) and checks that the pipeline recovers them, that SPY-like funds give beta ≈ 1 and alpha ≈ 0, that a fund's launch month is excluded, that the Bonferroni, Holm and Benjamini-Hochberg adjustments are applied correctly, and that the French CSV parser handles the file layout. **8 tests, run in CI** (GitHub Actions) together with the full demo pipeline on every push.

## Interview talking points

- **Most "alpha" is factor exposure.** CAPM alpha measures performance against the market only. A fund that tilts toward small, cheap, profitable or recently winning stocks will show CAPM alpha simply because those tilts earned premiums. Adding the factors re-labels that return as beta, which can be bought cheaply through ETFs. In this sample, IWF's CAPM alpha falls from +1.7% to +0.75% and Contrafund's from +1.4% to +0.55%. Neither was significant to begin with, which is the more honest point: the apparent outperformance was never reliable, and most of it is factor tilts.
- **R² tells you how much is left to explain.** Broad ETFs here have R² of 0.97-1.00 in the factor model, so little room remains for skill. Thematic and active funds have lower R², so idiosyncratic bets drive more of their returns, in either direction.
- **Significance needs care.** Monthly returns are autocorrelated and heteroskedastic (Newey-West), you test many funds (Bonferroni), and short samples can make HAC standard errors misleadingly small (the guard above).
- **Exposures drift.** The rolling charts show loadings are not constant; a fund's "style" in one window can differ sharply from another, which matters for risk management and for judging a manager.
- **Out-of-sample discipline.** Re-testing on post-2024 data rather than re-tuning on it.

## Limitations

- Fund returns are net of fees, so alpha is what an investor actually received, not the manager's gross skill.
- The French market factor is all CRSP stocks (including small caps), so SPY's CAPM alpha is not exactly zero; large-cap outperformance shows up as a small alpha and slightly negative size loading.
- Survivorship: funds were chosen in 2026, knowing they still exist.
- Yahoo adjusted prices are convenient but not research-grade; CRSP mutual fund data would be the professional source.

## Project structure

```
ff_alpha/
  config.py    funds, periods, models, settings
  data.py      French factors, fund returns, synthetic data
  models.py    regressions, Bonferroni, pre/post-2024 test
  rolling.py   rolling 36-month regressions
  report.py    tables and figures
  explain.py   LLM plain-English explanations
run.py         runs the full study
tests/         offline tests on simulated data
```
