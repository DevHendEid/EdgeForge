from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from edgeforge.core.models import MarketEvent


def write_events(path: str | Path, events: Iterable[MarketEvent]) -> int:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); count = 0
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(event.model_dump_json() + "\n"); count += 1
    return count


def read_events(path: str | Path) -> list[MarketEvent]:
    out: list[MarketEvent] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip(): out.append(MarketEvent.model_validate(json.loads(line)))
    return out
