from dataclasses import dataclass

from ocdvm.units import QuarterInputs, ebitda_oci, legacy_ebitda


@dataclass
class ValuationResult:
    ev_legacy: float
    ev_oci: float
    ev_total: float
    equity: float
    target: float


def ev_legacy(legacy_ebitda_val: float, m_software: float) -> float:
    return legacy_ebitda_val * m_software


def ev_oci(alpha: float, rev_oci: float, m_neo: float, q: float,
           ebitda_oci_val: float, m_cloud: float) -> float:
    """alpha*Rev*(M_Neo*Q) + (1-alpha)*EBITDA*M_Cloud."""
    neo_leg = alpha * rev_oci * (m_neo * q)
    cloud_leg = (1.0 - alpha) * ebitda_oci_val * m_cloud
    return neo_leg + cloud_leg


def value_company(inp: QuarterInputs, alpha: float, m_neo: float, q: float) -> ValuationResult:
    leg = ev_legacy(legacy_ebitda(inp), inp.m_software)
    oci = ev_oci(alpha, inp.rev_oci_ttm, m_neo, q, ebitda_oci(inp), inp.m_cloud)
    ev = leg + oci
    equity = ev - inp.net_debt
    target = equity / inp.shares
    return ValuationResult(ev_legacy=leg, ev_oci=oci, ev_total=ev, equity=equity, target=target)
