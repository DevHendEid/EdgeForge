# EdgeForge

**Quantitative Research & Market Microstructure Platform**

EdgeForge is an evidence-first platform for discovering, testing, validating, and eventually monitoring quantitative strategies. It is designed around market microstructure, order flow, liquidity, deterministic replay, reproducible research, and strict separation between development and out-of-sample evidence.

## Current implementation status — v0.4.0

- **Phase 0 — Foundation / architecture:** ✅ complete
- **Phase 1 — L3/MBO event engine + LOBSTER/ITCH:** ✅ complete
- **Phase 2 — L2/depth + free scale pipeline:** ✅ complete
- **Phase 3 — CME-specific validation:** ⏳ not implemented yet; sources/interfaces are catalogued only

### Phase 1
- canonical vendor-independent `MarketEvent`
- deterministic L3 order-by-order replay
- add / modify / cancel / execute / delete / clear lifecycle
- queue inspection and state hashes
- LOBSTER message adapter
- decoded Nasdaq ITCH 5.0 lifecycle adapter
- sequence-quality telemetry
- canonical JSONL persistence + optional Parquet

### Phase 2
- snapshot + delta L2 order book
- Binance, OKX, Hyperliquid and Coinbase adapters
- gap / duplicate / regression metrics
- imbalance + microprice features
- streaming JSONL normalization + optional ZSTD Parquet
- free-data-oriented acquisition/provenance foundation

## Dataset policy

EdgeForge combines complementary sources rather than pretending one dataset proves everything. The catalog includes LOBSTER, Nasdaq ITCH, FI-2010, BATS/PITCH development samples; Binance/OKX/Bybit/Hyperliquid/Coinbase/Polymarket scale sources; CME/dxFeed/AlgoSeek/Databento/Rithmic validation targets; and NQ OHLCV/VIX/FRED/economic calendars for later robustness work.

Raw licensed market data does **not** belong in Git. Every external corpus should have a manifest, source URL, license note, hash, retrieval timestamp, schema version, and normalizer version.

## Tech stack

Python 3.12+ is the primary language. Polars/PyArrow/Parquet and DuckDB are used for research storage; Pydantic for schemas; Typer for CLI; pytest/Hypothesis for testing. Rust remains an optional future optimization only after profiling identifies replay hot paths.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
edgeforge doctor
python scripts/verify_phases.py
```

## Architecture

```text
Raw source
   ↓
Source adapter
   ↓
Canonical MarketEvent
   ├── L3 order-by-order book → queue/replay/execution research
   └── L2 price-level book    → depth/imbalance/scale research
            ↓
      canonical storage
            ↓
 features → strategies → execution simulator → validation firewall
```

See `docs/PHASE1.md`, `docs/PHASE2.md`, `docs/ARCHITECTURE.md`, `docs/DATASETS.md`, and `docs/RESEARCH_PROTOCOL.md`.

## Quality & security baseline

The repository includes the DevHendEid GitHub Toolkit baseline: GitHub Actions, Dependabot, CodeQL, Codecov, pre-commit, Ruff/Mypy/Pytest, Semgrep, Gitleaks, Trivy, CODEOWNERS, PR/Issue templates, SECURITY and CONTRIBUTING policies.
