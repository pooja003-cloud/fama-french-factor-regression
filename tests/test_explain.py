"""Fund summaries: number check, Claude Code command, fallback. The CLI is stubbed."""
import json
import subprocess

import pytest

from ff_alpha import config, data, explain, models


@pytest.fixture(scope="module")
def facts():
    factors, rets = data.synthetic_data()
    res, _ = models.run_period(rets[["SPY", "IWM"]], factors, config.ORIGINAL_START, config.ORIGINAL_END,
                               config.MIN_MONTHS, "Main period 2010-2023", (6,))
    res = models.bonferroni(res)
    return res, explain.fund_facts("IWM", "iShares Russell 2000 ETF", res, None)


def test_number_check(facts):
    _, f = facts
    assert f["fund_type"] == "index fund"
    capm = f["periods"]["Main period 2010-2023"]["models"]["CAPM"]
    a = capm["alpha_pct_per_year"]
    r2 = capm["r_squared"]
    good = (f"Against the market alone IWM's alpha was {a:.2f}% a year, roughly {abs(a):.1f}%, "
            f"and the factors explain {r2 * 100:.0f}% of its returns over 168 months in 2010-2023.")
    assert explain.unsupported_numbers(good, f) == []
    bad = "A 10% market rise typically meant a 17.3% move."
    assert explain.unsupported_numbers(bad, f) == ["10", "17.3"]


def test_claude_code_strips_api_key_and_parses(facts, monkeypatch):
    res, f = facts
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-not-be-passed")
    seen = {}
    a = f["periods"]["Main period 2010-2023"]["models"]["FF5+MOM"]["alpha_pct_per_year"]

    def fake_run(cmd, input, capture_output, text, timeout, env):
        seen.update(cmd=cmd, env=env, input=input)
        out = {"result": f"IWM's six-factor alpha was {a:.2f}% a year.", "is_error": False,
               "modelUsage": {"claude-sonnet-5-5": {}}}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(out), stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    md, source, audit = explain.explain_all(res[res.ticker == "IWM"], None, {"IWM": "iShares Russell 2000 ETF"},
                                            provider="claude_code")
    assert "ANTHROPIC_API_KEY" not in seen["env"]
    assert seen["cmd"][1:3] == ["-p", "--output-format"] and "--tools" in seen["cmd"]
    assert '"ticker": "IWM"' in seen["input"]
    assert "claude-sonnet-5-5" in source and audit[0]["written_by"].startswith("language model")


def test_failed_number_check_falls_back_to_template(facts, monkeypatch):
    res, _ = facts
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/claude")

    def fake_run(cmd, input, capture_output, text, timeout, env):
        out = {"result": "A 10% market rise meant a 17.3% move.", "is_error": False}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(out), stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    md, _, audit = explain.explain_all(res[res.ticker == "IWM"], None, {"IWM": "x"}, provider="claude_code")
    assert audit[0]["written_by"].startswith("template") and audit[0]["unsupported_numbers"] == ["10", "17.3"]
    assert "Measured against the market alone" in md  # template text was used instead
