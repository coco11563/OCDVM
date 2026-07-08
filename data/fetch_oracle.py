import json
from dataclasses import dataclass

from data.http import get

CIK = "0001341439"
BASE = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"

# Oracle-specific us-gaap tags (verified against companyfacts CIK0001341439).
TAG_REVENUE = "RevenueFromContractWithCustomerExcludingAssessedTax"
TAG_OPINC = "OperatingIncomeLoss"
TAG_DEP = "Depreciation"                      # Oracle splits D&A into two tags
TAG_AMORT = "AmortizationOfIntangibleAssets"
TAG_DEBT = "DebtLongtermAndShorttermCombinedAmount"
TAG_CASH = "CashAndCashEquivalentsAtCarryingValue"
TAG_SHARES = "WeightedAverageNumberOfDilutedSharesOutstanding"
TAG_CAPEX = "PaymentsToAcquirePropertyPlantAndEquipment"
TAG_RPO = "RevenueRemainingPerformanceObligation"


@dataclass
class OracleFinancials:
    total_revenue_ttm: float
    operating_income_ttm: float
    dep_amort_ttm: float
    total_debt: float
    cash: float
    shares: float
    capex_ttm: float
    rpo: float


def parse_us_gaap_concept(js: dict, unit: str = "USD") -> list:
    out = []
    for row in js.get("units", {}).get(unit, []):
        if "val" in row and "end" in row:
            out.append({"start": row.get("start"), "end": row["end"],
                        "val": row["val"], "form": row.get("form"), "fp": row.get("fp")})
    out.sort(key=lambda r: r["end"])
    return out


def latest_ttm(values: list) -> float:
    """TTM for an income-statement flow, in $M.

    If the newest point is an annual (10-K / fp=FY) it already equals the trailing
    twelve months, so return it. Otherwise sum the last four quarterly (10-Q) points;
    fall back to the newest value if fewer than four quarters exist.
    """
    if not values:
        return 0.0
    newest = values[-1]
    if newest.get("form") == "10-K" or newest.get("fp") == "FY":
        return float(newest["val"]) / 1e6
    quarterly = [v for v in values if v.get("form") == "10-Q"]
    if len(quarterly) >= 4:
        return float(sum(v["val"] for v in quarterly[-4:])) / 1e6
    return float(newest["val"]) / 1e6


def _concept(tag: str, cache_dir: str) -> list:
    url = BASE.format(cik=CIK, tag=tag)
    body = get(url, cache_path=f"{cache_dir}/orcl_{tag}.json", ttl_hours=24)
    return parse_us_gaap_concept(json.loads(body))


def _latest_point(tag: str, cache_dir: str) -> float:
    vals = _concept(tag, cache_dir)
    return vals[-1]["val"] / 1e6 if vals else 0.0


def fetch_oracle(cache_dir: str = "data/raw") -> OracleFinancials:
    rev = latest_ttm(_concept(TAG_REVENUE, cache_dir))
    opinc = latest_ttm(_concept(TAG_OPINC, cache_dir))
    da = latest_ttm(_concept(TAG_DEP, cache_dir)) + latest_ttm(_concept(TAG_AMORT, cache_dir))
    debt = _latest_point(TAG_DEBT, cache_dir)
    cash = _latest_point(TAG_CASH, cache_dir)
    shares = _latest_point(TAG_SHARES, cache_dir)
    capex = latest_ttm(_concept(TAG_CAPEX, cache_dir))
    rpo = _latest_point(TAG_RPO, cache_dir)
    return OracleFinancials(rev, opinc, da, debt, cash, shares, capex, rpo)
