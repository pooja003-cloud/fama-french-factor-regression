# Fund summaries

_Written by: Claude Code (sonnet); model: claude-sonnet-5-5. 9 of 9 summaries came from the language model; every number in them was checked against `results/regressions.csv`, and any summary that failed the check was replaced by the fixed template._


## SPY: SPDR S&P 500 ETF

SPY, a fund that simply tracks the S&P 500, shows no reliable alpha in any of the four models for 2010 to 2023. Alpha is the return left over after accounting for the fund's exposure to broad market drivers, and for an index fund it reflects how the index performed relative to those exposures, not anyone's skill. The market-only estimate was 0.39% per year, but it shrank to 0.05% with size and value added, then turned slightly negative at -0.18% in the larger model. So the small positive figure came from common factor exposures, and none of these estimates differs meaningfully from zero.

The key exposure is the market, with a beta (sensitivity) of 0.99, so SPY moves almost one-for-one with stocks overall. It also leans toward large companies, with a size loading of -0.12, and slightly toward highly profitable firms, at 0.06. Momentum is essentially absent.

After 2024, the alpha change had a t-statistic of just 0.12, and the loadings did not significantly shift after correction. Only 30 months of data make this comparison uncertain.

_Source: language model, numbers checked._

## IWM: iShares Russell 2000 ETF

There is moderate evidence that IWM underperformed, in the Fama-French three-factor model and the five-factor-plus-momentum model, but this does not survive the strictest correction for running many tests at once. Alpha is the return left over after accounting for the fund's exposure to common drivers of returns. Because IWM is an index fund, its alpha reflects how the Russell 2000 index performed relative to those exposures, not manager skill. The market-only (CAPM) model showed alpha of -4.16% a year, but in the larger models it shrinks to between -1.2% and -1.6%. Much of what looked like weakness was really exposure to common factors. The biggest exposure is size: IWM behaves like a bet on small companies (0.86 in the three-factor model). It also moves roughly one-for-one with the overall market and leans slightly toward less profitable firms (-0.1). After 2024, alpha was more negative, but the change is statistically unclear (t-stat -1.36), and 30 months is a short sample. The factor loadings did change significantly, mainly a rise in the tilt toward stocks priced low relative to their accounting value, from 0.1 to about 0.3.

_Source: language model, numbers checked._

## IWD: iShares Russell 1000 Value ETF

IWD is an index fund of large U.S. companies priced low relative to their accounting value. It shows no reliable evidence of alpha, meaning return beyond what its exposures to common market drivers (called factors) would predict. From 2010 to 2023 its estimated alpha was negative, about -1.77% a year in the market-only model and between -1.17% and -1.52% in the richer models. None of these survived statistical correction for running many tests. Because this is an index fund, the figure describes how the index performed relative to its exposures, not manager skill. The estimate shrank somewhat once other factors were included, so part of it reflected common exposures.

Three exposures matter most. The fund moves almost one-for-one with the overall market (loading about 0.93). It tilts toward value stocks (0.33 in the three-factor model). It behaves like a bet on large companies, since its small-company exposure is near zero (-0.03).

After 2024, alpha barely changed (0.05 points a year). The value tilt grew stronger, reaching 0.64 in the three-factor model, and the loadings changed significantly even after correction. The sample is only 30 months, so this comparison is uncertain.

_Source: language model, numbers checked._

## IWF: iShares Russell 1000 Growth ETF

IWF, an index fund tracking large growth companies, shows no statistically reliable alpha, meaning return beyond what its exposures to common factors would predict. This holds even under the strictest correction for running many tests. In the market-only model, alpha was 1.71% a year, but it shrank to about 0.75% once size, value, profitability, investment and momentum were added. That small figure is simply how the index performed relative to its exposures, and it is too uncertain to count as meaningful.

Three exposures matter most. The fund has a market beta (sensitivity to overall stock market moves) of about 1.06, so it moves slightly more than the market. Its value loading is negative, about -0.21, so it behaves like a bet on stocks priced high relative to their accounting value, which is what growth means. Its size loading of about -0.12 shows a lean toward big companies over small ones.

From 2024-03 onward, alpha stayed statistically indistinguishable from zero, with a change of -0.36 points and a t-stat of -0.15. The factor loadings did change significantly, with the growth tilt deepening to about -0.46. The sample is only 30 months, so this comparison is uncertain.

_Source: language model, numbers checked._

## PDP: Invesco Dorsey Wright Momentum ETF

Over 2010-2023, there is no reliable evidence that Invesco Dorsey Wright Momentum ETF (PDP) beat or lagged what its exposures predict. Its alpha, the return left over after accounting for common drivers of stock returns, ranged from -0.81 to -1.97 percentage points a year across the four models. None was statistically distinguishable from zero, even before the strictest correction for running many tests. Because PDP is an index fund, this describes how its index performed relative to its factor exposures, not manager skill.

