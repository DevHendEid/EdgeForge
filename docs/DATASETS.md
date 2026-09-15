# EdgeForge Dataset Plan

EdgeForge is intentionally **zero-cost first**. We integrate every dataset class required to build the platform, while keeping licensed raw market data out of Git.

## Why multiple datasets?

No single free source covers every research requirement. EdgeForge separates four jobs:

1. **Order-event correctness** — LOBSTER, Nasdaq ITCH, BATS/PITCH samples, FI-2010.
2. **Scale and L2 replay** — OKX, Binance, Bybit, Hyperliquid, Coinbase, optional Polymarket.
3. **CME/NQ protocol validation** — official CME samples, dxFeed samples, AlgoSeek sandbox, then Databento/Rithmic only when access is available.
4. **Long-horizon robustness and regime context** — NQ OHLCV, VIX, FRED and official economic-release calendars.

## Dataset grades

- **L3/MBO**: individual orders and lifecycle/order identity. Suitable for queue-sensitive work.
- **Event-driven L2**: price-level deltas. Suitable for book reconstruction by price, not individual queue position.
- **Snapshots/MBP**: aggregated depth. Suitable for imbalance/footprint/depth features with limits.
- **Trades/BBO/OHLCV/context**: strategy screening and regime analysis, not exact queue replay.

## Raw-data policy

`data/raw/` is local-only and ignored by Git. Every acquired dataset must have a manifest containing source, URL/provider, retrieval time, SHA-256, schema/version, license note, first/last timestamp, event count and known gaps. Commercial CME/Databento/BMLL/Rithmic raw history must never be committed.

## Zero-cost acquisition order

Start with LOBSTER and Nasdaq ITCH samples, then FI-2010. Add OKX/Binance/Bybit/Hyperliquid for scale. Record Coinbase prospectively. Add official CME/dxFeed samples for CME-specific tests. Only after the pipeline is proven should a legitimate Databento/Rithmic/CME window be acquired.

## Context data and leakage

Economic series and calendars are time-varying datasets. EdgeForge must use publication timestamps/vintages, not today's revised values, when recreating historical decisions. VIX and macro/event features belong to research context and must never substitute for execution data.
