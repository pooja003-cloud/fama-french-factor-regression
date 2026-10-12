"""AI add-on: an everyday-language summary of each fund's results.

The language model only sees the numbers this pipeline computed (as JSON) and
is told not to introduce any others. Every number in its answer is then
checked against those results; a summary that fails the check is retried
once and otherwise replaced by the fixed template, so nothing unverified is
published.

Providers (same names and setup as my llm-earnings-signal project):

    claude_code  Claude Code CLI (`claude -p`) signed in with a Claude Pro/Max
                 plan. No API key; counts toward the plan's normal usage limits.
    anthropic    the paid Claude API, using ANTHROPIC_API_KEY.
    template     a fixed template; no language model at all.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile

import pandas as pd

from . import config

PROVIDERS = ("claude_code", "anthropic", "template")

SYSTEM_PROMPT = """You explain factor-regression results about one investment fund to a smart reader with no finance training.

Rules:
- Use ONLY numbers that appear in the data provided. Do not introduce any other number,
  not even an illustrative example such as "a 10% market rise". Round a number only to
  fewer decimal places (for example 1.42 may become 1.4).
- 120-180 words of flowing prose: no headings, no bullet lists, no markdown.
- Explain any technical term in a few words the first time you use it.
- Verdict on skill: use `significant_after_correction_all_36_tests` as the main verdict.
  If that is false but `significant_within_this_models_9_funds` is true for some models,
  say there is moderate evidence, name those models, and say whether the alpha is positive
  or negative. A raw p-value below 0.05 alone is never enough.
- Describe the 2-3 factor exposures that matter most in everyday terms (for example
  "behaves like a bet on small companies", "leans toward recent winners").
- If the market-only (CAPM) alpha shrinks or changes sign in the larger models, explain
  that what looked like skill or its absence was really exposure to common factors.
- If extension-period data is provided, say whether the picture changed after 2024 and
  that the short sample makes the comparison uncertain. The joint test p-values are about
  whether the factor LOADINGS changed, not alpha: judge the alpha change only by
  `alpha_change_t_stat`. Say the loadings changed only if
  `loadings_changed_significant_after_correction` is true.
- Describe value stocks as "priced low relative to their accounting value", never as "cheap".
- No investment advice. Write about the fund in the third person."""

USER_TEMPLATE = "Explain these results for {ticker}:\n\n{facts}"


# ---------------------------------------------------------------- facts
def fund_facts(ticker: str, name: str, res: pd.DataFrame, chg: pd.DataFrame | None) -> dict:
    d = res[(res.ticker == ticker) & (res.nw_lags == config.NW_LAGS_DEFAULT)]
    facts = {"ticker": ticker, "name": name, "periods": {}}
    for period, dp in d.groupby("period", sort=False):
        models = {}
        for _, r in dp.iterrows():
            cols = config.MODELS[r.model]
            m = {
                "alpha_pct_per_year": round(r.alpha_ann * 100, 2),
                "alpha_t_stat": round(r.alpha_t, 2),
                "alpha_p_corrected_all_36_tests": round(r.alpha_p_bonf, 3),
                "significant_after_correction_all_36_tests": bool(r.sig_bonf),
                "r_squared": round(r.r2, 3),
                "loadings": {config.FACTOR_LABELS[c]: {"beta": round(r[f"b_{c}"], 2),
                                                       "t_stat": round(r[f"t_{c}"], 1)} for c in cols},
            }
            if "alpha_p_holm_model" in r:
                m["alpha_p_corrected_within_this_models_9_funds"] = round(r.alpha_p_holm_model, 3)
                m["significant_within_this_models_9_funds"] = bool(r.sig_holm_model)
            models[r.model] = m
        facts["periods"][period] = {"sample": f"{dp.start.iloc[0]} to {dp.end.iloc[0]}",
                                    "months": int(dp.nobs.iloc[0]), "models": models}
    if chg is not None and not chg.empty and ticker in set(chg.ticker):
        c = chg[chg.ticker == ticker].iloc[0]
        facts["change_after_2024"] = {
            "alpha_change_pct_per_year": round(c.d_alpha_ann * 100, 2),
            "alpha_change_t_stat": round(c.d_alpha_t, 2),
            "loadings_joint_test_p_value_uncorrected": round(c.loadings_changed_p, 3),
            "loading_changes": {config.FACTOR_LABELS[k]: round(c[f"d_{k}"], 2)
                                for k in config.MODELS[config.ROLLING_MODEL]},
        }
        if "loadings_changed_p_holm" in c:
            facts["change_after_2024"]["loadings_joint_test_p_value_corrected_across_9_funds"] = \
                round(c.loadings_changed_p_holm, 3)
            facts["change_after_2024"]["loadings_changed_significant_after_correction"] = \
                bool(c.loadings_changed_p_holm < config.SIGNIFICANCE)
    return facts


# ---------------------------------------------------------------- number check
_NUM = re.compile(r"\d+(?:\.\d+)?")


def _numbers_in(obj) -> list[float]:
    """Every number in a facts dict: numeric values plus digits inside keys and strings."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += _numbers_in(k) + _numbers_in(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out += _numbers_in(v)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out.append(abs(float(obj)))
    elif isinstance(obj, str):
        out += [float(x) for x in _NUM.findall(obj)]
    return out


