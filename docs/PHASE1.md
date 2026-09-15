# Phase 1 — Genuine event-driven engine

Phase 1 makes vendor-independent order-event replay real, not aspirational.

Implemented:
- canonical L3 lifecycle (`ADD`, `MODIFY`, `CANCEL`, `EXECUTE`, `DELETE`, `CLEAR`)
- FIFO/priority queue inspection at price level
- deterministic state hashing
- sequence monotonicity checks and independent gap accounting
- LOBSTER message adapter
- decoded Nasdaq ITCH record adapter (`A/F/E/C/X/D/U`)
- JSONL canonical persistence and optional Parquet output
- deterministic fixture/integration tests

The repository intentionally does not redistribute commercial LOBSTER, Nasdaq, CME, or Databento history.
