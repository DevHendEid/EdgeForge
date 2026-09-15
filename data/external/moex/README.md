# MOEX Full Order Book sample dataset

This directory registers the official Moscow Exchange (MOEX) historical Full Order Book sample dataset used by EdgeForge for order-book ingestion and replay validation.

## Source

- Provider: Moscow Exchange (MOEX)
- Product: Historical Data — Full Order Book / Type A
- Official sample page: https://www.moex.com/ru/RegistrationSubscriptions/freeTrial.aspx
- Historical-data description: https://www.moex.com/a2863
- Market-data policy: https://www.moex.com/en/datapolicy/
- Sample period advertised by MOEX: 2014-09-01 through 2014-09-05
- Markets advertised on the sample page: Futures, Currencies, Equities, Options
- Format: CSV archives

## EdgeForge usage

Use these samples only as an external test/validation corpus for parsing, event normalization, order-book reconstruction, sequence checks, and replay tests. Do not treat them as CME/NQ data and do not mix them with CME validation results.

## Storage policy

The raw MOEX archives are intentionally **not mirrored into this Git repository**. MOEX's market-data terms distinguish individual use from redistribution and state that archive data received by end users must not be disseminated without prior written approval. A private GitHub repository does not itself change the provider's license terms.

For reproducibility, keep the raw archives outside Git under a local path such as:

```text
.data/external/moex/full_order_book/2014-09-01_2014-09-05/
```

Then record each downloaded archive's SHA-256 in `manifest.json` before using it in a reproducible experiment.

## Dataset status

- Official free sample: AVAILABLE FROM MOEX
- Raw bytes committed to EdgeForge: NO
- Redistribution permission established: NO
- Approved EdgeForge role: external validation / engineering fixture source
- Phase impact: supports Phase 1/2 book-engine validation; does not satisfy Phase 3 CME/NQ validation
