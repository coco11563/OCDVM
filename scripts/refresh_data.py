"""Daily/on-demand data refresh.

- Oracle totals + earnings dates: SEC EDGAR (reliable, keyless).
- Peers: built from config/peers_seed.json (agent-searched price/revenue/shares/net_debt
  are the source of truth). A live price refresh via Yahoo is attempted and, when it
  succeeds, overwrites the seed price; when it fails (throttled IP), the committed seed
  price is used. This is cache + optional refresh, not a fallback tower.
- Then reruns the model on the newest inputs/*.yaml and regenerates site/.

All network failures are logged and non-fatal.
"""
import glob
import json
import os
import subprocess
import sys

from data.fetch_oracle import fetch_oracle
from data.fetch_prices import fetch_prices
from data.earnings_dates import fetch_earnings_dates

PEERS_SEED = "config/peers_seed.json"


def refresh_peers(seed_path=PEERS_SEED) -> list:
    seeds = json.load(open(seed_path)) if os.path.exists(seed_path) else []
    peers = []
    for s in seeds:
        price = s["price"]
        try:
            price = float(fetch_prices(s["ticker"])["close"].iloc[-1])
            print(f"[refresh] {s['ticker']} live price {price}")
        except Exception as e:  # noqa: BLE001
            print(f"[refresh] {s['ticker']} live price unavailable ({e}); using seed {price}",
                  file=sys.stderr)
        peers.append({"ticker": s["ticker"], "revenue_ttm": s["revenue_ttm"],
                      "price": price, "shares": s["shares"], "net_debt": s.get("net_debt", 0.0)})
    return peers


def main():
    os.makedirs("data/raw", exist_ok=True)
    try:
        fin = fetch_oracle()
        json.dump(fin.__dict__, open("data/raw/oracle.json", "w"), indent=2)
        print(f"[refresh] oracle ok: revenue {fin.total_revenue_ttm:,.0f}M, "
              f"capex {fin.capex_ttm:,.0f}M, rpo {fin.rpo:,.0f}M")
    except Exception as e:  # noqa: BLE001
        print(f"[refresh] oracle fetch failed: {e}", file=sys.stderr)

    peers = refresh_peers()
    json.dump(peers, open("data/raw/peers.json", "w"), indent=2)
    print(f"[refresh] peers.json written with {len(peers)} peers")

    try:
        dates = fetch_earnings_dates()
        json.dump(dates, open("data/raw/earnings_dates.json", "w"), indent=2)
        print(f"[refresh] earnings dates: {dates[-3:] if dates else 'none'}")
    except Exception as e:  # noqa: BLE001
        print(f"[refresh] earnings dates fetch failed: {e}", file=sys.stderr)

    latest = sorted(glob.glob("inputs/2*.yaml"))
    if latest:
        print(f"[refresh] rerunning model on {latest[-1]}")
        subprocess.run([sys.executable, "run.py", "--inputs", latest[-1]], check=False)
    else:
        print("[refresh] no inputs/<quarter>.yaml found; skipping model run")


if __name__ == "__main__":
    main()
