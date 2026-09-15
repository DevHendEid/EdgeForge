from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from edgeforge.core.provenance import SourceManifest, sha256_file


def download_with_manifest(url: str, destination: str | Path, *, dataset: str, source: str,
                           license_status: str = "verify-source-terms") -> SourceManifest:
    """Download a publicly reachable file and write a provenance manifest beside it.

    This function does not bypass authentication, paywalls, robots, or licensing controls.
    """
    dest = Path(destination); dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    manifest = SourceManifest(source=source, dataset=dataset, license_status=license_status,
                              acquired_at=datetime.now(timezone.utc).isoformat(), source_url=url,
                              sha256=sha256_file(dest), redistribution_allowed=None,
                              metadata={"bytes": dest.stat().st_size})
    manifest_path = dest.with_suffix(dest.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest.model_dump(), indent=2), encoding="utf-8")
    return manifest
