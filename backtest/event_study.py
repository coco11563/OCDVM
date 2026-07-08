from dataclasses import dataclass

import pandas as pd


@dataclass
class EventStats:
    gap_pct: float
    drift_pct: float
    range_low: float
    range_high: float
    settle_close: float


def event_window(prices: pd.DataFrame, earnings_date, pre=5, post=20) -> pd.DataFrame:
    d = pd.to_datetime(earnings_date)
    df = prices.sort_values("date").reset_index(drop=True)
    after = df.index[df["date"] >= d]
    t0 = int(after[0]) if len(after) else len(df) - 1
    lo, hi = max(0, t0 - pre), min(len(df), t0 + post + 1)
    w = df.iloc[lo:hi].copy()
    w["t"] = range(lo - t0, hi - t0)
    return w.reset_index(drop=True)


def event_stats(window: pd.DataFrame) -> EventStats:
    pre = window[window["t"] < 0]
    post = window[window["t"] >= 0]
    prev_close = float(pre["close"].iloc[-1]) if len(pre) else float(post["open"].iloc[0])
    t0_open = float(post["open"].iloc[0])
    gap = t0_open / prev_close - 1.0
    settle = float(post["close"].iloc[-1])
    drift = settle / t0_open - 1.0
    return EventStats(gap_pct=gap, drift_pct=drift,
                      range_low=float(post["low"].min()),
                      range_high=float(post["high"].max()),
                      settle_close=settle)
