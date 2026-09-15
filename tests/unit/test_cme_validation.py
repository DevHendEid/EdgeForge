from __future__ import annotations

from datetime import datetime, timezone

import pytest

from edgeforge.core.models import Action, MarketEvent, Side
from edgeforge.validation.cme import CMEReplayValidator, TradingStatus, compare_checkpoints


def ev(
    sequence: int,
    action: Action,
    *,
    instrument: str = "NQZ6",
    stream_id: str | None = "publisher=1:channel=0",
    order_id: str | None = None,
    side: Side | None = None,
    price: int | None = None,
    size: int | None = None,
    priority: int | None = None,
) -> MarketEvent:
    return MarketEvent(
        venue="CME",
        instrument=instrument,
        event_ts=datetime(2026, 9, 15, tzinfo=timezone.utc),
        sequence=sequence,
        stream_id=stream_id,
        action=action,
        order_id=order_id,
        side=side,
        price=price,
        size=size,
        priority=priority,
    )


def test_repeated_venue_sequence_is_allowed_for_normalized_records() -> None:
    validator = CMEReplayValidator()
    validator.apply(ev(10, Action.ADD, order_id="1", side=Side.BID, price=100, size=5))
    validator.apply(ev(10, Action.ADD, order_id="2", side=Side.ASK, price=101, size=4))

    diagnostics = validator.stream_diagnostics("publisher=1:channel=0")
    assert diagnostics.repeated_sequence_records == 1
    assert diagnostics.regressions == 0
    assert diagnostics.gaps == 0


def test_sequence_scope_is_stream_not_instrument() -> None:
    validator = CMEReplayValidator()
    validator.apply(ev(10, Action.ADD, instrument="NQZ6", order_id="1", side=Side.BID, price=100, size=5))
    validator.apply(ev(11, Action.ADD, instrument="ESZ6", order_id="2", side=Side.ASK, price=101, size=4))
    validator.apply(ev(12, Action.ADD, instrument="NQZ6", order_id="3", side=Side.BID, price=99, size=2))
    diagnostics = validator.stream_diagnostics("publisher=1:channel=0")
    assert diagnostics.gaps == 0
    assert diagnostics.last_sequence == 12


def test_sequence_without_stream_id_does_not_make_false_gap_claims() -> None:
    validator = CMEReplayValidator()
    validator.apply(ev(10, Action.ADD, stream_id=None, order_id="1", side=Side.BID, price=100, size=5))
    validator.apply(ev(99, Action.ADD, stream_id=None, order_id="2", side=Side.ASK, price=101, size=4))
    assert validator.streams == ()


def test_gap_fails_closed_by_default() -> None:
    validator = CMEReplayValidator()
    validator.apply(ev(10, Action.ADD, order_id="1", side=Side.BID, price=100, size=5))
    with pytest.raises(ValueError, match="sequence gap"):
        validator.apply(ev(12, Action.ADD, order_id="2", side=Side.ASK, price=101, size=4))


def test_regression_fails_closed() -> None:
    validator = CMEReplayValidator(fail_on_gap=False)
    validator.apply(ev(10, Action.ADD, order_id="1", side=Side.BID, price=100, size=5))
    with pytest.raises(ValueError, match="sequence regression"):
        validator.apply(ev(9, Action.ADD, order_id="2", side=Side.ASK, price=101, size=4))


def test_halted_book_rejects_mutating_updates_but_allows_clear_and_fill() -> None:
    validator = CMEReplayValidator()
    validator.set_status("NQZ6", TradingStatus.HALTED)
    with pytest.raises(ValueError, match="status=halted"):
        validator.apply(ev(1, Action.ADD, order_id="1", side=Side.BID, price=100, size=1))

    validator.apply(ev(2, Action.FILL, order_id="1", side=Side.BID, price=100, size=1))
    validator.apply(ev(3, Action.CLEAR))
    assert validator.checkpoint("NQZ6").order_count == 0


def test_queue_ahead_uses_priority_order() -> None:
    validator = CMEReplayValidator()
    validator.apply(
        ev(1, Action.ADD, order_id="front", side=Side.BID, price=100, size=3, priority=1)
    )
    validator.apply(
        ev(2, Action.ADD, order_id="target", side=Side.BID, price=100, size=2, priority=2)
    )
    ahead = validator.queue_ahead("NQZ6", "target")
    assert ahead.orders_ahead == 1
    assert ahead.quantity_ahead == 3


def test_checkpoint_is_deterministic_and_comparable() -> None:
    left = CMEReplayValidator()
    right = CMEReplayValidator()
    events = [
        ev(1, Action.ADD, order_id="1", side=Side.BID, price=100, size=5),
        ev(2, Action.ADD, order_id="2", side=Side.ASK, price=101, size=4),
    ]
    for event in events:
        left.apply(event)
        right.apply(event)

    a = left.checkpoint("NQZ6")
    b = right.checkpoint("NQZ6")
    assert a == b
    assert compare_checkpoints(a, b) == ()
