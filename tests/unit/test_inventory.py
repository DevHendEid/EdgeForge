from __future__ import annotations

import json
from pathlib import Path

from edgeforge.data.inventory import (
    EvidenceLevel,
    ProvenanceClass,
    inspect_file,
    inventory_tree,
    write_inventory,
)


def test_official_databento_sample_is_admissible_l3(tmp_path: Path) -> None:
    path = tmp_path / "data/external/official-samples/databento/sample.pcap"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"pcap-test")

    record = inspect_file(path, tmp_path)
    assert record.provenance_class is ProvenanceClass.OFFICIAL_PUBLIC
    assert record.evidence_level is EvidenceLevel.L3
    assert "l3_replay" in record.admissible_uses
    assert record.quarantine_reason is None


def test_unknown_local_data_is_quarantined(tmp_path: Path) -> None:
    path = tmp_path / "mystery.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    record = inspect_file(path, tmp_path)
    assert record.provenance_class is ProvenanceClass.QUARANTINED
    assert record.admissible_uses == ("inspection_only",)
    assert record.quarantine_reason is not None


def test_inventory_outputs_machine_and_human_reports(tmp_path: Path) -> None:
    source = tmp_path / "data/external/official-samples/databento/sample.pcap.zst"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"compressed-test")

    records = inventory_tree(tmp_path)
    output = tmp_path / "out"
    write_inventory(records, output)

    payload = json.loads((output / "inventory.json").read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["provenance_class"] == "OFFICIAL_PUBLIC"
    assert (output / "quarantine.json").exists()
    assert "EdgeForge Data Inventory" in (output / "INVENTORY.md").read_text(encoding="utf-8")
