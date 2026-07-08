from ocdvm.peers import Peer
from data.fetch_peers import build_peer_from_price


def test_build_peer_from_price():
    p = build_peer_from_price("CRWV", revenue_ttm=5000.0, shares=480.0,
                              latest_close=100.0, net_debt=8000.0)
    assert isinstance(p, Peer)
    assert p.price == 100.0 and p.revenue_ttm == 5000.0
