from ocdvm.peers import Peer
from data.fetch_prices import fetch_prices


def build_peer_from_price(ticker, revenue_ttm, shares, latest_close, net_debt=0.0) -> Peer:
    return Peer(ticker=ticker, revenue_ttm=revenue_ttm, price=latest_close,
                shares=shares, net_debt=net_debt)


def build_peer(ticker, revenue_ttm, shares, net_debt=0.0, cache_dir="data/raw/prices") -> Peer:
    close = float(fetch_prices(ticker, cache_dir)["close"].iloc[-1])
    return build_peer_from_price(ticker, revenue_ttm, shares, close, net_debt)
