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
        # CSV flat files render prices in decimal units; canonical MBO uses 1e-9.
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
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed HTTPS URL by default
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
    # The downloaded prefix can begin/end mid-channel. Replay lifecycle must remain
    # internally valid, while packet-gap claims are reported rather than used as a gate.
    validator = CMEReplayValidator(fail_on_gap=False)
    event_count = 0
    for event in adapter.read():
        validator.apply(event)
        event_count += 1

    if action_counts["A"] == 0:
        raise RuntimeError("official public MBO sample prefix contains no Add records")
    if not validator.instruments:
        raise RuntimeError("official public MBO sample produced no instrument books")
    total_orders = sum(
        validator.checkpoint(instrument).order_count for instrument in validator.instruments
    )
    if total_orders == 0:
        raise RuntimeError("official public MBO replay ended with no resting orders")

    payload = {
        "source_url": args.url,
        "rows_downloaded": len(decoded_rows),
        "canonical_events": event_count,
        "action_counts": dict(sorted(action_counts.items())),
        "instrument_count": len(validator.instruments),
        "stream_count": len(validator.streams),
        "total_resting_orders": total_orders,
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
