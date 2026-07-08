from dataclasses import dataclass

MM = 1.0  # documents that monetary fields are in USD millions


@dataclass
class QuarterInputs:
    quarter: str
    rev_oci_ttm: float
    rev_oci_q: float
    oci_rev_growth: float
    oci_op_margin: float
    oci_fcf_margin: float
    capex_ttm: float
    capex_growth: float
    rpo: float
    rpo_growth: float
    customer_concentration: float | None
    total_ebitda: float
    net_debt: float
    shares: float
    current_price: float
    m_software: float
    m_cloud: float


def ebitda_oci(inp: QuarterInputs) -> float:
    """Modeled OCI EBITDA = OCI TTM revenue x OCI operating margin (not reported by Oracle)."""
    return inp.rev_oci_ttm * inp.oci_op_margin


def legacy_ebitda(inp: QuarterInputs) -> float:
    """Legacy EBITDA = total Oracle EBITDA - modeled OCI EBITDA (segments sum to whole)."""
    return inp.total_ebitda - ebitda_oci(inp)
