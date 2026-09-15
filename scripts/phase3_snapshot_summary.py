from __future__ import annotations

import argparse
import json
from pathlib import Path

from edgeforge.data.adapters.cme_pcap_snapshot import SnapshotMessage, iter_snapshot_messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize CME MDP3 template-52 snapshots from PCAP")
    parser.add_argument("pcap", type=Path)
    parser.add_argument("--output", type=Path, default=Path("phase3_snapshot_summary.json"))
    args = parser.parse_args()

    latest: dict[int, SnapshotMessage] = {}
    count = 0
    for snapshot in iter_snapshot_messages(args.pcap):
        count += 1
        current = latest.get(snapshot.security_id)
        if current is None or snapshot.sending_time_ns >= current.sending_time_ns:
            latest[snapshot.security_id] = snapshot

    securities: dict[str, object] = {}
    for security_id in sorted(latest):
        snapshot = latest[security_id]
        securities[str(security_id)] = {
            "packet_sequence": snapshot.packet_sequence,
            "sending_time_ns": snapshot.sending_time_ns,
            "last_sequence_processed": snapshot.last_sequence_processed,
            "report_sequence": snapshot.report_sequence,
            "level_count": len(snapshot.levels),
            "levels": [
                {
                    "side": level.side.value,
                    "level": level.level,
                    "price": level.price,
                    "size": level.size,
                    "num_orders": level.num_orders,
                }
                for level in snapshot.levels
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
