from __future__ import annotations

from edgeforge.book.l3 import L3OrderBook
from edgeforge.core.models import Action, Side
from edgeforge.data.adapters.databento_mbo import DATABENTO_PRICE_SCALE, DatabentoMBOAdapter


def base_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "ts_event": 1_725_000_000_123_456_789,
        "ts_recv": 1_725_000_000_223_456_789,
        "publisher_id": 1,
        "instrument_id": 123,
        "channel_id": 7,
        "action": "A",
        "side": "B",
        "price": 19_500_250_000_000,
        "size": 3,
        "order_id": 991,
        "flags": 0,
        "sequence": 10,
    }
    row.update(updates)
    return row


def test_databento_mbo_maps_core_fields_and_stream_scope() -> None:
    event = next(
        DatabentoMBOAdapter([base_row()], instrument_resolver=lambda _: "NQZ6").read()
    )

    assert event.instrument == "NQZ6"
    assert event.venue == "CME"
    assert event.action is Action.ADD
    assert event.side is Side.BID
    assert event.order_id == "991"
    assert event.price == 19_500_250_000_000
    assert event.price_scale == DATABENTO_PRICE_SCALE
    assert event.size == 3
    assert event.sequence == 10
    assert event.stream_id == "publisher=1:channel=7"
    assert event.priority == 1
    assert event.event_ts.tzinfo is not None
    assert event.recv_ts is not None and event.recv_ts.tzinfo is not None


def test_fill_and_trade_are_informational_cancel_reduces_book() -> None:
    rows = [
        base_row(action="A", order_id=100, size=5, sequence=1),
        base_row(action="T", side="B", order_id=0, size=2, sequence=2),
        base_row(action="F", side="A", order_id=100, size=2, sequence=2),
        base_row(action="C", side="A", order_id=100, size=2, sequence=2),
    ]
    events = list(DatabentoMBOAdapter(rows).read())
    assert [event.action for event in events] == [
        Action.ADD,
        Action.TRADE,
        Action.FILL,
        Action.CANCEL,
    ]
    assert events[1].order_id is None

    book = L3OrderBook()
    for event in events:
        book.apply(event.model_copy(update={"sequence": None}))
    assert book.orders["100"].size == 3


def test_modify_preserves_or_loses_priority_by_documented_rule() -> None:
    rows = [
        base_row(action="A", order_id=100, size=5, price=100, sequence=1),
        # Same price, smaller size: retains priority.
        base_row(action="M", order_id=100, size=4, price=100, sequence=2),
        # Size increase: loses priority.
        base_row(action="M", order_id=100, size=6, price=100, sequence=3),
        # Price change: loses priority again.
        base_row(action="M", order_id=100, size=6, price=101, sequence=4),
    ]
    events = list(DatabentoMBOAdapter(rows).read())
    assert [event.priority for event in events] == [1, 1, 2, 3]


def test_missing_modify_is_normalized_to_add() -> None:
    event = next(
        DatabentoMBOAdapter([base_row(action="M", order_id=500, sequence=1)]).read()
    )
    assert event.action is Action.ADD
    assert "normalized_from=modify_missing" in event.flags


def test_clear_removes_book_specific_fields() -> None:
    event = next(DatabentoMBOAdapter([base_row(action="R", side="N", order_id=0)]).read())
    assert event.action is Action.CLEAR
    assert event.side is None
    assert event.order_id is None
    assert event.price is None
    assert event.size is None


def test_unknown_action_fails_closed() -> None:
    try:
        list(DatabentoMBOAdapter([base_row(action="?")]).read())
    except ValueError as exc:
        assert "unknown Databento MBO action" in str(exc)
    else:
        raise AssertionError("unknown MBO action must fail closed")