def allowed_numbers(facts: dict) -> list[float]:
    vals = set(_numbers_in(facts))
    # shares (R², p-values) may be quoted as percentages
    vals |= {v * 100 for v in list(vals) if v <= 1}
    # small counts and structural numbers of the study: "two or three exposures",
    # "9 funds", "36 tests", "five-factor", "12 months"
    vals |= {0, 1, 2, 3, 4, 5, 6, 9, 12, 36, 72, 100}
    return sorted(vals)


def unsupported_numbers(text: str, facts: dict) -> list[str]:
    """Numbers in `text` that do not match any fact (allowing rounding to fewer decimals)."""
    allowed = allowed_numbers(facts)
    bad = []
    for tok in _NUM.findall(text):
        x = float(tok)
        decimals = len(tok.split(".")[1]) if "." in tok else 0
        tol = 0.5 * 10 ** (-decimals) + 1e-9
        if not any(abs(x - a) <= tol for a in allowed):
            bad.append(tok)
    return bad


# ---------------------------------------------------------------- template
def template_explanation(f: dict) -> str:
    """Deterministic fallback used when no language model is available."""
    parts = []
    for period, p in f["periods"].items():
        capm, full = p["models"]["CAPM"], p["models"]["FF5+MOM"]
        top = sorted(((k, v) for k, v in full["loadings"].items() if k != "Market"),
                     key=lambda kv: -abs(kv[1]["beta"]))[:2]
        tilts = ", ".join(f"{k.split(' (')[0].lower()} ({v['beta']:+.2f})" for k, v in top)
        if full["significant_after_correction_all_36_tests"]:
            verdict = "shows statistically reliable alpha even after the strictest correction"
        elif full.get("significant_within_this_models_9_funds"):
            verdict = ("is significant only when the 9 funds of this model are compared, "
                       "so the evidence is moderate")
        else:
            verdict = "shows no alpha that survives the multiple-testing correction"
        parts.append(
            f"**{period} ({p['sample']}, {p['months']} months).** Measured against the market alone, "
            f"{f['ticker']} earned {capm['alpha_pct_per_year']:+.2f}% a year of alpha. After adding size, "
            f"value, profitability, investment and momentum factors that becomes "
            f"{full['alpha_pct_per_year']:+.2f}% a year (t = {full['alpha_t_stat']:.2f}), and the result {verdict}. "
            f"Its market beta is {full['loadings']['Market']['beta']:.2f} and its largest style tilts are "
            f"{tilts}. Together the factors explain {full['r_squared']*100:.0f}% of its month-to-month returns.")
    if "change_after_2024" in f:
        c = f["change_after_2024"]
        parts.append(f"**After 2024.** Alpha changed by {c['alpha_change_pct_per_year']:+.2f}% a year "
                     f"(t = {c['alpha_change_t_stat']:.2f}); a joint test that all loadings stayed the same "
                     f"gives p = {c['loadings_joint_test_p_value_uncorrected']:.3f} before correction. The post-2024 sample is short, "
                     f"so treat this comparison as tentative.")
    return "\n\n".join(parts)


# ---------------------------------------------------------------- language models
class UsageLimitReached(RuntimeError):
    """The Claude subscription's usage limit is exhausted; re-run after it resets."""


class ClaudeCodeWriter:
    """Writes through the Claude Code CLI (`claude -p`) using a Claude Pro/Max login.

    No API key needed: run `claude` once and sign in with your subscription.
    ANTHROPIC_API_KEY is removed from the child process's environment so the
    call can only use the subscription, never pay-as-you-go API billing.
    """

    def __init__(self, model: str = "sonnet", timeout: int = 300):
        self.exe = shutil.which("claude")
        if self.exe is None:
            raise RuntimeError("`claude` not found. Install Claude Code (https://code.claude.com) and run "
                               "`claude` once to sign in with your Pro account.")
        self.cli_model = model
        self.label = f"Claude Code ({model})"
        self.model_ids: set[str] = set()
        self.timeout = timeout
        fd, self.prompt_file = tempfile.mkstemp(prefix="ff_system_prompt_", suffix=".txt")
        with os.fdopen(fd, "w") as fh:
            fh.write(SYSTEM_PROMPT)

    def command(self) -> list[str]:
        return [self.exe, "-p", "--output-format", "json", "--model", self.cli_model,
                "--system-prompt-file", self.prompt_file,
                "--tools", "", "--strict-mcp-config", "--disable-slash-commands",
                "--no-session-persistence", "--max-turns", "3"]

    def write(self, user_prompt: str) -> str:
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        proc = subprocess.run(self.command(), input=user_prompt, capture_output=True, text=True,
                              timeout=self.timeout, env=env)
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError:
            msg = (proc.stdout + proc.stderr).strip()[:300]
            if "limit" in msg.lower():
                raise UsageLimitReached(msg)
            raise RuntimeError(f"claude exited {proc.returncode}: {msg}")
        if out.get("is_error") or not out.get("result"):
            msg = str(out.get("result", ""))[:300]
            if "limit" in msg.lower() or out.get("subtype") == "error_rate_limit":
                raise UsageLimitReached(msg)
            raise RuntimeError(f"claude returned no text: {msg}")
        # Claude Code also uses a small helper model for housekeeping; record the main one
        used = set((out.get("modelUsage") or {}).keys())
        main = {m for m in used if self.cli_model in m}
        self.model_ids |= main or used
        return str(out["result"]).strip()


