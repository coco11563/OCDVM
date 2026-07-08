# OCDVM — Oracle Cloud Dynamic Valuation Model

**Design spec** · 2026-07-08 · status: approved for planning

## 1. Motivation

Traditional Oracle (ORCL) valuation applies one methodology (PE / EV/EBITDA) to the
whole company and ignores that OCI (Oracle Cloud Infrastructure) is an early-lifecycle
AI-infrastructure business that trades more like CoreWeave / Nebius than like the mature
Oracle database franchise.

OCDVM instead splits Oracle into two segments valued differently, and — the core
innovation — treats OCI as an asset whose **valuation methodology migrates over its
lifecycle**, from Neo-cloud (EV/Sales) toward mature Hyperscaler (EV/EBITDA), with the
migration speed driven by quantified fundamentals rather than subjective judgment.

```
EV_Oracle = EV_Legacy + EV_OCI
EV_Legacy = Legacy_EBITDA × M_Software
EV_OCI    = α · Rev_OCI · (M_Neo × Q)  +  (1−α) · EBITDA_OCI · M_Cloud
Equity    = EV_Oracle − NetDebt
Target    = Equity / Shares
```

α ∈ [0,1] is the degree to which OCI still prices as Neo-cloud. It is **computed** from
factors, not asserted.

## 2. Scope & non-goals

**In scope:** hybrid data ingestion, transparent factor→α engine, SOTP+migration
valuation, probability-weighted scenarios, 2D sensitivity, post-earnings price-box
validation with bounded calibration feedback, a clean PNG→Markdown→PDF report, a static
GitHub Pages dashboard, and daily GitHub Actions automation.

**Non-goals:** intraday/real-time trading signals; brittle in-Actions regex scraping of OCI
figures (gathered instead by an agent web-search pass, §3); options/derivatives modeling; a
server-side web app (static site only).

## 3. Data strategy (hybrid)

Auto-pull what is reliably machine-readable; hand-curate the handful of numbers that live
only in press-release text.

**Auto (keyless, cached under `data/raw/`):**
- `data/fetch_oracle.py` — SEC EDGAR XBRL (ORCL CIK 0001341439) companyfacts: total
  revenue, operating income, D&A (→ total EBITDA), total debt, cash & equivalents, diluted
  shares. Requires a User-Agent header (verified: HTTP 200).
- `data/fetch_peers.py` — CoreWeave (CRWV) and Nebius (NBIS) revenue from their filings;
  market cap = price × shares. Prices via Stooq CSV (daily OHLC, not rate-limited like
  Yahoo). Lambda / Crusoe / Together AI are **private** — config placeholders only,
  activated if a manual number is supplied.
- `data/fetch_prices.py` — daily OHLC "boxes" for ORCL/CRWV/NBIS from Stooq; historical
  prices also reconstruct historical peer EV/Sales for the backtest.
- `data/earnings_dates.py` — earnings/filing dates from SEC submissions JSON, with a
  curated fallback list.

**Search-gathered, agent-driven (`inputs/<quarter>.yaml`, ~15 fields from the earnings
release):** OCI revenue (TTM + latest Q), OCI YoY growth, OCI operating margin (estimate),
OCI FCF margin, CapEx (TTM) + CapEx growth, RPO + RPO growth, customer concentration
(nullable), plus overrides for multiples, net debt, shares, and scenario/probability
settings.

These figures are **not typed by hand and not screen-scraped by a brittle parser**. When
Oracle reports, an agent (Claude, in-session) runs a web-search pass: locate the official
Oracle investor-relations press release + earnings call coverage, extract each figure,
**cross-check every number against its source and flag conflicts**, and write the
`inputs/<quarter>.yaml` with a `source:` URL and `confidence`/`estimated` flag per field.
The human glances at the produced YAML and commits it — that commit triggers the on-push
rerun (§9). Rationale: OCI figures live in prose whose wording/layout changes each quarter;
an agent handles that robustly and surfaces disagreements, whereas a fixed regex silently
grabs wrong numbers. This figure-gathering runs in a Claude session, **not** inside GitHub
Actions; the daily price/multiple refresh remains fully automated in Actions.

**Flagged data caveats (uncertainty is explicit):**
- Oracle does **not** report OCI-only EBITDA. The `(1−α)` leg uses a modeled value:
  `EBITDA_OCI = Rev_OCI × oci_margin_input`, clearly labeled as *modeled, not reported*.
  OCI FCF margin is likewise an input.
- `Legacy_EBITDA = total Oracle EBITDA − modeled EBITDA_OCI`, so the two segments sum to
  the whole company by construction.
- Peer-multiple validation of the Neo leg only exists from ~2025 onward (CoreWeave IPO'd
  March 2025). Earlier backtest quarters validate the Legacy leg and the total, not M_Neo.

## 4. Engine (`ocdvm/`)

- `factors.py` — normalizes each factor to [0,1] against editable anchor thresholds in
  config; drops undisclosed factors and renormalizes weights (recording which were active);
  computes **CEI = OCI rev growth ÷ CapEx growth** and its regime (Neo <1, Transition ≈1,
  Hyperscaler >1); outputs **α** as the transparent weighted average of active factors.
  Factors: OCI revenue growth, CapEx growth, CapEx/Revenue, operating margin, FCF margin,
  RPO growth, customer concentration.
- `peers.py` — per-peer EV/Sales → revenue-weighted median = **M_Neo**; quality adjustment
  **Q** = f(revenue quality, diversification, balance sheet, enterprise ecosystem), so the
  effective OCI-Neo multiple is `M_Neo × Q` (Q typically 0.9–1.2).
