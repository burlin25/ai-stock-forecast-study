# Prospective AI stock forecast study

A data science portfolio project by Josh Burlingame evaluating whether an agent-assisted
forecasting workflow can improve daily closing-price predictions over a no-change baseline.

**Status, November 5, 2026:** pre-evaluation. The official-close sources were validated
for all 30 stocks. Numeric practice forecasts were saved after the study's deadline
and are excluded from evaluation. A subsequent integrated input run had four transport
failures. The first evaluation session will be frozen only after a successful on-time
morning rehearsal. **No prospective accuracy or model outperformance is claimed.**

## Research design

- **Universe:** 30 purposively selected US-listed stocks across 11 sectors, frozen before
  evaluation. This is a diverse sample, not a representative random sample.
- **Duration:** 60 consecutive eligible regular trading sessions, with 1,800 planned,
  dependent forecast attempts. Missing sessions remain in the study denominator.
- **Inputs:** the previous 60 completed daily OHLCV sessions and up to three timestamped
  news-feed titles per stock from the previous 72 hours.
- **Forecast timing:** 08:30 America/Detroit, with durable publication strictly before
  09:15 Eastern. Late forecasts are missing, never retrospectively filled.
- **Baseline:** the previous valid regular-session close, equivalent to zero price return.
- **Primary endpoint:** baseline absolute return error minus model absolute return error,
  averaged equally across eligible paired stocks within each day, then equally across days.
  Positive values favor the forecasting arm.
- **Uncertainty:** exploratory moving-block resampling of whole trading-day means, retaining
  shared market exposure and serial dependence. This is a pilot, not 1,800 independent trials.

For previous close `b`, predicted close `p`, and actual close `a`:

```text
Model absolute return error    = |a / b - p / b|
Baseline absolute return error = |a / b - 1|
Paired improvement             = baseline error - model error
```

Secondary measures include per-stock price MAE/RMSE, normalized return errors, directional
accuracy with explicit flat-return handling, coverage and missingness. Pooled dollar errors
across different stock price scales are not the primary endpoint.

## Data and implementation

The standard-library Python workflow archives source responses and immutable input/response
snapshots locally. SQLite events use unique idempotency keys, transactions and triggers that
reject updates/deletions. The Excel report is derived from those records.

Yahoo Finance supplies free daily OHLCV data and bounded RSS titles. Official closing prices
come from Nasdaq's Historical NOCP endpoint for Nasdaq-listed stocks and completed-session
NYSE closing-auction records for NYSE-listed stocks. Prices are corroborated within half a
cent. Missing/stale inputs, unresolved splits and conflicting closes are retained as failures
or pending records, rather than silently imputed. Free endpoints have no uptime guarantee.

The current arm is **agent-assisted**, using existing chat tools. Exact model identity,
generation controls and fresh-context isolation are unavailable. The recurring chat may
contain prior context even though supplied forecast inputs exclude prior scores/outcomes.
This is not a fully reproducible API-model benchmark or a retrospective LLM backtest.

The detailed [protocol](outputs/study/PROTOCOL.md), frozen [prompt](outputs/study/config/prompt.txt),
[universe](outputs/study/config/universe.json), and [calendar](outputs/study/config/calendar.json)
document the pilot. The dated pre-start 1.1 addendum supersedes historical source-blocker
notes preserved in the protocol.

## Repository contents

- `outputs/study/scripts/study.py`: collection, immutable publication, reconciliation and scoring.
- `outputs/study/scripts/official_closes.py`: exchange-source validation and strict date/identity checks.
- `outputs/study/scripts/complete_rehearsal.py`: prevents evaluation activation after a late/incomplete rehearsal.
- `outputs/study/scripts/build_workbook.mjs`: optional Excel report builder using the desktop app's bundled Artifact Tool.
- `outputs/study/tests/`: isolated synthetic tests; no synthetic records enter evaluation data.
- `outputs/study/config/study.example.json`: portable initial configuration template.

Raw news archives, source databases, generated reports, credentials, local scheduling prompts
and machine-specific settings are excluded from Git. This repository is the code/protocol
portfolio, not the complete private audit archive.

## Run tests

Python 3.12 or newer, with an available `America/Detroit` timezone database:

```sh
python3 -m unittest discover -s outputs/study/tests -v
```

The tests use isolated synthetic fixtures and do not require network access. They cover
return scoring, scale invariance, flat returns, exchange holidays/early closes, append-only
storage, duplicate recovery, late publication and official-close parsing.

## Run the collection workflow

Copy `outputs/study/config/study.example.json` to `outputs/study/config/study.json` for a
**separate new study**. Do not replace an existing active study's configuration.

```sh
python3 outputs/study/scripts/study.py status
python3 outputs/study/scripts/study.py collect --target YYYY-MM-DD --mode dry_run
```

Data collection requires HTTPS access. Numeric generation is an agent step governed by the
frozen prompt, followed by `study.py submit`; the Python collector does not call a paid model
API or autonomously produce AI predictions. The report builder additionally requires the
desktop app's bundled runtime and a local runtime configuration.

The local 08:30 weekday heartbeat is configured separately in the desktop app. Cloning this
repository does not create that schedule, and GitHub Actions below runs tests only. There
are no trading or brokerage connections.

## Interpretation

Report coverage and limitations alongside any future accuracy metrics. Preserve missingness,
do not backfill predictions, and label provider/model changes as separate phases. Sixty
sessions can support a pilot assessment, but not broad market or stock-selection claims.
