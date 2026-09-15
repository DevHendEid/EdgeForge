from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from edgeforge.data.registry import by_key


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register a locally acquired dataset artifact without committing raw data to Git."
    )
    parser.add_argument("dataset_key", help="Key from edgeforge.data.registry")
    parser.add_argument("file", type=Path, help="Local raw dataset file")
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=Path("data/manifests"),
        help="Directory for tracked provenance manifests",
    )
    parser.add_argument("--note", default="", help="Optional acquisition/license note")
    args = parser.parse_args()

    spec = by_key(args.dataset_key)
    path = args.file.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"Not a file: {path}")

    args.manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset_key": spec.key,
        "dataset_name": spec.name,
        "source_url": spec.url,
        "market": spec.market,
        "grade": spec.grade,
        "phase": spec.phase,
        "local_file": str(path),
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "license_note": spec.license_note,
        "user_note": args.note,
    }
    output = args.manifest_dir / f"{spec.key}--{path.name}.manifest.json"
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
