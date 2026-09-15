from __future__ import annotations

import argparse
from pathlib import Path

from edgeforge.data.inventory import inventory_tree, write_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory EdgeForge research datasets")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="workspace/data root to inspect (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default="data/manifests/phase3-inventory",
        help="directory for inventory.json, quarantine.json and INVENTORY.md",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    records = inventory_tree(root)
    write_inventory(records, output)

    quarantined = sum(record.quarantine_reason is not None for record in records)
    print(f"Inventoried {len(records)} data files")
    print(f"Quarantined/unclear: {quarantined}")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
