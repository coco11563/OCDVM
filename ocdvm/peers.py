from dataclasses import dataclass


@dataclass
class Peer:
    ticker: str
    revenue_ttm: float
    price: float
    shares: float
    net_debt: float = 0.0


def ev_sales(peer: Peer) -> float:
    ev = peer.price * peer.shares + peer.net_debt
    return ev / peer.revenue_ttm


def revenue_weighted_median(peers: list) -> float:
    rows = sorted(((ev_sales(p), p.revenue_ttm) for p in peers), key=lambda x: x[0])
    total = sum(w for _, w in rows)
    cum = 0.0
    for mult, w in rows:
        cum += w
        if cum >= 0.5 * total:
            return mult
    return rows[-1][0]


def quality_factor(subscores: dict, cfg: dict) -> float:
    weights = cfg["weights"]
    composite = sum(subscores[k] * weights[k] for k in weights)  # 0..1
    q = cfg["center"] + (composite - 0.5) * 2.0 * cfg["span"]
    return max(cfg["q_min"], min(cfg["q_max"], q))
