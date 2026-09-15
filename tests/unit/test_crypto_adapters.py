from edgeforge.data.adapters.crypto import BinanceDepthAdapter, OkxBooksAdapter
from edgeforge.replay.engine import replay_l2


def test_binance_depth_adapter() -> None:
    msgs = [{"E": 1_700_000_000_000, "u": 10, "b": [["100.0", "2.0"]], "a": [["101.0", "3.0"]]}]
    assert replay_l2(BinanceDepthAdapter(msgs, "BTCUSDT")).errors == 0


def test_okx_snapshot_adapter() -> None:
    payloads = [{"action":"snapshot","data":[{"ts":"1700000000000","bids":[["100","2","0","1"]],"asks":[["101","3","0","1"]]}]}]
    report = replay_l2(OkxBooksAdapter(payloads, "BTC-USDT"))
    assert report.errors == 0
