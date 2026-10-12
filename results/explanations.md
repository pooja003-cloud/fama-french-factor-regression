# Fund summaries

_Written by: Claude Code (sonnet); model: claude-sonnet-5-5. 9 of 9 summaries came from the language model; every number in them was checked against `results/regressions.csv`, and any summary that failed the check was replaced by the fixed template._


## SPY: SPDR S&P 500 ETF

SPY, the fund tracking the S&P 500 index, shows no evidence of manager skill. Skill here means "alpha," the return left over after accounting for the risks the fund takes. After correcting for the many tests run, no alpha was statistically distinguishable from zero, and none passed even within a single model's nine funds. In the market-only model, alpha was 0.39% per year. It shrank to 0.05 with size and value factors added, then turned slightly negative at -0.18 in the larger model. So the small apparent edge was really exposure to common return drivers.

The biggest exposure is the overall market: a beta of 0.99 means the fund moves almost one-for-one with stocks generally. Second, a size loading of -0.12 shows a mild tilt toward large companies over small ones. Third, a profitability loading of 0.06 shows a faint lean toward firms with strong profits. It shows essentially no tilt toward recent winners.

After March 2024, the picture looks much the same. The alpha change was negligible, and the loadings did not significantly change after correction. Only 30 months of data make that comparison uncertain.

_Source: language model, numbers checked._

## IWM: iShares Russell 2000 ETF

IWM, a fund holding small U.S. companies, shows no convincing evidence of skill. After correcting for the many tests run across all funds and models, no model finds a reliable alpha (return left over after accounting for common drivers of returns). There is moderate evidence of a negative alpha in two models, the three-factor model and the five-factor-plus-momentum model, with roughly -1.6 and -1.4 percentage points per year. The market-only model showed -4.16, but that shrinks in the larger models, so much of the apparent shortfall came from exposure to common factors rather than stock picking.

The fund moves about one-for-one with the overall market and behaves strongly like a bet on small companies (size loading about 0.83). It also leans slightly toward stocks priced low relative to their accounting value and toward less profitable firms.

After 2024, the 30-month sample shows alpha still negative, about -3.65 in the fullest model. The change is not statistically distinguishable from before (t-stat -1.36). The factor loadings did change significantly, mainly a stronger tilt toward stocks priced low relative to their accounting value (up 0.19), though the short sample makes this uncertain.

_Source: language model, numbers checked._

## IWD: iShares Russell 1000 Value ETF

IWD, the iShares Russell 1000 Value ETF, shows no evidence of skill or lack of it. Its alpha (return beyond what common risk factors explain) was slightly negative in every model for 2010-2023, about -1.77% a year in the market-only model and -1.36% in the fullest one, and none was significant after correcting for all 36 tests run. The fund mainly behaves like the overall market, with a market sensitivity of 0.93, plus a clear tilt toward value stocks, meaning those priced low relative to their accounting value (loading 0.26). It also has a small tilt toward companies that invest conservatively (0.14). Because these factors explain so much, the market-only alpha moved a little but never became meaningful.

After 2024, the 30-month sample is short, so comparisons are uncertain. The alpha barely changed (change t-stat 0.02), and it remained insignificant. The factor loadings did change significantly after correction, mainly a stronger value tilt, rising by 0.31.

_Source: language model, numbers checked._

## IWF: iShares Russell 1000 Growth ETF

The iShares Russell 1000 Growth ETF (IWF) shows no evidence of investment skill. Alpha, the return left over after accounting for market and style effects, was not statistically significant in any model, even before the strict correction for running many tests at once. In the market-only model, alpha was about 1.7% per year. In the larger models it shrank to roughly 0.8%, so the apparent outperformance mostly reflected exposure to common factors rather than skill.

The clearest exposure is a strong lean away from value stocks, meaning those priced low relative to their accounting value. IWF behaves like a bet on growth companies. It also tilts toward big companies rather than small ones, and its market sensitivity (beta) is about 1.06, so it moves slightly more than the overall market. It also leans mildly toward firms that invest aggressively.

After 2024, alpha turned slightly lower, but the change was tiny and statistically indistinguishable from zero. The factor loadings did change significantly, mainly through a stronger tilt away from value. With only 30 months of data, that comparison is uncertain.

_Source: language model, numbers checked._

## PDP: Invesco Dorsey Wright Momentum ETF

PDP is a fund that buys stocks that have recently been rising. The analysis asks whether it earned anything beyond what its exposure to common market drivers (called factors) would predict. That leftover is called alpha. For 2010 to 2023, alpha was negative in every model, about -1.97% a year in the fullest one. After correcting for the many tests run, none of this is statistically distinguishable from zero, so there is no evidence of skill or of its absence.

