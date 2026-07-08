import pytest

from ocdvm.factors import normalize, cei, cei_regime, compute_alpha
from tests.conftest import make_inputs

CFG = {
    "anchors": {
        "oci_rev_growth":        {"lo": 0.20, "hi": 1.00, "weight": 0.20},
        "capex_growth":          {"lo": 0.10, "hi": 1.20, "weight": 0.15},
        "capex_to_revenue":      {"lo": 0.15, "hi": 0.90, "weight": 0.15},
        "oci_op_margin":         {"lo": 0.40, "hi": 0.00, "weight": 0.20},
        "oci_fcf_margin":        {"lo": 0.30, "hi": -0.40, "weight": 0.15},
        "rpo_growth":            {"lo": 0.15, "hi": 0.80, "weight": 0.10},
        "customer_concentration": {"lo": 0.10, "hi": 0.70, "weight": 0.05},
    },
    "cei_bands": {"neo_below": 0.9, "hyper_above": 1.1},
}


def test_normalize_clamped_and_inverted():
    assert normalize(0.60, 0.20, 1.00) == (0.60 - 0.20) / (1.00 - 0.20)
    assert normalize(5.0, 0.20, 1.00) == 1.0
    assert normalize(-5.0, 0.20, 1.00) == 0.0
    assert normalize(0.10, 0.40, 0.00) == pytest.approx(0.75)


def test_cei_and_regime():
    assert cei(0.55, 0.70) == 0.55 / 0.70
    assert cei_regime(0.5) == "neo"
    assert cei_regime(1.0) == "transition"
    assert cei_regime(1.5) == "hyperscaler"


def test_alpha_all_factors_in_range():
    r = compute_alpha(make_inputs(), CFG)
    assert 0.0 <= r.alpha <= 1.0
    assert set(r.active_factors) == set(CFG["anchors"])
    assert abs(sum(r.weights_used.values()) - 1.0) < 1e-9


def test_alpha_drops_missing_and_renormalizes():
    r = compute_alpha(make_inputs(customer_concentration=None), CFG)
    assert "customer_concentration" not in r.active_factors
    assert abs(sum(r.weights_used.values()) - 1.0) < 1e-9
