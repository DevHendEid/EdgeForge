# EdgeForge Master Roadmap

Status: ACTIVE
Owner: EdgeForge project
Primary branch: `main`
Current project phase: **Phase 3 — CME-specific validation**

## 1. Mission

EdgeForge is not a single trading bot and not a generic backtesting toy. It is a **quantitative research and strategy-development laboratory** whose job is to discover, test, reject, validate, deploy, and monitor strategies that originate from plausible market inefficiencies.

The target workflow is:

**Discover Inefficiency → Build Hypothesis → Acquire Data → Build Prototype → Backtest → Robustness Testing → Out-of-Sample Validation → Compare Versions → Paper Trade → Deploy → Monitor → Detect Decay → Research Again**

The goal is not to produce a beautiful historical equity curve. The goal is to determine whether an apparent edge is economically plausible, statistically credible, reproducible, robust to perturbation, executable after costs, and persistent enough to justify paper or live deployment.

## 2. Non-negotiable principles

1. **Evidence first.** Every strategy starts from a phenomenon, anomaly, market-structure mechanism, behavioral mechanism, informational delay, liquidity effect, or structural rationale.
2. **Hypothesis before optimization.** Define the expected mechanism, event, horizon, instruments, variables, and failure conditions before tuning parameters.
3. **Raw-data provenance.** Every external corpus must have source, license/entitlement note, retrieval time, checksum, schema, symbol mapping, date range, and normalizer version.
4. **Canonical data model.** Strategy code must consume EdgeForge canonical objects, never depend directly on a vendor schema.
5. **L2 is not L3.** Never infer queue priority from MBP/L2 when order-level evidence is unavailable.
6. **Deterministic replay.** The same data, code, and configuration must reproduce the same book state, trades, and result hashes.
7. **Chronological research discipline.** Development, validation, and final holdout must remain temporally separated.
8. **Sealed holdout.** The final holdout must not be repeatedly inspected or used for optimization.
9. **Realistic execution.** Fees, commissions, slippage, latency, order type, queue assumptions, session rules, and liquidity constraints are part of the strategy definition.
10. **Try to break the strategy.** Robustness work is adversarial: parameter perturbation, cost stress, regime tests, cross-period tests, cross-market tests, Monte Carlo, bootstrap, and multiple-testing controls.
11. **Research history is immutable.** Every experiment must record code version, data version, configuration, outputs, and verdict.
12. **Zero-cost-first data policy.** Use legal public datasets, official samples, and user-entitled data first. Paid CME multi-year MBO is not required to continue building the platform.
13. **No silent promotion.** A strategy can move to the next lifecycle state only after explicit gates pass.
14. **No deployment from one backtest.** A strong in-sample result is evidence for more testing, not evidence for capital deployment.

## 3. End-state platform

EdgeForge should ultimately contain these systems:

- **Research Registry** — anomaly, sources, papers, rationale, hypothesis, required data, status.
- **Data Registry** — provider/source metadata, legal status, coverage, schema, hashes, manifests.
- **Acquisition Layer** — public/legal downloads, provider APIs, resumable jobs, integrity checks.
- **Canonical Data Layer** — vendor adapters into one stable market-event model.
- **Book / Replay Engine** — L3 order-by-order and L2 price-level deterministic reconstruction.
- **Feature Layer** — order flow, spread, imbalance, microprice, queue, volatility, session/event context.
- **Strategy Specification Layer** — declarative strategy rules independent of vendor format.
- **Backtesting Engine** — deterministic signal and trade replay.
- **Execution Simulator** — realistic fills, slippage, fees, latency, queue assumptions, partial fills.
- **Experiment System** — immutable experiment IDs, configs, code/data fingerprints, artifacts.
- **Validation Engine** — OOS, walk-forward, regime, cross-market, cost stress, sensitivity tests.
- **Statistical Analysis** — bootstrap, Monte Carlo, confidence intervals, multiple-testing controls, PBO/DSR when applicable.
- **Strategy Registry** — versioned strategies with evidence and deployment status.
- **Monitoring System** — realized PnL, drawdown, slippage, fills, latency, edge-decay indicators.
- **Reporting Dashboard** — research verdicts, comparisons, plots, diagnostics, provenance.

