# EdgeForge GitHub Research Registry

Purpose: preserve every useful GitHub project discovered during market-data, CME/Databento, NQ, order-book and validation research so future EdgeForge work can reuse code patterns, test ideas, debugging approaches, data-access methods and research controls without repeating discovery.

This registry is intentionally broader than a dataset list. Some repositories contain data samples, some contain acquisition/cleaning code, some contain MBO/LOB reconstruction logic, and some are methodology or infrastructure references. `RAW PRESENT` means public repository payloads appear to contain market-data files. `RAW EXTERNAL` means the code expects local/provider data but does not ship it. `REFERENCE ONLY` means use the ideas/code patterns, not the data payload.

## Operating rules

- Never assume a public GitHub repository grants redistribution rights for third-party market data.
- Keep CME/Databento raw commercial payloads outside ordinary Git unless the applicable license explicitly permits repository storage/redistribution.
- Preserve provider/source, pull date, schema, symbology, SHA-256 and exact time window for every acquired corpus.
- Never relabel MBP/L2 as MBO/L3.
- Prefer official samples and provider APIs for final validation; use third-party repos as engineering references, fixtures and research inspiration.
- If an external repository conflicts with EdgeForge invariants, EdgeForge wins: fail closed, preserve temporal provenance, no silent gap repair, no holdout leakage.

---

# A. Highest-priority CME / Databento references

## 1. deeleeramone/openbb-cme-databento
URL: https://github.com/deeleeramone/openbb-cme-databento

**What it offers**
- OpenBB + Databento CME integration.
- CME Globex definitions, continuous futures OHLCV, live trades and SQLite-backed serving.
- Useful symbol/metadata/database patterns for large CME universes.

**Data state:** RAW EXTERNAL — requires Databento access/API key.

**EdgeForge use**
- Borrow ideas for continuous-contract metadata, instrument definitions and term structures.
- Compare database schema choices against EdgeForge DuckDB/Parquet model.
- Useful reference for serving historical data to dashboards/APIs.

**Watch-outs**
- Continuous futures are research convenience, not contract-identity ground truth for queue-sensitive execution.
- Do not copy provider data into Git from generated SQLite files.

Priority: **A**

## 2. sevakkhan26/data_scraping_cme_databento
URL: https://github.com/sevakkhan26/data_scraping_cme_databento

**What it offers**
- Databento CME historical downloader.
- BBO cleaning, standardization, QA and reporting.
- Explicit runtime raw-data directory and environment configuration.
- Micro Bitcoin (MBT) BBO example pipeline.

**Data state:** RAW EXTERNAL — repository docs state downloaded data are created locally and gitignored.

**EdgeForge use**
- Reference for resumable/scheduled acquisition jobs.
- Compare range/daily backfill semantics with EdgeForge acquisition contracts.
- Reuse ideas for per-day replacement, audit reports and post-download cleaning gates.

**Watch-outs**
- BBO is not MBO.
- Keep API credentials out of version control.

Priority: **A**

## 3. donald-terrasparq/level2-futures-pipeline
URL: https://github.com/donald-terrasparq/level2-futures-pipeline

**What it offers**
- CME Globex ES/NQ Databento MBP-10 ETL.
- Raw tick fetch, 10-second snapshots, 1-minute aggregation.
- Polars, Parquet, DuckDB, cost estimation, CLI and feature engineering.
- Order-book imbalance, depth slope, microprice, pressure and message-rate features.

**Data state:** RAW EXTERNAL — requires Databento API key.

**EdgeForge use**
- Strong reference for Phase 3 MBP-10 adapter and derived feature pipeline.
- Compare partitioning and metadata-catalog design.
- Use as a checklist for integrating `trades` alongside MBP-10 to avoid fake VWAP/volume proxies.

**Watch-outs**
- Repository itself notes MBP-10 cannot provide true traded volume by itself.
- MBP-10 is not queue-level MBO.

Priority: **A**

## 4. Tomashcv/NasdaqFuturesResearch
URL: https://github.com/Tomashcv/NasdaqFuturesResearch

