# Prospective AI closing-price pilot — protocol 1.0

Owner: Josh Burlingame. Portfolio research, no trading or brokerage connection.
Setup date: November 4, 2026 (America/Detroit). Evaluation has not started.

## Current implementation addendum — November 5, 2026 (pre-start 1.1)

This dated addendum supersedes the source-validation blocker described in the original
setup text below. Josh's official-close requirement is retained; the proposed vendor-close
amendment was not accepted and is not applied. All 30 completed-session closes were
successfully fetched from exchange-hosted sources and corroborated against Yahoo daily
Close within half a cent. Raw responses and retrieval timestamps are archived.

Nasdaq-listed stocks: use Nasdaq's company Historical NOCP endpoint
`https://api.nasdaq.com/api/company/SYMBOL/historical-nocp?timeframe=M6&limit=150`,
require an exact dated NOCP table row and a positive finite price. NYSE-listed stocks:
use `https://www.nyse.com/api/auction-charts?symbol=SYMBOL&tradeDate=MM-DD-YYYY&auctionType=closing`,
require the requested symbol, XNYS, exact session date and actual session-final timestamp,
and use the record's `price` field, never a pre-close average indicative clearing price.
Ordinary final time is 16:00 Eastern, early closes use the validated 13:00 time. These
are free public website endpoints, not licensed guaranteed feeds. HTTP/data failures
mean abstention or pending actuals, never quote substitution. Nasdaq's primary definition:
https://www.nasdaq.com/market-activity/stocks/msft/historical-nocp . NYSE page:
https://www.nyse.com/nyse-auction-data .

Yahoo still supplies the prior 60 daily OHLCV rows and bounded news titles. The baseline
uses the official native previous-session close, corroborated with Yahoo within $0.005.
Targets use the official exchange source, also corroborated. Disagreements withhold
forecast/scoring and preserve an exception record. Native prices are not dividend-added;
current split-unit conflicts force abstention/review. Small Yahoo binary float deviations
are not corporate-action adjustments. No evaluation source was changed mid-study.

A November 5 numeric practice batch contains 30 predictions and no realized outcomes.
It was generated after 09:15 and is excluded from evaluation. The existing 08:30 weekday
heartbeat will resume SETUP ONLY to run a fresh on-time morning rehearsal automatically.
Evaluation remains inactive until `scripts/complete_rehearsal.py` verifies 30 saved numeric
attempts on 30 official-baseline inputs between 08:30 and 09:15 Eastern and under 45 minutes.
It then freezes the next eligible session strictly AFTER that rehearsal as session 1.
If the November 6 rehearsal succeeds, the earliest start is Monday, November 9, 2026.
The original 60-session horizon and user decision are retained; no past session is filled.

Current workspace: `/Users/joshburlingame/Documents/ChatGPT/Stock Study/outputs/study`.
The original workspace was copied and preserved. SQLite integrity passed. The old
protocol is archived at data/protocols/protocol-v1.0-original.md. The original setup
sections below are historical where they conflict with this dated addendum.

## Question and design

Does one frozen agent-assisted forecasting workflow improve next-session absolute
price-return error over the previous-close baseline? This is a prospective 60-session
pilot, not a historical LLM backtest or a claim that newer models outperform a previous
ChatGPT study. The 30 stocks are a diverse purposive sample of US-listed large liquid
equities across all 11 sectors, not a representative random sample. Liquidity is a
practical selection criterion, verified with positive volume in all 60 input sessions,
not a formally optimized liquidity screen. The specified universe is frozen only after
all symbols pass access, identity, USD, exchange and 60-session completeness checks.
Sector labels are broad GICS-style research classifications, not licensed GICS data.
No replacements were proposed. No substitutions after start without an explicit,
dated protocol amendment. Delistings and failures remain in the missingness denominator.

Start: the next eligible regular US equity trading session strictly after setup and a
successful end-to-end dry run. Start remains unset until the readiness gates pass.
Then freeze 60 consecutive sessions, including sessions with missing forecasts.
There are 1,800 planned forecasts with shared market exposure and serial dependence,
not 1,800 independent observations. The pilot may be extended only by a preregistered
amendment before seeing the extension's outcomes.

## Calendar and timing

The weekday heartbeat is requested for 08:30 America/Detroit. The script uses a
2026–2027 exchange calendar transcribed from NYSE's official holiday/hours page,
verified November 4, 2026: https://www.nyse.com/trade/hours-calendars . The dated
calendar snapshot is in config/calendar.json. Thanksgiving and Christmas closures,
January 1 and MLK Day 2027 matter for this pilot. November 27 and December 24, 2026
close at 13:00 Eastern. Ordinary sessions close at 16:00. Federal bank holidays
are not automatically exchange holidays. Unexpected exchange closures require a
dated calendar amendment based on an exchange announcement, retaining the old schedule.
The code refuses dates outside the validated years. Calendar/halt notices must be
checked before activation and weekly. An affected unscheduled closure must not be
silently scored as an ordinary session.

