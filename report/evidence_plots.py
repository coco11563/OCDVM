"""Corroborating-evidence plots: the data behind the valuation, not the valuation output.

All titleless (labels/legends only), matplotlib Agg, saved to PNG. Each returns its path.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _fy(end_iso: str) -> str:
    return "FY" + end_iso[2:4]  # '2026-05-31' -> 'FY26'


def plot_factor_breakdown(result, path):
    """How alpha is built: each factor's Neo-ness score (0-1) and its weight."""
    scores = result["factor_scores"]
    weights = result["weights_used"]
    names = sorted(scores, key=lambda n: weights.get(n, 0), reverse=True)
    vals = [scores[n] for n in names]
    labels = [f"{n}  ({weights.get(n, 0) * 100:.0f}%)" for n in names]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(labels, vals, color="#3b7dd8")
    ax.axvline(result["alpha"], color="#d1495b", linestyle="--",
               label=f"α = {result['alpha']:.2f}")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Neo-ness score (1 = fully Neo-cloud, 0 = Hyperscaler)")
    ax.invert_yaxis()
    ax.legend(loc="lower right")
    return _save(fig, path)


def plot_peer_multiples(result, path):
    """Peer EV/Sales vs the revenue-weighted median M_Neo and the effective OCI multiple."""
    peers = result["peers_detail"]
    fig, ax = plt.subplots(figsize=(5, 4))
    tickers = [p["ticker"] for p in peers]
    evs = [p["ev_sales"] for p in peers]
    ax.bar(tickers, evs, color="#6c8ebf")
    for i, p in enumerate(peers):
        ax.text(i, p["ev_sales"], f"{p['ev_sales']:.1f}x", ha="center", va="bottom", fontsize=8)
    ax.axhline(result["m_neo"], color="#2e7d32", linestyle="-",
               label=f"M_Neo (rev-wtd median) = {result['m_neo']:.1f}x")
    ax.axhline(result["oci_multiple_effective"], color="#d1495b", linestyle="--",
               label=f"OCI eff. = M_Neo×Q = {result['oci_multiple_effective']:.1f}x")
    ax.set_ylabel("EV / Sales (TTM)")
    ax.legend(fontsize=7)
    return _save(fig, path)


def plot_fundamental_trends(series, oci_history, path):
    """Oracle revenue / CapEx / RPO trajectories (SEC annual), with OCI overlaid on revenue."""
    rev = series.get("revenue", {})
    capex = series.get("capex", {})
    rpo = series.get("rpo", {})
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))

    ax = axes[0]
    xs = list(rev)[-6:]
    ax.bar([_fy(x) for x in xs], [rev[x] / 1000 for x in xs], color="#9bb7d4", label="Total")
    if oci_history:
        ox = [k for k in oci_history if k in xs] or list(oci_history)
        ax.bar([_fy(x) for x in ox], [oci_history[x] / 1000 for x in ox],
               color="#d1495b", label="OCI (IaaS)")
    ax.set_ylabel("Revenue ($B)")
    ax.legend(fontsize=7)

    ax = axes[1]
    cx = list(capex)[-6:]
    ax.bar([_fy(x) for x in cx], [capex[x] / 1000 for x in cx], color="#e0a458")
    ax.set_ylabel("CapEx ($B)")

    ax = axes[2]
    rx = list(rpo)[-6:]
    ax.bar([_fy(x) for x in rx], [rpo[x] / 1000 for x in rx], color="#7a9e7e")
    ax.set_ylabel("RPO ($B)")
    return _save(fig, path)


def plot_ev_reconciliation(result, path):
    """Model EV (Legacy + OCI) vs the market's EV (equity + net debt)."""
    fig, ax = plt.subplots(figsize=(4.5, 4))
    b = 1e3
    ax.bar("Model", result["ev_legacy"] / b, color="#9bb7d4", label="Legacy")
    ax.bar("Model", result["ev_oci"] / b, bottom=result["ev_legacy"] / b,
           color="#d1495b", label="OCI")
    ax.bar("Market", result["market_cap"] / b, color="#b0b0b0", label="Equity (mkt cap)")
    ax.bar("Market", result["net_debt"] / b, bottom=result["market_cap"] / b,
           color="#5a5a5a", label="Net debt")
    ax.set_ylabel("Enterprise value ($B)")
    ax.legend(fontsize=7)
    return _save(fig, path)


def plot_price_history(price_df, result, path):
    """ORCL close over the last year with the model target and Bear-Bull band."""
    scn = result["scenarios"]
    bear, bull = min(scn.values()), max(scn.values())
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(price_df["date"], price_df["close"], color="#333333", linewidth=1.0, label="ORCL close")
    ax.axhline(result["target"], color="#2e7d32", linestyle="-",
               label=f"target ${result['target']:.0f}")
    ax.axhspan(bear, bull, color="#2e7d32", alpha=0.10, label="Bear–Bull")
    ax.set_ylabel("price $")
    ax.legend(fontsize=7, loc="upper right")
    fig.autofmt_xdate()
    return _save(fig, path)