**What it offers**
- NQ/MNQ acquisition, validation, canonicalization and research platform.
- Size/hash verification, immutable raw layer, lineage, causal definitions, transaction-cost controls and one-shot holdout receipts.
- Strong governance patterns for paid data and research integrity.

**Data state:** REFERENCE ONLY — project explicitly excludes raw DBN, canonical Parquet and row-level derived payloads.

**EdgeForge use**
- Very strong reference for fail-closed acquisition and temporal integrity.
- Compare sealed-holdout receipts, paid-request authorization and immutable raw promotion semantics.
- Useful model for reproducibility contracts.

Priority: **A**

## 5. Nicholashsw/fx-options-vrp
URL: https://github.com/Nicholashsw/fx-options-vrp

**What it offers**
- CME FX futures/options research using Databento `GLBX.MDP3`.
- Reproducibility, statistics/definitions jobs, diagnostics, paper/report workflow.

**Data state:** RAW EXTERNAL — raw DBN files intentionally not committed.

**EdgeForge use**
- Research-job organization, reproducibility and report-generation patterns.
- Useful example of separating licensed raw data from public research outputs.

Priority: **A**

## 6. MacroOps/macro-ops-databento-streamer
URL: https://github.com/MacroOps/macro-ops-databento-streamer

**What it offers**
- Databento streaming/integration reference.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Reference when EdgeForge later adds live/forward recording.
- Compare reconnect/subscription/state handling with EdgeForge live capture.

Priority: **B**

## 7. databento/databento-python
URL: https://github.com/databento/databento-python

**What it offers**
- Official Python client and examples.
- Historical metadata, cost estimation, symbology, `mbo`, `mbp-1`, trades, async downloads and DBN I/O.

**Data state:** OFFICIAL CLIENT; provider data external.

**EdgeForge use**
- Canonical API behavior and schema semantics.
- Use as the primary implementation reference before third-party wrappers.
- Cost estimation should be checked before any paid acquisition.

Priority: **A**

## 8. nautechsystems/nautilus_trader
URL: https://github.com/nautechsystems/nautilus_trader

**What it offers**
- Production-grade Databento adapter and DBN ingestion patterns.
- Strong typed event model, live/historical integration and benchmark/test patterns.

**Data state:** REFERENCE ONLY; market data external.

**EdgeForge use**
- Compare event model, instrument mapping and adapter boundaries.
- Valuable when implementing high-performance DBN/MBO parsing.

Priority: **A**

---

# B. CME MDP 3.0 / MBO reconstruction references

## 9. richie-ma/cme.mdp
URL: https://github.com/richie-ma/cme.mdp

**What it offers**
- CME MDP cleaning and analysis.
- MBP/MBO parsing, order-book reconstruction, order IDs and priority research.
- Points to CME sample files.

**Data state:** RAW EXTERNAL / OFFICIAL SAMPLE REFERENCES.

**EdgeForge use**
- Cross-check CME protocol semantics.
- Useful independent reconstruction reference.

Priority: **A**

## 10. WelokkDev/mdp3-book
URL: https://github.com/WelokkDev/mdp3-book

**What it offers**
- CME MDP 3.0 limit-order-book reconstruction directly from Databento DBN.
- Decodes `mbo`, `trades`, `mbp-10`, `status`, `definition`.
- FIFO queue, `queue_ahead`, modify-priority handling, stop/latency logic, invariant harness and differential validation.
- Documents real NQ MBO replay validation and cross-checking against Databento decoders.

**Data state:** RAW EXTERNAL — repository explicitly states licensed market data are not committed; small provider test fixtures only.

**EdgeForge use**
- One of the strongest references for our MBO replay/book engine.
- Compare modify-priority semantics, halt/status gating, queue-ahead and invariant design.
- Add differential tests between EdgeForge and an independent reconstruction implementation.

**Watch-outs**
- Project is work in progress and says license is not yet chosen.
- Do not copy code wholesale without a compatible license.

Priority: **A+**

## 11. parthokunda/MDP-Order-Book-Generator
URL: https://github.com/parthokunda/MDP-Order-Book-Generator

**What it offers**
- C++ CME Globex MDP 3.0 order-book generation from PCAP.
- README points to an official Databento sample-PCAP download.
- Snapshot Full Refresh handling.

