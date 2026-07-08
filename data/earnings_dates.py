import json

from data.http import get

SUB = "https://data.sec.gov/submissions/CIK{cik}.json"


def parse_filing_dates(js: dict, forms=("10-Q", "10-K")) -> list:
    recent = js["filings"]["recent"]
    pairs = [(d, f) for f, d in zip(recent["form"], recent["filingDate"]) if f in forms]
    return sorted(d for d, _ in pairs)


def fetch_earnings_dates(cik: str = "0001341439", cache_dir: str = "data/raw") -> list:
    body = get(SUB.format(cik=cik), cache_path=f"{cache_dir}/orcl_submissions.json", ttl_hours=24)
    return parse_filing_dates(json.loads(body))