The fund moves almost one-for-one with the overall market (a market exposure of 0.99 to 1.03). It leans strongly toward recent winners, with a momentum loading of 0.27. It also tilts away from stocks priced low relative to their accounting value, with a value loading of -0.1, and slightly toward smaller companies.

From March 2024 to August 2026, only 30 months, alpha was more negative, at -5.57% a year. The change from the earlier period was not statistically meaningful. The factor exposures did change significantly, with momentum rising to 0.6. The short sample makes this comparison uncertain.

_Source: language model, numbers checked._

## FCNTX: Fidelity Contrafund (active)

Fidelity Contrafund shows no statistical evidence of manager skill. In the 2010-2023 period, its "alpha" (return beyond what its risks explain) was not significant in any of the four models, even after correcting for the many tests run. That also holds when each model is judged among the nine funds. The simple market-only estimate of 1.38% a year shrank to 0.54% once size, value, and momentum were added, and 0.55% in the fullest model. So the apparent edge mostly reflected exposure to common factors, and it was never distinguishable from zero.

Three exposures matter most. The fund moves almost one-for-one with the overall market (about 0.98). It leans toward growth stocks, which are priced high relative to their accounting value (value loading -0.24 in one model). It also tilts toward large companies and, more modestly, toward firms that invest aggressively.

After 2024, alpha rose by 1.67 points a year, but its t-statistic of 0.89 means that change is not reliable. The factor loadings did change significantly after correction, notably the investment tilt, which turned from negative to positive. With only 30 months, that comparison remains uncertain.

_Source: language model, numbers checked._

## ARKK: ARK Innovation ETF (active)

ARK Innovation ETF shows no evidence of investing skill. After correcting for the many comparisons run, none of the 36 tests is significant, and no single model reaches significance even among its own nine funds. Alpha, the return left over after accounting for common drivers, was -2.58% a year against the market alone, then -1.35%, 3.76% and 4.2% as more factors were added. Its sign changed, which suggests the early picture mostly reflected exposure to common factors, and every version is statistically indistinguishable from zero.

The fund's behavior is clearer. It amplifies the market, with a beta (sensitivity) of about 1.5 to 1.7. It behaves like a bet on small companies, and leans strongly away from value stocks, which are priced low relative to their accounting value, favoring expensive growth names. It also tilts toward firms with weak profitability.

After 2024, over just 30 months, the pattern looked similar. The alpha change was small (t-stat 0.19), and loadings did not significantly change after correction. The short sample makes this comparison uncertain.

_Source: language model, numbers checked._

## BOTZ: Global X Robotics & AI ETF

The Global X Robotics & AI ETF (BOTZ) shows no reliable evidence of investment skill. Skill is measured by "alpha," the return left over after accounting for the fund's exposure to broad market patterns. In 2016-2023, alpha was negative in every model, from -4.99% a year in the market-only model to about -2.4% in the richest one. None of these was statistically significant, even before the stricter correction for running many tests. The shrinkage suggests the apparent shortfall partly reflected common factor exposures rather than manager choices.

The fund's biggest trait is high market sensitivity: a beta of about 1.25 means it tends to move more than the overall stock market. It also leans toward growth stocks, meaning companies not priced low relative to their accounting value (value loading -0.35 in the three-factor model). In the larger models it tilts toward firms with weaker profitability (about -0.4).

After March 2024, alpha looked worse, around -16% to -17% a year. The change of -13.68 has a t-statistic of -1.56, which is not convincing, and 30 months is a short sample. The factor exposures did not change significantly.

_Source: language model, numbers checked._

## AIQ: Global X Artificial Intelligence & Technology ETF

AIQ is an exchange-traded fund holding artificial intelligence and technology companies. The data show no evidence of skill. Alpha, the return left over after accounting for broad market forces, was 1.8% a year in the market-only model and 3.6% in the richest model. After correcting for running 36 tests, none of these is distinguishable from luck, and none is significant even among the nine funds within each model.

The fund's main trait is high market sensitivity. Its beta, a measure of how strongly it moves with the overall stock market, was about 1.1, so it tends to swing a bit more than the market. It also has a negative value loading, meaning it behaves like the opposite of stocks priced low relative to their accounting value: a growth-oriented tilt. Its small-company tilt was mild and faded in the larger models.

After 2024, alpha barely changed, down 2.1 points with a t-statistic of -0.46, which is noise. The factor loadings did change significantly after correction: market sensitivity rose, and the fund leaned toward large companies and less profitable firms. With only 30 months of data, that comparison is uncertain.

_Source: language model, numbers checked._