**Data state:** OFFICIAL SAMPLE DOWNLOAD REFERENCE.

**EdgeForge use**
- Useful for PCAP ingestion and CME snapshot logic.
- Excellent independent engineering fixture for packet-level parser validation.

Priority: **A**

## 12. LironKruchinin/backtesting
URL: https://github.com/LironKruchinin/backtesting

**What it offers**
- Research code referencing local Databento NQ TBBO/DBN corpora.
- Concrete NQ file windows and population-size assumptions appear in research configs/examples.

**Data state:** LOCAL PATH REFERENCES; raw provider data not assumed public.

**EdgeForge use**
- Useful examples for defining exact research populations and keeping dataset bounds explicit.
- Potential ideas for NQ microstructure hypotheses.

Priority: **B**

## 13. Banawastaken/claude-projects
URL: https://github.com/Banawastaken/claude-projects

**What it offers**
- NQ research code referencing Databento trades/BBO DBN filenames and derived minute caches.

**Data state:** LOCAL PATH REFERENCES / derived workflow.

**EdgeForge use**
- Source of research ideas and file-layout conventions only.
- Verify every derived-data provenance claim before reuse.

Priority: **C**

## 14. jbot-bit/myprojectx
URL: https://github.com/jbot-bit/myprojectx

**What it offers**
- Scripts for ingesting local Databento `.dbn.zst` NQ files into DuckDB and creating 1m/5m bars.

**Data state:** LOCAL PATH REFERENCES.

**EdgeForge use**
- Compare DBN-to-DuckDB ingestion and aggregation logic.

Priority: **B**

## 15. TradeStax/kairos
URL: https://github.com/TradeStax/kairos

**What it offers**
- Documentation/examples for Databento DBN naming and NQ trades/MBP-10 workflows.

**Data state:** REFERENCE ONLY.

**EdgeForge use**
- File-layout and operational conventions.

Priority: **C**

---

# C. NQ / futures research and validation projects

## 16. teaceo-debug/DEEP6
URL: https://github.com/teaceo-debug/DEEP6

**What it offers**
- NQ/Databento acquisition/replay code.
- Explicit downloader supporting `mbo`, `mbp-10` and `trades`.
- Manifests and derived-data research references.

**Data state:** RAW EXTERNAL / MANIFESTS / DERIVED REFERENCES.

**EdgeForge use**
- Strong reference for NQ-specific download workflows and footprint/replay experiments.
- Compare our data-manifest and cost-control design.

Priority: **A**

## 17. prashanthaitha24/nq-strategy-b-bot
URL: https://github.com/prashanthaitha24/nq-strategy-b-bot

**What it offers**
- Databento `GLBX.MDP3`, `NQ.c.0`, OHLCV acquisition script.

**Data state:** RAW EXTERNAL; script-driven acquisition.

**EdgeForge use**
- Simple NQ bars acquisition reference for strategy screening.

Priority: **C**

## 18. johnsontrades1/session-conditions
URL: https://github.com/johnsontrades1/session-conditions

**What it offers**
- Incremental NQ Databento fetch with a cost guard.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Useful idea: hard budget ceiling before provider request.
- Compare incremental resume semantics.

Priority: **B**

## 19. RAIZ44/Quantitative-and-Algorithmic-Trading-Research-Project-FMU
URL: https://github.com/RAIZ44/Quantitative-and-Algorithmic-Trading-Research-Project-FMU

**What it offers**
- Databento event verification code with NQ continuous symbols.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Research-event verification and data cross-check ideas.

Priority: **C**

## 20. AnthonyMunozPerez/market-data-strategy-lab
URL: https://github.com/AnthonyMunozPerez/market-data-strategy-lab

**What it offers**
- Databento feed integration and strategy-lab patterns.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Candidate design reference for separating feeds from strategy research.

Priority: **C**

## 21. thealgochef/Trade-Lab
URL: https://github.com/thealgochef/Trade-Lab

**What it offers**
- Live Databento validation runbook using `GLBX.MDP3` and NQ continuous symbols.

**Data state:** RAW EXTERNAL / operational docs.

**EdgeForge use**
- Useful future runbook template for live-vs-historical parity validation.

