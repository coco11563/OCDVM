import json
from dataclasses import dataclass

from data.http import get

CIK = "0001341439"
BASE = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"


@dataclass
class OracleFinancials:
    total_revenue_ttm: float
    operating_income_ttm: float
    dep_amort_ttm: float
    total_debt: float
    cash: float
    shares: float


def parse_us_gaap_concept(js: dict, unit: str = "USD") -> list:
    out = []
    for row in js.get("units", {}).get(unit, []):
        if "val" in row and "end" in row:
            out.append({"start": row.get("start"), "end": row["end"],
                        "val": row["val"], "form": row.get("form"), "fp": row.get("fp")})
    out.sort(key=lambda r: r["end"])
    return out


def latest_ttm(values: list) -> float:
    """Sum the last 4 quarterly (10-Q) points; fall back to latest annual value. Returns $M."""
    quarterly = [v for v in values if v.get("form") == "10-Q"]
    if len(quarterly) >= 4:
        return float(sum(v["val"] for v in quarterly[-4:])) / 1e6
    return float(values[-1]["val"]) / 1e6


def _concept(tag: str, cache_dir: str) -> list:
    url = BASE.format(cik=CIK, tag=tag)
    body = get(url, cache_path=f"{cache_dir}/orcl_{tag}.json", ttl_hours=24)
    return parse_us_gaap_concept(json.loads(body))


def _latest_point(tag: str, cache_dir: str) -> float:
    return _concept(tag, cache_dir)[-1]["val"] / 1e6


def fetch_oracle(cache_dir: str = "data/raw") -> OracleFinancials:
    rev = latest_ttm(_concept("RevenueFromContractWithCustomerExcludingAssessedTax", cache_dir))
    opinc = latest_ttm(_concept("OperatingIncomeLoss", cache_dir))
    da = latest_ttm(_concept("DepreciationDepletionAndAmortization", cache_dir))
    debt = _latest_point("LongTermDebtNoncurrent", cache_dir)
    cash = _latest_point("CashAndCashEquivalentsAtCarryingValue", cache_dir)
    shares = _latest_point("WeightedAverageNumberOfDilutedSharesOutstanding", cache_dir)
    return OracleFinancials(rev, opinc, da, debt, cash, shares)