At each heartbeat, first mark previously elapsed unfilled sessions missing, reconcile
prior published forecasts to completed regular-session daily closes, then collect
today's inputs. The information cutoff is the actual collection start time in UTC.
Only prior completed daily bars are retained. Intraday bars, after-hours quotes,
regularMarketPrice and current-session news published after the cutoff are excluded.
RSS retrieval can finish after the cutoff, but publication timestamps must be at or
before it. Save the complete 30-symbol forecast batch strictly before 09:15 Eastern.
The publication time is the durable database commit time, never an edited timestamp.
If collection or generation runs late, mark missing; never backfill. Missing sessions
are discovered at the next successful run, with discovery timestamp distinguished
from the missed deadline. Pending future sessions and pending actuals remain distinct.

## Data inputs, sources and archives

Price endpoint: https://query1.finance.yahoo.com/v8/finance/chart/SYMBOL?range=1y&interval=1d&events=div%2Csplits&includeAdjustedClose=true

This is a free, unofficial Yahoo endpoint, requiring no paid subscription/key in the
live test. No uptime promise or official exchange certification is implied. Daily
OHLCV Close is used, never a quote field. Yahoo reports regular-session historical
daily closes, but independent verification as the exchange's official auction close
has not been established. This is a readiness issue under the requested official-close
requirement; do not relabel it as certified or activate evaluation until resolved.
Stooq failed the live probe (verification HTML) and is not an approved fallback.
Do not silently change sources. A new source requires validation and amendment.

Use exactly the preceding 60 valid exchange sessions for each symbol, ordered oldest
to newest, with open/high/low/close in USD and share volume. Positive finite values,
valid OHLC bounds, expected dates, symbol, exchange and USD currency are checked.
Any gap or stale latest session means abstain. Archive raw response bytes, URL,
HTTP status/headers, retrieval start/end timestamps and SHA-256. A 15-minute same-run
cache limits duplicate downloads. Sequential requests are spaced by at least 0.6s,
with 12-second timeouts and at most three attempts with exponential backoff.
Failures and attempts remain in the log. Do not substitute a cached stale session.

