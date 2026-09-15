from __future__ import annotations

import struct
from pathlib import Path

from edgeforge.book.l2 import L2OrderBook
from edgeforge.core.models import Side
from edgeforge.data.adapters.cme_pcap_snapshot import iter_snapshot_messages, snapshot_to_events


def _snapshot_payload() -> bytes:
    block_len = 22
    payload = bytearray(59 + 3 + block_len * 2)
    struct.pack_into("<I", payload, 0, 99)  # last sequence processed
    struct.pack_into("<i", payload, 8, 12345)  # security id
    struct.pack_into("<I", payload, 12, 7)  # report sequence
    struct.pack_into("<Q", payload, 16, 1_725_000_000_000_000_000)
    struct.pack_into("<Q", payload, 24, 1_725_000_000_000_000_001)
    struct.pack_into("<H", payload, 59, block_len)
    payload[61] = 2

    first = 62
    struct.pack_into("<q", payload, first, 20_000_000_000_000)
    struct.pack_into("<i", payload, first + 8, 4)
    struct.pack_into("<i", payload, first + 12, 2)
    payload[first + 16] = 1
    payload[first + 21] = ord("0")

    second = first + block_len
    struct.pack_into("<q", payload, second, 20_000_250_000_000)
    struct.pack_into("<i", payload, second + 8, 3)
    struct.pack_into("<i", payload, second + 12, 1)
    payload[second + 16] = 1
    payload[second + 21] = ord("1")
    return bytes(payload)


def _pcap_bytes() -> bytes:
    snap = _snapshot_payload()
    message = bytearray(10 + len(snap))
    struct.pack_into("<H", message, 0, len(message))
    struct.pack_into("<H", message, 4, 52)
    message[10:] = snap

    cbe = bytearray(12 + len(message))
    struct.pack_into("<I", cbe, 0, 123)
    struct.pack_into("<Q", cbe, 4, 1_725_000_000_000_000_100)
    cbe[12:] = message

    udp = struct.pack("!HHHH", 10000, 10001, 8 + len(cbe), 0) + bytes(cbe)
    ipv4 = bytearray(20)
    ipv4[0] = 0x45
    struct.pack_into("!H", ipv4, 2, 20 + len(udp))
    ipv4[8] = 64
    ipv4[9] = 17
    ethernet = b"\x00" * 12 + struct.pack("!H", 0x0800)
    frame = ethernet + bytes(ipv4) + udp

    global_header = (
        b"\xd4\xc3\xb2\xa1"
        + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 1)
    )
    packet_header = struct.pack("<IIII", 0, 0, len(frame), len(frame))
    return global_header + packet_header + frame


def test_template52_snapshot_decodes_and_replays(tmp_path: Path) -> None:
    path = tmp_path / "sample.pcap"
    path.write_bytes(_pcap_bytes())

    snapshots = list(iter_snapshot_messages(path))
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.security_id == 12345
    assert snapshot.packet_sequence == 123
    assert len(snapshot.levels) == 2
    assert snapshot.levels[0].side is Side.BID
    assert snapshot.levels[1].side is Side.ASK

    book = L2OrderBook()
    for event in snapshot_to_events(snapshot):
        book.apply(event)
    assert book.best_bid() == (20_000_000_000_000, 4)
    assert book.best_ask() == (20_000_250_000_000, 3)
