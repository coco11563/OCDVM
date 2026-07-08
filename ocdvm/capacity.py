"""Bottom-up MW-capacity OCI revenue engine (a cross-check / scenario layer).

Models OCI revenue from datacenter capacity the way sell-side capacity notes do:
  new MW added   = annual CapEx / build-cost per MW
  billed MW      = new MW * utilization * (1 - contract_mix_haircut)
  full run-rate  = billed MW * revenue per MW
  new OCI rev    = full run-rate * ramp_factor   (capacity energizes through the year)

It is deliberately NOT part of the main valuation: forward revenue must not be multiplied
by a trailing EV/Sales multiple. The engine instead (a) cross-checks the OCI revenue path,
(b) exposes the two load-bearing knobs (build-cost/MW and revenue/MW) as scenarios, and
(c) reports unit economics (yield, payback, pre-tax ROIC, break-even) and the projected CEI,
which drives how fast alpha should migrate — not the target price directly.

Contract-mix haircut: a large share of Oracle's AI backlog is prepaid or customer-supplied
GPU, which does not earn owner-operator revenue; the haircut discounts installed MW to
billed MW so "installed" is not mistaken for "billed".
"""
from dataclasses import dataclass


@dataclass
class CapacityInputs:
    capex: float                 # annual CapEx ($M)
    prior_capex: float           # prior-year CapEx ($M), for CapEx growth / CEI
    prior_oci_rev: float         # prior-year OCI revenue base ($M)
    build_cost_per_mw: float     # $M per MW (full-stack incl. GPUs)
    rev_per_mw: float            # $M per billed MW per year
    ramp_factor: float           # 0-1 weighted fraction of full run-rate captured this year
    utilization: float           # 0-1 energized+contracted fraction of installed MW
    contract_mix_haircut: float  # 0-1 fraction of MW on prepaid/customer-supplied GPU (no owner rev)
    opex_per_mw: float           # $M per MW per year, power+operations (for ROIC)
    gpu_life_years: float        # depreciation life for ROIC


@dataclass
class CapacityResult:
    new_mw: float
    billed_mw: float
    full_runrate_revenue: float
    new_oci_revenue: float
    projected_oci_total: float
    oci_growth: float
    capex_growth: float
    projected_cei: float
    revenue_yield: float          # rev/MW ÷ build-cost/MW (gross, nameplate)
    gross_payback_years: float
    pretax_roic: float            # (rev - opex - depreciation) ÷ build-cost, per billed MW
    breakeven_rev_per_mw: float   # rev/MW at which pre-tax ROIC = 0


def new_mw(capex: float, build_cost_per_mw: float) -> float:
    return capex / build_cost_per_mw if build_cost_per_mw else 0.0


def billed_mw(mw: float, utilization: float, contract_mix_haircut: float) -> float:
    return mw * utilization * (1.0 - contract_mix_haircut)


def full_runrate_revenue(mw: float, rev_per_mw: float,
                         utilization: float, contract_mix_haircut: float) -> float:
    return billed_mw(mw, utilization, contract_mix_haircut) * rev_per_mw


def new_oci_revenue(capex, build_cost_per_mw, rev_per_mw, ramp_factor,
                    utilization, contract_mix_haircut) -> float:
    mw = new_mw(capex, build_cost_per_mw)
    return full_runrate_revenue(mw, rev_per_mw, utilization, contract_mix_haircut) * ramp_factor


def revenue_yield(rev_per_mw: float, build_cost_per_mw: float) -> float:
    return rev_per_mw / build_cost_per_mw if build_cost_per_mw else 0.0


def gross_payback_years(build_cost_per_mw: float, rev_per_mw: float) -> float:
    return build_cost_per_mw / rev_per_mw if rev_per_mw else float("inf")


def pretax_roic(rev_per_mw, opex_per_mw, build_cost_per_mw, gpu_life_years) -> float:
    """Operating profit per billed MW ÷ build-cost per MW (pre-tax, after opex + depreciation)."""
    dep = build_cost_per_mw / gpu_life_years if gpu_life_years else float("inf")
    op = rev_per_mw - opex_per_mw - dep
    return op / build_cost_per_mw if build_cost_per_mw else 0.0


def breakeven_rev_per_mw(opex_per_mw, build_cost_per_mw, gpu_life_years) -> float:
    dep = build_cost_per_mw / gpu_life_years if gpu_life_years else float("inf")
    return opex_per_mw + dep


def capacity_build(inp: CapacityInputs) -> CapacityResult:
    mw = new_mw(inp.capex, inp.build_cost_per_mw)
    bmw = billed_mw(mw, inp.utilization, inp.contract_mix_haircut)
    frr = bmw * inp.rev_per_mw
    new_rev = frr * inp.ramp_factor
    total = inp.prior_oci_rev + new_rev
    oci_g = new_rev / inp.prior_oci_rev if inp.prior_oci_rev else 0.0
    capex_g = inp.capex / inp.prior_capex - 1.0 if inp.prior_capex else 0.0
    cei = oci_g / capex_g if capex_g else float("inf")
    return CapacityResult(
        new_mw=mw, billed_mw=bmw, full_runrate_revenue=frr, new_oci_revenue=new_rev,
        projected_oci_total=total, oci_growth=oci_g, capex_growth=capex_g, projected_cei=cei,
        revenue_yield=revenue_yield(inp.rev_per_mw, inp.build_cost_per_mw),
        gross_payback_years=gross_payback_years(inp.build_cost_per_mw, inp.rev_per_mw),
        pretax_roic=pretax_roic(inp.rev_per_mw, inp.opex_per_mw, inp.build_cost_per_mw, inp.gpu_life_years),
        breakeven_rev_per_mw=breakeven_rev_per_mw(inp.opex_per_mw, inp.build_cost_per_mw, inp.gpu_life_years),
    )


def roic_grid(cost_axis, rev_axis, opex_per_mw, gpu_life_years):
    """Pre-tax ROIC over (build-cost/MW rows × revenue/MW cols)."""
    import numpy as np
    g = np.zeros((len(cost_axis), len(rev_axis)))
    for i, cost in enumerate(cost_axis):
        for j, rev in enumerate(rev_axis):
            g[i, j] = pretax_roic(rev, opex_per_mw, cost, gpu_life_years)
    return g


def cei_grid(cost_axis, rev_axis, base: CapacityInputs):
    """Projected CEI over (build-cost/MW rows × revenue/MW cols)."""
    import numpy as np
    from dataclasses import replace
    g = np.zeros((len(cost_axis), len(rev_axis)))
    for i, cost in enumerate(cost_axis):
        for j, rev in enumerate(rev_axis):
            r = capacity_build(replace(base, build_cost_per_mw=cost, rev_per_mw=rev))
            g[i, j] = r.projected_cei
    return g
