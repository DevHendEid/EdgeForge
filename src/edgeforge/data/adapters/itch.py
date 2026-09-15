from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Iterator, Mapping, Any

from edgeforge.core.models import Action, MarketEvent, Side


class ItchRecordAdapter:
    """Adapter for decoded Nasdaq ITCH records.

    Binary decoding is deliberately isolated from canonical normalization.  Any
    decoder can feed dict-like records with ITCH message fields into this class.
    Supported types: A/F add, E/C execute, X cancel, D delete, U replace.
    """

    def __init__(self, records: Iterable[Mapping[str, Any]], instrument: str, venue: str = "XNAS") -> None:
        self.records = records; self.instrument = instrument; self.venue = venue

    @staticmethod
    def _ts(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return datetime.fromtimestamp(float(value), tz=timezone.utc)

    def __iter__(self) -> Iterator[MarketEvent]:
        for i, r in enumerate(self.records, start=1):
            typ = str(r["type"]); ts = self._ts(r["timestamp"]); seq = int(r.get("sequence", i))
            side = Side.BID if str(r.get("side", "B")).upper().startswith("B") else Side.ASK
            price = int(r.get("price", 0)); size = int(r.get("size", 0)); oid = str(r.get("order_id", "")) or None
            base = dict(venue=self.venue, instrument=self.instrument, event_ts=ts, sequence=seq,
                        side=side, price=price, size=size, source="nasdaq-itch")
            if typ in {"A", "F"}:
                yield MarketEvent(action=Action.ADD, order_id=oid, **base)
            elif typ in {"E", "C"}:
                yield MarketEvent(action=Action.EXECUTE, order_id=oid, **base)
            elif typ == "X":
                yield MarketEvent(action=Action.CANCEL, order_id=oid, **base)
            elif typ == "D":
                yield MarketEvent(action=Action.DELETE, order_id=oid, **base)
            elif typ == "U":
                old_id = str(r["old_order_id"])
                yield MarketEvent(action=Action.DELETE, order_id=old_id, **base)
                yield MarketEvent(action=Action.ADD, order_id=oid, **base)
