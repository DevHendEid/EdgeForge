from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
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
    "F": Action.FILL,
    "N": None,
}

_SIDES: dict[str, Side | None] = {
    "A": Side.ASK,
    "B": Side.BID,
    "N": None,
}

InstrumentResolver = Callable[[int], str]


@dataclass(slots=True)
class _RestingOrder:
    price: int
    size: int
    priority: int


def _ns_to_datetime(value: int | str) -> datetime:
    ns = int(value)
    seconds, nanos = divmod(ns, 1_000_000_000)
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=nanos // 1_000)


def _required(row: Mapping[str, Any], key: str) -> Any:
    if key not in row:
        raise ValueError(f"missing Databento MBO field: {key}")
    return row[key]


def _optional_int(row: Mapping[str, Any], key: str) -> int | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    return int(value)


class DatabentoMBOAdapter:
    """Normalize decoded Databento MBO rows into EdgeForge ``MarketEvent`` objects.

    The adapter follows Databento's documented normalized MBO lifecycle:

    - Add inserts a resting order.
    - Cancel removes the *quantity in the record* from a resting order.
    - Modify replaces price/size and loses priority only when price changes or size grows.
    - Trade and Fill are informational and do not directly mutate the resting book.
    - Clear removes all resting orders for the instrument.

    Raw CME MDP 3.0 packet/SBE decoding is a separate evidence layer.

    Databento's normalized MBO schema does not expose CME's native PriorityID. EdgeForge
    therefore maintains a deterministic stream-order priority surrogate. It preserves
    priority on same-price size reductions, and assigns new priority after price change
    or size increase. It must never be described as native CME PriorityID evidence.
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
        resting: dict[tuple[int, str], _RestingOrder] = {}

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
            price = _optional_int(row, "price")
            size = _optional_int(row, "size")
            sequence = _optional_int(row, "sequence")
            flags_value = _optional_int(row, "flags")
            publisher_id = _optional_int(row, "publisher_id")
            channel_id = _optional_int(row, "channel_id")

            order_id: str | None = None if order_id_value == 0 else str(order_id_value)
            priority: int | None = None
            extra_flags: list[str] = []
            order_key = None if order_id is None else (instrument_id, order_id)

            if action is Action.CLEAR:
                side = None
                order_id = None
                price = None
                size = None
                priority_clock[instrument_id] = 0
                for key in [key for key in resting if key[0] == instrument_id]:
                    del resting[key]

            elif action is Action.ADD:
                if order_key is None or price is None or size is None:
                    raise ValueError("Databento Add requires order_id, price and size")
                next_priority = priority_clock.get(instrument_id, 0) + 1
                priority_clock[instrument_id] = next_priority
                priority = next_priority
                resting[order_key] = _RestingOrder(price=price, size=size, priority=priority)

            elif action is Action.CANCEL:
                if order_key is None or size is None:
                    raise ValueError("Databento Cancel requires order_id and size")
                existing = resting.get(order_key)
                if existing is not None:
                    if size > existing.size:
                        raise ValueError("Databento cancel quantity exceeds tracked resting size")
                    existing.size -= size
                    priority = existing.priority
                    if existing.size == 0:
                        del resting[order_key]

            elif action is Action.MODIFY:
                if order_key is None or price is None or size is None:
                    raise ValueError("Databento Modify requires order_id, price and size")
                existing = resting.get(order_key)
                if existing is None:
                    # Matches Databento's documented reducer example: a missing Modify
                    # is treated as a new resting order rather than silently discarded.
                    next_priority = priority_clock.get(instrument_id, 0) + 1
                    priority_clock[instrument_id] = next_priority
                    priority = next_priority
                    resting[order_key] = _RestingOrder(price=price, size=size, priority=priority)
                    action = Action.ADD
                    extra_flags.append("normalized_from=modify_missing")
                else:
                    loses_priority = existing.price != price or existing.size < size
                    if loses_priority:
                        next_priority = priority_clock.get(instrument_id, 0) + 1
                        priority_clock[instrument_id] = next_priority
                        priority = next_priority
                    else:
                        priority = existing.priority
                    existing.price = price
                    existing.size = size

            elif action is Action.TRADE:
                order_id = None

            elif action is Action.FILL:
                # Databento explicitly documents Fill as informational. The associated
                # resting-order quantity change is represented by a Cancel record.
                priority = resting[order_key].priority if order_key in resting else None

            flag_items: list[str] = []
            if flags_value is not None:
                flag_items.append(f"databento_flags={flags_value}")
            flag_items.extend(extra_flags)
            if priority is not None:
                flag_items.append("priority=stream_order_surrogate")

            stream_parts = []
            if publisher_id is not None:
                stream_parts.append(f"publisher={publisher_id}")
            if channel_id is not None:
                stream_parts.append(f"channel={channel_id}")
            stream_id = ":".join(stream_parts) if stream_parts else None

            yield MarketEvent(
                venue=self._venue,
                instrument=self._resolve(instrument_id),
                event_ts=_ns_to_datetime(_required(row, "ts_event")),
                recv_ts=_ns_to_datetime(row["ts_recv"]) if row.get("ts_recv") not in (None, "") else None,
                sequence=sequence,
                stream_id=stream_id,
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
