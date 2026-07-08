import argparse
import csv
import json
import os

from ocdvm.config import load_config
from ocdvm.inputs import load_inputs
from ocdvm.factors import compute_alpha
from ocdvm.peers import Peer, ev_sales, revenue_weighted_median, quality_factor
from ocdvm.valuation import value_company, legacy_ebitda, ebitda_oci
from ocdvm.scenarios import Scenario, scenario_target, probability_weighted, expected_return
from ocdvm.sensitivity import sensitivity_grid
from report.plots import plot_sotp, plot_sensitivity, plot_scenarios, plot_alpha_cei
from report.evidence_plots import (plot_factor_breakdown, plot_peer_multiples,
                                   plot_fundamental_trends, plot_ev_reconciliation,
                                   plot_price_history)
from report.commentary import build_commentary, commentary_markdown, commentary_html
from report.dashboard import render_dashboard
from report.build_report import build_markdown, to_pdf, html_to_pdf


def assemble_result(inp, cfg, peers, subscores) -> dict:
    a = compute_alpha(inp, cfg["factors"])
    m_neo = revenue_weighted_median(peers) if peers else cfg["defaults"].get("m_neo_fallback", 10.0)
    q = quality_factor(subscores, cfg["quality"])
    val = value_company(inp, a.alpha, m_neo, q)
    prices, probs = {}, {}
    for name, s in cfg["scenarios"].items():
        scn = Scenario(name, s["prob"], s["growth_mult"], s["m_neo_delta"], s["alpha_delta"])
        prices[name] = scenario_target(inp, a.alpha, m_neo, q, scn)
        probs[name] = s["prob"]
    pw = probability_weighted(prices, probs)
    grid = sensitivity_grid(inp, a.alpha, q,
                            cfg["sensitivity"]["growth_axis"], cfg["sensitivity"]["mneo_axis"])
    peers_detail = sorted(
        [{"ticker": p.ticker, "ev_sales": ev_sales(p), "revenue_ttm": p.revenue_ttm} for p in peers],
        key=lambda d: d["ev_sales"])
    market_cap = inp.current_price * inp.shares
    market_ev = market_cap + inp.net_debt
    return {
        "quarter": inp.quarter, "alpha": a.alpha, "cei": a.cei, "regime": a.regime,
        "factor_scores": a.factor_scores, "weights_used": a.weights_used,
        "m_neo": m_neo, "q": q, "oci_multiple_effective": m_neo * q,
        "legacy_ebitda": legacy_ebitda(inp), "ebitda_oci": ebitda_oci(inp),
        "ev_legacy": val.ev_legacy, "ev_oci": val.ev_oci, "ev_total": val.ev_total,
        "equity": val.equity, "target": val.target,
        "scenarios": prices, "pw_price": pw,
        "expected_return": expected_return(pw, inp.current_price),
        "sensitivity": grid.tolist(),
        "sensitivity_axes": {"growth": cfg["sensitivity"]["growth_axis"],
                             "mneo": cfg["sensitivity"]["mneo_axis"]},
        "current_price": inp.current_price,
        "peers_detail": peers_detail,
        "market_cap": market_cap, "market_ev": market_ev, "net_debt": inp.net_debt,
        "rev_oci_ttm": inp.rev_oci_ttm, "rev_oci_q": inp.rev_oci_q,
        "oci_rev_growth": inp.oci_rev_growth, "capex_ttm": inp.capex_ttm,
        "capex_growth": inp.capex_growth, "rpo": inp.rpo, "rpo_growth": inp.rpo_growth,
        "oci_fcf_margin": inp.oci_fcf_margin, "oci_op_margin": inp.oci_op_margin,
    }


def _load_peers():
    """Prefer the live-refreshed cache (data/raw/peers.json); otherwise build peers from
    the committed seed (config/peers_seed.json), which carries agent-searched prices."""
    cache = "data/raw/peers.json"
    if os.path.exists(cache):
        return [Peer(ticker=p["ticker"], revenue_ttm=p["revenue_ttm"], price=p["price"],
                     shares=p["shares"], net_debt=p.get("net_debt", 0.0))
                for p in json.load(open(cache))]
    seed = "config/peers_seed.json"
    if os.path.exists(seed):
        return [Peer(ticker=s["ticker"], revenue_ttm=s["revenue_ttm"], price=s["price"],
                     shares=s["shares"], net_debt=s.get("net_debt", 0.0))
                for s in json.load(open(seed))]
    return []


