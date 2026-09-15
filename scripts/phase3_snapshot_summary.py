from __future__ import annotations

import argparse
import json
from pathlib import Path

from edgeforge.data.adapters.cme_pcap_snapshot import SnapshotLevel, iter_snapshot_messages


LevelKey = tuple[str, int]


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize CME MDP3 template-52 snapshots from PCAP")
    parser.add_argument("pcap", type=Path)
    parser.add_argument("--output", type=Path, default=Path("phase3_snapshot_summary.json"))
    args = parser.parse_args()

    count = 0
    latest_meta: dict[int, dict[str, int]] = {}
    levels: dict[int, dict[LevelKey, tuple[int, SnapshotLevel]]] = {}

    for snapshot in iter_snapshot_messages(args.pcap):
        count += 1
        security_levels = levels.setdefault(snapshot.security_id, {})
        for level in snapshot.levels:
            key = (level.side.value, level.level)
            current = security_levels.get(key)
            if current is None or snapshot.sending_time_ns >= current[0]:
                security_levels[key] = (snapshot.sending_time_ns, level)

        current_meta = latest_meta.get(snapshot.security_id)
        if current_meta is None or snapshot.sending_time_ns >= current_meta["sending_time_ns"]:
            latest_meta[snapshot.security_id] = {
                "packet_sequence": snapshot.packet_sequence,
                "sending_time_ns": snapshot.sending_time_ns,
                "last_sequence_processed": snapshot.last_sequence_processed,
                "report_sequence": snapshot.report_sequence,
            }

    securities: dict[str, object] = {}
    for security_id in sorted(levels):
        ordered_levels = [
            item[1]
            for _, item in sorted(
                levels[security_id].items(),
                key=lambda entry: (entry[0][0], entry[0][1]),
            )
        ]
        meta = latest_meta[security_id]
        securities[str(security_id)] = {
            **meta,
            "level_count": len(ordered_levels),
            "levels": [
                {
                    "side": level.side.value,
                    "level": level.level,
                    "price": level.price,
                    "size": level.size,
                    "num_orders": level.num_orders,
                }
                for level in ordered_levels
            ],
        }

    payload = {
        "snapshot_messages": count,
        "security_count": len(securities),
        "security_ids": [int(value) for value in sorted(securities, key=int)],
        "securities": securities,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"snapshot_messages={count}")
    print(f"security_count={len(securities)}")
    print("security_ids=" + " ".join(str(value) for value in payload["security_ids"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
