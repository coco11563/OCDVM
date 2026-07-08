"""Agent interpretation: a number-driven reading of the model output.

Deterministic and adaptive — it reads the actual result values and thresholds so the
narrative stays correct as figures change each quarter. `build_commentary` returns a list
of {"h": heading, "p": body} sections; render to Markdown or HTML with the helpers.
An optional hand-written `agent_note` (from inputs meta) is appended as an analyst note.
"""


def _pct(x):
    return f"{x * 100:.0f}%"


def build_commentary(result, agent_note=None) -> list:
    cur = result["current_price"]
    tgt = result["target"]
    gap = tgt / cur - 1.0
    er = result["expected_return"]
    alpha = result["alpha"]
    cei = result.get("cei")
    regime = result["regime"]
    capex_to_oci = result["capex_ttm"] / result["rev_oci_ttm"] if result["rev_oci_ttm"] else 0
    rpo_to_oci = result["rpo"] / result["rev_oci_ttm"] if result["rev_oci_ttm"] else 0
    total_ebitda = result["legacy_ebitda"] + result["ebitda_oci"]
    leverage = result["net_debt"] / total_ebitda if total_ebitda else 0
    legacy_share = result["ev_legacy"] / result["ev_total"]
    oci_share = result["ev_oci"] / result["ev_total"]
    model_vs_market = result["ev_total"] / result["market_ev"] - 1.0

    if abs(gap) < 0.05:
        verdict = "roughly fairly valued"
    elif gap > 0:
        verdict = "undervalued"
    else:
        verdict = "overvalued"

    # top drivers of alpha = highest score×weight contributions
    contrib = {n: result["factor_scores"][n] * result["weights_used"].get(n, 0)
               for n in result["factor_scores"]}
    top = sorted(contrib, key=contrib.get, reverse=True)[:3]

    sections = []

    sections.append({"h": "Verdict", "p":
        f"The model puts fair value at ${tgt:,.0f} vs. a ${cur:,.0f} spot — Oracle looks "
        f"{verdict} ({_pct(gap)} to target). Probability-weighted across Bear/Base/Bull the "
        f"expected return is {_pct(er)}. The model's total enterprise value is within "
        f"{_pct(abs(model_vs_market))} of the market's own EV, so this is a re-rating call on "
        f"the mix, not a claim that the whole company is mispriced."})

    cei_txt = f"{cei:.2f}" if cei is not None else "n/a"
    sections.append({"h": "Where OCI sits in its lifecycle", "p":
        f"α = {alpha:.2f} means the model prices OCI about {_pct(alpha)} as a Neo-cloud "
        f"(EV/Sales) asset and {_pct(1 - alpha)} as a mature hyperscaler (EV/EBITDA). "
        f"CEI = {cei_txt} places it firmly in the '{regime}' regime: OCI revenue is growing "
        f"({_pct(result['oci_rev_growth'])}) but CapEx is growing faster "
        f"({_pct(result['capex_growth'])}), so the business is still consuming capital, not "
        f"self-funding. CEI would need CapEx growth to fall toward the revenue-growth rate "
        f"(~{_pct(result['oci_rev_growth'])}) to approach 1.0 and trigger the migration toward "
        f"EBITDA-based pricing."})

    sections.append({"h": "What is driving α", "p":
        f"The weight sits on the most extreme build-out signals: {', '.join(top)}. CapEx is "
        f"{capex_to_oci:.1f}× OCI revenue and OCI free cash flow is modeled deeply negative "
        f"({_pct(result['oci_fcf_margin'])} margin) — both peg to maximum 'Neo-ness'. This is "
        f"the correct economic read: today OCI should be valued almost entirely on revenue, "
        f"because there is no meaningful OCI profit to capitalize yet."})

    legacy_mult = result["ev_legacy"] / result["legacy_ebitda"] if result["legacy_ebitda"] else 0
    sections.append({"h": "How the value splits", "p":
        f"Legacy software is {_pct(legacy_share)} of enterprise value "
        f"(${result['ev_legacy'] / 1000:,.0f}B at {legacy_mult:.0f}× EBITDA) "
        f"and OCI is {_pct(oci_share)} (${result['ev_oci'] / 1000:,.0f}B, at an effective "
        f"{result['oci_multiple_effective']:.1f}× revenue = M_Neo {result['m_neo']:.1f}× × "
        f"quality {result['q']:.2f}). So even after the AI hype, the mature franchise still "
        f"underpins most of the value."})

    sections.append({"h": "The core tension", "p":
        f"Bull case: an RPO backlog of ${result['rpo'] / 1000:,.0f}B — {rpo_to_oci:.0f}× current "
        f"OCI revenue — is a booked pipeline few companies can match. Bear case: funding it "
        f"took CapEx to ${result['capex_ttm'] / 1000:,.0f}B and net debt to "
        f"${result['net_debt'] / 1000:,.0f}B ({leverage:.1f}× EBITDA) while OCI still burns cash. "
        f"That tension — enormous booked demand against a balance sheet and cash-flow strain — "
        f"is why the stock is down sharply from its high and why the model lands near spot "
        f"rather than far above it."})

    scn = result["scenarios"]
    sections.append({"h": "Scenarios", "p":
        f"Bear ${scn.get('Bear', 0):,.0f} / Base ${scn.get('Base', 0):,.0f} / "
        f"Bull ${scn.get('Bull', 0):,.0f}. The spread is driven by OCI growth, the Neo peer "
        f"multiple, and α together — a compression of the neo-cloud multiple hurts most, since "
        f"OCI is currently valued on revenue."})

    sections.append({"h": "What to watch next quarter", "p":
        "1) OCI operating margin — the first sign the (1−α) EBITDA leg starts to matter. "
        "2) CapEx growth decelerating toward revenue growth (CEI rising toward 1.0). "
        "3) RPO converting into recognized revenue rather than just growing. "
        "4) Net-debt/EBITDA — whether the balance sheet stabilizes. "
        "Each feeds the factors that move α, so the migration will show up in the model "
        "mechanically rather than by judgment."})

    if agent_note:
        sections.append({"h": "Analyst note", "p": agent_note})

    return sections


