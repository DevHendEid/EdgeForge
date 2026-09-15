from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from edgeforge.core.models import Action, MarketEvent, Side


class LobsterMessageAdapter:
    """Parse LOBSTER message CSV into canonical order events.

    LOBSTER event types: 1 submit, 2 partial cancel, 3 delete, 4 visible
    execution, 5 hidden execution. Hidden executions are emitted as trades
    because they do not reference a visible resting order that can be replayed.
    """

    def __init__(self, path: str | Path, instrument: str, trading_date: str, venue: str = "XNAS") -> None:
        self.path = Path(path); self.instrument = instrument; self.venue = venue
        self.base = datetime.fromisoformat(trading_date).replace(tzinfo=timezone.utc)

    def __iter__(self) -> Iterator[MarketEvent]:
        with self.path.open(newline="") as f:
            for seq, row in enumerate(csv.reader(f), start=1):
                if len(row) < 6:
                    continue
                seconds, event_type, order_id, size, price, direction = row[:6]
                ts = self.base + timedelta(seconds=float(seconds))
                typ = int(event_type); side = Side.BID if int(direction) == 1 else Side.ASK
                common = dict(venue=self.venue, instrument=self.instrument, event_ts=ts, sequence=seq,
                              side=side, price=int(price), size=int(size), source="lobster")
                if typ == 1:
                    yield MarketEvent(action=Action.ADD, order_id=order_id, **common)
                elif typ == 2:
                    yield MarketEvent(action=Action.CANCEL, order_id=order_id, **common)
                elif typ == 3:
                    yield MarketEvent(action=Action.DELETE, order_id=order_id, **common)
                elif typ == 4:
                    yield MarketEvent(action=Action.EXECUTE, order_id=order_id, **common)
                elif typ == 5:
                    yield MarketEvent(action=Action.TRADE, trade_id=f"hidden-{seq}", **common)
