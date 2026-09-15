from __future__ import annotations

import argparse
import csv
import io
import json
import urllib.request
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator

from edgeforge.data.adapters.databento_mbo import DATABENTO_PRICE_SCALE, DatabentoMBOAdapter
from edgeforge.validation.cme import CMEReplayValidator

DEFAULT_URL = (
    "https://hist.databento.com/v0/dataset/sample/download/"
    "glbx.mdp3/mbo?sample_type=futures"
)

OrderState = tuple[str, int, int]


def _timestamp_ns(value: str) -> int:
    text = value.strip()
    if text.isdigit():
        return int(text)
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return int(parsed.timestamp() * 1_000_000_000)


def _price_fixed(value: str) -> int | None:
    text = value.strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        return int(Decimal(text) * DATABENTO_PRICE_SCALE)
    except InvalidOperation as exc:
        raise ValueError(f"invalid price: {value!r}") from exc


def _integer(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return int(text)


def _rows(url: str, limit: int) -> Iterator[dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": "EdgeForge-Phase3/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - user may override URL explicitly
        text = io.TextIOWrapper(response, encoding="utf-8", newline="")
        reader = csv.DictReader(text)
        required = {
            "ts_event",
            "publisher_id",
            "instrument_id",
            "action",
            "side",
            "price",
            "size",
            "channel_id",
            "order_id",
            "flags",
            "sequence",
        }
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"official MBO CSV missing fields: {sorted(missing)}")

        for index, row in enumerate(reader):
            if index >= limit:
                return
            yield {
                "ts_event": _timestamp_ns(row["ts_event"]),
                "ts_recv": _timestamp_ns(row["ts_recv"]) if row.get("ts_recv") else None,
                "publisher_id": _integer(row.get("publisher_id")),
                "instrument_id": int(row["instrument_id"]),
                "action": row["action"],
                "side": row.get("side") or "N",
                "price": _price_fixed(row["price"]),
                "size": _integer(row.get("size")),
                "channel_id": _integer(row.get("channel_id")),
                "order_id": _integer(row.get("order_id")) or 0,
                "flags": _integer(row.get("flags")),
                "sequence": _integer(row.get("sequence")),
            }


def _reference_reducer(rows: list[dict[str, Any]]) -> dict[int, dict[str, OrderState]]:
    """Independent reducer implementing Databento's documented MBO lifecycle.

    This intentionally does not call EdgeForge adapters/books. It is the differential
    oracle for the public normalized sample.
    """

    books: dict[int, dict[str, OrderState]] = {}
    for row in rows:
        instrument_id = int(row["instrument_id"])
        action = str(row["action"])
        order_id_value = int(row.get("order_id", 0) or 0)
        order_id = str(order_id_value) if order_id_value else None
        side_code = str(row.get("side") or "N")
        side = "bid" if side_code == "B" else "ask" if side_code == "A" else "none"
        price = row.get("price")
        size = row.get("size")
        book = books.setdefault(instrument_id, {})

        if action in {"T", "F", "N"}:
            continue
        if action == "R":
            book.clear()
            continue
        if order_id is None:
            raise ValueError(f"reference reducer requires order_id for action={action}")
        if price is None or size is None:
            raise ValueError(f"reference reducer requires price/size for action={action}")
        price = int(price)
        size = int(size)

        if action == "A":
            if order_id in book:
                raise ValueError(f"duplicate order_id in reference reducer: {order_id}")
            book[order_id] = (side, price, size)
        elif action == "C":
            existing = book.get(order_id)
            if existing is None:
                raise KeyError(f"reference cancel missing order: {order_id}")
            existing_side, existing_price, existing_size = existing
            if size > existing_size:
                raise ValueError("reference cancel exceeds resting quantity")
            remaining = existing_size - size
            if remaining == 0:
                del book[order_id]
            else:
                book[order_id] = (existing_side, existing_price, remaining)
        elif action == "M":
            # Databento's documented example treats a missing Modify as Add.
            book[order_id] = (side, price, size)
        else:
            raise ValueError(f"unknown reference action: {action}")
    return books


def _edgeforge_state(validator: CMEReplayValidator) -> dict[int, dict[str, OrderState]]:
    result: dict[int, dict[str, OrderState]] = {}
    for instrument in validator.instruments:
        state: dict[str, OrderState] = {}
        for order_id, order in validator.state(instrument).book.orders.items():
            state[order_id] = (order.side.value, order.price, order.size)
        result[int(instrument)] = state
    return result


def _diff_count(
    left: dict[int, dict[str, OrderState]],
    right: dict[int, dict[str, OrderState]],
) -> tuple[int, list[dict[str, Any]]]:
    divergences: list[dict[str, Any]] = []
    for instrument_id in sorted(set(left) | set(right)):
        left_book = left.get(instrument_id, {})
        right_book = right.get(instrument_id, {})
        for order_id in sorted(set(left_book) | set(right_book)):
            if left_book.get(order_id) != right_book.get(order_id):
                divergences.append(
                    {
                        "instrument_id": instrument_id,
                        "order_id": order_id,
                        "edgeforge": left_book.get(order_id),
                        "reference": right_book.get(order_id),
                    }
                )
    return len(divergences), divergences[:100]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stream and replay a prefix of Databento's official public GLBX.MDP3 MBO sample"
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--limit", type=int, default=20_000)
    parser.add_argument("--output", type=Path, default=Path("phase3_public_mbo_evidence.json"))
    args = parser.parse_args()
    if args.limit < 500:
        raise SystemExit("--limit must be at least 500 for the Phase 3 empirical gate")

    decoded_rows = list(_rows(args.url, args.limit))
    if len(decoded_rows) < 500:
        raise RuntimeError(f"official public sample yielded only {len(decoded_rows)} rows")

    action_counts = Counter(str(row["action"]) for row in decoded_rows)
    adapter = DatabentoMBOAdapter(decoded_rows)
    # A normalized historical sample can interleave/reorder native channel sequence
    # values relative to its exported event ordering. We record gap/regression
    # diagnostics, but reserve fail-closed sequence enforcement for raw stream replay.
    validator = CMEReplayValidator(fail_on_gap=False, fail_on_regression=False)
    event_count = 0
    for event in adapter.read():
        validator.apply(event)
        event_count += 1

    reference = _reference_reducer(decoded_rows)
    edgeforge = _edgeforge_state(validator)
    divergence_count, divergence_sample = _diff_count(edgeforge, reference)

    if action_counts["A"] == 0:
        raise RuntimeError("official public MBO sample prefix contains no Add records")
    if not validator.instruments:
        raise RuntimeError("official public MBO sample produced no instrument books")
    total_orders = sum(
        validator.checkpoint(instrument).order_count for instrument in validator.instruments
    )
    if total_orders == 0:
        raise RuntimeError("official public MBO replay ended with no resting orders")
    if divergence_count:
        raise RuntimeError(
            f"EdgeForge diverged from independent documented MBO reducer: {divergence_count} orders"
        )

    payload = {
        "source_url": args.url,
        "rows_downloaded": len(decoded_rows),
        "canonical_events": event_count,
        "action_counts": dict(sorted(action_counts.items())),
        "instrument_count": len(validator.instruments),
        "stream_count": len(validator.streams),
        "total_resting_orders": total_orders,
        "unexplained_divergence_count": divergence_count,
        "divergence_sample": divergence_sample,
        "streams": {
            stream_id: asdict(validator.stream_diagnostics(stream_id))
            for stream_id in validator.streams
        },
        "sample_checkpoints": {
            instrument: asdict(validator.checkpoint(instrument))
            for instrument in validator.instruments[:20]
        },
    }
    args.output.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
