from pathlib import Path

from edgeforge.data.adapters.crypto import BinanceDepthAdapter, OkxBooksAdapter
from edgeforge.data.adapters.jsonl_payload import read_jsonl
from edgeforge.data.adapters.lobster import LobsterMessageAdapter
from edgeforge.replay.engine import replay_l2, replay_l3
from edgeforge.storage.jsonl import read_events, write_events

FIX = Path(__file__).parents[1] / "fixtures"


def test_phase1_normalize_persist_replay(tmp_path: Path) -> None:
    out = tmp_path / "events.jsonl"
    src = LobsterMessageAdapter(FIX / "lobster_message.csv", "TEST", "2012-06-21")
    assert write_events(out, src) == 6
    report = replay_l3(read_events(out))
    assert report.errors == 0 and report.state_hash is not None


def test_phase2_binance_workflow() -> None:
    report = replay_l2(BinanceDepthAdapter(read_jsonl(FIX / "binance_depth.jsonl"), "BTCUSDT"))
    assert report.events == 5 and report.errors == 0


def test_phase2_okx_workflow() -> None:
    report = replay_l2(OkxBooksAdapter(read_jsonl(FIX / "okx_books.jsonl"), "BTC-USDT"))
    assert report.errors == 0