## 4. Strategy lifecycle

Every strategy must have exactly one lifecycle state:

`IDEA → RESEARCH → HYPOTHESIS_REGISTERED → PROTOTYPE → BACKTESTED → VALIDATION → PAPER → LIMITED_LIVE → PRODUCTION → MONITORING → REVIEW → IMPROVE | REDUCE | PAUSE | RETIRE`

### Required strategy record

Each strategy receives a stable ID, for example `ORB_NQ_v1`, and stores:

- phenomenon / anomaly
- economic or market-microstructure rationale
- falsifiable hypothesis
- required data and minimum evidence level
- instruments and sessions
- entry / exit / risk rules
- all tunable parameters and allowed search ranges
- development period
- validation period
- sealed holdout definition
- cost/slippage assumptions
- experiment IDs
- known limitations
- final research verdict

### Research verdict fields

The system should eventually report more than one metric:

- Edge evidence: `WEAK / MODERATE / STRONG`
- Statistical credibility: `FAIL / WARNING / PASS`
- OOS evidence: `FAIL / UNKNOWN / PASS`
- Walk-forward stability: `FAIL / WARNING / PASS`
- Cost resilience: `FAIL / WARNING / PASS`
- Parameter stability: `FAIL / WARNING / PASS`
- Regime robustness: `FAIL / WARNING / PASS`
- Cross-market evidence: `FAIL / UNKNOWN / PASS`
- Execution evidence: `FAIL / UNKNOWN / PASS`
- Overfit risk: `LOW / MEDIUM / HIGH`
- Deployment status: `REJECTED / RESEARCH_ONLY / PAPER_ONLY / LIMITED_LIVE / PRODUCTION_ELIGIBLE`

No single metric, including Sharpe ratio or Profit Factor, can override failed evidence gates.

## 5. Research methodology

### 5.1 Discovery

Potential sources include:

- academic finance and market-microstructure papers
- SSRN / journal research
- known historical anomalies
- exchange mechanics and market design
- liquidity and execution effects
- order-flow behavior
- information-release effects
- behavioral effects such as underreaction, overreaction, herding
- structural effects tied to session boundaries, auctions, rolls, rebalancing, or participant constraints

The research registry must preserve every source and must distinguish **source evidence** from **our hypothesis**.

### 5.2 Hypothesis registration

Before strategy optimization, write:

- mechanism
- event definition
- expected direction of effect
- time horizon
- instruments
- market regime assumptions
- required data granularity
- dependent variable
- explanatory variables
- success criterion
- failure criterion
- plausible confounders

A hypothesis should be falsifiable. If the expected effect cannot be contradicted by data, it is not ready for research.

### 5.3 Prototype

The first implementation should be intentionally simple. Avoid large parameter searches during initial proof-of-concept work.

A prototype can answer only:

> Does the proposed effect appear to exist strongly enough to justify deeper validation?

It cannot establish production readiness.

### 5.4 Development and validation split

Use chronological partitions. Never randomly shuffle time-series observations when temporal leakage can occur.

Recommended logical partitions:

- `DEV` — hypothesis implementation and limited tuning
- `VALIDATION` — model selection and robustness confirmation
- `SEALED_HOLDOUT` — final one-shot evidence

For labels or features whose information windows overlap, add purging/embargo logic before claiming independent folds.

### 5.5 Walk-forward

Walk-forward analysis is required for strategies whose parameters or market behavior may change over time. Parameter selection must use only history available before each test window.

Do not optimize on future observations and then replay the past with the resulting parameter set.

### 5.6 Multiple testing and selection bias

The project must track the number of strategy variants, parameter searches, feature combinations, and hypotheses attempted.

