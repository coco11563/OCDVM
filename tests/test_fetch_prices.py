import pytest

from data.fetch_prices import parse_stooq_csv, parse_yahoo_chart


def test_parse_stooq():
    with open("tests/fixtures/orcl_stooq_sample.csv") as f:
        df = parse_stooq_csv(f.read())
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert len(df) >= 5
    assert df["date"].is_monotonic_increasing
    assert (df["high"] >= df["low"]).all()


def test_parse_stooq_rejects_challenge_page():
    with pytest.raises(ValueError):
        parse_stooq_csv("<!DOCTYPE html><html>JS challenge</html>")


def test_parse_yahoo_chart():
    js = {"chart": {"result": [{
        "timestamp": [1751500800, 1751587200],
        "indicators": {"quote": [{
            "open": [142.0, 143.0], "high": [144.0, 145.5],
            "low": [141.0, 142.5], "close": [143.2, 145.0],
            "volume": [1000, 1200]}]}}]}}
    df = parse_yahoo_chart(js)
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert len(df) == 2
    assert df["close"].iloc[-1] == 145.0
    assert (df["high"] >= df["low"]).all()
