from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from edgeforge.data.adapters.databento_mbo import DatabentoMBOAdapter
from edgeforge.validation.cme import CMEReplayValidator


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            rows.append(value)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize decoded Databento CME MBO JSONL and validate deterministic replay"
    )
    parser.add_argument("input", type=Path, help="decoded Databento MBO JSONL")
    parser.add_argument("--symbol-map", type=Path, help="JSON object mapping instrument_id to symbol")
    parser.add_argument("--output", type=Path, default=Path("phase3_checkpoints.json"))
    parser.add_argument("--allow-gaps", action="store_true")
    args = parser.parse_args()

    symbol_map: dict[str, str] = {}
    if args.symbol_map:
        raw = json.loads(args.symbol_map.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("symbol map must be a JSON object")
        symbol_map = {str(key): str(value) for key, value in raw.items()}

    rows = _read_jsonl(args.input)
    resolver = lambda instrument_id: symbol_map.get(str(instrument_id), str(instrument_id))
    adapter = DatabentoMBOAdapter(rows, instrument_resolver=resolver)
    validator = CMEReplayValidator(fail_on_gap=not args.allow_gaps)

    for event in adapter.read():
        validator.apply(event)

    payload: dict[str, Any] = {}
    for instrument in sorted(validator._states):  # intentionally report every touched instrument
        state = validator.state(instrument)
        payload[instrument] = {
            "checkpoint": asdict(validator.checkpoint(instrument)),
            "sequence": asdict(state.sequence),
            "status": state.status.value,
        }

    args.output.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Validated {len(rows)} decoded MBO rows across {len(payload)} instruments")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
