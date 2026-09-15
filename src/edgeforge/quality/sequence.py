from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SequenceStats:
    events: int = 0
    gaps: int = 0
    duplicates: int = 0
    regressions: int = 0
    first: int | None = None
    last: int | None = None


class SequenceTracker:
    def __init__(self) -> None:
        self.stats = SequenceStats()

    def observe(self, seq: int | None) -> None:
        if seq is None:
            return
        s = self.stats
        s.events += 1
        if s.first is None:
            s.first = s.last = seq
            return
        assert s.last is not None
        if seq == s.last:
            s.duplicates += 1
        elif seq < s.last:
            s.regressions += 1
        elif seq > s.last + 1:
            s.gaps += seq - s.last - 1
        s.last = max(s.last, seq)
