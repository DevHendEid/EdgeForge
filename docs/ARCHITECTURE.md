# EdgeForge Architecture

## Principle

Strategies consume canonical research objects, never vendor-specific schemas.

```text
Raw source -> Adapter -> Canonical events -> Book/replay -> Features -> Strategy
                                               |              |
                                               v              v
                                          Provenance      Validation
```

## Layers

1. **Data acquisition**: legal/public samples or user-entitled feeds.
2. **Raw preservation**: immutable source files + SHA-256 + source manifest.
3. **Normalization**: vendor-specific adapter to canonical `MarketEvent`.
4. **Replay**: deterministic L3/L2 book reconstruction with invariants.
5. **Feature layer**: order flow, imbalance, spread, queue, footprint, volatility.
6. **Strategy layer**: signal generation independent of vendor schemas.
7. **Execution simulation**: commissions, slippage, latency, order type, queue model.
8. **Validation**: dev/validation/sealed holdout, walk-forward, Monte Carlo, bootstrap, regimes.
9. **Registry/reporting**: experiment metadata, reproducibility hashes, promotion status.

## Performance plan

Python + Polars/DuckDB is the default. Rust is introduced only after profiling proves a hot path cannot meet throughput requirements. This avoids premature systems complexity while keeping a clean FFI boundary available for future high-throughput replay.