Why: a winning backtest selected from many trials cannot be judged as if it were the only trial.

Planned controls:

- trial-count logging
- Deflated Sharpe Ratio where appropriate
- Probability of Backtest Overfitting / CSCV for sufficiently structured search experiments
- stricter significance thresholds when many hypotheses are tested
- explicit distinction between pre-registered and exploratory research

### 5.7 Robustness battery

A strategy must be attacked with:

- parameter sensitivity surfaces, not just one optimum
- neighboring time-window definitions
- alternative entry/exit timing
- commission stress
- 1x / 2x / 3x plausible slippage stress
- dynamic slippage where possible
- latency assumptions
- partial-fill assumptions
- liquidity constraints
- high/low volatility regimes
- trend/range regimes
- event/non-event sessions
- cross-year analysis
- cross-contract analysis
- cross-market or related-market analysis when the mechanism should generalize
- bootstrap confidence intervals
- Monte Carlo path analysis
- trade-order permutations where meaningful
- tail-loss analysis

### 5.8 Execution reality

Execution evidence must match the data resolution.

- OHLCV can support coarse strategy screening.
- trades/BBO can support better timing and aggressor-side studies.
- MBP/L2 supports price-level depth research but not true order queue priority.
- MBO/L3 supports order-by-order book events and queue-position research.

A strategy requiring queue priority cannot receive an execution `PASS` from OHLCV or MBP alone.

## 6. External research findings integrated into this roadmap

The following practices are adopted from established quantitative-research literature and production backtesting systems:

1. **Backtest overfitting must be measured, not merely discussed.** Bailey, Borwein, López de Prado, and Zhu proposed Probability of Backtest Overfitting (PBO) using combinatorially symmetric cross-validation (CSCV) for investment simulations.
   - Reference: https://papers.ssrn.com/sol3/Papers.cfm?abstract_id=2326253

2. **Selection bias inflates performance statistics.** Bailey and López de Prado's Deflated Sharpe Ratio explicitly adjusts for selection bias from multiple trials and non-normal returns.
   - Reference: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551

3. **Multiple testing requires a higher evidentiary bar.** Harvey, Liu, and Zhu show that conventional significance thresholds become unreliable when researchers test many candidate factors.
   - Reference: https://academic.oup.com/rfs/article-abstract/29/1/5/1843824

4. **Walk-forward optimization should use trailing historical windows and apply selected parameters only to later data.** It is useful because parameter quality can change across market regimes, but frequent re-optimization can itself increase overfitting risk.
   - Reference: https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/walk-forward-optimization

5. **Execution assumptions must be explicit.** Mature backtesting engines expose separate fill, fee, slippage, margin, and execution models rather than hiding execution inside the signal rule.
   - Reference: https://www.quantconnect.com/docs/v1/algorithm-reference/trading-and-orders

6. **MBO and MBP evidence must remain distinct.** Databento documents MBO as order-level events keyed by `order_id`, including add/cancel/modify/trade/fill/clear events, while MBP represents aggregated price levels.
   - References:
     - https://databento.com/docs/schemas-and-data-formats/mbo
     - https://databento.com/docs/schemas-and-data-formats/mbp-1

7. **CME-specific book validation should follow exchange semantics.** CME's MDP 3.0 MBO certification material validates dissemination of individual orders and quotes at price levels; EdgeForge should treat exchange behavior as the primary semantic authority for CME replay rules.
   - Reference: https://www.cmegroup.com/tools-information/webhelp/autocert-mdp3-with-mbo/Content/GettingStarted.html

## 7. Data policy and zero-cost-first strategy

### Data classes

- `OFFICIAL_PUBLIC`
- `PUBLIC_WITH_CLEAR_LICENSE`
- `PUBLIC_LICENSE_UNCLEAR`
- `USER_ENTITLED`
- `COMMERCIAL_REFERENCE_ONLY`
- `DERIVED_ONLY`
- `QUARANTINED`