Priority: **B**

## 22. jeremysecondstate/ducketz
URL: https://github.com/jeremysecondstate/ducketz

**What it offers**
- Databento cold-start documentation with CME context symbols including NQ/ES.

**Data state:** REFERENCE ONLY.

**EdgeForge use**
- Operational cold-start/checklist ideas.

Priority: **C**

## 23. johnamcruz/Futures-Foundation-Model
URL: https://github.com/johnamcruz/Futures-Foundation-Model

**What it offers**
- Databento DBN append/update workflows with overlap conflict checks.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Strong idea for fail-closed append/update when provider bars conflict in overlaps.
- Potential reference for dataset versioning and incremental corpus maintenance.

Priority: **B**

## 24. Jozosco/Nexus
URL: https://github.com/Jozosco/Nexus

**What it offers**
- Databento `GLBX.MDP3` raw-data directory conventions and explicit handling of broken artifacts.

**Data state:** repository search shows README/metadata; usable target data not guaranteed.

**EdgeForge use**
- Useful negative-pattern reference: quarantine bad artifacts rather than silently ingesting them.

Priority: **C**

---

# D. Databento tooling / adapters / agent integration

## 25. Nice-Wolf-Studio/databento-mcp-server
URL: https://github.com/Nice-Wolf-Studio/databento-mcp-server

**What it offers**
- Databento MCP/server integration, including ES/NQ symbol mapping.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Useful if EdgeForge later exposes controlled data queries to agents/tools.
- Keep API-key and paid-download authorization behind explicit policy gates.

Priority: **B**

## 26. GeneBO98/tradetally
URL: https://github.com/GeneBO98/tradetally

**What it offers**
- Databento futures symbol mapping and continuous-contract integration.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Additional symbol-resolution reference.

Priority: **C**

## 27. Aryan-20-04/mdrap
URL: https://github.com/Aryan-20-04/mdrap

**What it offers**
- Databento feed mapping for ES/NQ/CL and related research data access.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Feed-adapter and symbol-map comparison.

Priority: **C**

## 28. ml4t/live
URL: https://github.com/ml4t/live

**What it offers**
- Databento live-feed adapter patterns.

**Data state:** RAW EXTERNAL.

**EdgeForge use**
- Future live recording/strategy integration reference.

Priority: **B**

## 29. pathwaycom/pathway
URL: https://github.com/pathwaycom/pathway

**What it offers**
- Example project replaying Databento CME option data and computing option Greeks.

**Data state:** RAW EXTERNAL / example code.

**EdgeForge use**
- Useful if EdgeForge expands into options context, Greeks or event-stream processing.

Priority: **C**

---

# E. Order-book / LOB fixtures and non-CME research references

## 30. bigfatwhale/orderbook
URL: https://github.com/bigfatwhale/orderbook

**What it offers**
- LOBSTER, BATS PITCH and FullDepth parsers/fixtures.
- Small committed test files useful for regression tests.

**Data state:** SMALL PUBLIC FIXTURES; repository license was not clearly detected in prior review.

**EdgeForge use**
- Excellent engineering fixtures for parser/book tests.
- Keep attribution and do not assume broad redistribution rights.

Priority: **A**

## 31. rorysroes/SGX-Full-OrderBook-Tick-Data-Trading-Strategy
URL: https://github.com/rorysroes/SGX-Full-OrderBook-Tick-Data-Trading-Strategy

**What it offers**
- SGX full-order-book research and a small committed CSV fixture.

**Data state:** SMALL PUBLIC FIXTURE; repository license was not detected in prior review.

**EdgeForge use**
- Additional full-book regression/testing source and ML ideas.

Priority: **B**

## 32. stefan-jansen/machine-learning-for-trading
URL: https://github.com/stefan-jansen/machine-learning-for-trading

**What it offers**
- ITCH/microstructure data-processing and ML research patterns.

**Data state:** external datasets/scripts.

**EdgeForge use**
- Feature engineering and research-pipeline inspiration.
- Do not treat book-forecasting benchmarks as proof of executable edge.

Priority: **B**

---

# F. Repositories to inspect further before adoption

