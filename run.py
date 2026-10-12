"""Run the full study.

    python run.py                 # real data -> results/
    python run.py --llm claude_code   # fund summaries via Claude Code (Pro plan, no API key)
    python run.py --no-llm        # same as --llm template
    python run.py --refresh       # re-download factors and prices
    python run.py --demo          # simulated data with known answers -> results_demo/
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ff_alpha import config, data, explain, models, report, rolling

ROOT = Path(__file__).parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true", help="use synthetic data (offline pipeline check)")
    ap.add_argument("--refresh", action="store_true", help="ignore cached downloads")
    ap.add_argument("--llm", choices=explain.PROVIDERS, default=config.LLM_PROVIDER,
                    help="who writes the fund summaries (default: %(default)s)")
    ap.add_argument("--no-llm", action="store_true", help="same as --llm template")
    args = ap.parse_args()

    out = ROOT / ("results_demo" if args.demo else "results")
    figs = out / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    suffix = " [SYNTHETIC DATA]" if args.demo else ""
    tickers = [f.ticker for f in config.FUNDS]
    names = {f.ticker: f.name for f in config.FUNDS}

    # 1. Data --------------------------------------------------------------
    print("Loading data...")
    if args.demo:
        factors, rets = data.synthetic_data()
    else:
        factors = data.load_factors(ROOT / "data" / "raw", refresh=args.refresh)
        rets = data.load_fund_returns(tickers, ROOT / "data" / "raw", refresh=args.refresh)
    ext_end = config.EXTENSION_END or factors.index.max()
    print(f"  factors: {factors.index.min()} to {factors.index.max()}")

    inception = pd.DataFrame({
        "Fund": tickers,
        "First full month": [str(data.first_full_month(rets[t])) for t in tickers],
        "Original-period start": [str(max(config.ORIGINAL_START, data.first_full_month(rets[t]))) for t in tickers],
    })
    print(inception.to_string(index=False))

    # 2-4. Regressions -----------------------------------------------------
    lags = (config.NW_LAGS_DEFAULT, *config.NW_LAGS_ROBUSTNESS)
    print("Running CAPM / FF3 / FF5 / FF5+MOM regressions...")
    r1, s1 = models.run_period(rets, factors, config.ORIGINAL_START, config.ORIGINAL_END,
                               config.MIN_MONTHS, "Main period 2010-2023", lags)
    r2, s2 = models.run_period(rets, factors, config.EXTENSION_START, ext_end,
                               config.MIN_MONTHS_EXTENSION, f"Extension 2024-03 to {ext_end}", lags)
    res = models.bonferroni(pd.concat([r1, r2], ignore_index=True))
    skipped = pd.concat([s1, s2], ignore_index=True)
    chg = models.structural_change(rets, factors, ext_end=ext_end)
    res.to_csv(out / "regressions.csv", index=False)
    chg.to_csv(out / "structural_change.csv", index=False)

    # Robustness: start the extension in January 2024 instead of March
    r_jan, _ = models.run_period(rets, factors, pd.Period("2024-01", "M"), ext_end,
                                 config.MIN_MONTHS_EXTENSION, f"Extension 2024-01 to {ext_end}",
                                 (config.NW_LAGS_DEFAULT,))
    r_jan = models.bonferroni(r_jan)
    r_jan.to_csv(out / "extension_from_jan2024.csv", index=False)

    # 5. Rolling -------------------------------------------------------------
    print("Rolling 36-month regressions...")
    roll = rolling.rolling_loadings(rets, factors, end=ext_end)
    roll_out = roll.copy()
    roll_out["month"] = roll_out["month"].astype(str)
    roll_out.to_csv(out / "rolling_loadings.csv", index=False)

    # Figures ----------------------------------------------------------------
    periods = list(dict.fromkeys(res.period))
    for i, p in enumerate(periods):
        tag = "main_period" if i == 0 else "extension"
        report.plot_alpha_by_model(res, p, figs / f"alpha_by_model_{tag}.png", f" ({p}){suffix}")
        report.plot_loadings_heatmap(res, p, figs / f"loadings_{tag}.png", f" ({p}){suffix}")
        report.plot_r2(res, p, figs / f"r2_{tag}.png", f" ({p}){suffix}")
    for t in tickers:
        report.plot_rolling_fund(roll, t, figs / f"rolling_{t}.png", suffix)
    report.plot_rolling_compare(roll, ["SPY", "ARKK", "BOTZ", "AIQ"], figs / "rolling_ai_vs_market.png",
                                f": AI / thematic funds vs SPY{suffix}")

    # Summary markdown -------------------------------------------------------
    md = [f"# Results{suffix}\n",
          f"Factors: Ken French library, {factors.index.min()} to {factors.index.max()}. "
          f"Newey-West lags = {config.NW_LAGS_DEFAULT} unless stated. Alpha in % per year "
          f"(monthly x 12). Bonferroni: p x number of fund-model tests in the period.\n",
          "## Sanity check\n", report.sanity_check(res), "\n",
          "## Fund samples\n", report._md_table(inception), "\n"]
    if not skipped.empty:
        md += ["Excluded from a period:\n", report._md_table(skipped), "\n"]
    for i, p in enumerate(periods):
        tag = "main_period" if i == 0 else "extension"
        md += [f"## {p}\n", f"![alpha](figures/alpha_by_model_{tag}.png)\n",
               "### Alpha by model\n", report._md_table(report.alpha_table(res, p)), "\n",
               "### FF5 + momentum loadings, beta (t-stat)\n",
               report._md_table(report.loadings_table(res, p)), "\n",
               f"![loadings](figures/loadings_{tag}.png)\n",
               "### Robustness: alpha t-stat by Newey-West lag\n",
               report._md_table(report.robustness_table(res, p)), "\n"]
        if i > 0:
            md += ["_In this short sample the short-sample guard floors most standard errors at the "
                   "plain OLS value, so many t-statistics are identical across lags. This is expected; "
                   "the unguarded Newey-West t-statistics are in `regressions.csv` (`alpha_t_nw_raw`)._\n"]
    md += ["## How the verdict depends on the test family\n",
           "Smallest adjusted p-value in each period when correcting across the 9 funds within one "
           "model, instead of across all 36 fund-model tests.\n",
           report._md_table(report.family_table(res)), "\n",
           f"## Extension starting January 2024 instead of March\n",
           f"Significant alphas after Bonferroni (36 tests): {int(r_jan.sig_bonf.sum())} of {len(r_jan)}.\n",
           report._md_table(report.alpha_table(r_jan, r_jan.period.iloc[0])), "\n"]
    md += ["## Did it hold after 2024? Change in FF5+MOM alpha and loadings, Δ (t-stat)\n",
           report._md_table(report.change_table(chg)) if not chg.empty else "_Not enough data._", "\n",
           "![rolling](figures/rolling_ai_vs_market.png)\n"]
    (out / "summary.md").write_text("\n".join(md))

    # 6. AI add-on -------------------------------------------------------------
    provider = "template" if args.no_llm else args.llm
    print(f"Writing fund summaries ({provider})...")
    text, source, audit = explain.explain_all(res, chg, names, provider=provider)
    if args.demo:
        text = text.replace("# Fund summaries", "# Fund summaries [SYNTHETIC DATA]", 1)
    (out / "explanations.md").write_text(text)
    (out / "explanations_check.json").write_text(json.dumps({"source": source, "funds": audit}, indent=2))

    print("\n" + report.sanity_check(res))
    n_sig = res[(res.nw_lags == config.NW_LAGS_DEFAULT) & res.sig_bonf]
    print(f"\nAlphas significant after Bonferroni (lag {config.NW_LAGS_DEFAULT}): "
          f"{len(n_sig)} of {len(res[res.nw_lags == config.NW_LAGS_DEFAULT])}")
    for _, r in n_sig.iterrows():
        print(f"  {r.period:28s} {r.ticker:6s} {r.model:8s} {r.alpha_ann*100:+.2f}%/yr  t={r.alpha_t:.2f}")
    print(f"Explanations written by: {source}")
    print(f"Done -> {out}/summary.md")


if __name__ == "__main__":
    main()
