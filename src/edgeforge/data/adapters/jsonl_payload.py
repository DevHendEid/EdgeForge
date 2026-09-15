from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Any


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError("JSONL payloads must be JSON objects")
                yield obj
