from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Side(StrEnum):
    BID = "bid"
    ASK = "ask"


class Action(StrEnum):
    ADD = "add"
    MODIFY = "modify"
    CANCEL = "cancel"
    EXECUTE = "execute"
    DELETE = "delete"
    CLEAR = "clear"
    SNAPSHOT = "snapshot"
    UPSERT_LEVEL = "upsert_level"
    DELETE_LEVEL = "delete_level"
    TRADE = "trade"


class MarketEvent(BaseModel):
    """Canonical market event used by every EdgeForge adapter.

    Price is an integer in adapter-defined fixed-point units.  `price_scale`
    records the denominator needed to recover the decimal price.
    """

    model_config = ConfigDict(frozen=True)

    venue: str
    instrument: str
    event_ts: datetime
    recv_ts: datetime | None = None
    sequence: int | None = Field(default=None, ge=0)
    action: Action
    side: Side | None = None
    price: int | None = None
    price_scale: int = Field(default=10_000, gt=0)
    size: int | None = Field(default=None, ge=0)
    order_id: str | None = None
    priority: int | None = Field(default=None, ge=0)
    trade_id: str | None = None
    level: int | None = Field(default=None, ge=0)
    flags: tuple[str, ...] = ()
    source: str | None = None

    @model_validator(mode="after")
    def validate_event(self) -> "MarketEvent":
        if self.event_ts.tzinfo is None:
            raise ValueError("event_ts must be timezone-aware")
        if self.recv_ts is not None and self.recv_ts.tzinfo is None:
            raise ValueError("recv_ts must be timezone-aware")
        if self.action in {Action.ADD, Action.MODIFY}:
            if self.order_id is None or self.side is None or self.price is None or self.size is None:
                raise ValueError("ADD/MODIFY require order_id, side, price, and size")
        if self.action in {Action.UPSERT_LEVEL, Action.DELETE_LEVEL}:
            if self.side is None or self.price is None:
                raise ValueError("L2 level updates require side and price")
        if self.action is Action.TRADE and (self.price is None or self.size is None):
            raise ValueError("TRADE requires price and size")
        return self

    @property
    def price_decimal(self) -> float | None:
        return None if self.price is None else self.price / self.price_scale

    @classmethod
    def utc_now(cls) -> datetime:
        return datetime.now(timezone.utc)
