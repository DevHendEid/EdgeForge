from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Protocol

from edgeforge.core.models import MarketEvent


class EventAdapter(Protocol):
    def read(self) -> Iterator[MarketEvent]: ...


def replay(events: Iterable[MarketEvent]) -> Iterator[MarketEvent]:
    yield from events
