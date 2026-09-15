from pathlib import Path

from edgeforge.data.adapters.cme_pcap_snapshot import iter_snapshot_messages
from edgeforge.data.adapters.lobster import LobsterMessageAdapter
from edgeforge.replay.engine import replay_l3

p = Path("tests/fixtures/lobster_message.csv")
r = replay_l3(LobsterMessageAdapter(p, "TEST", "2012-06-21"))
print(f"Phase 1 replay events={r.events} errors={r.errors} hash={r.state_hash}")
print("Phase 2 adapters are covered by pytest test_crypto_adapters.py")

sample = Path("data/external/official-samples/databento/dc3-glbx-a-20230716T133000.pcap")
if sample.exists():
    snapshots = list(iter_snapshot_messages(sample))
    securities = sorted({snapshot.security_id for snapshot in snapshots})
    print(
        "Phase 3 official CME sample "
        f"snapshots={len(snapshots)} securities={len(securities)}"
    )
else:
    print("Phase 3 sample unavailable in working tree; run git lfs pull")
