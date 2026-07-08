from dataclasses import dataclass, replace

from ocdvm.units import QuarterInputs
from ocdvm.valuation import value_company


@dataclass
class Scenario:
    name: str
    prob: float
    growth_mult: float   # scales rev_oci_ttm
    m_neo_delta: float   # additive to M_Neo
    alpha_delta: float   # additive to alpha, result clamped [0,1]


def scenario_target(inp: QuarterInputs, base_alpha: float, base_m_neo: float,
                    q: float, scn: Scenario) -> float:
    inp2 = replace(inp, rev_oci_ttm=inp.rev_oci_ttm * scn.growth_mult)
    alpha = max(0.0, min(1.0, base_alpha + scn.alpha_delta))
    m_neo = base_m_neo + scn.m_neo_delta
    return value_company(inp2, alpha, m_neo, q).target


def probability_weighted(name_to_price: dict, name_to_prob: dict) -> float:
    return sum(name_to_price[k] * name_to_prob[k] for k in name_to_price)


def expected_return(pw_price: float, current_price: float) -> float:
    return pw_price / current_price - 1.0
