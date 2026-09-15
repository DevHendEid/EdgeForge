from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from edgeforge.core.models import Action, MarketEvent, Side


@dataclass(slots=True)
class Order:
    order_id: str
    side: Side
    price: int
    size: int
    priority: int | None = None


class L3OrderBook:
    """Deterministic visible order-by-order book for replay and validation."""

    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}
        self.last_sequence: int | None = None

    def apply(self, event: MarketEvent) -> None:
        self._check_sequence(event)
        match event.action:
            case Action.CLEAR | Action.SNAPSHOT:
                self.orders.clear()
            case Action.ADD:
                self._add(event)
            case Action.MODIFY:
                self._modify(event)
            case Action.CANCEL | Action.EXECUTE:
                self._reduce(event)
            case Action.DELETE:
                self._delete(event)
            case Action.TRADE | Action.FILL:
                # Normalized trade/fill records can be informational. Any resting
                # quantity change must arrive as a source-specific lifecycle event
                # such as CANCEL/EXECUTE rather than being inferred here.
                return
            case _:
                raise ValueError(f"unsupported L3 action: {event.action}")
        self.assert_invariants()

    def _check_sequence(self, event: MarketEvent) -> None:
        if event.sequence is None:
            return
        if self.last_sequence is not None and event.sequence <= self.last_sequence:
            raise ValueError(f"non-monotonic sequence: {event.sequence} <= {self.last_sequence}")
        self.last_sequence = event.sequence

    def _add(self, event: MarketEvent) -> None:
        assert event.order_id and event.side and event.price is not None and event.size is not None
        if event.size <= 0:
            raise ValueError("ADD requires positive size")
        if event.order_id in self.orders:
            raise ValueError(f"duplicate order_id: {event.order_id}")
        self.orders[event.order_id] = Order(event.order_id, event.side, event.price, event.size, event.priority)

    def _modify(self, event: MarketEvent) -> None:
        assert event.order_id and event.side and event.price is not None and event.size is not None
        if event.size <= 0:
            raise ValueError("MODIFY requires positive size")
        if event.order_id not in self.orders:
            raise KeyError(f"cannot modify missing order: {event.order_id}")
        self.orders[event.order_id] = Order(event.order_id, event.side, event.price, event.size, event.priority)

    def _reduce(self, event: MarketEvent) -> None:
        if event.order_id is None or event.size is None or event.size <= 0:
            raise ValueError("CANCEL/EXECUTE require order_id and positive size")
        order = self.orders.get(event.order_id)
        if order is None:
            raise KeyError(f"cannot reduce missing order: {event.order_id}")
        if event.size > order.size:
            raise ValueError("event size exceeds resting order size")
        order.size -= event.size
        if order.size == 0:
            del self.orders[event.order_id]

    def _delete(self, event: MarketEvent) -> None:
        if event.order_id is None:
            raise ValueError("DELETE requires order_id")
        if self.orders.pop(event.order_id, None) is None:
            raise KeyError(f"cannot delete missing order: {event.order_id}")

    def depth(self, side: Side) -> list[tuple[int, int]]:
        aggregated: dict[int, int] = {}
        for order in self.orders.values():
            if order.side is side:
                aggregated[order.price] = aggregated.get(order.price, 0) + order.size
        return sorted(aggregated.items(), key=lambda x: x[0], reverse=side is Side.BID)

    def queue(self, side: Side, price: int) -> list[Order]:
        rows = [o for o in self.orders.values() if o.side is side and o.price == price]
        return sorted(rows, key=lambda o: (o.priority is None, o.priority or 0, o.order_id))

    def best_bid(self) -> tuple[int, int] | None:
        levels = self.depth(Side.BID)
        return levels[0] if levels else None

    def best_ask(self) -> tuple[int, int] | None:
        levels = self.depth(Side.ASK)
        return levels[0] if levels else None

    def state_hash(self) -> str:
        payload = "|".join(
            f"{o.order_id}:{o.side}:{o.price}:{o.size}:{o.priority}"
            for o in sorted(self.orders.values(), key=lambda x: x.order_id)
        )
        return sha256(payload.encode()).hexdigest()

    def assert_invariants(self) -> None:
        if any(order.size <= 0 for order in self.orders.values()):
            raise AssertionError("resting orders must have positive size")
        bid = self.best_bid()
        ask = self.best_ask()
        if bid and ask and bid[0] > ask[0]:
            raise AssertionError("crossed book")
