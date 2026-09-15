from datetime import datetime, timezone

import pytest

from edgeforge.book.l3 import L3OrderBook
from edgeforge.core.models import Action, MarketEvent, Side

TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


def event(action: Action, oid: str, side: Side | None = None, price: int | None = None, size: int | None = None) -> MarketEvent:
    return MarketEvent(venue="TEST", instrument="X", event_ts=TS, action=action, side=side, price=price, size=size, order_id=oid)


def test_add_execute_and_depth() -> None:
    book = L3OrderBook()
    book.apply(event(Action.ADD, "1", Side.BID, 100, 5))
    book.apply(event(Action.ADD, "2", Side.BID, 100, 3))
    assert book.best_bid() == (100, 8)
    book.apply(event(Action.EXECUTE, "1", size=2))
    assert book.best_bid() == (100, 6)
    book.assert_invariants()


def test_overfill_fails_closed() -> None:
    book = L3OrderBook()
    book.apply(event(Action.ADD, "1", Side.ASK, 101, 1))
    with pytest.raises(ValueError):
        book.apply(event(Action.EXECUTE, "1", size=2))
