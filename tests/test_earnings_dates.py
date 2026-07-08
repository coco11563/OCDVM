from data.earnings_dates import parse_filing_dates


def test_parse_filing_dates():
    js = {"filings": {"recent": {
        "form": ["10-Q", "8-K", "10-K", "10-Q"],
        "filingDate": ["2026-03-10", "2026-03-10", "2025-06-20", "2025-12-08"]}}}
    dates = parse_filing_dates(js, forms=("10-Q", "10-K"))
    assert dates == ["2025-06-20", "2025-12-08", "2026-03-10"]
