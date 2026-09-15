from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from edgeforge.book.l2 import L2OrderBook
from edgeforge.book.l3 import L3OrderBook
from edgeforge.core.models import MarketEvent
from edgeforge.quality.sequence import SequenceTracker


@dataclass(frozen=True, slots=True)
class ReplayReport:
    events: int
    errors: int
    state_hash: str | None
    sequence_gaps: int


def replay_l3(events: Iterable[MarketEvent], strict: bool = True) -> ReplayReport:
    book = L3OrderBook(); tracker = SequenceTracker(); count = errors = 0
    for event in events:
        count += 1; tracker.observe(event.sequence)
        try:
            book.apply(event)
        except (ValueError, KeyError, AssertionError):
            errors += 1
            if strict:
                raise
    return ReplayReport(count, errors, book.state_hash(), tracker.stats.gaps)


def replay_l2(events: Iterable[MarketEvent], strict: bool = True) -> ReplayReport:
    book = L2OrderBook(); tracker = SequenceTracker(); count = errors = 0
    for event in events:
        count += 1; tracker.observe(event.sequence)
        try:
            book.apply(event)
        except (ValueError, KeyError, AssertionError):
            errors += 1
            if strict:
                raise
    return ReplayReport(count, errors, None, tracker.stats.gaps)
