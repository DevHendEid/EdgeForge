from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from edgeforge.data.registry import by_key


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def filename_from_url(url: str) -> str:
    name = Path(urlparse(url).path).name
    return name or "download.bin"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download a dataset artifact from an explicit URL into Git-ignored raw storage and "
            "write a provenance manifest. Use only URLs you are authorized to access."
        )
    )
    parser.add_argument("dataset_key", help="Key from edgeforge.data.registry")
    parser.add_argument("--url", required=True, help="Direct authorized download URL")
    parser.add_argument("--filename", help="Override output filename")
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--manifest-dir", type=Path, default=Path("data/manifests"))
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    spec = by_key(args.dataset_key)
    target_dir = args.raw_root / spec.key
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / (args.filename or filename_from_url(args.url))

    request = urllib.request.Request(
        args.url,
        headers={"User-Agent": "EdgeForge-dataset-acquirer/1.0"},
    )
    with urllib.request.urlopen(request) as response, target.open("wb") as handle:
        shutil.copyfileobj(response, handle)

    args.manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset_key": spec.key,
        "dataset_name": spec.name,
        "registry_url": spec.url,
        "download_url": args.url,
        "market": spec.market,
        "grade": spec.grade,
        "phase": spec.phase,
        "filename": target.name,
        "local_file": str(target.resolve()),
        "size_bytes": target.stat().st_size,
        "sha256": sha256_file(target),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "license_note": spec.license_note,
        "user_note": args.note,
    }
    manifest_path = args.manifest_dir / f"{spec.key}--{target.name}.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(target)
    print(manifest_path)


if __name__ == "__main__":
    main()
