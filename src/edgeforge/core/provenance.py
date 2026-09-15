from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import BaseModel, Field


class SourceManifest(BaseModel):
    source: str
    dataset: str
    license_status: str
    acquired_at: str | None = None
    source_url: str | None = None
    sha256: str | None = None
    schema_version: str = "1"
    notes: str | None = None
    redistribution_allowed: bool | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
