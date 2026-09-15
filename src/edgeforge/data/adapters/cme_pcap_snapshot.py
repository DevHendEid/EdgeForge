from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from edgeforge.core.models import Action, MarketEvent, Side

PRICE_SCALE = 1_000_000_000
SNAPSHOT_TEMPLATE_ID = 52


@dataclass(frozen=True, slots=True)
class SnapshotLevel:
    price: int
    size: int
    num_orders: int
    level: int
    side: Side


@dataclass(frozen=True, slots=True)
class SnapshotMessage:
    packet_sequence: int
    sending_time_ns: int
    last_sequence_processed: int
    security_id: int
    report_sequence: int
    transact_time_ns: int
    update_time_ns: int
    levels: tuple[SnapshotLevel, ...]


def _pcap_endian(header: bytes) -> str:
    if len(header) < 24:
        raise ValueError("truncated PCAP global header")
    magic = header[:4]
    if magic in {b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"}:
        return "<"
    if magic in {b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"}:
        return ">"
    raise ValueError(f"unsupported PCAP magic: {magic.hex()}")


def iter_pcap_packets(path: Path) -> Iterator[bytes]:
    with path.open("rb") as handle:
        global_header = handle.read(24)
        endian = _pcap_endian(global_header)
        while True:
            packet_header = handle.read(16)
            if not packet_header:
                return
            if len(packet_header) != 16:
                raise ValueError("truncated PCAP packet header")
            _, _, captured_len, _ = struct.unpack(f"{endian}IIII", packet_header)
            packet = handle.read(captured_len)
            if len(packet) != captured_len:
                raise ValueError("truncated PCAP packet payload")
            yield packet


def _udp_payload(frame: bytes) -> tuple[int, bytes] | None:
    if len(frame) < 14:
        return None
    offset = 14
    ether_type = struct.unpack_from("!H", frame, 12)[0]
    if ether_type in {0x8100, 0x88A8}:
        if len(frame) < 18:
            return None
        ether_type = struct.unpack_from("!H", frame, 16)[0]
        offset = 18
    if ether_type != 0x0800 or len(frame) < offset + 20:
        return None

    version_ihl = frame[offset]
    if version_ihl >> 4 != 4:
        return None
    ihl = (version_ihl & 0x0F) * 4
    if ihl < 20 or len(frame) < offset + ihl + 8:
        return None
    if frame[offset + 9] != 17:  # UDP
        return None

    udp_offset = offset + ihl
    source_port, _, udp_length, _ = struct.unpack_from("!HHHH", frame, udp_offset)
    if udp_length < 8 or len(frame) < udp_offset + udp_length:
        return None
    return source_port, frame[udp_offset + 8 : udp_offset + udp_length]


def _parse_snapshot(payload: bytes, packet_sequence: int, sending_time_ns: int) -> SnapshotMessage:
    if len(payload) < 62:
        raise ValueError("truncated template 52 payload")

    last_sequence_processed = struct.unpack_from("<I", payload, 0)[0]
    security_id = struct.unpack_from("<i", payload, 8)[0]
    report_sequence = struct.unpack_from("<I", payload, 12)[0]
    transact_time_ns = struct.unpack_from("<Q", payload, 16)[0]
    update_time_ns = struct.unpack_from("<Q", payload, 24)[0]

    group_offset = 59
    block_length = struct.unpack_from("<H", payload, group_offset)[0]
    group_count = payload[group_offset + 2]
    if block_length < 22:
        raise ValueError(f"unexpected snapshot group block length: {block_length}")

    levels: list[SnapshotLevel] = []
    cursor = group_offset + 3
    for _ in range(group_count):
        if cursor + block_length > len(payload):
            raise ValueError("truncated snapshot repeating group")
        price = struct.unpack_from("<q", payload, cursor)[0]
        size = struct.unpack_from("<i", payload, cursor + 8)[0]
        num_orders = struct.unpack_from("<i", payload, cursor + 12)[0]
        level = payload[cursor + 16]
        entry_type = payload[cursor + 21]
        if entry_type == ord("0"):
            side = Side.BID
        elif entry_type == ord("1"):
            side = Side.ASK
        else:
            # Template 52 also carries non-book statistics such as settlement entries.
            cursor += block_length
            continue
        if size > 0:
            levels.append(
                SnapshotLevel(
                    price=price,
                    size=size,
                    num_orders=num_orders,
                    level=level,
                    side=side,
                )
            )
        cursor += block_length

    return SnapshotMessage(
        packet_sequence=packet_sequence,
        sending_time_ns=sending_time_ns,
        last_sequence_processed=last_sequence_processed,
        security_id=security_id,
        report_sequence=report_sequence,
        transact_time_ns=transact_time_ns,
        update_time_ns=update_time_ns,
        levels=tuple(levels),
    )


def iter_snapshot_messages(path: Path) -> Iterator[SnapshotMessage]:
    """Decode CME MDP 3.0 template 52 snapshots from a classic Ethernet/IPv4/UDP PCAP.

    The parser is intentionally narrow and fail-closed. It is not a general CME MDP 3.0
    decoder and does not claim to decode incremental MBO messages.
    """

    for frame in iter_pcap_packets(path):
        udp = _udp_payload(frame)
        if udp is None:
            continue
        source_port, payload = udp
        if source_port in {319, 320}:  # timing/PTP traffic used by the reference parser
            continue
        if len(payload) < 12:
            continue
        packet_sequence = struct.unpack_from("<I", payload, 0)[0]
        sending_time_ns = struct.unpack_from("<Q", payload, 4)[0]
        cursor = 12
        while cursor < len(payload):
            if cursor + 10 > len(payload):
                raise ValueError("truncated CME binary message header")
            message_size = struct.unpack_from("<H", payload, cursor)[0]
            template_id = struct.unpack_from("<H", payload, cursor + 4)[0]
            if message_size < 10 or cursor + message_size > len(payload):
                raise ValueError("invalid CME binary message size")
            if template_id == SNAPSHOT_TEMPLATE_ID:
                yield _parse_snapshot(
                    payload[cursor + 10 : cursor + message_size],
                    packet_sequence,
                    sending_time_ns,
                )
            cursor += message_size


def snapshot_to_events(snapshot: SnapshotMessage) -> Iterator[MarketEvent]:
    """Convert one price-level snapshot into canonical L2 events."""

    from datetime import datetime, timezone

    event_ts = datetime.fromtimestamp(
        snapshot.transact_time_ns / 1_000_000_000, tz=timezone.utc
    )
    instrument = str(snapshot.security_id)
    yield MarketEvent(
        venue="CME",
        instrument=instrument,
        event_ts=event_ts,
        sequence=snapshot.packet_sequence,
        action=Action.CLEAR,
        source="cme-mdp3:pcap:template52",
    )
    for level in snapshot.levels:
        yield MarketEvent(
            venue="CME",
            instrument=instrument,
            event_ts=event_ts,
            sequence=snapshot.packet_sequence,
            action=Action.UPSERT_LEVEL,
            side=level.side,
            price=level.price,
            price_scale=PRICE_SCALE,
            size=level.size,
            level=level.level,
            flags=(f"num_orders={level.num_orders}",),
            source="cme-mdp3:pcap:template52",
        )
