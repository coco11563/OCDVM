import pytest

from ocdvm.capacity import (CapacityInputs, capacity_build, new_mw, pretax_roic,
                            breakeven_rev_per_mw, roic_grid, cei_grid)


def _note_inputs(**kw):
    """Fitzsimmons headline assumptions: util=1, no haircut -> reproduces his ~$23B new OCI."""
    base = dict(capex=110400.0, prior_capex=55663.0, prior_oci_rev=18100.0,
                build_cost_per_mw=46.0, rev_per_mw=13.5, ramp_factor=0.71,
                utilization=1.0, contract_mix_haircut=0.0,
                opex_per_mw=0.0, gpu_life_years=6.1)
    base.update(kw)
    return CapacityInputs(**base)


def test_new_mw_matches_note():
    assert new_mw(110400.0, 46.0) == pytest.approx(2400.0)


def test_reproduces_fitzsimmons_headline():
    r = capacity_build(_note_inputs())
    assert r.new_mw == pytest.approx(2400.0)
    assert r.full_runrate_revenue == pytest.approx(2400.0 * 13.5)      # 32400
    assert r.new_oci_revenue == pytest.approx(23004.0, rel=1e-3)       # ~$23B
    assert r.projected_oci_total == pytest.approx(41104.0, rel=1e-3)   # ~$41.1B
    assert r.oci_growth == pytest.approx(1.271, rel=1e-2)              # +127%
    assert r.projected_cei == pytest.approx(1.29, rel=2e-2)           # jumps into hyperscaler
    # note's own ~13% ROIC comes from ~0 opex + ~6.1yr life
    assert r.pretax_roic == pytest.approx(0.129, abs=0.01)


def test_realistic_haircut_lowers_revenue_and_cei():
    r = capacity_build(_note_inputs(utilization=0.90, contract_mix_haircut=0.20))
    assert r.new_oci_revenue < 23004.0                # delivery friction cuts the headline
    assert r.new_oci_revenue == pytest.approx(23004.0 * 0.72, rel=1e-3)
    assert r.projected_cei < 1.29                     # regime change is fragile


def test_roic_sensitivity_to_revenue_per_mw():
    # with real opex and 5.5yr life, ROIC collapses as rev/MW falls toward CoreWeave levels
    high = pretax_roic(13.5, 2.5, 46.0, 5.5)
    low = pretax_roic(6.0, 2.5, 46.0, 5.5)
    assert high > low
    assert low < 0                                    # below break-even -> value-destructive
    assert breakeven_rev_per_mw(2.5, 46.0, 5.5) == pytest.approx(2.5 + 46.0 / 5.5)


def test_grids_shapes():
    g = roic_grid([35, 46], [6, 13.5], opex_per_mw=2.5, gpu_life_years=5.5)
    assert g.shape == (2, 2)
    c = cei_grid([35, 46], [6, 13.5], _note_inputs(utilization=0.9, contract_mix_haircut=0.2))
    assert c.shape == (2, 2)
