from ocdvm.units import QuarterInputs


def make_inputs(**kw):
    base = dict(quarter="2026Q4", rev_oci_ttm=12000.0, rev_oci_q=3500.0,
                oci_rev_growth=0.55, oci_op_margin=0.10, oci_fcf_margin=-0.20,
                capex_ttm=25000.0, capex_growth=0.70, rpo=130000.0, rpo_growth=0.40,
                customer_concentration=0.40, total_ebitda=25000.0, net_debt=76000.0,
                shares=2800.0, current_price=140.0, m_software=13.0, m_cloud=20.0)
    base.update(kw)
    return QuarterInputs(**base)