### Required manifest fields

Every acquired corpus should record:

- dataset key
- source/provider
- source URL
- license / entitlement note
- retrieval timestamp
- SHA-256
- file size
- raw format
- schema
- instrument/symbol
- venue
- start/end timestamps
- event/row count
- sequence/gap diagnostics
- normalizer version
- canonical output hash

### Current free-data strategy

Do not block the project on multi-year paid CME MBO.

Use:

- official CME/Databento public samples for CME parser/replay validation
- LOBSTER and Nasdaq ITCH for L3 architecture and order-event validation
- FI-2010 for L2 feature/ML benchmarking
- Binance / OKX / Hyperliquid / Coinbase / Bybit where legally accessible for large-scale depth pipelines
- NQ OHLCV for strategy screening and long-horizon robustness
- VIX, FRED, and official economic calendars for regime/event context

Only require long-history true CME MBO when a strategy's final claim depends on queue-level execution or CME-specific microstructure that cannot be validated from free samples.

## 8. Project roadmap

### Phase 0 — Foundation / architecture — COMPLETE

Delivered:

- package structure
- canonical models
- provenance foundation
- CLI/testing/security baseline
- documented architecture

Exit gate: project structure stable enough for data adapters and replay engines.

### Phase 1 — L3/MBO engine + LOBSTER/ITCH — COMPLETE

Delivered:

- canonical `MarketEvent`
- deterministic L3 lifecycle
- add / modify / cancel / execute / delete / clear
- queue inspection
- state hashes
- LOBSTER adapter
- decoded Nasdaq ITCH lifecycle adapter
- sequence telemetry

Exit gate: deterministic order-by-order replay works on non-CME sources and fixtures.

### Phase 2 — L2/depth + free-scale pipeline — COMPLETE

Delivered:

- L2 snapshot/delta book
- Binance / OKX / Hyperliquid / Coinbase adapters
- gap/duplicate/regression telemetry
- imbalance and microprice features
- JSONL and optional Parquet normalization
- acquisition/provenance baseline

Exit gate: price-level replay and free-source scale pipeline function independently of L3.

### Data / research expansion — COMPLETE ENOUGH TO PROCEED

Delivered:

- expanded dataset registry
- GitHub research registry
- 31 external research repositories registered as submodules
- repository inventory
- official Databento CME sample intake
- Git LFS rules for scoped binary samples/commercial intake

This work remains open-ended, but it is no longer a blocker for Phase 3.

### Phase 3 — CME-specific validation — CURRENT PHASE

Goal: prove EdgeForge can ingest and reconstruct CME semantics correctly before using CME-specific microstructure claims.

#### Phase 3A — Actual Data Inventory

Build an automated inventory over all locally available/publicly accessible corpora.

For every file:

- path
- source repo/dataset
- format
- compressed/uncompressed size
- SHA-256
- symbol/instrument where detectable
- date range
- resolution/schema
- raw vs derived
- L1/L2/L3/OHLCV classification
- redistribution/license status
- admissible EdgeForge uses

Deliverables:

- `data/manifests/` normalized manifests
- machine-readable inventory
- human-readable inventory report
- quarantine list for uncertain provenance

Exit gate: no dataset is used in research without known provenance and evidence level.

#### Phase 3B — CME sample ingestion

Implement validated ingestion path from official CME/Databento sample material into canonical events.

Required checks:

- timestamp semantics
- instrument mapping
- action mapping
- side mapping
- order IDs
- sequence handling
- book-clear semantics
- status/session handling
- duplicate/gap detection

Exit gate: sample converts deterministically into canonical representation with reproducible hashes.

#### Phase 3C — Differential book validation

Compare EdgeForge reconstruction against independent implementations/references already registered in the repository, especially:

- `mdp3-book`
- `cme.mdp`
- `MDP-Order-Book-Generator`
- Databento official decoder behavior
- CME MDP 3.0 documentation

Compare:

- event counts
- best bid/ask
- depth state
- queue order where evidence permits
- state hashes at checkpoints
- trades/fills
- reset/clear events

Exit gate: unexplained divergence count is zero on the official validation corpus.

#### Phase 3D — CME invariant harness

Add invariant/property tests for:

- impossible negative size
- unknown cancel/modify
- crossed/locked-book cases according to feed semantics
- sequence regression
- session/status transitions
- book clear/reset
- modify priority behavior
- queue-ahead accounting
- deterministic replay

Exit gate: all known adversarial fixtures fail closed and all official fixtures pass.

#### Phase 3E — Performance profiling

Measure:

- events/sec
- memory
- replay determinism
- storage throughput
- feature throughput

Only after profiling may Rust be proposed for a proven hot path.

Exit gate: documented performance baseline and bottleneck evidence.

### Phase 4 — Research Registry + Experiment System

Goal: turn ad-hoc research into reproducible registered experiments.

Build:

- `HypothesisSpec`
- `StrategySpec`
- `ExperimentSpec`
- experiment IDs
- config snapshotting
- code commit fingerprint
- dataset-manifest fingerprints
- artifact registry
- trial-count logging
- immutable result summaries

Exit gate: any result can be reproduced from Git commit + manifests + experiment config.

### Phase 5 — Backtesting + execution realism

Build a unified strategy runner separated from execution assumptions.

Required execution components:

- commission model
- fee model
- fixed/dynamic slippage
- latency model
- market/limit/stop semantics
- partial fills
- session boundaries
- position/risk constraints
- L2 execution approximation
- optional L3 queue model where data supports it

Exit gate: signal generation and execution simulation can be varied independently.

### Phase 6 — Validation firewall

Build reusable validation workflows:

- chronological dev/validation/holdout
- sealed holdout access control
- walk-forward
- parameter sensitivity surfaces
- cost stress
- latency stress
- regime tests
- cross-period tests
- cross-market tests
- bootstrap
- Monte Carlo
- PBO/CSCV for structured searches
- DSR / multiple-testing adjustments when applicable

Exit gate: strategy cannot receive a promotion verdict without completing its required validation matrix.

### Phase 7 — First reference strategy: NQ ORB + order-flow filter

Use the previously studied NQ ORB example as a **platform integration specimen**, not as assumed alpha.

Research target:

- opening range phenomenon
- liquidity / information absorption rationale
- long-only baseline first
- explicit OR window
- close-above-range condition
- order-flow / volume-delta filter where evidence supports it
- stop/target/session exit

Required experiments:

- reproduce baseline rules from raw/approved data
- year-by-year performance
- parameter neighborhoods
- alternate OR windows
- delta-threshold sensitivity
- RR sensitivity
- transaction-cost stress
- volatility regimes
- walk-forward
- bootstrap
- Monte Carlo
- sealed holdout
- ES/YM/RTY mechanism comparison where data permits

Success criterion: not profitability alone; the goal is to prove the full EdgeForge research pipeline can accept, challenge, and issue a defensible verdict on one strategy.

### Phase 8 — Strategy factory

After the reference strategy proves the workflow, add multiple hypothesis families:

- information underreaction/overreaction
- liquidity imbalance
- order-flow persistence/reversal
- opening/closing auction effects
- volatility expansion/contraction
- structural session effects
- futures roll / rebalancing effects
- event-driven effects
- queue/microstructure effects where L3 data is available

Each family must use the same registry, experiment, and validation contracts.

### Phase 9 — Paper trading

Requirements before paper promotion:

- validated data path
- stable strategy version
- cost-resilient OOS evidence
- execution model documented
- operational risk controls
- replay/live feature parity tests

Paper trading must record:

- expected vs actual fills
- slippage
- signal latency
- order latency
- strategy state
- data gaps
- live-vs-backtest divergences

### Phase 10 — Limited live

Capital deployment is outside the research proof itself and requires separate risk governance.

Minimum technical requirements:

