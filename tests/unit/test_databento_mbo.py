from __future__ import annotations

from edgeforge.core.models import Action, Side
from edgeforge.data.adapters.databento_mbo import DATABENTO_PRICE_SCALE, DatabentoMBOAdapter


def test_databento_mbo_maps_core_fields() -> None:
    rows = [
        {
            "ts_event": 1_725_000_000_123_456_789,
            "ts_recv": 1_725_000_000_223_456_789,
            "instrument_id": 123,
            "action": "A",
            "side": "B",
            "price": 19_500_250_000_000,
            "size": 3,
            "order_id": 991,
            "flags": 0,
            "sequence": 10,
        }
    ]
    event = next(DatabentoMBOAdapter(rows, instrument_resolver=lambda _: "NQZ6").read())

    assert event.instrument == "NQZ6"
    assert event.venue == "CME"
    assert event.action is Action.ADD
    assert event.side is Side.BID
    assert event.order_id == "991"
    assert event.price == 19_500_250_000_000
    assert event.price_scale == DATABENTO_PRICE_SCALE
    assert event.size == 3
    assert event.sequence == 10
    assert event.event_ts.tzinfo is not None
    assert event.recv_ts is not None and event.recv_ts.tzinfo is not None


def test_fill_reduces_resting_order_and_trade_is_informational() -> None:
    rows = [
        {
            "ts_event": 1_725_000_000_000_000_000,
            "instrument_id": 1,
            "action": "F",
            "side": "A",
            "price": 20_000_000_000_000,
            "size": 2,
            "order_id": 100,
            "sequence": 1,
        },
        {
            "ts_event": 1_725_000_000_000_000_001,
            "instrument_id": 1,
            "action": "T",
            "side": "B",
            "price": 20_000_000_000_000,
            "size": 2,
            "order_id": 0,
            "sequence": 1,
        },
    ]
    events = list(DatabentoMBOAdapter(rows).read())
    assert events[0].action is Action.EXECUTE
    assert events[0].order_id == "100"
    assert events[1].action is Action.TRADE
    assert events[1].order_id is None


def test_clear_removes_book_specific_fields() -> None:
    row = {
        "ts_event": 1_725_000_000_000_000_000,
        "instrument_id": 1,
        "action": "R",
        "side": "N",
        "price": 0,
        "size": 0,
        "order_id": 0,
        "sequence": 7,
    }
    event = next(DatabentoMBOAdapter([row]).read())
    assert event.action is Action.CLEAR
    assert event.side is None
    assert event.order_id is None
    assert event.price is None
    assert event.size is None


def test_unknown_action_fails_closed() -> None:
    row = {
        "ts_event": 1_725_000_000_000_000_000,
        "instrument_id": 1,
        "action": "?",
    }
    try:
        list(DatabentoMBOAdapter([row]).read())
    except ValueError as exc:
        assert "unknown Databento MBO action" in str(exc)
    else:
        raise AssertionError("unknown MBO action must fail closed")
