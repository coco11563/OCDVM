from dataclasses import dataclass

from ocdvm.units import QuarterInputs


def normalize(value: float, lo: float, hi: float) -> float:
    """Linear map value in [lo,hi] -> [0,1], clamped. If hi<lo, the mapping inverts."""
    if hi == lo:
        return 0.0
    t = (value - lo) / (hi - lo)
    return max(0.0, min(1.0, t))


def cei(oci_rev_growth: float, capex_growth: float):
    if capex_growth == 0:
        return None
    return oci_rev_growth / capex_growth


def cei_regime(cei_value) -> str:
    if cei_value is None:
        return "undefined"
    if cei_value < 0.9:
        return "neo"
    if cei_value > 1.1:
        return "hyperscaler"
    return "transition"


@dataclass
class AlphaResult:
    alpha: float
    factor_scores: dict
    weights_used: dict
    active_factors: list
    cei: float | None
    regime: str


def _factor_raw_values(inp: QuarterInputs) -> dict:
    capex_to_rev = inp.capex_ttm / inp.rev_oci_ttm if inp.rev_oci_ttm else None
    return {
        "oci_rev_growth": inp.oci_rev_growth,
        "capex_growth": inp.capex_growth,
        "capex_to_revenue": capex_to_rev,
        "oci_op_margin": inp.oci_op_margin,
        "oci_fcf_margin": inp.oci_fcf_margin,
        "rpo_growth": inp.rpo_growth,
        "customer_concentration": inp.customer_concentration,
    }


def compute_alpha(inp: QuarterInputs, cfg: dict) -> AlphaResult:
    anchors = cfg["anchors"]
    raw = _factor_raw_values(inp)
    scores, weights = {}, {}
    for name, spec in anchors.items():
        val = raw.get(name)
        if val is None:
            continue
        scores[name] = normalize(val, spec["lo"], spec["hi"])
        weights[name] = spec["weight"]
    total_w = sum(weights.values())
    weights_used = {k: v / total_w for k, v in weights.items()} if total_w else {}
    alpha = sum(scores[k] * weights_used[k] for k in weights_used)
    c = cei(inp.oci_rev_growth, inp.capex_growth)
    return AlphaResult(alpha=alpha, factor_scores=scores, weights_used=weights_used,
                       active_factors=list(scores), cei=c, regime=cei_regime(c))
