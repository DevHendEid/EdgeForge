from __future__ import annotations

from edgeforge.core.models import Action, MarketEvent, Side


class L2OrderBook:
    """Price-level book for snapshot + delta feeds (crypto/MBP style)."""

    def __init__(self) -> None:
        self.bids: dict[int, int] = {}
        self.asks: dict[int, int] = {}
        self.last_sequence: int | None = None
        self.initialized = False

    def apply(self, event: MarketEvent) -> None:
        if event.sequence is not None:
            if self.last_sequence is not None and event.sequence < self.last_sequence:
                raise ValueError("regressing L2 sequence")
            self.last_sequence = event.sequence
        if event.action in {Action.CLEAR, Action.SNAPSHOT}:
            self.bids.clear(); self.asks.clear(); self.initialized = True
            return
        if event.action not in {Action.UPSERT_LEVEL, Action.DELETE_LEVEL}:
            return
        assert event.side is not None and event.price is not None
        book = self.bids if event.side is Side.BID else self.asks
        size = event.size or 0
        if event.action is Action.DELETE_LEVEL or size == 0:
            book.pop(event.price, None)
        else:
            book[event.price] = size
        self.assert_invariants()

    def depth(self, side: Side) -> list[tuple[int, int]]:
        src = self.bids if side is Side.BID else self.asks
        return sorted(src.items(), reverse=side is Side.BID)

    def best_bid(self) -> tuple[int, int] | None:
        d = self.depth(Side.BID); return d[0] if d else None

    def best_ask(self) -> tuple[int, int] | None:
        d = self.depth(Side.ASK); return d[0] if d else None

    def assert_invariants(self) -> None:
        if any(v <= 0 for v in (*self.bids.values(), *self.asks.values())):
            raise AssertionError("L2 level sizes must be positive")
        bid, ask = self.best_bid(), self.best_ask()
        if bid and ask and bid[0] > ask[0]:
            raise AssertionError("crossed L2 book")
