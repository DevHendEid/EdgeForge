from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from edgeforge.core.models import Action, MarketEvent, Side
from edgeforge.validation.cme import CMEReplayValidator


def _events(count: int) -> list[MarketEvent]:
    events: list[MarketEvent] = []
    sequence = 1
    for index in range(count):
        order_id = str(index + 1)
        side = Side.BID if index % 2 == 0 else Side.ASK
        price = 100_000 if side is Side.BID else 100_001
        events.append(
            MarketEvent(
                venue="CME",
                instrument="BENCH",
                event_ts=datetime(2026, 1, 1, tzinfo=timezone.utc),
                sequence=sequence,
                action=Action.ADD,
                side=side,
                price=price,
                size=1,
                order_id=order_id,
                priority=index + 1,
            )
        )
        sequence += 1
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark CME L3 replay throughput")
    parser.add_argument("--events", type=int, default=100_000)
    args = parser.parse_args()
    if args.events <= 0:
        raise SystemExit("--events must be positive")

    events = _events(args.events)
    validator = CMEReplayValidator()
    start = time.perf_counter()
    for event in events:
        validator.apply(event)
    elapsed = time.perf_counter() - start
    rate = args.events / elapsed
    checkpoint = validator.checkpoint("BENCH")

    print(f"events={args.events}")
    print(f"elapsed_seconds={elapsed:.6f}")
    print(f"events_per_second={rate:.0f}")
    print(f"state_hash={checkpoint.state_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
