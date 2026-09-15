# Databento commercial/raw data intake

This directory is reserved for Databento-downloaded raw datasets that you intentionally choose to keep in this private repository via Git LFS.

## Primary EdgeForge target

- Dataset: `GLBX.MDP3`
- Primary schema: `mbo`
- Target instruments: NQ, ES, YM, RTY, CL, GC

Typical large-file formats tracked by LFS here include `.dbn`, `.dbn.zst`, `.zst`, `.parquet`, `.csv`, `.csv.gz`, `.gz`, and `.zip`.

## Organization

Prefer a structure such as:

```text
data/commercial/databento/
  GLBX.MDP3/
    NQ/
      mbo/
        2026-03/
        2026-04/
    ES/
    GC/
  manifests/
```

For every file, record provider, dataset, schema, symbols, date range, retrieval/job identifier if available, file size, SHA-256, retrieval timestamp, and entitlement/license note.

## Important

Git LFS changes storage mechanics only. It does not grant redistribution/storage rights beyond the active Databento/CME agreement.
