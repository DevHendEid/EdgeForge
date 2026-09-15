from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256

from edgeforge.book.l3 import L3OrderBook
from edgeforge.core.models import Action, MarketEvent, Side


class TradingStatus(StrEnum):
    UNKNOWN = "unknown"
    PREOPEN = "preopen"
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"
    HALTED = "halted"


@dataclass(slots=True)
class SequenceDiagnostics:
    records: int = 0
    gaps: int = 0
    regressions: int = 0
    repeated_sequence_records: int = 0
    first_sequence: int | None = None
    last_sequence: int | None = None

    def observe(self, sequence: int | None) -> None:
        self.records += 1
        if sequence is None:
            return
        if self.first_sequence is None:
            self.first_sequence = sequence
        if self.last_sequence is not None:
            if sequence < self.last_sequence:
                self.regressions += 1
            elif sequence == self.last_sequence:
                # One native exchange message can normalize to multiple records.
                self.repeated_sequence_records += 1
            elif sequence > self.last_sequence + 1:
                self.gaps += sequence - self.last_sequence - 1
        self.last_sequence = sequence


@dataclass(frozen=True, slots=True)
class ReplayCheckpoint:
    instrument: str
    event_count: int
    venue_sequence: int | None
    best_bid: tuple[int, int] | None
    best_ask: tuple[int, int] | None
    order_count: int
    state_hash: str
    depth_hash: str


@dataclass(slots=True)
class CMEInstrumentState:
    book: L3OrderBook = field(default_factory=L3OrderBook)
    sequence: SequenceDiagnostics = field(default_factory=SequenceDiagnostics)
    status: TradingStatus = TradingStatus.UNKNOWN
    event_count: int = 0


class CMEReplayValidator:
    """CME-specific deterministic replay wrapper with fail-closed diagnostics.

    Venue sequence diagnostics are intentionally kept outside ``L3OrderBook`` because
    exchange/native messages may normalize into more than one MBO record with the same
    venue sequence number.  The book therefore receives a copy with ``sequence=None``;
    regressions and gaps are tracked explicitly here instead of being conflated with a
    duplicate canonical event.
    """

    def __init__(self, *, fail_on_gap: bool = True, fail_on_regression: bool = True) -> None:
        self._states: dict[str, CMEInstrumentState] = {}
        self.fail_on_gap = fail_on_gap
        self.fail_on_regression = fail_on_regression

    def state(self, instrument: str) -> CMEInstrumentState:
        return self._states.setdefault(instrument, CMEInstrumentState())

    def set_status(self, instrument: str, status: TradingStatus) -> None:
        self.state(instrument).status = status

    def apply(self, event: MarketEvent) -> None:
        state = self.state(event.instrument)
        previous_gaps = state.sequence.gaps
        previous_regressions = state.sequence.regressions
        state.sequence.observe(event.sequence)

        if self.fail_on_regression and state.sequence.regressions > previous_regressions:
            raise ValueError(
                f"CME sequence regression for {event.instrument}: {event.sequence} "
                f"after {state.sequence.last_sequence}"
            )
        if self.fail_on_gap and state.sequence.gaps > previous_gaps:
            raise ValueError(f"CME sequence gap detected for {event.instrument}")

        # A market-data book can still receive clear/reset messages outside OPEN.
        if state.status in {TradingStatus.HALTED, TradingStatus.CLOSED} and event.action not in {
            Action.CLEAR,
            Action.TRADE,
        }:
            raise ValueError(
                f"book-mutating event {event.action} received while {event.instrument} "
                f"status={state.status}"
            )

        # Sequence validation is handled above with CME/provider semantics.
        state.book.apply(event.model_copy(update={"sequence": None}))
        state.event_count += 1

    def checkpoint(self, instrument: str) -> ReplayCheckpoint:
        state = self.state(instrument)
        depth_payload = self._depth_payload(state.book)
        return ReplayCheckpoint(
            instrument=instrument,
            event_count=state.event_count,
            venue_sequence=state.sequence.last_sequence,
            best_bid=state.book.best_bid(),
            best_ask=state.book.best_ask(),
            order_count=len(state.book.orders),
            state_hash=state.book.state_hash(),
            depth_hash=sha256(depth_payload.encode()).hexdigest(),
        )

    @staticmethod
    def _depth_payload(book: L3OrderBook) -> str:
        rows: list[str] = []
        for side in (Side.BID, Side.ASK):
            rows.extend(f"{side}:{price}:{size}" for price, size in book.depth(side))
        return "|".join(rows)


def compare_checkpoints(
    actual: ReplayCheckpoint,
    expected: ReplayCheckpoint,
) -> tuple[str, ...]:
    """Return field names that diverge; an empty tuple is a differential PASS."""

    fields = (
        "event_count",
        "venue_sequence",
        "best_bid",
        "best_ask",
        "order_count",
        "state_hash",
        "depth_hash",
    )
    return tuple(name for name in fields if getattr(actual, name) != getattr(expected, name))
