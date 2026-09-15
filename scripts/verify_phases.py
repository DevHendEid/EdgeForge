from pathlib import Path

from edgeforge.data.adapters.lobster import LobsterMessageAdapter
from edgeforge.replay.engine import replay_l3

p = Path("tests/fixtures/lobster_message.csv")
r = replay_l3(LobsterMessageAdapter(p, "TEST", "2012-06-21"))
print(f"Phase 1 replay events={r.events} errors={r.errors} hash={r.state_hash}")
print("Phase 2 adapters are covered by pytest test_crypto_adapters.py")
