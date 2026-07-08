from data.fetch_prices import parse_stooq_csv


def test_parse_stooq():
    with open("tests/fixtures/orcl_stooq_sample.csv") as f:
        df = parse_stooq_csv(f.read())
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert len(df) >= 5
    assert df["date"].is_monotonic_increasing
    assert (df["high"] >= df["low"]).all()
