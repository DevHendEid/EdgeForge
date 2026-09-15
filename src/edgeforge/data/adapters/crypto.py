from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Iterator, Mapping

from edgeforge.core.models import Action, MarketEvent, Side


def _fixed(value: str | float | int, scale: int) -> int:
    return int(Decimal(str(value)) * scale)


def _ts_ms(value: Any) -> datetime:
    return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)


class BinanceDepthAdapter:
    """Normalize Binance-style depth update messages (bids `b`, asks `a`)."""
    def __init__(self, messages: Iterable[Mapping[str, Any]], instrument: str, scale: int = 100_000_000) -> None:
        self.messages = messages; self.instrument = instrument; self.scale = scale

    def __iter__(self) -> Iterator[MarketEvent]:
        for msg in self.messages:
            seq = int(msg.get("u", 0)); ts = _ts_ms(msg.get("E", msg.get("T", 0)))
            for key, side in (("b", Side.BID), ("a", Side.ASK)):
                for price, qty in msg.get(key, []):
                    size = _fixed(qty, self.scale); action = Action.DELETE_LEVEL if size == 0 else Action.UPSERT_LEVEL
                    yield MarketEvent(venue="BINANCE", instrument=self.instrument, event_ts=ts, sequence=seq,
                                      action=action, side=side, price=_fixed(price, self.scale), size=size,
                                      price_scale=self.scale, source="binance-depth")


class OkxBooksAdapter:
    """Normalize OKX books/books-l2-tbt payloads."""
    def __init__(self, payloads: Iterable[Mapping[str, Any]], instrument: str, scale: int = 100_000_000) -> None:
        self.payloads = payloads; self.instrument = instrument; self.scale = scale

    def __iter__(self) -> Iterator[MarketEvent]:
        seq = 0
        for payload in self.payloads:
            action_name = str(payload.get("action", "update"))
            for block in payload.get("data", []):
                ts = _ts_ms(block["ts"])
                if action_name == "snapshot":
                    seq += 1
                    yield MarketEvent(venue="OKX", instrument=self.instrument, event_ts=ts, sequence=seq,
                                      action=Action.SNAPSHOT, source="okx-books")
                for key, side in (("bids", Side.BID), ("asks", Side.ASK)):
                    for row in block.get(key, []):
                        seq += 1; price, qty = row[0], row[1]; size = _fixed(qty, self.scale)
                        yield MarketEvent(venue="OKX", instrument=self.instrument, event_ts=ts, sequence=seq,
                                          action=Action.DELETE_LEVEL if size == 0 else Action.UPSERT_LEVEL,
                                          side=side, price=_fixed(price, self.scale), size=size,
                                          price_scale=self.scale, source="okx-books")

class HyperliquidL2Adapter:
    """Normalize Hyperliquid L2 book snapshots (`levels`: [bids, asks])."""
    def __init__(self, payloads: Iterable[Mapping[str, Any]], instrument: str, scale: int = 100_000_000) -> None:
        self.payloads = payloads; self.instrument = instrument; self.scale = scale

    def __iter__(self) -> Iterator[MarketEvent]:
        seq = 0
        for payload in self.payloads:
            data = payload.get("data", payload)
            ts = _ts_ms(data.get("time", data.get("ts", 0)))
            levels = data.get("levels", [[], []])
            seq += 1
            yield MarketEvent(venue="HYPERLIQUID", instrument=self.instrument, event_ts=ts, sequence=seq,
                              action=Action.SNAPSHOT, source="hyperliquid-l2")
            for rows, side in zip(levels, (Side.BID, Side.ASK), strict=False):
                for row in rows:
                    seq += 1
                    price = row.get("px", row.get("price")); qty = row.get("sz", row.get("size"))
                    size = _fixed(qty, self.scale)
                    yield MarketEvent(venue="HYPERLIQUID", instrument=self.instrument, event_ts=ts, sequence=seq,
                                      action=Action.UPSERT_LEVEL, side=side, price=_fixed(price, self.scale), size=size,
                                      price_scale=self.scale, source="hyperliquid-l2")


class CoinbaseL2Adapter:
    """Normalize Coinbase Advanced Trade `l2_data` snapshot/update envelopes."""
    def __init__(self, payloads: Iterable[Mapping[str, Any]], instrument: str, scale: int = 100_000_000) -> None:
        self.payloads = payloads; self.instrument = instrument; self.scale = scale

    def __iter__(self) -> Iterator[MarketEvent]:
        seq = 0
        for payload in self.payloads:
            events = payload.get("events", [])
            for event in events:
                typ = str(event.get("type", "update"))
                if typ == "snapshot":
                    seq += 1
                    ts = datetime.now(timezone.utc)
                    yield MarketEvent(venue="COINBASE", instrument=self.instrument, event_ts=ts, sequence=seq,
                                      action=Action.SNAPSHOT, source="coinbase-l2")
                for upd in event.get("updates", []):
                    seq += 1
                    raw_ts = upd.get("event_time") or payload.get("timestamp")
                    if isinstance(raw_ts, str) and raw_ts:
                        ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                    else:
                        ts = datetime.now(timezone.utc)
                    side = Side.BID if str(upd.get("side", "bid")).lower() in {"bid", "buy"} else Side.ASK
                    price = upd.get("price_level", upd.get("price")); qty = upd.get("new_quantity", upd.get("size", "0"))
                    size = _fixed(qty, self.scale)
                    yield MarketEvent(venue="COINBASE", instrument=self.instrument, event_ts=ts, sequence=seq,
                                      action=Action.DELETE_LEVEL if size == 0 else Action.UPSERT_LEVEL,
                                      side=side, price=_fixed(price, self.scale), size=size,
                                      price_scale=self.scale, source="coinbase-l2")
