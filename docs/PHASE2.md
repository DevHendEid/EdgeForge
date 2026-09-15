# Phase 2 — Free depth scale validation

Phase 2 adds a vendor-independent L2 snapshot/delta book suitable for free crypto depth corpora and recording.

Implemented:
- L2 price-level book with snapshot/reset, upsert, delete, best bid/ask and invariants
- Binance depth-update normalizer
- OKX books/books-l2-tbt normalizer
- sequence gap/duplicate/regression telemetry
- JSONL streaming persistence and optional ZSTD Parquet
- microstructure primitives: top-level imbalance and microprice

Planned acquisition is deliberately source-separated. Raw files remain outside Git; only source manifests, hashes, and normalized test fixtures belong in the repository.
