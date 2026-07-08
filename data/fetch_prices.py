"""Daily OHLC price boxes.

Price data source of truth for OCDVM is agent-searched values committed to
`config/peers_seed.json` (peer prices) and the `current_price` input field (ORCL),
because free scriptable daily-OHLC feeds are unreliable: Stooq now serves a JavaScript
proof-of-work challenge and Yahoo rate-limits many client IPs.

`fetch_prices` targets Yahoo's public chart JSON API as a single optional refresh — it
works from most CI/server IPs even when a given desktop IP is throttled. Callers treat a
failure as "no fresh prices" and fall back to the committed values (see scripts/refresh_data.py).
`parse_stooq_csv` remains for anyone supplying a Stooq CSV export by hand.
"""
import io
import json

import pandas as pd

from data.http import get

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range={rng}"


def parse_stooq_csv(text: str) -> pd.DataFrame:
    if not text[:4].lower().startswith("date"):
        raise ValueError("not a Stooq CSV (got an HTML/challenge page)")
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "open", "high", "low", "close", "volume"]].sort_values("date")
    return df.reset_index(drop=True)


def parse_yahoo_chart(js: dict) -> pd.DataFrame:
    result = js["chart"]["result"][0]
    ts = result["timestamp"]
    q = result["indicators"]["quote"][0]
    df = pd.DataFrame({
        "date": pd.to_datetime(ts, unit="s").normalize(),
        "open": q["open"], "high": q["high"], "low": q["low"],
        "close": q["close"], "volume": q["volume"],
    })
    df = df.dropna(subset=["open", "high", "low", "close"]).sort_values("date")
    return df.reset_index(drop=True)


def fetch_prices(ticker: str, cache_dir: str = "data/raw/prices", rng: str = "1y") -> pd.DataFrame:
    url = YAHOO.format(sym=ticker.upper(), rng=rng)
    body = get(url, cache_path=f"{cache_dir}/{ticker.lower()}.json", ttl_hours=12)
    return parse_yahoo_chart(json.loads(body))