class AnthropicWriter:
    """Writes with the paid Claude API (needs ANTHROPIC_API_KEY)."""

    def __init__(self, model: str = config.LLM_MODEL_DEFAULT):
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set (the anthropic provider is pay as you go).")
        self.client, self.model = anthropic.Anthropic(), model
        self.label = f"Claude API ({model})"
        self.model_ids = {model}

    def write(self, user_prompt: str) -> str:
        msg = self.client.messages.create(model=self.model, max_tokens=600, system=SYSTEM_PROMPT,
                                          messages=[{"role": "user", "content": user_prompt}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def make_writer(provider: str):
    if provider == "template":
        return None
    if provider == "claude_code":
        return ClaudeCodeWriter(os.environ.get("FF_CLAUDE_CODE_MODEL", config.CLAUDE_CODE_MODEL))
    if provider == "anthropic":
        return AnthropicWriter(os.environ.get("FF_LLM_MODEL", config.LLM_MODEL_DEFAULT))
    raise ValueError(f"unknown provider {provider} (use {', '.join(PROVIDERS)})")


def checked_explanation(writer, facts: dict) -> tuple[str | None, list[str]]:
    """Ask the model, check every number, retry once with the problems listed."""
    prompt = USER_TEMPLATE.format(ticker=facts["ticker"], facts=json.dumps(facts, indent=1))
    bad: list[str] = []
    for attempt in range(2):
        text = writer.write(prompt)
        bad = unsupported_numbers(text, facts)
        if not bad:
            return text, []
        prompt = (USER_TEMPLATE.format(ticker=facts["ticker"], facts=json.dumps(facts, indent=1))
                  + f"\n\nYour previous answer used numbers that are not in the data: {', '.join(bad)}. "
                    "Rewrite it using only numbers from the data.")
    return None, bad


# ---------------------------------------------------------------- all funds
def explain_all(res: pd.DataFrame, chg: pd.DataFrame | None, names: dict[str, str],
                provider: str = "template") -> tuple[str, str, list[dict]]:
    """Returns (markdown, source label, audit rows)."""
    writer = None
    if provider != "template":
        try:
            writer = make_writer(provider)
        except Exception as exc:
            print(f"  {provider} unavailable ({exc}); using the template")
    sections, audit = [], []
    for ticker in dict.fromkeys(res.ticker):
        facts = fund_facts(ticker, names.get(ticker, ticker), res, chg)
        text, bad, note = None, [], "template"
        if writer is not None:
            try:
                text, bad = checked_explanation(writer, facts)
                note = "language model, numbers checked" if text else "template (model text failed the number check)"
            except UsageLimitReached as exc:
                print(f"  usage limit reached at {ticker}; remaining funds use the template. Re-run later. ({exc})")
                writer = None
                note = "template (usage limit reached)"
            except Exception as exc:
                print(f"  {provider} failed for {ticker} ({exc!r}); using the template")
                note = "template (model call failed)"
        audit.append({"ticker": ticker, "written_by": note, "unsupported_numbers": bad})
        sections.append(f"## {ticker}: {facts['name']}\n\n{text or template_explanation(facts)}\n\n"
                        f"_Source: {note}._")
    n_llm = sum(a["written_by"].startswith("language model") for a in audit)
    if writer is not None and n_llm:
        ids = ", ".join(sorted(getattr(writer, "model_ids", set()))) or "unknown"
        source = f"{writer.label}; model: {ids}"
    else:
        source = "fixed template (no language model)"
    if n_llm:
        header = (f"# Fund summaries\n\n_Written by: {source}. {n_llm} of {len(audit)} summaries came from the "
                  f"language model; every number in them was checked against `results/regressions.csv`, and any "
                  f"summary that failed the check was replaced by the fixed template._\n")
    else:
        header = (f"# Fund summaries\n\n_Written by: {source}. Run `python run.py --llm claude_code` "
                  f"for summaries written by a language model._\n")
    return header + "\n\n" + "\n\n".join(sections) + "\n", source, audit
