from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path


class EvidenceLevel(StrEnum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    OHLCV = "OHLCV"
    UNKNOWN = "UNKNOWN"


class ProvenanceClass(StrEnum):
    OFFICIAL_PUBLIC = "OFFICIAL_PUBLIC"
    PUBLIC_WITH_CLEAR_LICENSE = "PUBLIC_WITH_CLEAR_LICENSE"
    PUBLIC_LICENSE_UNCLEAR = "PUBLIC_LICENSE_UNCLEAR"
    USER_ENTITLED = "USER_ENTITLED"
    COMMERCIAL_REFERENCE_ONLY = "COMMERCIAL_REFERENCE_ONLY"
    DERIVED_ONLY = "DERIVED_ONLY"
    QUARANTINED = "QUARANTINED"


_DATA_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".parquet",
    ".dbn",
    ".zst",
    ".gz",
    ".pcap",
    ".h5",
    ".hdf5",
    ".feather",
    ".arrow",
}


@dataclass(frozen=True, slots=True)
class InventoryRecord:
    path: str
    size_bytes: int
    sha256: str
    format: str
    compressed: bool
    source_hint: str
    evidence_level: EvidenceLevel
    provenance_class: ProvenanceClass
    raw_or_derived: str
    admissible_uses: tuple[str, ...]
    quarantine_reason: str | None = None


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _format(path: Path) -> str:
    name = path.name.lower()
    for compound in (".pcap.zst", ".dbn.zst", ".csv.gz"):
        if name.endswith(compound):
            return compound.removeprefix(".")
    return path.suffix.lower().removeprefix(".") or "unknown"


def _source_hint(relative: str) -> str:
    parts = Path(relative).parts
    if "official-samples" in parts and "databento" in parts:
        return "Databento official public sample / CME GLBX MDP3"
    if "commercial" in parts and "cme" in parts:
        return "CME commercial/user-entitled intake"
    if "commercial" in parts and "databento" in parts:
        return "Databento commercial/user-entitled intake"
    if "external" in parts and "github" in parts:
        return "third-party GitHub research repository"
    return "local/unknown"


def _evidence_level(path: Path, relative: str) -> EvidenceLevel:
    name = path.name.lower()
    text = relative.lower()
    if "ohlcv" in name or any(token in name for token in ("1m", "5m", "1h", "daily")):
        return EvidenceLevel.OHLCV
    if "mbo" in text or "orderbook" in text or "order-book" in text:
        return EvidenceLevel.L3
    if "mbp" in text or "depth" in text or "level2" in text or "l2" in text:
        return EvidenceLevel.L2
    if "trades" in text or "bbo" in text or "quotes" in text:
        return EvidenceLevel.L1
    if "official-samples/databento" in text and (name.endswith(".pcap") or name.endswith(".pcap.zst")):
        return EvidenceLevel.L3
    return EvidenceLevel.UNKNOWN


def _provenance(relative: str) -> tuple[ProvenanceClass, str | None]:
    text = relative.lower()
    if "data/external/official-samples/databento" in text:
        return ProvenanceClass.OFFICIAL_PUBLIC, None
    if "data/commercial/cme" in text or "data/commercial/databento" in text:
        return ProvenanceClass.USER_ENTITLED, None
    if "/results/" in text or text.startswith("results/"):
        return ProvenanceClass.DERIVED_ONLY, None
    if "external/github" in text:
        return (
            ProvenanceClass.PUBLIC_LICENSE_UNCLEAR,
            "public repository does not by itself establish data redistribution rights",
        )
    return ProvenanceClass.QUARANTINED, "source/license entitlement not established"


def _raw_or_derived(relative: str) -> str:
    text = relative.lower()
    if "/results/" in text or "/features/" in text or "/labels/" in text:
        return "derived"
    return "raw_or_unknown"


def _uses(level: EvidenceLevel, provenance: ProvenanceClass) -> tuple[str, ...]:
    if provenance in {ProvenanceClass.QUARANTINED, ProvenanceClass.PUBLIC_LICENSE_UNCLEAR}:
        return ("inspection_only",)
    match level:
        case EvidenceLevel.L3:
            return ("l3_replay", "queue_research", "execution_validation")
        case EvidenceLevel.L2:
            return ("l2_replay", "depth_features", "liquidity_research")
        case EvidenceLevel.L1:
            return ("trade_quote_research", "timing_research")
        case EvidenceLevel.OHLCV:
            return ("strategy_screening", "long_horizon_robustness")
        case _:
            return ("inspection_only",)


def inspect_file(path: Path, root: Path) -> InventoryRecord:
    relative = path.relative_to(root).as_posix()
    provenance, quarantine_reason = _provenance(relative)
    evidence = _evidence_level(path, relative)
    fmt = _format(path)
    return InventoryRecord(
        path=relative,
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
        format=fmt,
        compressed=fmt.endswith("zst") or fmt.endswith("gz") or fmt == "zip",
        source_hint=_source_hint(relative),
        evidence_level=evidence,
        provenance_class=provenance,
        raw_or_derived=_raw_or_derived(relative),
        admissible_uses=_uses(evidence, provenance),
        quarantine_reason=quarantine_reason,
    )


def inventory_tree(root: Path) -> list[InventoryRecord]:
    root = root.resolve()
    records: list[InventoryRecord] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        lower = path.name.lower()
        if path.suffix.lower() not in _DATA_SUFFIXES and not any(
            lower.endswith(suffix) for suffix in (".pcap.zst", ".dbn.zst", ".csv.gz")
        ):
            continue
        records.append(inspect_file(path, root))
    return records


def write_inventory(records: list[InventoryRecord], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in records]
    (output_dir / "inventory.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    quarantined = [row for row in payload if row["quarantine_reason"] is not None]
    (output_dir / "quarantine.json").write_text(
        json.dumps(quarantined, indent=2, default=str) + "\n", encoding="utf-8"
    )

    lines = [
        "# EdgeForge Data Inventory",
        "",
        f"Files inventoried: **{len(records)}**",
        f"Quarantined/unclear: **{len(quarantined)}**",
        "",
        "| Path | Evidence | Provenance | Size | SHA-256 | Uses |",
        "|---|---|---|---:|---|---|",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{record.path}`",
                    record.evidence_level.value,
                    record.provenance_class.value,
                    str(record.size_bytes),
                    f"`{record.sha256}`",
                    ", ".join(record.admissible_uses),
                )
            )
            + " |"
        )
    (output_dir / "INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
