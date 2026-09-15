from __future__ import annotations

from pathlib import Path
from typing import Iterable

from edgeforge.core.models import MarketEvent


def write_events_parquet(path: str | Path, events: Iterable[MarketEvent]) -> int:
    """Write canonical events to Parquet when PyArrow is installed."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install EdgeForge base dependencies (pyarrow) for Parquet output") from exc
    rows = [e.model_dump(mode="json") for e in events]
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path, compression="zstd")
    return len(rows)
