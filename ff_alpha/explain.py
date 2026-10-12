"""AI add-on: plain-English explanation of each fund's results.

The LLM only sees the numbers this pipeline computed and is told not to
invent any. Without an ANTHROPIC_API_KEY (or with --no-llm) a deterministic
template writes the explanation instead, so the pipeline always completes.
"""
from __future__ import annotations

import json
import os

import pandas as pd

from . import config

SYSTEM_PROMPT = """You explain factor-regression results to a smart reader with no finance training.
Rules:
- Use ONLY the numbers in the data provided. Never invent figures, dates or fund facts.
- 120-180 words, plain English, no jargon without a one-line explanation, no bullet lists.
- Say whether the fund earned real alpha after accounting for common factors, using the
  Bonferroni-adjusted verdict as the final word (a raw p < 0.05 alone is not enough).
- Describe the 2-3 factor exposures that matter most in everyday terms (e.g. "behaves like
  a bet on small companies", "leans toward recent winners").
- If CAPM alpha shrinks or vanishes in the larger models, explain that the "skill" was
  really exposure to rewarded factors.
- If extension-period data is provided, say whether the picture changed after 2024 and note
  the short sample makes that comparison uncertain.
- No investment advice."""


def fund_facts(ticker: str, name: str, res: pd.DataFrame, chg: pd.DataFrame | None) -> dict:
    d = res[(res.ticker == ticker) & (res.nw_lags == config.NW_LAGS_DEFAULT)]
    facts = {"ticker": ticker, "name": name, "periods": {}}
    for period, dp in d.groupby("period", sort=False):
        models = {}
        for _, r in dp.iterrows():
            cols = config.MODELS[r.model]
            models[r.model] = {
                "alpha_pct_per_year": round(r.alpha_ann * 100, 2),
                "alpha_t_stat": round(r.alpha_t, 2),
                "alpha_p_bonferroni": round(r.alpha_p_bonf, 3),
                "significant_after_bonferroni": bool(r.sig_bonf),
                "r_squared": round(r.r2, 3),
                "loadings": {config.FACTOR_LABELS[c]: {"beta": round(r[f"b_{c}"], 2),
                                                       "t_stat": round(r[f"t_{c}"], 1)} for c in cols},
            }
        facts["periods"][period] = {"sample": f"{dp.start.iloc[0]} to {dp.end.iloc[0]}",
                                    "months": int(dp.nobs.iloc[0]), "models": models}
    if chg is not None and not chg.empty and ticker in set(chg.ticker):
        c = chg[chg.ticker == ticker].iloc[0]
        facts["change_after_2024"] = {
            "alpha_change_pct_per_year": round(c.d_alpha_ann * 100, 2),
            "alpha_change_t_stat": round(c.d_alpha_t, 2),
            "p_value_all_loadings_unchanged": round(c.loadings_changed_p, 3),
            "loading_changes": {config.FACTOR_LABELS[k]: round(c[f"d_{k}"], 2)
                                for k in config.MODELS[config.ROLLING_MODEL]},
        }
    return facts


def template_explanation(f: dict) -> str:
    """Deterministic fallback used when no LLM is available."""
    parts = []
    for period, p in f["periods"].items():
        capm, full = p["models"]["CAPM"], p["models"]["FF5+MOM"]
        top = sorted(((k, v) for k, v in full["loadings"].items() if k != "Market"),
                     key=lambda kv: -abs(kv[1]["beta"]))[:2]
        tilts = ", ".join(f"{k.split(' (')[0].lower()} ({v['beta']:+.2f})" for k, v in top)
        verdict = ("still shows statistically reliable alpha" if full["significant_after_bonferroni"]
                   else "shows no alpha that survives the multiple-testing correction")
        parts.append(
            f"**{period} ({p['sample']}, {p['months']} months).** Measured against the market alone, "
            f"{f['ticker']} earned {capm['alpha_pct_per_year']:+.2f}% a year of alpha. After adding size, "
            f"value, profitability, investment and momentum factors that becomes "
            f"{full['alpha_pct_per_year']:+.2f}% a year (t = {full['alpha_t_stat']:.2f}), so the fund {verdict}. "
            f"Its market beta is {full['loadings']['Market']['beta']:.2f} and its largest style tilts are "
            f"{tilts}. Together the factors explain {full['r_squared']*100:.0f}% of its month-to-month returns.")
    if "change_after_2024" in f:
        c = f["change_after_2024"]
        parts.append(f"**After 2024.** Alpha changed by {c['alpha_change_pct_per_year']:+.2f}% a year "
                     f"(t = {c['alpha_change_t_stat']:.2f}); a joint test that all loadings stayed the same "
                     f"gives p = {c['p_value_all_loadings_unchanged']:.3f}. The post-2024 sample is short, "
                     f"so treat this comparison as tentative.")
    return "\n\n".join(parts)


def llm_explanation(f: dict, client, model: str) -> str:
    msg = client.messages.create(
        model=model, max_tokens=600, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "Explain these results:\n\n" + json.dumps(f, indent=1)}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def explain_all(res: pd.DataFrame, chg: pd.DataFrame | None, names: dict[str, str],
                use_llm: bool = True) -> tuple[str, str]:
    """Returns (markdown, source) where source names who wrote the text."""
    client, model, source = None, os.environ.get("FF_LLM_MODEL", config.LLM_MODEL_DEFAULT), "template"
    if use_llm and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic

            client = anthropic.Anthropic()
            source = f"LLM ({model})"
        except ImportError:
            print("  anthropic package not installed; using template explanations")
    sections = []
    for ticker in dict.fromkeys(res.ticker):
        facts = fund_facts(ticker, names.get(ticker, ticker), res, chg)
        text = None
        if client is not None:
            try:
                text = llm_explanation(facts, client, model)
            except Exception as exc:
                print(f"  LLM call failed for {ticker} ({exc!r}); using template")
        sections.append(f"## {ticker}: {facts['name']}\n\n{text or template_explanation(facts)}")
    header = (f"# Plain-English results\n\n_Written by: {source}. Every number comes from "
              f"`results/regressions.csv`; check there before quoting._\n")
    return header + "\n\n" + "\n\n".join(sections) + "\n", source
