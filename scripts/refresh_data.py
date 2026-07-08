"""Daily/on-demand data refresh: pull Oracle financials, peer prices, earnings dates,
then rerun the model on the newest inputs/*.yaml and regenerate site/.

Peer revenue/shares/net_debt come from config/peers_seed.json (agent-maintained);
peer *price* is fetched live from Stooq. Oracle totals and earnings dates come from
SEC EDGAR. Network failures are logged and skipped, never fatal.
"""
import glob
import json
import os
import subprocess
import sys

from data.fetch_oracle import fetch_oracle
from data.fetch_peers import build_peer
from data.earnings_dates import fetch_earnings_dates

PEERS_SEED = "config/peers_seed.json"


def refresh_peers(seed_path=PEERS_SEED) -> list:
    peers = []
    seeds = json.load(open(seed_path)) if os.path.exists(seed_path) else []
    for s in seeds:
        try:
            p = build_peer(s["ticker"], s["revenue_ttm"], s["shares"], s.get("net_debt", 0.0))
            peers.append({"ticker": p.ticker, "revenue_ttm": p.revenue_ttm,
                          "price": p.price, "shares": p.shares, "net_debt": p.net_debt})
        except Exception as e:  # noqa: BLE001
            print(f"[refresh] peer {s['ticker']} price fetch failed: {e}", file=sys.stderr)
    return peers


def main():
    os.makedirs("data/raw", exist_ok=True)
    try:
        fin = fetch_oracle()
        json.dump(fin.__dict__, open("data/raw/oracle.json", "w"), indent=2)
        print("[refresh] oracle financials ok:", fin.total_revenue_ttm, "M revenue TTM")
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