- hard risk limits
- kill switch
- max position/exposure
- daily loss limit
- connectivity/data health gates
- execution reconciliation
- immutable audit logs
- deployment version pinning

Start with limited size only after paper evidence is satisfactory.

### Phase 11 — Monitoring / edge decay

Monitor realized behavior against research distributions:

- PnL distribution
- drawdown
- win/loss distribution
- expectancy
- slippage
- fill quality
- latency
- turnover
- volatility/regime mix
- feature distributions
- signal frequency

Trigger a `REVIEW` when live behavior materially departs from expected research ranges.

Do not automatically re-optimize a degrading strategy; first diagnose whether the cause is execution, market regime, data quality, implementation drift, or genuine edge decay.

### Phase 12 — Reporting dashboard and research operations

Build views for:

- active hypotheses
- experiment lineage
- dataset provenance
- strategy comparison
- validation matrix
- deployment states
- monitoring alerts
- edge-decay reviews
- retired strategies and reasons

## 9. Immediate work queue

The next work should occur in this order:

1. **Phase 3A: automated actual-data inventory.**
2. Normalize manifests for the files already present in the external research workspace.
3. Build admissibility classifications: raw/derived, L1/L2/L3/OHLCV, legal/provenance status.
4. Implement official CME/Databento sample ingestion.
5. Add CME-specific canonical mapping tests.
6. Build differential replay harness against independent implementations.
7. Add CME invariant/property tests.
8. Profile replay performance.
9. Only then start Phase 4 experiment/strategy registry expansion.
10. Use NQ ORB as the first complete end-to-end strategy specimen after the validation firewall exists.

## 10. GitHub workflow for every contributor or agent

Anyone working on EdgeForge should follow this sequence:

1. Read this roadmap.
2. Read `docs/ARCHITECTURE.md` and `docs/RESEARCH_PROTOCOL.md`.
3. Check the current phase and choose work only from that phase unless fixing a regression.
4. Do not change scientific or data semantics silently.
5. Add or update tests with every behavior change.
6. Preserve provenance and source references.
7. Do not touch sealed holdout data during development.
8. Do not introduce paid-data assumptions as mandatory dependencies.
9. Record important decisions in documentation or an ADR/decision log.
10. Before marking a task complete, provide evidence: tests, manifests, hashes, comparison reports, or benchmark outputs.

### Definition of Done for a technical task

A task is not complete merely because code runs. It should have, where applicable:

- code
- tests
- documentation
- provenance impact assessed
- deterministic output where required
- failure behavior tested
- no new data leakage
- no silent semantic change
- reproducibility instructions

## 11. Things we intentionally do not do

- optimize dozens of indicators until one looks profitable
- repeatedly inspect holdout results
- infer L3 queue behavior from L2
- call a strategy validated because of one strong Sharpe/Profit Factor
- ignore commissions/slippage/latency
- hide failed experiments
- silently repair gaps in raw data
- treat public GitHub repos as automatic redistribution permission
- require expensive data before the platform has earned the need for it
- move to Rust simply because it is faster in theory

## 12. Current status snapshot

As of the current `main` state:

- Phase 0 — complete
- Phase 1 — complete
- Phase 2 — complete
- external research registry — established
- 31 external research repositories — registered as submodules
- repository inventory — present
- official Databento sample — present through Git LFS
- CME-specific validation — **current active phase**
- multi-year paid CME MBO — not available and not a blocker

## 13. North-star outcome

EdgeForge succeeds when a researcher can take a new market-inefficiency idea and move through the entire lifecycle without losing provenance, contaminating holdouts, confusing data granularity, or hiding failed experiments.

The final product should function as a **research factory for market edges**, where the default outcome of weak evidence is rejection, not promotion.

The strongest strategy is not the one with the prettiest backtest. It is the one whose economic rationale, data provenance, statistical evidence, execution assumptions, robustness, out-of-sample behavior, and live monitoring all survive independent scrutiny.
