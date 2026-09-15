# EdgeForge Data Source Registry

This document is the human-readable companion to `src/edgeforge/data/registry.py`.

## Status model

EdgeForge distinguishes **registered source** from **raw bytes present locally**. A source may be useful and fully integrated into the research plan even when its raw data are not committed to Git. Raw licensed market data live outside Git; reproducibility is maintained through manifests, hashes, timestamps and source metadata.

Use these operational states:

- `REGISTERED`: source is known to EdgeForge and has provenance/role metadata.
- `ACQUIRABLE`: there is an official/public/API path to obtain data.
- `LOCAL`: raw data have been downloaded outside Git and registered with a SHA-256 manifest.
- `NORMALIZED`: an EdgeForge adapter has produced canonical events.
- `VALIDATED`: replay/invariant/data-quality tests passed for a defined corpus.
- `REFERENCE_ONLY`: repository/provider is useful for code, methodology or discovery but its raw data are absent or redistribution rights are unclear.

## Highest-priority market data

| Key | Source | Grade / role | Access policy |
|---|---|---|---|
| `databento-glbx-mdp3` | Databento GLBX.MDP3 | Genuine CME MBO/MBP/TBBO/trades | Commercial/licensed; local only unless license explicitly permits otherwise |
| `cme-datamine` | CME DataMine | Canonical CME historical data | Commercial/sample/trial depending product |
| `cme-mdp-sample` | CME official samples | CME protocol validation | Official samples only |
| `rithmic-cme` | Rithmic | Secondary CME feed / cross-vendor checks | Trial/subscription |
| `bmll-l3-futures` | BMLL Level 3 Futures | Futures MBO/L3 | Commercial/sample depending current offer |
| `dxfeed-samples` | dxFeed samples | Independent sample validation | Free samples |
| `lobster-sample` | LOBSTER | Order-event replay | Official public samples |
| `nasdaq-itch-sample` | Nasdaq TotalView-ITCH | Native order-event feed | Official samples where offered |
| `fi-2010` | FI-2010 | L2 ML benchmark | Free academic dataset |
| `moex-full-order-book-sample` | MOEX | Full order book sample | Official sample; raw archives remain external |

## Free/public scale corpora

The project also registers OKX, Binance, Bybit, Hyperliquid, Coinbase, Polymarket, Kraken and Tardis as scale/cross-venue sources. These are useful for pipeline stress testing, snapshot/delta recovery, storage and feature engineering, but aggregated L2 must never be labeled as MBO.

## GitHub research/data references

The following repositories are now registered explicitly so they are not lost between research sessions:

- `https://github.com/bigfatwhale/orderbook` — parsers and small BATS/LOBSTER/FullDepth fixtures. GitHub reports no repository license; do not vendor its files automatically.
- `https://github.com/richie-ma/cme.mdp` — GPL-3.0 CME MDP parsing/reconstruction reference; useful for MBO/MBP and queue-priority logic.
- `https://github.com/rorysroes/SGX-Full-OrderBook-Tick-Data-Trading-Strategy` — SGX full-book research repository; no detected repository license, therefore reference-only by default.
- `https://github.com/teaceo-debug/DEEP6` — NQ/Databento manifests, derived-data and NQ research references. Referenced local DBN files are not assumed redistributable.
- `https://github.com/Nicholashsw/fx-options-vrp` — Databento GLBX.MDP3 methodology; raw commercial data are deliberately absent.
- `https://github.com/nautechsystems/nautilus_trader` — production-quality Databento integration reference.
- `https://github.com/databento/databento-python` — official Databento Python client/examples.
- `https://github.com/stefan-jansen/machine-learning-for-trading` — ITCH/microstructure/ML research patterns.
- `https://github.com/s583381747/nq-quant` — NQ research reference; verify any dataset claims before use.

## Data acquisition discipline

1. Prefer official/free/legal sources first.
2. Download raw files to `data/raw/<dataset-key>/` or another local/external storage path. `data/raw/` is Git-ignored.
3. Run `python scripts/register_local_dataset.py <dataset-key> <file>` to create a reproducibility manifest with SHA-256.
4. Never infer that a public GitHub file has redistribution rights merely because the repository is public.
5. Never treat bars, snapshots or MBP as MBO.
6. Preserve exact source URL, retrieval time, file size and checksum for every acquired artifact.

## Current limitation

Registration does **not** mean every raw dataset is already downloaded. Many datasets are very large, commercial, require credentials, or have terms that prevent mirroring. EdgeForge tracks them centrally so acquisition and validation can proceed without losing provenance or mixing incompatible data grades.
