# Phase 3 — CME-Specific Validation

Status: **IMPLEMENTATION ACTIVE — empirical gate pending CI/reference replay**

Phase 3 exists to prevent EdgeForge from making CME-specific microstructure claims before the platform has demonstrated that it can preserve provenance, normalize MBO semantics, reconstruct the visible order book deterministically, detect sequence/data-quality problems, and compare its state against independent references.

## 3A — Actual data inventory

Implemented:

- `edgeforge.data.inventory`
- `scripts/phase3_inventory.py`
- SHA-256 for every inventoried data file
- format/compression classification
- L1/L2/L3/OHLCV evidence classification
- provenance classes from the master roadmap
- explicit quarantine for unknown or license-unclear corpora
- machine-readable `inventory.json`
- machine-readable `quarantine.json`
- human-readable `INVENTORY.md`

Important rule: a public GitHub repository does not by itself establish redistribution rights for data found inside it. Such data defaults to `PUBLIC_LICENSE_UNCLEAR` and is admissible only for inspection until its license/provenance is resolved.

Run against the complete local research workspace with:

```bash
python scripts/phase3_inventory.py ~/market-data-repos \
  --output data/manifests/phase3-local-inventory
```

The generated inventory is environment-specific and should only be committed when it contains no private paths/secrets and when redistribution of the metadata itself is acceptable.

## 3B — CME / Databento MBO normalization

Implemented:

- `edgeforge.data.adapters.databento_mbo.DatabentoMBOAdapter`
- nanosecond `ts_event` / `ts_recv` normalization
- Databento 1e-9 price scale
- CME instrument resolver hook
- Add / Cancel / Modify / Clear / Trade / Fill mapping
- Fill → `Action.EXECUTE` for resting visible quantity reduction
- Clear → instrument book reset
- strict unknown-action failure
- venue sequence preservation
- deterministic stream-order priority surrogate for Add/Modify events

The priority surrogate is intentionally labeled. Databento's normalized MBO schema does not expose CME's native `PriorityID`; therefore EdgeForge must not call the surrogate a native CME PriorityID. It is valid for deterministic ordering and for provider-documented snapshot ordering, but final queue claims must match the evidence actually present.

### Raw PCAP boundary

The official sample in this repository is a raw CME MDP 3.0 PCAP capture. `DatabentoMBOAdapter` consumes decoded MBO rows; it is **not** a fake PCAP decoder.

The raw packet/SBE decode step must preserve its own provenance and can be provided by:

- an independently validated CME MDP 3.0 decoder,
- a provider-supported decode/export path,
- or a reference implementation whose outputs are then differentially validated.

This separation is deliberate: raw packet decoding and canonical market-event normalization are different evidence layers.

## 3C — Differential reconstruction validation

Implemented:

- `edgeforge.validation.cme.CMEReplayValidator`
- deterministic per-instrument L3 reconstruction
- reproducible state hashes
- reproducible depth hashes
- best bid / best ask checkpoints
- order-count checkpoints
- `compare_checkpoints()` divergence reporting
- queue-ahead quantity/order accounting
- `scripts/phase3_validate_mbo_jsonl.py`

Reference implementations registered for differential work:

- `external/github/cme-databento/MDP-Order-Book-Generator`
- `external/github/cme-databento/cme.mdp`
- `external/github/cme-databento/mdp3-book`
- Databento documented MBO behavior
- CME MDP 3.0 / MBO documentation and certification semantics

Differential PASS means unexplained divergence is zero for the compared corpus/checkpoints. A reference implementation is evidence, not authority; CME exchange semantics and provider schema documentation take precedence when references disagree.

## 3D — CME invariant harness

Implemented invariants / fail-closed behavior:

- sequence regression detection
- sequence gap detection
- repeated venue sequence support for one native message normalized into multiple rows
- unknown cancel/modify behavior inherited from the deterministic L3 book
- positive resting quantity invariant
- no crossed visible book invariant
- deterministic clear/reset
- deterministic queue ordering when priority evidence exists
- queue-ahead accounting
- halted/closed mutation guard with explicit clear/trade exceptions
- deterministic replay checkpoints

Automated tests:

- `tests/unit/test_databento_mbo.py`
- `tests/unit/test_cme_validation.py`
- `tests/unit/test_inventory.py`

The invariant set is intentionally stricter than a permissive parser. Unknown or contradictory state fails closed rather than being silently repaired.

## 3E — Performance profiling

Implemented:

- `scripts/phase3_benchmark_replay.py`
- reproducible state hash printed with benchmark result
- event throughput measurement independent from strategy logic

Run:

```bash
python scripts/phase3_benchmark_replay.py --events 100000
```

There is no arbitrary performance threshold that can trigger a Rust rewrite. Python remains the default until profiling on representative data demonstrates a concrete throughput/latency bottleneck.

## Official sample receipt

Pinned manifest:

`data/manifests/databento_cme_mdp3_sample.json`

Official sample files:

- `dc3-glbx-a-20230716T133000.pcap`
  - size: 60,824 bytes
  - SHA-256: `cfd06c71c99c0b3fd33f7ee3285b2bbbba9c4f03cb65d362e60a16f2d78a99e1`
- `dc3-glbx-a-20230716T133000.pcap.zst`
  - size: 15,597 bytes
  - SHA-256: `59cbedb003fdbfa0ee800c31ac936f1c30053389dd4108f0e6d8ac679c242d6b`

The manifest classifies only this official public sample. It does not grant or imply redistribution rights for commercial CME/Databento history.

## CI gate

`.github/workflows/phase3-cme.yml` performs:

1. LFS checkout of the official sample.
2. Exact SHA-256 verification.
3. Phase 3 unit/invariant tests.
4. Deterministic replay benchmark smoke test.
5. Compilation of the independent `MDP-Order-Book-Generator` reference decoder.

## External semantic authorities used

- CME MBO FAQ: MBO exposes individual orders, anonymous OrderID, and PriorityID used for book sorting; PriorityID may change when an order is modified/refreshed.
- CME AutoCert MBO book-management tests: clients must reconstruct orders/cancellations and confirm price/quantity in proper book priority.
- Databento MBO schema: MBO contains order-level events keyed by `order_id`, nanosecond timestamps, sequence, actions, sides, price, size and flags.
- Databento MBO snapshots: snapshot begins with Clear followed by Add records and preserves priority order per instrument/price.

See the master roadmap for research-policy implications.

## Completion gate

Phase 3 can be marked **COMPLETE** only when all of the following are true:

- [x] inventory tooling implemented
- [x] official sample hashes/manifests pinned
- [x] decoded MBO → canonical adapter implemented
- [x] sequence/gap/regression handling implemented
- [x] deterministic CME replay checkpoints implemented
- [x] queue-ahead accounting implemented
- [x] status guard implemented
- [x] invariant/unit tests implemented
- [x] performance benchmark implemented
- [x] independent reference decoder compile gate implemented
- [ ] Phase 3 CI passes on the final branch head
- [ ] official sample/reference replay produces a reproducible comparison artifact
- [ ] unexplained differential divergence count is zero for the chosen official validation corpus

Until the final three empirical gates pass, documentation must say **Phase 3 implementation complete, validation evidence pending**, not simply `COMPLETE`.