def _load_evidence(inputs_path: str) -> dict:
    """Gather corroborating data for the evidence plots. Each source is best-effort;
    a failure just omits that chart (network is not required to produce a report)."""
    import yaml
    ev = {}
    raw = yaml.safe_load(open(inputs_path)) or {}
    meta = raw.get("meta", {}) or {}
    ev["oci_history"] = meta.get("oci_history")
    ev["agent_note"] = meta.get("agent_note")
    try:
        from data.history import oracle_annual_series
        ev["series"] = oracle_annual_series()
    except Exception as e:  # noqa: BLE001
        print(f"[evidence] annual series unavailable: {e}")
    try:
        from data.fetch_prices import fetch_prices
        ev["price_df"] = fetch_prices("ORCL")
    except Exception as e:  # noqa: BLE001
        print(f"[evidence] ORCL price history unavailable: {e}")
    return ev


def append_history(csv_path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            w.writeheader()
        w.writerow(row)


def generate_outputs(result, outdir, evidence=None) -> dict:
    os.makedirs(outdir, exist_ok=True)
    evidence = evidence or {}
    # model-output plots
    plots = {
        "sotp": plot_sotp(result, os.path.join(outdir, "sotp.png")),
        "scenarios": plot_scenarios(result, os.path.join(outdir, "scenarios.png")),
        "sensitivity": plot_sensitivity(result, os.path.join(outdir, "sensitivity.png")),
        "alpha_cei": plot_alpha_cei(result, os.path.join(outdir, "alpha_cei.png")),
    }
    # corroborating-evidence plots
    plots["factor_breakdown"] = plot_factor_breakdown(
        result, os.path.join(outdir, "factor_breakdown.png"))
    if result.get("peers_detail"):
        plots["peer_multiples"] = plot_peer_multiples(
            result, os.path.join(outdir, "peer_multiples.png"))
    plots["ev_reconciliation"] = plot_ev_reconciliation(
        result, os.path.join(outdir, "ev_reconciliation.png"))
    if evidence.get("series"):
        plots["fundamental_trends"] = plot_fundamental_trends(
            evidence["series"], evidence.get("oci_history"),
            os.path.join(outdir, "fundamental_trends.png"))
    if evidence.get("price_df") is not None and len(evidence["price_df"]):
        plots["price_history"] = plot_price_history(
            evidence["price_df"], result, os.path.join(outdir, "price_history.png"))

    sections = build_commentary(result, evidence.get("agent_note"))
    paths = dict(plots)
    rel = {k: os.path.basename(v) for k, v in plots.items()}
    paths["markdown"] = build_markdown(result, rel, os.path.join(outdir, "report.md"),
                                       commentary_md=commentary_markdown(sections))
    paths["dashboard"] = render_dashboard(result, rel, os.path.join(outdir, "index.html"),
                                          commentary=commentary_html(sections))
    # PDF from the styled dashboard via Chrome (unicode-safe); fall back to pandoc on the markdown
    pdf = html_to_pdf(paths["dashboard"], os.path.join(outdir, "report.pdf"))
    if not pdf:
        to_pdf(paths["markdown"], os.path.join(outdir, "report.pdf"))
    return paths


def _publish_site(outdir, paths):
    import shutil
    os.makedirs("site", exist_ok=True)
    for k, v in paths.items():
        if k in ("markdown", "dashboard"):
            continue
        shutil.copy(v, os.path.join("site", os.path.basename(v)))
    shutil.copy(paths["dashboard"], "site/index.html")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--config", default="config/model_config.yaml")
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    inp = load_inputs(args.inputs)
    peers = _load_peers()
    result = assemble_result(inp, cfg, peers, cfg["quality"]["subscores"])
    outdir = os.path.join(args.outdir, inp.quarter)
    os.makedirs(outdir, exist_ok=True)
    json.dump(result, open(os.path.join(outdir, "result.json"), "w"), indent=2)
    append_history(os.path.join(args.outdir, "factors_history.csv"),
                   {"quarter": inp.quarter, "alpha": result["alpha"], "cei": result["cei"],
                    "regime": result["regime"], "m_neo": result["m_neo"], "q": result["q"],
                    "target": result["target"], "pw_price": result["pw_price"]})
    paths = generate_outputs(result, outdir, evidence=_load_evidence(args.inputs))
    _publish_site(outdir, paths)
    print(json.dumps({"quarter": inp.quarter, "target": round(result["target"], 2),
                      "pw_price": round(result["pw_price"], 2),
                      "expected_return": round(result["expected_return"], 4),
                      "alpha": round(result["alpha"], 3), "cei": result["cei"],
                      "regime": result["regime"], "m_neo": round(result["m_neo"], 2)}, indent=2))
    return result


if __name__ == "__main__":
    main()
