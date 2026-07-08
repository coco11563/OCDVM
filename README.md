# OCDVM — Oracle Cloud Dynamic Valuation Model

A dynamic **sum-of-the-parts + valuation-migration** model for Oracle (ORCL). It values
Legacy software and OCI separately, and migrates OCI from Neo-cloud (EV/Sales) toward
mature Hyperscaler (EV/EBITDA) pricing via a transparent, factor-driven weight **α**.

```
EV_Oracle = EV_Legacy + EV_OCI
EV_Legacy = Legacy_EBITDA × M_Software
EV_OCI    = α · Rev_OCI · (M_Neo × Q)  +  (1−α) · EBITDA_OCI · M_Cloud
Target    = (EV_Oracle − NetDebt) / Shares
```

α ∈ [0,1] is computed from OCI fundamentals (revenue growth, CapEx intensity, margins,
FCF, RPO growth, customer concentration) normalized against editable anchor thresholds —
not asserted by hand. **CEI** = OCI revenue growth ÷ CapEx growth flags the lifecycle
regime (Neo < 0.9, Transition, Hyperscaler > 1.1).

## Quick start
```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python run.py --inputs inputs/example.yaml     # demo run with placeholder figures
```
Outputs land in `outputs/<quarter>/` (`result.json`, `report.pdf`, PNGs) and the static
dashboard in `site/index.html`.

## Quarterly update
When Oracle reports, follow **`inputs/AGENT_SEARCH.md`**: an agent web-search pass writes
`inputs/<quarter>.yaml` with sourced figures, then:
```bash
python scripts/refresh_data.py                 # SEC totals + live peer prices
python run.py --inputs inputs/<quarter>.yaml
git add inputs config && git commit -m "data: <quarter>" && git push
```
The push triggers `.github/workflows/on-push.yml`, which republishes the GitHub Pages
dashboard. `.github/workflows/daily.yml` refreshes prices/peer-multiples every weekday and
redeploys automatically.

## Layout
- `ocdvm/` — pure valuation engine (units, valuation, factors, peers, scenarios, sensitivity).
- `data/` — SEC EDGAR + Stooq fetchers (keyless, stdlib `urllib`, cached).
- `backtest/` — post-earnings event study + validation scorecard.
- `calibration/` — bounded EWMA feedback that tunes M_Neo only on systematic error.
- `report/` — titleless PNGs, Markdown/PDF report, Jinja2 dashboard.
- `config/model_config.yaml` — all assumptions (factor weights, anchors, multiples, scenarios).

## Important caveats
- **OCI EBITDA and OCI margins are modeled, not reported.** Oracle does not break out
  OCI-only profitability; `EBITDA_OCI = OCI revenue × oci_op_margin` (an input you control),
  and `Legacy_EBITDA = total EBITDA − modeled OCI EBITDA`. These are clearly flagged in the
  report and dashboard.
- **Backtest depth on the Neo-multiple leg starts ~2025** — CoreWeave IPO'd March 2025, so
  peer-multiple validation only exists from then; earlier quarters validate the Legacy leg
  and the total only.
- All monetary values are in **USD millions**, shares in **millions**, price in **$/share**.

## Calibration guardrails
`python run.py --inputs <q> --calibrate` proposes an M_Neo adjustment **only** when the
model shows systematic error across ≥3 quarters (EWMA), capped at ±10%/quarter and hard-
clamped to [5×, 20×]. Every change is logged; the uncalibrated target is always shown too.
