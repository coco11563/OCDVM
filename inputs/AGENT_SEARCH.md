# Quarterly Agent Search Checklist

When Oracle reports (fiscal Q1≈Sep, Q2≈Dec, Q3≈Mar, Q4≈Jun), an agent gathers the
press-release-only figures via web search and writes `inputs/<quarter>.yaml`.
**Do not hand-type from memory; every figure needs a `source:` URL and cross-check.**

## Source priority
1. Oracle Investor Relations press release (investor.oracle.com) — primary.
2. Oracle 10-Q / 10-K on SEC EDGAR — for totals and net debt.
3. Earnings-call transcript / prepared remarks — for OCI growth %, RPO, CapEx guidance.

## Fields to fill in `inputs/<quarter>.yaml`
| field | meaning | typical source |
|-------|---------|----------------|
| `quarter` | e.g. `2026Q4` (Oracle fiscal) | — |
| `rev_oci_ttm` | OCI/IaaS revenue, trailing 12 months ($M) | press release + prior 3 Qs |
| `rev_oci_q` | OCI revenue this quarter ($M) | press release |
| `oci_rev_growth` | OCI YoY growth (decimal, 0.55=55%) | press release headline |
| `oci_op_margin` | **modeled** OCI operating margin (decimal) | analyst estimate / assumption |
| `oci_fcf_margin` | **modeled** OCI FCF margin (decimal, may be negative) | assumption |
| `capex_ttm` | total CapEx TTM ($M) | cash-flow statement |
| `capex_growth` | CapEx YoY growth (decimal) | vs year-ago |
| `rpo` | remaining performance obligations ($M) | press release |
| `rpo_growth` | RPO YoY growth (decimal) | vs year-ago |
| `customer_concentration` | share of OCI rev from top customers (decimal) or null | call commentary |
| `total_ebitda` | total Oracle EBITDA TTM ($M) | op income + D&A (SEC) |
| `net_debt` | total debt − cash ($M) | balance sheet (SEC) |
| `shares` | diluted shares (M) | SEC |
| `current_price` | ORCL last close ($) | Stooq / any quote |
| `m_software` | Legacy EV/EBITDA multiple (×) | config default 13, adjust w/ peers SAP/IBM |
| `m_cloud` | mature-hyperscaler EV/EBITDA multiple (×) | config default 20 |

Add a `meta:` block:
```yaml
meta:
  source: "https://investor.oracle.com/..."   # primary press release
  retrieved: "YYYY-MM-DD"
  estimated: ["oci_op_margin", "oci_fcf_margin"]   # fields that are modeled, not reported
```

## Cross-check rules
- If two sources disagree on a figure, record both in `meta` and use the SEC/press-release value; flag the conflict.
- `rev_oci_ttm` must be ≈ sum of the last four quarterly OCI figures; if not, re-derive.
- Sanity: OCI YoY growth for a Neo-cloud-stage business is typically 40–120%; a value outside that band needs a second look.

## Also update
- `config/peers_seed.json` — CoreWeave (CRWV) and Nebius (NBIS) `revenue_ttm`, `shares`, `net_debt` from their latest filings (price is fetched live).

## Then
```bash
python scripts/refresh_data.py            # pulls SEC totals + live peer prices
python run.py --inputs inputs/<quarter>.yaml
git add inputs/<quarter>.yaml config/peers_seed.json && git commit -m "data: <quarter> figures"
git push                                  # on-push workflow republishes the dashboard
```
