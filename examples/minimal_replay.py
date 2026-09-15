from datetime import datetime, timezone

from edgeforge.book.l3 import L3OrderBook
from edgeforge.core.models import Action, MarketEvent, Side

book = L3OrderBook()
book.apply(MarketEvent(
    venue="DEMO",
    instrument="EDGE",
    event_ts=datetime.now(timezone.utc),
    action=Action.ADD,
    side=Side.BID,
    price=100_000,
    size=5,
    order_id="demo-1",
))
print(book.best_bid())