The main exposures are as follows. It moves almost one-for-one with the overall market (a beta of about 0.99). Once momentum is included, it clearly leans toward recent winners (0.27). It also tilts away from stocks priced low relative to their accounting value (-0.1 to -0.23).

After 2024, over just 30 months, the alpha estimate fell by 3.59 points a year. The t-statistic of -1.18 says that is not a clear change. The factor loadings did change significantly, however, with the momentum lean rising to 0.6. The short sample makes this comparison uncertain.

_Source: language model, numbers checked._

## FCNTX: Fidelity Contrafund (active)

Fidelity Contrafund, an actively managed large-growth fund, shows no reliable evidence of alpha (return beyond what its exposures to common market factors would predict). In 2010-2023 the simple market-only estimate was 1.38% a year, but it shrank to 0.55% once the fuller models were used, and none of the estimates survived the strict correction for running many tests. The apparent edge mostly reflected the fund's factor exposures. Three of these matter most. It moves almost one-for-one with the overall market (beta 0.98). It leans toward large companies, and toward growth stocks, meaning stocks priced high relative to their accounting value. It also tilts toward firms that invest aggressively, with a slight lean toward recent winners.

After 2024 the picture is mixed, though only 30 months of data make comparisons uncertain. Alpha rose to 2.22% a year in the fullest model, but the change of 1.67 points has a t-statistic of 0.89, which is well within chance. The factor loadings did change significantly, mainly the investment tilt, which moved from -0.24 to 0.21.

_Source: language model, numbers checked._

## ARKK: ARK Innovation ETF (active)

ARK Innovation ETF, an actively managed fund, shows no statistically reliable alpha, meaning no return beyond what its exposure to common market drivers (called factors) would predict. This holds in all four models for 2014-2023, even after correcting for the many tests run. Using only the market as a yardstick, the fund looked like it lagged by about 2.6% a year. In the richer models the sign flipped to roughly 3.8% to 4.2% a year. Neither figure is distinguishable from zero, so the apparent weakness mostly reflected factor exposure rather than manager skill or its absence.

Three exposures matter most. First, the fund amplifies market swings, with a market beta (sensitivity) of about 1.5 to 1.7. Second, it behaves like a bet on small companies. Third, it leans toward growth stocks, which are priced high relative to their accounting value, and toward firms with weak profitability.

After 2024, the alpha estimate barely changed, and that change was statistically negligible. The factor loadings did not change significantly after correction, though the 30-month sample is short, so this comparison is uncertain.

_Source: language model, numbers checked._

## BOTZ: Global X Robotics & AI ETF

BOTZ, an index fund tracking AI and robotics companies, shows no reliable alpha, meaning no return beyond what its exposures to common market drivers (called factors) would predict. In the 2016-2023 sample, the market-only estimate was -4.99% per year, shrinking to -2.44% once all factors were included, and none of these results was statistically meaningful after correction. So the index's modest shortfall mostly reflected how it was exposed to those factors rather than anything separate.

The largest exposure is to the overall stock market: a beta (sensitivity) of about 1.24, so the fund tends to move more than the market. It also leans away from priced-low-relative-to-accounting-value stocks in the simpler model (-0.35), behaving like a growth bet. It tilts slightly away from firms with strong profitability (-0.42).

After 2024, the estimated alpha fell to about -16 to -17% per year, but the change had a t-statistic of -1.56, too weak to be confident about. With only 30 months, the comparison is uncertain. The loadings did not significantly change.

_Source: language model, numbers checked._

## AIQ: Global X Artificial Intelligence & Technology ETF

AIQ is an index fund focused on artificial intelligence and technology companies. From mid-2018 to 2023, its alpha (return left over after accounting for common market drivers) was 1.84% per year using the market-only model and 3.64% with the fullest model. Neither is statistically distinguishable from zero, even before the strictest corrections, so there is no reliable evidence of alpha. Because this is an index fund, that figure only describes how the index performed relative to its exposures, not any manager's skill.

Three exposures matter most. First, the fund moves slightly more than the overall market (a market beta of about 1.1). Second, it leans toward stocks priced high relative to their accounting value, a growth-style tilt (about -0.3). Third, it holds a little less in highly profitable firms than the typical stock, a tilt that becomes much stronger later.

After 2024, the alpha estimate fell by 2.12 points per year, but with a t-statistic of -0.46 that change is negligible. The factor loadings did change significantly: market sensitivity rose to about 1.4, and the profitability tilt deepened to about -0.8. The 30-month sample is short, so the comparison is uncertain.

_Source: language model, numbers checked._
