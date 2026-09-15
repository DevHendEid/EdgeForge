from datetime import datetime, timezone

from edgeforge.book.l2 import L2OrderBook
from edgeforge.core.models import Action, MarketEvent, Side


def ev(seq: int, side: Side, price: int, size: int) -> MarketEvent:
    return MarketEvent(venue="X", instrument="Y", event_ts=datetime.now(timezone.utc), sequence=seq,
                       action=Action.UPSERT_LEVEL if size else Action.DELETE_LEVEL,
                       side=side, price=price, size=size)


def test_l2_upsert_delete() -> None:
    b = L2OrderBook(); b.apply(ev(1, Side.BID, 100, 4)); b.apply(ev(2, Side.ASK, 101, 5))
    assert b.best_bid() == (100, 4); assert b.best_ask() == (101, 5)
    b.apply(ev(3, Side.BID, 100, 0)); assert b.best_bid() is None
