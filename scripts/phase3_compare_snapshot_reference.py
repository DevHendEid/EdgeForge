from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


Row = tuple[int, str, int, int, int, int]


def _edgeforge_rows(path: Path) -> set[Row]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    securities = payload.get("securities", {})
    rows: set[Row] = set()
    for security_id, details in securities.items():
        for level in details.get("levels", []):
            rows.add(
                (
                    int(security_id),
                    str(level["side"]),
                    int(level["level"]),
                    int(level["price"]),
                    int(level["size"]),
                    int(level["num_orders"]),
                )
            )
    return rows


def _reference_rows(path: Path) -> set[Row]:
    rows: set[Row] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.add(
                (
                    int(row["security_id"]),
                    row["side"],
                    int(row["level"]),
                    int(row["price"]),
                    int(row["size"]),
                    int(row["num_orders"]),
                )
            )
    return rows


def _serialize(rows: set[Row]) -> list[dict[str, Any]]:
    return [
        {
            "security_id": row[0],
            "side": row[1],
            "level": row[2],
            "price": row[3],
            "size": row[4],
            "num_orders": row[5],
        }
        for row in sorted(rows)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare EdgeForge CME snapshots to reference output")
    parser.add_argument("edgeforge_json", type=Path)
    parser.add_argument("reference_csv", type=Path)
    parser.add_argument("--report", type=Path, default=Path("phase3_differential_report.json"))
    args = parser.parse_args()

    edgeforge = _edgeforge_rows(args.edgeforge_json)
    reference = _reference_rows(args.reference_csv)
    only_edgeforge = edgeforge - reference
    only_reference = reference - edgeforge
    report = {
        "edgeforge_rows": len(edgeforge),
        "reference_rows": len(reference),
        "unexplained_divergence_count": len(only_edgeforge) + len(only_reference),
        "only_edgeforge": _serialize(only_edgeforge),
        "only_reference": _serialize(only_reference),
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["unexplained_divergence_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
