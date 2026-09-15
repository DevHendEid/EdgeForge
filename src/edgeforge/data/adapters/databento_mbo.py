from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import datetime, timezone
from typing import Any

from edgeforge.core.models import Action, MarketEvent, Side

DATABENTO_PRICE_SCALE = 1_000_000_000

_ACTIONS: dict[str, Action | None] = {
    "A": Action.ADD,
    "C": Action.CANCEL,
    "M": Action.MODIFY,
    "R": Action.CLEAR,
    "T": Action.TRADE,
    "F": Action.EXECUTE,
    "N": None,
}

_SIDES: dict[str, Side | None] = {
    "A": Side.ASK,
    "B": Side.BID,
    "N": None,
}

InstrumentResolver = Callable[[int], str]


def _ns_to_datetime(value: int | str) -> datetime:
    ns = int(value)
    seconds, nanos = divmod(ns, 1_000_000_000)
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=nanos // 1_000)


def _required(row: Mapping[str, Any], key: str) -> Any:
    if key not in row:
        raise ValueError(f"missing Databento MBO field: {key}")
    return row[key]


class DatabentoMBOAdapter:
    """Normalize decoded Databento MBO rows into EdgeForge ``MarketEvent`` objects.

    This adapter deliberately consumes *decoded* MBO rows. It does not pretend that a
    PCAP capture is already decoded MBO. Raw CME MDP 3.0 packet/SBE decoding remains a
    separate provenance-preserving acquisition step.

    Databento MBO uses nanosecond UNIX timestamps, a 1e-9 price scale, venue sequence
    numbers and one-character action/side codes. Fill records are mapped to
    ``Action.EXECUTE`` because they reduce a displayed resting order; Trade records are
    informational and do not mutate the resting book in EdgeForge's L3 engine.

    Databento's normalized MBO schema does not expose CME's native PriorityID field.
    EdgeForge therefore records a deterministic *stream-order priority surrogate* for
    Add/Modify events. Snapshot Add rows are documented by Databento as preserving
    priority order, making this useful for deterministic replay, but it must not be
    represented as the native CME PriorityID in research claims.
    """

    def __init__(
        self,
        rows: Iterable[Mapping[str, Any]],
        *,
        instrument_resolver: InstrumentResolver | None = None,
        venue: str = "CME",
        source: str = "databento:GLBX.MDP3:mbo",
        strict: bool = True,
    ) -> None:
        self._rows = rows
        self._resolve = instrument_resolver or (lambda instrument_id: str(instrument_id))
        self._venue = venue
        self._source = source
        self._strict = strict

    def read(self) -> Iterator[MarketEvent]:
        priority_clock: dict[int, int] = {}
        for row in self._rows:
            action_code = str(_required(row, "action"))
            if action_code not in _ACTIONS:
                if self._strict:
                    raise ValueError(f"unknown Databento MBO action: {action_code!r}")
                continue
            action = _ACTIONS[action_code]
            if action is None:
                continue

            side_code = str(row.get("side", "N"))
            if side_code not in _SIDES:
                if self._strict:
                    raise ValueError(f"unknown Databento MBO side: {side_code!r}")
                side = None
            else:
                side = _SIDES[side_code]

            instrument_id = int(_required(row, "instrument_id"))
            order_id_value = int(row.get("order_id", 0) or 0)
            price_value = row.get("price")
            size_value = row.get("size")
            sequence_value = row.get("sequence")
            flags_value = row.get("flags")

            order_id: str | None = None if order_id_value == 0 else str(order_id_value)
            price: int | None = None if price_value is None else int(price_value)
            size: int | None = None if size_value is None else int(size_value)
            sequence: int | None = None if sequence_value is None else int(sequence_value)
            priority: int | None = None

            if action is Action.CLEAR:
                side = None
                order_id = None
                price = None
                size = None
                priority_clock[instrument_id] = 0
            elif action in {Action.ADD, Action.MODIFY}:
                next_priority = priority_clock.get(instrument_id, 0) + 1
                priority_clock[instrument_id] = next_priority
                priority = next_priority

            if action is Action.TRADE:
                order_id = None

            flag_items: list[str] = []
            if flags_value is not None:
                flag_items.append(f"databento_flags={int(flags_value)}")
            if priority is not None:
                flag_items.append("priority=stream_order_surrogate")

            yield MarketEvent(
                venue=self._venue,
                instrument=self._resolve(instrument_id),
                event_ts=_ns_to_datetime(_required(row, "ts_event")),
                recv_ts=_ns_to_datetime(row["ts_recv"]) if row.get("ts_recv") is not None else None,
                sequence=sequence,
                action=action,
                side=side,
                price=price,
                price_scale=DATABENTO_PRICE_SCALE,
                size=size,
                order_id=order_id,
                priority=priority,
                flags=tuple(flag_items),
                source=self._source,
            )
