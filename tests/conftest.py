from ocdvm.units import QuarterInputs


def make_inputs(**kw):
    base = dict(quarter="2026Q4", rev_oci_ttm=12000.0, rev_oci_q=3500.0,
                oci_rev_growth=0.55, oci_op_margin=0.10, oci_fcf_margin=-0.20,
                capex_ttm=25000.0, capex_growth=0.70, rpo=130000.0, rpo_growth=0.40,
                customer_concentration=0.40, total_ebitda=25000.0, net_debt=76000.0,
                shares=2800.0, current_price=140.0, m_software=13.0, m_cloud=20.0)
    base.update(kw)
    return QuarterInputs(**base)


def make_result(**kw):
    """A complete result dict as assemble_result() produces — for report/commentary tests."""
    base = dict(
        quarter="2026Q4", alpha=0.80, cei=0.47, regime="neo",
        factor_scores={"oci_rev_growth": 0.71, "capex_growth": 1.0, "capex_to_revenue": 1.0,
                       "oci_op_margin": 0.70, "oci_fcf_margin": 1.0, "rpo_growth": 1.0,
                       "customer_concentration": 0.83},
        weights_used={"oci_rev_growth": 0.20, "capex_growth": 0.15, "capex_to_revenue": 0.15,
                      "oci_op_margin": 0.20, "oci_fcf_margin": 0.15, "rpo_growth": 0.10,
                      "customer_concentration": 0.05},
        m_neo=9.0, q=1.07, oci_multiple_effective=9.63,
        legacy_ebitda=27728.0, ebitda_oci=2172.0,
        ev_legacy=360464.0, ev_oci=157941.0, ev_total=518405.0,
        equity=420153.0, target=144.18, pw_price=147.37, expected_return=0.029,
        scenarios={"Bear": 119.3, "Base": 144.2, "Bull": 181.8},
        sensitivity=[[100, 110], [120, 130]],
        sensitivity_axes={"growth": [0.8, 1.0], "mneo": [8.0, 10.0]},
        current_price=143.23,
        peers_detail=[{"ticker": "CRWV", "ev_sales": 9.18, "revenue_ttm": 6230.0},
                      {"ticker": "NBIS", "ev_sales": 120.5, "revenue_ttm": 530.0}],
        market_cap=417372.0, market_ev=515624.0, net_debt=98252.0,
        rev_oci_ttm=18100.0, rev_oci_q=5800.0, oci_rev_growth=0.77,
        capex_ttm=55663.0, capex_growth=1.6238, rpo=638000.0, rpo_growth=3.6285,
        oci_fcf_margin=-1.00, oci_op_margin=0.12)
    base.update(kw)
    return base
