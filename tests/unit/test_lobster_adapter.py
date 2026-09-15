from pathlib import Path

from edgeforge.data.adapters.lobster import LobsterMessageAdapter
from edgeforge.replay.engine import replay_l3


def test_lobster_fixture_replays_cleanly() -> None:
    p = Path(__file__).parents[1] / "fixtures" / "lobster_message.csv"
    events = list(LobsterMessageAdapter(p, "TEST", "2012-06-21"))
    report = replay_l3(events)
    assert report.events == 6
    assert report.errors == 0
