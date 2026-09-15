# GitHub dataset/research references

This directory documents external GitHub sources discovered during EdgeForge data research. The repositories themselves are **not vendored here automatically** because repository visibility is not the same as permission to redistribute contained market data.

## Registered repositories

- `bigfatwhale/orderbook` — parsers plus small LOBSTER/BATS/FullDepth test fixtures. GitHub reports no repository license.
- `richie-ma/cme.mdp` — GPL-3.0 CME MDP parsing/reconstruction reference; useful for MBP/MBO and queue-priority logic.
- `rorysroes/SGX-Full-OrderBook-Tick-Data-Trading-Strategy` — full-order-book research repository; no detected repository license.
- `teaceo-debug/DEEP6` — NQ/Databento manifest and derived-data research references. Referenced local DBN data are not assumed redistributable.
- `Nicholashsw/fx-options-vrp` — Databento GLBX.MDP3 methodology; raw licensed files are intentionally absent.
- `nautechsystems/nautilus_trader` — Databento adapter/event-model implementation reference.
- `databento/databento-python` — official Databento client/examples.
- `stefan-jansen/machine-learning-for-trading` — ITCH/microstructure/ML research reference.
- `s583381747/nq-quant` — NQ research repository; dataset claims require independent provenance checks.

See `docs/DATA_SOURCE_REGISTRY.md` and `src/edgeforge/data/registry.py` for canonical metadata.

## Import rule

When a GitHub-hosted data file has a clear license that permits the intended use, download it to `data/raw/<dataset-key>/` and register it with:

```bash
python scripts/acquire_dataset.py <dataset-key> --url <direct-authorized-url>
```

For files obtained manually/API/authenticated download:

```bash
python scripts/register_local_dataset.py <dataset-key> /path/to/file
```

Raw files remain outside Git by default; the generated manifest records SHA-256 and provenance.
