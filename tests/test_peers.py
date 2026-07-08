from ocdvm.peers import Peer, ev_sales, revenue_weighted_median, quality_factor

QCFG = {"q_min": 0.85, "q_max": 1.20,
        "weights": {"revenue_quality": 0.3, "diversification": 0.3,
                    "balance_sheet": 0.2, "ecosystem": 0.2},
        "center": 1.0, "span": 0.20}


def test_ev_sales():
    p = Peer("CRWV", revenue_ttm=5000.0, price=100.0, shares=480.0, net_debt=8000.0)
    assert ev_sales(p) == (100.0 * 480.0 + 8000.0) / 5000.0


def test_revenue_weighted_median_picks_50pct_crossing():
    peers = [
        Peer("A", revenue_ttm=1000.0, price=10.0, shares=100.0),
        Peer("B", revenue_ttm=3000.0, price=20.0, shares=1000.0),
        Peer("C", revenue_ttm=1000.0, price=50.0, shares=200.0),
    ]
    assert abs(revenue_weighted_median(peers) - (20.0 * 1000.0) / 3000.0) < 1e-9


def test_quality_factor_bounds_and_center():
    q = quality_factor({"revenue_quality": 0.5, "diversification": 0.5,
                        "balance_sheet": 0.5, "ecosystem": 0.5}, QCFG)
    assert abs(q - 1.0) < 1e-9
    q_hi = quality_factor({"revenue_quality": 1.0, "diversification": 1.0,
                           "balance_sheet": 1.0, "ecosystem": 1.0}, QCFG)
    assert abs(q_hi - 1.20) < 1e-9
