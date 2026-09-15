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
    best_bid: tuple[int, int] | None
    best_ask: tuple[int, int] | None
    order_count: int
    state_hash: str
    depth_hash: str


@dataclass(frozen=True, slots=True)
class QueueAhead:
    orders_ahead: int
    quantity_ahead: int


@dataclass(slots=True)
class CMEInstrumentState:
    book: L3OrderBook = field(default_factory=L3OrderBook)
    status: TradingStatus = TradingStatus.UNKNOWN
    event_count: int = 0


class CMEReplayValidator:
    """CME-specific deterministic replay wrapper with fail-closed diagnostics.

    CME/provider sequence numbers are stream/channel scoped, not instrument scoped.
    EdgeForge therefore tracks sequence diagnostics by ``MarketEvent.stream_id`` and
    keeps instrument book state separately. This avoids false gap reports when many
    instruments are interleaved on one multicast/provider channel.
    """

    def __init__(self, *, fail_on_gap: bool = True, fail_on_regression: bool = True) -> None:
        self._states: dict[str, CMEInstrumentState] = {}
        self._streams: dict[str, SequenceDiagnostics] = {}
        self.fail_on_gap = fail_on_gap
        self.fail_on_regression = fail_on_regression

    @property
    def instruments(self) -> tuple[str, ...]:
        return tuple(sorted(self._states))

    @property
    def streams(self) -> tuple[str, ...]:
        return tuple(sorted(self._streams))

    def state(self, instrument: str) -> CMEInstrumentState:
        return self._states.setdefault(instrument, CMEInstrumentState())

    def stream_diagnostics(self, stream_id: str) -> SequenceDiagnostics:
        return self._streams.setdefault(stream_id, SequenceDiagnostics())

    def set_status(self, instrument: str, status: TradingStatus) -> None:
        self.state(instrument).status = status

    def apply(self, event: MarketEvent) -> None:
        state = self.state(event.instrument)

        # Sequence validation is only meaningful when the adapter identifies the
        # sequencing scope. With no stream_id, we preserve the event but do not make
        # packet-loss claims from an instrument-filtered sequence.
        if event.sequence is not None and event.stream_id is not None:
            diagnostics = self.stream_diagnostics(event.stream_id)
            previous_sequence = diagnostics.last_sequence
            previous_gaps = diagnostics.gaps
            previous_regressions = diagnostics.regressions
            diagnostics.observe(event.sequence)

            if self.fail_on_regression and diagnostics.regressions > previous_regressions:
                raise ValueError(
                    f"CME sequence regression for stream {event.stream_id}: "
                    f"{event.sequence} after {previous_sequence}"
                )
            if self.fail_on_gap and diagnostics.gaps > previous_gaps:
                raise ValueError(
                    f"CME sequence gap detected for stream {event.stream_id}: "
                    f"{previous_sequence} -> {event.sequence}"
                )

        # A market-data book can still receive clear/reset and informational records
        # outside OPEN.
        if state.status in {TradingStatus.HALTED, TradingStatus.CLOSED} and event.action not in {
            Action.CLEAR,
            Action.TRADE,
            Action.FILL,
        }:
            raise ValueError(
                f"book-mutating event {event.action} received while {event.instrument} "
                f"status={state.status}"
            )

        # The generic L3 book must not re-interpret a provider/channel sequence as an
        # instrument-local strictly increasing sequence.
        state.book.apply(event.model_copy(update={"sequence": None}))
        state.event_count += 1

    def queue_ahead(self, instrument: str, order_id: str) -> QueueAhead:
        state = self.state(instrument)
        order = state.book.orders.get(order_id)
        if order is None:
            raise KeyError(f"unknown order: {order_id}")
        queue = state.book.queue(order.side, order.price)
        quantity = 0
        count = 0
        for queued in queue:
            if queued.order_id == order_id:
                return QueueAhead(orders_ahead=count, quantity_ahead=quantity)
            count += 1
            quantity += queued.size
        raise AssertionError("order exists in book but not in its price queue")

    def checkpoint(self, instrument: str) -> ReplayCheckpoint:
        state = self.state(instrument)
        depth_payload = self._depth_payload(state.book)
        return ReplayCheckpoint(
            instrument=instrument,
            event_count=state.event_count,
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
        "best_bid",
        "best_ask",
        "order_count",
        "state_hash",
        "depth_hash",
    )
    return tuple(name for name in fields if getattr(actual, name) != getattr(expected, name))