- `valuation.py` — the SOTP + migration core (formulas in §1). Pure functions:
  known inputs → deterministic EV, equity, target.
- `scenarios.py` — Bear/Base/Bull via deltas on OCI growth, M_Neo, α → probability-weighted
  price, expected return vs. current price, downside / upside.
- `sensitivity.py` — 2D grid (OCI growth × Neo multiple) → price matrix.

## 5. Config (`config/model_config.yaml`)

All model assumptions, versioned in git: factor weights, anchor thresholds, default
M_Software (~12–15×) and M_Cloud, Q sub-scores, scenario deltas & probabilities,
calibration bounds. A rerun with the same inputs + config is fully reproducible.

## 6. Factor mining / history

Every run appends computed factors, CEI, α, multiples, and target price to
`outputs/factors_history.csv`. Over quarters this builds the time series that reveals what
actually drives the migration — the empirical basis for refining α weights, replacing
hand-set assumptions.

## 7. Backtest & calibration

- `backtest/event_study.py` — per earnings date, a −5…+20 trading-day window of daily
  boxes; computes earnings gap, post-earnings drift, and realized trading range.
- `backtest/validation.py` — overlays that quarter's model output on the realized boxes and
  scores: containment (did fair value land inside the eventual box?), direction (did price
  drift toward target?), error % vs. settle price, band hit-rate (did the path stay within
  Bear–Bull?). Appends to `outputs/validation_history.csv`.
- `calibration/tune.py` — **bounded** feedback with hard guardrails so it tracks signal not
  noise:
  - Adjusts assumptions (M_Neo, Q, α anchors) only when error is systematic across multiple
    quarters (EWMA of errors), never a single quarter.
  - Bounded step per quarter (default ±10%, hard caps in config).
  - Every change logged to `calibration_log.csv` with before/after + rationale.
  - Report **always shows uncalibrated target alongside calibrated**; adjustment never
    hidden.
  - Runs only under an explicit `--calibrate` flag; never silent.

**Backtest bootstrap:** to have history now, past quarters are reconstructed — hand-curated
historical OCI figures + Stooq-derived historical peer multiples. Depth = number of curated
quarters, limited on the Neo leg to ~2025+ (see §3 caveat).

## 8. Reporting

`report/` generates clean **titleless PNGs** (SOTP breakdown bar, sensitivity heatmap,
α & CEI gauges, scenario bars, event-study box chart with target line + Bear/Base/Bull band
overlaid) → assembled Markdown → PDF via the pandoc/Chrome pipeline. Per-run output:
`outputs/<quarter>/report.pdf` + CSV tables.

## 9. Automation & publishing (GitHub Actions → Pages)

Public repo (free unlimited Actions + free Pages). No server required.

- **Scheduled workflow** — daily, weekday after US close: refresh SEC totals + Stooq boxes +
  peer prices → recompute multiples, factors, CEI, validation → rebuild dashboard → deploy
  to Pages, committing the refreshed data cache back to the repo (versions history + keeps
  the cron alive past GitHub's 60-day inactivity pause).
- **On-push workflow** — committing a new `inputs/<quarter>.yaml` triggers a full rerun +
  redeploy (the human-in-the-loop quarterly step).
- **Pages dashboard** — Jinja2 → static `index.html` + PNGs: current target price, SOTP
  breakdown, α/CEI, scenario band, sensitivity heatmap, event-study box chart, validation
  scorecard with cumulative accuracy. No server-side runtime.
- **Secrets:** none (SEC/Stooq keyless); SEC User-Agent via env var.
- **Server fallback (only if outgrown):** the identical pipeline runs as a cron job on the
  `gpu_pub` server that rsyncs the same static site — no code changes. Not needed now.

## 10. CLI & layout

```
run.py --inputs inputs/2026Q2.yaml [--calibrate]   # full model run → outputs/2026Q2/
OCDVM/
  ocdvm/        factors.py peers.py valuation.py scenarios.py sensitivity.py
  data/         fetch_oracle.py fetch_peers.py fetch_prices.py earnings_dates.py raw/
  backtest/     event_study.py validation.py
  calibration/  tune.py
  report/       plots.py build_report.py templates/
  config/       model_config.yaml
  inputs/       <quarter>.yaml snapshots
  outputs/      <quarter>/ factors_history.csv validation_history.csv calibration_log.csv
  site/         index.html (generated) + assets
  .github/workflows/  daily.yml  on-push.yml
  tests/
```

## 11. Testing

pytest on: valuation math (known inputs → known EV), α edge cases (all factors vs.
missing-and-renormalized), CEI regime boundaries, sensitivity-grid monotonicity, calibration
bound enforcement (never exceeds hard caps), and validation-metric correctness on a synthetic
price path.

## 12. First run

Agent web-search pass (§3) gathers Oracle's latest reported quarter's OCI figures and current
CRWV/NBIS multiples into `inputs/<quarter>.yaml` with `source:` URLs, then the model produces
a live target price immediately — every estimated assumption (OCI margins, Q sub-scores,
scenario deltas) clearly marked for correction.

## 13. Quarterly update loop

Each time Oracle reports: (1) agent web-search pass writes the new `inputs/<quarter>.yaml`
with sourced figures; (2) human glances + commits; (3) on-push workflow reruns the model and
redeploys the dashboard; (4) the prior quarter's target is validated against the realized
post-earnings daily boxes (§7), extending `validation_history.csv`; (5) optional `--calibrate`
applies bounded feedback. Between reports, the daily Actions job keeps prices, peer multiples,
and the event-study window current.
