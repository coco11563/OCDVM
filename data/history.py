"""Oracle annual (fiscal-year) time series from SEC EDGAR, for corroborating trend charts."""
from data.fetch_oracle import _concept, TAG_REVENUE, TAG_CAPEX, TAG_RPO


def annual_fy(values: list) -> dict:
    """Return {fiscal_year_end: value_$M} for annual (10-K / fp=FY) points only."""
    out = {}
    for v in values:
        if v.get("form") == "10-K" and v.get("fp") == "FY":
            out[v["end"]] = v["val"] / 1e6
    return dict(sorted(out.items()))


def oracle_annual_series(cache_dir: str = "data/raw") -> dict:
    return {
        "revenue": annual_fy(_concept(TAG_REVENUE, cache_dir)),
        "capex": annual_fy(_concept(TAG_CAPEX, cache_dir)),
        "rpo": annual_fy(_concept(TAG_RPO, cache_dir)),
    }
