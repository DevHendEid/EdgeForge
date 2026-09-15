from edgeforge.data.adapters.crypto import CoinbaseL2Adapter, HyperliquidL2Adapter
from edgeforge.replay.engine import replay_l2


def test_hyperliquid_snapshot() -> None:
    payloads = [{"data":{"time":1700000000000,"levels":[[{"px":"100","sz":"2"}],[{"px":"101","sz":"3"}]]}}]
    assert replay_l2(HyperliquidL2Adapter(payloads, "BTC")).errors == 0


def test_coinbase_snapshot_update() -> None:
    payloads = [{"events":[{"type":"snapshot","updates":[
        {"side":"bid","price_level":"100","new_quantity":"2","event_time":"2026-01-01T00:00:00Z"},
        {"side":"offer","price_level":"101","new_quantity":"3","event_time":"2026-01-01T00:00:00Z"}]}]}]
    assert replay_l2(CoinbaseL2Adapter(payloads, "BTC-USD")).errors == 0
