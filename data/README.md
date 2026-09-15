# Data directory

- `raw/`: local source files; normally ignored except `.gitkeep`.
- `canonical/`: normalized EdgeForge partitions; large generated outputs are local/artifact storage, not Git.
- `manifests/`: provenance and checksum manifests.
- `context/`: small derived/context tables when their license permits committing them.

Never commit licensed CME/Databento raw files or secrets/API keys.
