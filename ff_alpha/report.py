"""Tables (CSV + Markdown) and figures (PNG)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from . import config  # noqa: E402

# Palette (reference dataviz palette, light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
DIVERGING = LinearSegmentedColormap.from_list("rd_gy_bu", ["#e34948", "#f0efec", "#2a78d6"])
EXT_SHADE = "#f0efec"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK_2, "text.color": INK,
    "xtick.color": INK_2, "ytick.color": INK_2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "legend.frameon": False,
})


def _fmt(x: float, nd: int = 2) -> str:
    return "" if pd.isna(x) else f"{x:.{nd}f}"


def _md_table(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
def alpha_table(res: pd.DataFrame, period: str, lags: int = config.NW_LAGS_DEFAULT) -> pd.DataFrame:
    d = res[(res.period == period) & (res.nw_lags == lags)].copy()
    out = pd.DataFrame({
        "Fund": d.ticker, "Model": d.model,
        "Alpha (% / yr)": (d.alpha_ann * 100).map(_fmt),
        "t(alpha)": d.alpha_t.map(_fmt),
        "p": d.alpha_p.map(lambda p: _fmt(p, 3)),
        "p (Bonferroni)": d.alpha_p_bonf.map(lambda p: _fmt(p, 3)),
        "p (Holm)": d.alpha_p_holm.map(lambda p: _fmt(p, 3)),
        "p (BH)": d.alpha_p_bh.map(lambda p: _fmt(p, 3)),
        "Significant (Bonf.)": np.where(d.sig_bonf, "yes", "no"),
        "Mkt beta": d["b_Mkt-RF"].map(_fmt),
        "R²": d.r2.map(_fmt),
        "Months": d.nobs, "Sample": d.start + " to " + d.end,
    })
    return out


def loadings_table(res: pd.DataFrame, period: str, model: str = "FF5+MOM",
                   lags: int = config.NW_LAGS_DEFAULT) -> pd.DataFrame:
    d = res[(res.period == period) & (res.nw_lags == lags) & (res.model == model)]
    out = pd.DataFrame({"Fund": d.ticker, "Alpha (% / yr)": (d.alpha_ann * 100).map(_fmt)})
    for c in config.MODELS[model]:
        out[c] = [f"{b:.2f} ({t:.1f})" for b, t in zip(d[f"b_{c}"], d[f"t_{c}"])]
    out["R²"] = d.r2.map(_fmt).values
    return out


def robustness_table(res: pd.DataFrame, period: str) -> pd.DataFrame:
    d = res[res.period == period]
    piv = d.pivot_table(index=["ticker", "model"], columns="nw_lags", values="alpha_t")
    sig = d.pivot_table(index=["ticker", "model"], columns="nw_lags", values="sig_bonf", aggfunc="max")
    out = pd.DataFrame(index=piv.index)
    for lag in piv.columns:
        out[f"t (lag {lag})"] = piv[lag].map(_fmt)
    out["Bonferroni verdict stable"] = np.where(sig.nunique(axis=1) == 1, "yes", "NO")
    order = {m: i for i, m in enumerate(config.MODELS)}
    out = out.reset_index().rename(columns={"ticker": "Fund", "model": "Model"})
    out["_o"] = out.Model.map(order)
    return out.sort_values(["Fund", "_o"]).drop(columns="_o")


def change_table(chg: pd.DataFrame) -> pd.DataFrame:
    if chg.empty:
        return chg
    cols = config.MODELS[config.ROLLING_MODEL]
    out = pd.DataFrame({"Fund": chg.ticker,
                        "Months pre / post": chg.nobs_pre.astype(str) + " / " + chg.nobs_post.astype(str),
                        "Δ alpha (% / yr)": [f"{a*100:.2f} ({t:.1f})" for a, t in zip(chg.d_alpha_ann, chg.d_alpha_t)]})
    for c in cols:
        out[f"Δ {c}"] = [f"{b:.2f} ({t:.1f})" for b, t in zip(chg[f"d_{c}"], chg[f"dt_{c}"])]
    out["p (all loadings unchanged)"] = chg.loadings_changed_p.map(lambda p: _fmt(p, 3))
    if "loadings_changed_p_holm" in chg:
        out["p Holm (9 funds)"] = chg.loadings_changed_p_holm.map(lambda p: _fmt(p, 3))
        out["p Bonferroni (9 funds)"] = chg.loadings_changed_p_bonf.map(lambda p: _fmt(p, 3))
    return out


def sanity_check(res: pd.DataFrame) -> str:
    d = res[(res.ticker == "SPY") & (res.model == "CAPM") & (res.nw_lags == config.NW_LAGS_DEFAULT)]
    lines = []
    for _, r in d.iterrows():
        ok = abs(r["b_Mkt-RF"] - 1) < 0.05 and abs(r.alpha_ann) < 0.015
        lines.append(f"- {r.period}: SPY CAPM beta = {r['b_Mkt-RF']:.3f}, alpha = {r.alpha_ann*100:.2f}% / yr, "
                     f"R² = {r.r2:.3f} -> {'PASS' if ok else 'CHECK DATA'}")
    return "\n".join(lines) if lines else "- SPY not in sample"


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def plot_alpha_by_model(res: pd.DataFrame, period: str, path: Path, title_suffix: str = "") -> None:
    """Annualized alpha with 95% Newey-West CI for each fund under each model."""
    d = res[(res.period == period) & (res.nw_lags == config.NW_LAGS_DEFAULT)]
    funds = list(dict.fromkeys(d.ticker))
    models = list(config.MODELS)
    fig, ax = plt.subplots(figsize=(8, 0.55 * len(funds) + 1.6))
    h = 0.8 / len(models)
    for j, m in enumerate(models):
        dm = d[d.model == m].set_index("ticker").reindex(funds)
        y = np.arange(len(funds)) + (j - (len(models) - 1) / 2) * h
        a = dm.alpha_ann * 100
        ci = 1.96 * dm.alpha_se * 12 * 100
        ax.barh(y, a, height=h * 0.85, color=SERIES[j], label=m, zorder=2)
        ax.errorbar(a, y, xerr=ci, fmt="none", ecolor=INK_2, elinewidth=0.8, capsize=0, zorder=3)
        for yi, ai, s in zip(y, a, dm.sig_bonf):
            if s:
                ax.text(ai + (0.3 if ai >= 0 else -0.3), yi, "*", va="center",
                        ha="left" if ai >= 0 else "right", color=INK, fontsize=11)
    ax.axvline(0, color=AXIS, linewidth=1, zorder=1)
    ax.set_yticks(np.arange(len(funds)), funds)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Annualized alpha (% per year), bars = 95% Newey-West CI")
    ax.set_title(f"Annualized alpha by model{title_suffix}", loc="left")
    ax.legend(ncol=len(models), loc="upper left", bbox_to_anchor=(0, -0.12 - 0.3 / len(funds)))
    fig.text(0.01, 0.005, "* significant after Bonferroni correction across funds x models",
             color=INK_2, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_loadings_heatmap(res: pd.DataFrame, period: str, path: Path, title_suffix: str = "") -> None:
    model = "FF5+MOM"
    d = res[(res.period == period) & (res.nw_lags == config.NW_LAGS_DEFAULT) & (res.model == model)]
    cols = config.MODELS[model]
    mat = d.set_index("ticker")[[f"b_{c}" for c in cols]].copy()
    mat.columns = cols
    plot = mat.copy()
    plot["Mkt-RF"] = plot["Mkt-RF"] - 1  # centre market beta on 1
    lim = max(0.5, float(np.nanmax(np.abs(plot.values))))
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(mat) + 1.4))
    ax.imshow(plot.values, cmap=DIVERGING, vmin=-lim, vmax=lim, aspect="auto")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat.values[i, j]:.2f}", ha="center", va="center", fontsize=8, color=INK)
    ax.set_xticks(range(len(cols)), ["Market (vs 1)", "Size", "Value", "Profit.", "Invest.", "Momentum"])
    ax.set_yticks(range(len(mat)), mat.index)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"FF5 + momentum loadings{title_suffix}", loc="left")
    fig.text(0.01, 0.01, "Blue = positive tilt, red = negative; market beta coloured relative to 1",
             color=INK_2, fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _shade_extension(ax, x_end) -> None:
    x0 = config.EXTENSION_START.to_timestamp()
    if x_end > x0:
        ax.axvspan(x0, x_end, color=EXT_SHADE, zorder=0, linewidth=0)


def plot_rolling_fund(roll: pd.DataFrame, ticker: str, path: Path, title_suffix: str = "") -> None:
    d = roll[roll.ticker == ticker].copy()
    if d.empty:
        return
    x = d.month.dt.to_timestamp() if hasattr(d.month, "dt") else pd.PeriodIndex(d.month).to_timestamp()
    panels = [("alpha_ann", "Alpha (% / yr)", 100)] + \
             [(c, config.FACTOR_LABELS[c], 1) for c in config.MODELS[config.ROLLING_MODEL]] + \
             [("r2", "R²", 1)]
    fig, axes = plt.subplots(2, 4, figsize=(12, 5), sharex=True)
    for ax, (col, label, scale) in zip(axes.flat, panels):
        _shade_extension(ax, x.max())
        ax.axhline(1 if col == "Mkt-RF" else 0, color=AXIS, linewidth=1, zorder=1)
        ax.plot(x, d[col] * scale, color=SERIES[0], linewidth=1.6, zorder=2)
        ax.set_title(label, loc="left", fontsize=9)
        ax.tick_params(axis="x", labelrotation=0, labelsize=8)
    fig.suptitle(f"{ticker}: rolling {config.ROLLING_WINDOW}-month {config.ROLLING_MODEL} regression"
                 f"{title_suffix}", x=0.01, ha="left", fontweight="bold")
    fig.text(0.01, 0.005, "Each point uses the 36 months ending that month. Shaded: windows ending "
             "in the 2024+ extension period.", color=INK_2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_rolling_compare(roll: pd.DataFrame, tickers: list[str], path: Path, title_suffix: str = "") -> None:
    """Market, growth (HML), momentum and alpha for a few funds side by side."""
    tickers = [t for t in tickers if t in set(roll.ticker)][:4]
    if not tickers:
        return
    panels = [("Mkt-RF", "Market beta", 1), ("HML", "Value loading (negative = growth)", 1),
              ("MOM", "Momentum loading", 1), ("alpha_ann", "Alpha (% / yr)", 100)]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), sharex=True)
    xmax = None
    for ax, (col, label, scale) in zip(axes, panels):
        for i, t in enumerate(tickers):
            d = roll[roll.ticker == t]
            x = d.month.dt.to_timestamp()
            xmax = x.max() if xmax is None else max(xmax, x.max())
            ax.plot(x, d[col] * scale, color=SERIES[i], linewidth=1.6, label=t, zorder=2)
        ax.axhline(1 if col == "Mkt-RF" else 0, color=AXIS, linewidth=1, zorder=1)
        ax.set_title(label, loc="left", fontsize=9)
    for ax in axes:
        _shade_extension(ax, xmax)
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle(f"Rolling {config.ROLLING_WINDOW}-month exposures{title_suffix}", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_r2(res: pd.DataFrame, period: str, path: Path, title_suffix: str = "") -> None:
    d = res[(res.period == period) & (res.nw_lags == config.NW_LAGS_DEFAULT)]
    funds = list(dict.fromkeys(d.ticker))
    models = list(config.MODELS)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    w = 0.8 / len(models)
    for j, m in enumerate(models):
        dm = d[d.model == m].set_index("ticker").reindex(funds)
        ax.bar(np.arange(len(funds)) + (j - (len(models) - 1) / 2) * w, dm.r2, width=w * 0.85,
               color=SERIES[j], label=m, zorder=2)
    ax.set_xticks(range(len(funds)), funds)
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("R²")
    ax.set_title(f"How much of each fund's return the factors explain{title_suffix}", loc="left")
    ax.legend(ncol=4, loc="lower left", bbox_to_anchor=(0, 1.02 - 0.13), fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def family_table(res: pd.DataFrame) -> pd.DataFrame:
    """For each period x model x lag: smallest alpha p-value corrected across the
    9 funds of that model, and how many funds are significant."""
    rows = []
    order = {m: i for i, m in enumerate(config.MODELS)}
    for (period, model, lag), d in res.groupby(["period", "model", "nw_lags"], sort=False):
        best = d.loc[d.alpha_p.idxmin()]
        rows.append({"Period": period, "Model": model, "NW lags": lag, "Fund": best.ticker,
                     "Alpha (% / yr)": _fmt(best.alpha_ann * 100),
                     "p Bonferroni (9)": _fmt(best.alpha_p_bonf_model, 3),
                     "p Holm (9)": _fmt(best.alpha_p_holm_model, 3),
                     "Significant funds (Holm)": int(d.sig_holm_model.sum()), "_o": order[model]})
    out = pd.DataFrame(rows).sort_values(["Period", "_o", "NW lags"], key=lambda c: c if c.name != "Period" else c.str.startswith("Ext"))
    return out.drop(columns="_o")