These appeared in search and may contain useful implementation ideas, but should be reviewed file-by-file before EdgeForge depends on them:

- https://github.com/MacroOps/macro-ops-databento-streamer
- https://github.com/amandanish882/fxfixaware_wpattern
- https://github.com/Eleven-Trading/TradeNote
- https://github.com/ayushkaf/millibot
- https://github.com/cobriensr/Options-Strike-Calculator
- https://github.com/jeffgat/trading-engine
- https://github.com/intrepidkarthi/orderbook
- https://github.com/Jaspinder2003/LobSim

Classification for this section: **DISCOVERY CANDIDATES**, not trusted dependencies.

---

# EdgeForge adoption plan from this registry

## Immediate ideas to implement

1. **Differential MBO reconstruction testing**
   - Compare EdgeForge book state against `mdp3-book` style invariant/differential oracles.
   - Validate `mbo -> reconstructed MBP-10` across every event boundary on a small licensed NQ corpus.

2. **Paid-acquisition guardrail**
   - Before any Databento request: estimate cost, write intent receipt, require explicit budget authorization, then download.
   - Inspired by `NasdaqFuturesResearch`, `session-conditions` and official Databento examples.

3. **Raw promotion protocol**
   - Download to staging.
   - Verify provider size + SHA-256.
   - Only then promote to immutable raw storage.
   - Never overwrite raw silently.

4. **Overlap conflict gate**
   - Incremental data updates must fail if overlapping provider rows disagree unexpectedly.
   - Inspired by `Futures-Foundation-Model`.

5. **Status/halt-aware book invariants**
   - Crossed-book invariants must consider instrument trading status and pre-open/halt states.
   - Inspired by `mdp3-book`.

6. **MBO priority tests**
   - Explicitly test size increase, size decrease, price change, fill+modify and queue-priority behavior.
   - Preserve `order_id`, priority semantics and `queue_ahead` where defensible.

7. **Dual-schema validation**
   - MBO for exact order lifecycle.
   - MBP-10 for independent aggregate-state checks.
   - Trades for execution prints.
   - Definition/status for contract identity and trading-state context.

8. **Research-vs-execution firewall**
   - Bars and continuous contracts can screen strategies.
   - Queue-sensitive final validation must use actual contracts/order-level data.

9. **Fixture library**
   - Build a tiny legally distributable test corpus from official Databento/CME samples, provider test vectors, Nasdaq ITCH samples, LOBSTER/BATS fixtures and MOEX sample manifests.

10. **Research reference policy**
   - Do not vendor third-party repository code unless its license is compatible.
   - Prefer linking/reference notes when licensing is absent or unclear.

## Problems these repos can help solve

- CME/Databento acquisition and cost control.
- DBN decoding and schema versioning.
- NQ/ES contract and continuous-symbol mapping.
- MBO/MBP/trades cross-validation.
- Order-book reconstruction and FIFO queue logic.
- Status/halt handling.
- Snapshot/delta recovery.
- Data corruption detection.
- Incremental backfill and overlap reconciliation.
- DuckDB/Parquet partitioning.
- Order-book feature engineering.
- Live/historical parity.
- Reproducibility, lineage and holdout governance.
- Research agent/tool access without exposing secrets or bypassing spend controls.

## Do not copy blindly

A useful repository can still contain incorrect market-microstructure assumptions. Before adopting any algorithm:

1. identify the exact source schema and venue;
2. confirm timestamps and sequence semantics;
3. verify side/action conventions;
4. test against a known fixture;
5. reproduce with an independent implementation;
6. document the copied idea and its license;
7. add regression tests before treating it as EdgeForge behavior.

---

# Search terms used / to repeat periodically

- `Databento CME futures`
- `CME/Databento`
- `GLBX.MDP3`
- `NQ.c.0 databento`
- `NQ MBO`
- `.dbn.zst NQ`
- `CME MDP order book`
- `CME MDP3 reconstruction`
- `MBP-10 futures`
- `market by order futures`
- `order book reconstruction CME`
- `Databento parquet`
- `Databento DuckDB`
- `MBO queue position`
- `NQ order book`

Refresh this registry when a repository materially changes, a stronger implementation appears, or a source's license/data boundary becomes clearer.
