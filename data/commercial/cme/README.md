# CME commercial/raw data intake

This directory is reserved for CME commercial/raw datasets that you intentionally choose to keep in this private repository via Git LFS.

## Expected files

Typical large-file formats tracked by LFS here include `.dbn`, `.dbn.zst`, `.zst`, `.parquet`, `.csv`, `.csv.gz`, `.gz`, and `.zip`.

## Organization

Prefer a structure such as:

```text
data/commercial/cme/
  NQ/
    2026-03/
    2026-04/
  ES/
  GC/
  manifests/
```

For every raw file, keep a manifest with provider, product, instrument, date range, retrieval time, size, SHA-256, schema/feed type, and license/access note.

## Important

Git LFS changes how large files are stored; it does not change CME licensing terms. Only place data here that you are authorized to possess/store under your active agreement.
