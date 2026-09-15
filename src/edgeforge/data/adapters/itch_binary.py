from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO, Iterator

from edgeforge.core.models import Action, MarketEvent, Side


def _u48(raw: bytes) -> int:
    return int.from_bytes(raw, "big", signed=False)


@dataclass(frozen=True, slots=True)
class ItchHeader:
    stock_locate: int
    tracking_number: int
    timestamp_ns: int


class Itch5Decoder:
    """Minimal Nasdaq ITCH 5.0 binary decoder for visible order lifecycle messages.

    Supports A/F/E/C/X/D/U. Input may be a raw concatenated message stream or
    SoupBinTCP-style records when `length_prefixed=True` (2-byte big-endian length).
    """

    LENGTHS = {"A": 36, "F": 40, "E": 31, "C": 36, "X": 23, "D": 19, "U": 35}

    def __init__(self, stream: BinaryIO, *, length_prefixed: bool = True) -> None:
        self.stream = stream; self.length_prefixed = length_prefixed

    @classmethod
    def from_path(cls, path: str | Path, *, length_prefixed: bool = True) -> "Itch5Decoder":
        return cls(Path(path).open("rb"), length_prefixed=length_prefixed)

    @staticmethod
    def _header(msg: bytes) -> ItchHeader:
        return ItchHeader(struct.unpack_from(">H", msg, 1)[0], struct.unpack_from(">H", msg, 3)[0], _u48(msg[5:11]))

    def __iter__(self) -> Iterator[dict[str, object]]:
        while True:
            if self.length_prefixed:
                pfx = self.stream.read(2)
                if not pfx:
                    return
                if len(pfx) != 2:
                    raise EOFError("truncated ITCH length prefix")
                n = struct.unpack(">H", pfx)[0]
                msg = self.stream.read(n)
                if len(msg) != n:
                    raise EOFError("truncated ITCH message")
            else:
                type_byte = self.stream.read(1)
                if not type_byte:
                    return
                typ = type_byte.decode("ascii")
                n = self.LENGTHS.get(typ)
                if n is None:
                    raise ValueError(f"unsupported unframed ITCH message {typ!r}; framing required to skip unknown types")
                msg = type_byte + self.stream.read(n - 1)
                if len(msg) != n:
                    raise EOFError("truncated ITCH message")
            typ = chr(msg[0])
            if typ not in self.LENGTHS:
                continue
            if len(msg) != self.LENGTHS[typ]:
                raise ValueError(f"unexpected {typ} length {len(msg)}")
            h = self._header(msg)
            base: dict[str, object] = {"type": typ, "timestamp_ns": h.timestamp_ns,
                                      "stock_locate": h.stock_locate, "tracking_number": h.tracking_number}
            if typ in {"A", "F"}:
                base.update(order_id=struct.unpack_from(">Q", msg, 11)[0], side=chr(msg[19]),
                            size=struct.unpack_from(">I", msg, 20)[0],
                            stock=msg[24:32].decode("ascii").strip(),
                            price=struct.unpack_from(">I", msg, 32)[0])
            elif typ == "E":
                base.update(order_id=struct.unpack_from(">Q", msg, 11)[0], size=struct.unpack_from(">I", msg, 19)[0],
                            match_number=struct.unpack_from(">Q", msg, 23)[0])
            elif typ == "C":
                base.update(order_id=struct.unpack_from(">Q", msg, 11)[0], size=struct.unpack_from(">I", msg, 19)[0],
                            match_number=struct.unpack_from(">Q", msg, 23)[0], printable=chr(msg[31]),
                            execution_price=struct.unpack_from(">I", msg, 32)[0])
            elif typ == "X":
                base.update(order_id=struct.unpack_from(">Q", msg, 11)[0], size=struct.unpack_from(">I", msg, 19)[0])
            elif typ == "D":
                base.update(order_id=struct.unpack_from(">Q", msg, 11)[0])
            elif typ == "U":
                base.update(old_order_id=struct.unpack_from(">Q", msg, 11)[0], order_id=struct.unpack_from(">Q", msg, 19)[0],
                            size=struct.unpack_from(">I", msg, 27)[0], price=struct.unpack_from(">I", msg, 31)[0])
            yield base


class ItchBinaryAdapter:
    """Decode ITCH 5.0 and normalize order lifecycle while tracking order metadata."""

    def __init__(self, decoder: Itch5Decoder, trading_date: str, venue: str = "XNAS") -> None:
        self.decoder = decoder; self.venue = venue
        self.base = datetime.fromisoformat(trading_date).replace(tzinfo=timezone.utc)
        self.orders: dict[str, tuple[str, Side, int]] = {}

    def __iter__(self) -> Iterator[MarketEvent]:
        sequence = 0
        for r in self.decoder:
            sequence += 1; typ = str(r["type"]); ts = self.base + timedelta(microseconds=int(r["timestamp_ns"]) / 1000)
            if typ in {"A", "F"}:
                oid = str(r["order_id"]); side = Side.BID if r["side"] == "B" else Side.ASK
                instrument = str(r["stock"]); price = int(r["price"]); size = int(r["size"])
                self.orders[oid] = (instrument, side, price)
                yield MarketEvent(venue=self.venue, instrument=instrument, event_ts=ts, sequence=sequence,
                                  action=Action.ADD, side=side, price=price, size=size, order_id=oid,
                                  source="nasdaq-itch-5.0")
                continue
            if typ == "U":
                old = str(r["old_order_id"]); new = str(r["order_id"])
                meta = self.orders.pop(old, None)
                if meta is None:
                    raise KeyError(f"ITCH replace references unknown order {old}")
                instrument, side, old_price = meta
                yield MarketEvent(venue=self.venue, instrument=instrument, event_ts=ts, sequence=sequence * 2,
                                  action=Action.DELETE, side=side, price=old_price, size=0, order_id=old,
                                  source="nasdaq-itch-5.0")
                price = int(r["price"]); size = int(r["size"]); self.orders[new] = (instrument, side, price)
                yield MarketEvent(venue=self.venue, instrument=instrument, event_ts=ts, sequence=sequence * 2 + 1,
                                  action=Action.ADD, side=side, price=price, size=size, order_id=new,
                                  source="nasdaq-itch-5.0")
                continue
            oid = str(r["order_id"]); meta = self.orders.get(oid)
            if meta is None:
                raise KeyError(f"ITCH event references unknown order {oid}")
            instrument, side, price = meta
            if typ in {"E", "C"}:
                action = Action.EXECUTE; size = int(r["size"])
            elif typ == "X":
                action = Action.CANCEL; size = int(r["size"])
            elif typ == "D":
                action = Action.DELETE; size = 0; self.orders.pop(oid, None)
            else:
                continue
            yield MarketEvent(venue=self.venue, instrument=instrument, event_ts=ts, sequence=sequence,
                              action=action, side=side, price=price, size=size, order_id=oid,
                              trade_id=str(r.get("match_number")) if "match_number" in r else None,
                              source="nasdaq-itch-5.0")
            if action in {Action.EXECUTE, Action.CANCEL}:
                pass