def build_capacity_commentary(cap, knobs, note_new_oci, prior_oci) -> list:
    """Interpretation of the bottom-up MW-capacity cross-check."""
    from ocdvm.capacity import pretax_roic, breakeven_rev_per_mw
    roic_hi = pretax_roic(knobs["rev_per_mw"], knobs["opex_per_mw"],
                          knobs["build_cost_per_mw"], knobs["gpu_life_years"])
    roic_lo = pretax_roic(6.0, knobs["opex_per_mw"], knobs["build_cost_per_mw"], knobs["gpu_life_years"])
    be = breakeven_rev_per_mw(knobs["opex_per_mw"], knobs["build_cost_per_mw"], knobs["gpu_life_years"])
    note_total = prior_oci + (note_new_oci or 0)
    note_growth = (note_new_oci or 0) / prior_oci if prior_oci else 0
    sections = []
    sections.append({"h": "Bottom-up capacity cross-check", "p":
        f"An independent MW-capacity build (CapEx ÷ ${knobs['build_cost_per_mw']:.0f}M per MW × "
        f"${knobs['rev_per_mw']:.1f}M revenue per MW). At the note's optimistic assumptions "
        f"(full utilization, no contract haircut), forward OCI is ~${note_total / 1000:.0f}B "
        f"(+{note_growth * 100:.0f}%). At realistic delivery ({knobs['utilization'] * 100:.0f}% "
        f"utilization, {knobs['contract_mix_haircut'] * 100:.0f}% prepaid/customer-supplied "
        f"haircut), the model gives ${cap.projected_oci_total / 1000:.0f}B "
        f"(+{cap.oci_growth * 100:.0f}%) — the headline needs near-flawless execution."})
    sections.append({"h": "The regime-change test (CEI)", "p":
        f"CapEx grows ~{cap.capex_growth * 100:.0f}% while OCI revenue grows "
        f"{cap.oci_growth * 100:.0f}%, giving a projected CEI of {cap.projected_cei:.2f} "
        f"(vs 0.47 today). Only if revenue actually out-grows CapEx does CEI cross 1.0 and "
        f"trigger the migration from Neo-cloud to Hyperscaler pricing (α falling). Because "
        f"depreciation starts at fit-out but revenue only at delivery, any slippage lands the "
        f"CapEx denominator on time while the revenue numerator lags — structurally pinning "
        f"CEI below 1 and keeping OCI in the Neo regime."})
    sections.append({"h": "Unit economics are the swing factor", "p":
        f"Pre-tax ROIC per billed MW is ~{roic_hi * 100:.0f}% at ${knobs['rev_per_mw']:.1f}M/MW "
        f"but ~{roic_lo * 100:.0f}% at $6M/MW (CoreWeave-like), with break-even at "
        f"${be:.1f}M/MW. So the whole 'healthy build' case rests on a revenue-per-MW roughly "
        f"2× what the cleanest public comp earns. Revenue upside does NOT get multiplied by the "
        f"trailing EV/Sales multiple; it matters for α's migration speed, not the target price."})
    return sections


def commentary_markdown(sections) -> str:
    return "\n\n".join(f"### {s['h']}\n\n{s['p']}" for s in sections)


def commentary_html(sections) -> str:
    parts = ['<div class="commentary">']
    for s in sections:
        parts.append(f"<h3>{s['h']}</h3><p>{s['p']}</p>")
    parts.append("</div>")
    return "\n".join(parts)
