"""Record Coinbase Advanced Trade L2 websocket envelopes to JSONL.

Requires: pip install -e '.[live]'
The raw recording stays under data/raw/ and is ignored by Git.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path


async def main(product_id: str, output: Path) -> None:
    try:
        import websockets
    except ImportError as exc:
        raise SystemExit("Install EdgeForge live extra: pip install -e '.[live]'") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    uri = "wss://advanced-trade-ws.coinbase.com"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "subscribe", "product_ids": [product_id], "channel": "level2"}))
        with output.open("a", encoding="utf-8") as f:
            async for msg in ws:
                f.write(msg + "\n"); f.flush()


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("product_id"); p.add_argument("--output", type=Path, default=Path("data/raw/coinbase/l2.jsonl"))
    a = p.parse_args(); asyncio.run(main(a.product_id, a.output))
