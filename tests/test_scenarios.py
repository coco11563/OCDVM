from ocdvm.scenarios import Scenario, scenario_target, probability_weighted, expected_return
from ocdvm.valuation import value_company
from tests.conftest import make_inputs


def test_base_scenario_matches_value_company():
    inp = make_inputs()
    base = Scenario("Base", 0.5, growth_mult=1.0, m_neo_delta=0.0, alpha_delta=0.0)
    assert abs(scenario_target(inp, 0.8, 10.0, 1.0, base)
               - value_company(inp, 0.8, 10.0, 1.0).target) < 1e-9


def test_probability_weighted_and_return():
    pw = probability_weighted({"Bear": 100.0, "Base": 150.0, "Bull": 200.0},
                              {"Bear": 0.25, "Base": 0.5, "Bull": 0.25})
    assert pw == 100.0 * 0.25 + 150.0 * 0.5 + 200.0 * 0.25
    assert abs(expected_return(150.0, 120.0) - 0.25) < 1e-9