News: one exact Yahoo Finance RSS query per symbol, `s=SYMBOL&region=US&lang=en-US` at
https://feeds.finance.yahoo.com/rss/2.0/headline . This bounded feed retrieval is the
news search protocol. No general web search, article expansion or subjective selection.
Parse the source pubDate; retain only the last 72 hours through the cutoff, deduplicate
URLs, sort descending publication timestamp then URL, and supply at most three titles
per stock, each truncated to 300 characters. No article bodies/descriptions are supplied.
Archive the query, raw feed, excluded items and exact title content supplied with source,
URL, publication and retrieval timestamps. Unparseable or post-cutoff items are excluded.
A valid empty feed window means zero news titles; a failed feed fetch means input failure.
Feed coverage and company relevance are imperfect and not independently adjudicated.
Raw archives may contain excluded future items: ONLY data/inputs/*.json is model input.
Raw news stays local; do not redistribute third-party article text in a public portfolio.

## Corporate actions and close reconciliation

Yahoo daily Close is conventionally split-adjusted and not dividend-adjusted. Do not
use Adj Close. Store the original baseline close as supplied at forecast time; compute
price returns, not total shareholder returns. Cash ex-dividend price drops count as
price movements; log dividend metadata and do not add distributions to actual prices.
On a detected split at or after the target date, reconciliation flags the record and
withholds scoring until price units are explicitly reconciled in an appended correction
or amendment. It never overwrites a frozen forecast or silently removes the failure.
Unresolved splits, stale data or unavailable closes remain pending/flagged. Source
revisions after initial reconciliation require appended correction records, retaining
the original; the report currently uses original actuals until a reviewed correction
resolver is implemented. Do not append purported corrections and assume they are applied.
Same-day splits may not be announced in the feed before cutoff. That detection limitation
must be disclosed. Cross-check action notices before activation and each affected run.

## Forecast arm and audit trail

Only agent-assisted-v1 is configured. No API credentials were found in the environment
(only existence was checked); no paid model API is required. The frozen prompt is
config/prompt.txt, hashed into each snapshot/forecast. Every forecast uses only the
sanitized structured input (60 OHLCV rows and bounded titles). Exact exposed model
identity and settings must be recorded; when unavailable, use the literal "unavailable".
The present interface does not expose a reliably pinned model version or sampling
controls. This prevents calling the study a reproducible API/model experiment.
Provider/model changes begin a separately labeled phase, never pooled as a fixed model.
If a future run exposes a different identity, stop prediction and append an amendment
before starting a new phase. Default-model drift may be undetectable and is a limitation.

Fresh isolated generation is not available in this recurring chat without delegation.
The heartbeat preserves conversation. The frozen prompt explicitly excludes prior
outcomes, and sanitized input files contain none, but cognitive context contamination
cannot be ruled out. Reconciliation before forecasting further limits isolation.
Do not describe this as blinded or a clean causal comparison of model versions.
No prior scores, historical performance summaries or raw rejected news enter the
supplied forecast input. Save exact response JSON and real generation/save timestamps.
Every batch must include exactly one published prediction or reasoned abstention for
all 30 symbols. Input failures force abstention. All-or-nothing publication avoids
partially duplicated sessions. A conflicting second batch is refused, not overwritten.

## Outcomes and scoring

For baseline b, predicted close p and actual regular close a:

- Predicted return = p/b − 1; realized price return = a/b − 1.
- Model absolute return error = |a/b − p/b|.
- Baseline absolute return error = |a/b − 1| (zero-return forecast).
- Paired improvement = baseline error − model error; positive favors the model.

Primary endpoint: the mean paired improvement across eligible paired stocks within
each trading session, then the unweighted mean across sessions with at least one
eligible pair. Report scored days/60, scored pairs/1,800 and daily coverage alongside
the endpoint. A day with no pair has unavailable error, not zero. Partial-day coverage
can cause selection bias. Also report a sensitivity analysis restricted to fully
scored 30-stock sessions. Missing forecasts and unresolved actuals are never silently
treated as correct or imputed with the baseline.

Secondary: actual-minus-predicted residuals in dollars, per-stock dollar MAE and RMSE,
absolute return errors (normalized to the frozen previous close), paired baseline
return MAE and directional accuracy. Direction is down/flat/up, with flat defined as
absolute return ≤1e-12 to accommodate floating-point error. A direction is correct
only when the three-way labels match. Thus the no-change baseline is directionally
correct only on flat realized returns. Do not drop zero-return cases or credit a
flat prediction as up/down. No pooled dollar-error headline across price scales.
Charts are created when observations exist, not populated with fabricated zero results.

Uncertainty: deterministic-seed 10,000-replicate circular moving-block bootstrap of
whole trading-day means, five consecutive days per block. All eligible stocks of a
day stay together implicitly through its daily mean. Exploratory 95% percentile
interval only after at least 20 scored days. At final reporting also inspect block
length sensitivity (1 and 10 days), serial dependence and missingness. Consecutive
days with no pairs must be disclosed; do not imply that deleting gaps preserves
original temporal spacing. The pilot cannot establish broad stock-selection or market
generalization. No automatic significance claim or independence-based p-value.

## Records, recovery and reporting

data/events.sqlite is authoritative. A unique idempotency key and transaction protect
each batch. SQL triggers reject UPDATE and DELETE. Preserve the database, its WAL
and raw archives; use SQLite backup API before public portfolio packaging. Immutable
snapshots/inputs/responses are written with atomic hard links and conflict checks.
data/events.jsonl and reports/report.json are reproducible exports. Excel is a
regenerated readable report, never the sole record. Corrections/amendments are new
events with original IDs, reason, author, time and old/new values; no erasure.

The daily heartbeat is not a guaranteed job queue. Local computer must remain on,
app running, workspace available, network access permitted and subscription capacity
available before 08:30 through 09:15. No API purchase is needed. A delayed wakeup
cannot make a retrospective forecast. Routine run outputs should be quiet; weekly
coverage/performance summaries and actionable failures/final results are meaningful
notifications, subject to the platform's notification capabilities.

After session 60, make no more predictions. Continue only final close reconciliation,
report and data-quality review. Once all published forecasts have actuals or documented
unresolvable outcomes, append a completion event and pause this heartbeat via the
automation tool using its saved ID. If self-pause is unavailable, notify Josh that
manual pause in Scheduled is required; do not claim it stopped.

## Readiness gates and amendments

Require all 30 symbol checks, full live input collection, actual agent dry-run
responses, timestamp/idempotency tests, scoring/missed-run tests, workbook render
inspection, a measured completion duration within the 45-minute window, official-close
validation or explicit acceptance of a vendor-close amendment, and an automation readback.
An afternoon dry run is not proof of morning source availability. Until those gates
are met, the heartbeat may monitor setup but must not start evaluation or set a start
date. Changes to this protocol/prompt/source/model or sample after freeze require
dated append-only amendment records, separately labeled phases when appropriate.
