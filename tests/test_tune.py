from calibration.tune import ewma, propose_m_neo

CFG = {"ewma_lambda": 0.5, "max_step_pct": 0.10, "min_quarters": 3,
       "m_neo_hard_min": 5.0, "m_neo_hard_max": 20.0}


def test_ewma_recency_weighted():
    assert abs(ewma([0.1, 0.2, 0.3], 0.5) - (
        (0.3 * 0.5 + 0.2 * 0.25 + 0.1 * 0.125) / (0.5 + 0.25 + 0.125))) < 1e-9


def test_no_change_below_min_quarters():
    m, log = propose_m_neo(10.0, [0.2, 0.2], CFG)
    assert m == 10.0 and log["applied"] is False


def test_positive_error_lowers_multiple_capped():
    m, log = propose_m_neo(10.0, [0.5, 0.5, 0.5], CFG)   # model too high
    assert m < 10.0
    assert m >= 10.0 * (1 - CFG["max_step_pct"])         # step capped at 10%
    assert log["applied"] is True


def test_hard_clamp():
    m, _ = propose_m_neo(5.2, [0.9, 0.9, 0.9], CFG)
    assert m >= CFG["m_neo_hard_min"]
