import pandas as pd

from backtest.event_study import event_window, event_stats


def _prices():
    dates = pd.date_range("2026-03-02", periods=30, freq="B")
    closes = [100 + i for i in range(30)]
    return pd.DataFrame({"date": dates,
                         "open": [c - 0.5 for c in closes],
                         "high": [c + 1 for c in closes],
                         "low":  [c - 1 for c in closes],
                         "close": closes, "volume": [1] * 30})


def test_window_and_stats():
    df = _prices()
    w = event_window(df, "2026-03-11", pre=5, post=20)
    assert (w["t"] == 0).any()
    s = event_stats(w)
    assert s.range_high >= s.range_low
    assert s.settle_close == w[w["t"] >= 0]["close"].iloc[-1]
