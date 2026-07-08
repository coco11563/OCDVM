import io

import pandas as pd

from data.http import get

STOOQ = "https://stooq.com/q/d/l/?s={sym}.us&i=d"


def parse_stooq_csv(text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "open", "high", "low", "close", "volume"]].sort_values("date")
    return df.reset_index(drop=True)


def fetch_prices(ticker: str, cache_dir: str = "data/raw/prices") -> pd.DataFrame:
    url = STOOQ.format(sym=ticker.lower())
    body = get(url, cache_path=f"{cache_dir}/{ticker.lower()}.csv", ttl_hours=12)
    return parse_stooq_csv(body.decode("utf-8"))
