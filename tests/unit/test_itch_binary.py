import io
import struct

from edgeforge.data.adapters.itch_binary import Itch5Decoder, ItchBinaryAdapter
from edgeforge.replay.engine import replay_l3


def framed(msg: bytes) -> bytes:
    return struct.pack(">H", len(msg)) + msg


def header(t: bytes, ns: int) -> bytes:
    return t + struct.pack(">HH", 1, 2) + ns.to_bytes(6, "big")


def test_binary_add_execute_delete_replay() -> None:
    add = header(b"A", 1_000) + struct.pack(">Q", 42) + b"B" + struct.pack(">I", 10) + b"AAPL    " + struct.pack(">I", 1234500)
    exe = header(b"E", 2_000) + struct.pack(">QIQ", 42, 4, 99)
    delete = header(b"D", 3_000) + struct.pack(">Q", 42)
    decoder = Itch5Decoder(io.BytesIO(framed(add) + framed(exe) + framed(delete)))
    events = list(ItchBinaryAdapter(decoder, "2026-01-02"))
    assert replay_l3(events).errors == 0
