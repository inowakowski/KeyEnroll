"""HID transport: frames that belong to other programs are skipped."""

from __future__ import annotations

import struct

import pytest
from fido2.hid import CTAPHID, TYPE_INIT, ConnectionFailure, CtapHidDevice

from keyenroll.fido import devices
from keyenroll.fido.devices import SharedHidDevice

BROADCAST = 0xFFFFFFFF
OWN = 0x0A0B0C0D
OTHER = 0x11223344
SIZE = 64


class Descriptor:
    path = "fake-hid"
    report_size_out = SIZE
    report_size_in = SIZE
    product_name = "YubiKey"
    serial_number = None


def frame(channel: int, cmd: int, payload: bytes) -> bytes:
    return struct.pack(">IBH", channel, TYPE_INIT | cmd, len(payload)) + payload.ljust(
        SIZE - 7, b"\0"
    )


class Wire:
    """A key on a HID bus shared with another program (as on Windows: every
    open handle sees every input report)."""

    def __init__(self, noise: int = 1):
        self.noise = noise
        self.inbox: list[bytes] = []
        self.closed = False

    def write_packet(self, data: bytes) -> None:
        channel, cmd = struct.unpack_from(">IB", data)
        payload = data[7 : 7 + struct.unpack_from(">H", data, 5)[0]]
        cmd &= 0x7F
        for _ in range(self.noise):
            # Another program's INIT response and one of its CBOR responses.
            self.inbox.append(frame(BROADCAST, CTAPHID.INIT, b"\x99" * 8 + b"\0" * 9))
            self.inbox.append(frame(OTHER, CTAPHID.CBOR, b"\x00"))
        if cmd == CTAPHID.INIT:
            body = payload[:8] + struct.pack(">IBBBBB", OWN, 2, 5, 7, 4, 0x05)
            self.inbox.append(frame(BROADCAST, CTAPHID.INIT, body))
        else:
            assert channel == OWN
            self.inbox.append(frame(OWN, CTAPHID.KEEPALIVE, b"\x01"))
            self.inbox.append(frame(OTHER, CTAPHID.KEEPALIVE, b"\x02"))
            self.inbox.append(frame(OWN, cmd, payload))

    def read_packet(self) -> bytes:
        return self.inbox.pop(0)

    def close(self) -> None:
        self.closed = True


def test_plain_fido2_device_fails_on_another_programs_frames():
    # Documents why SharedHidDevice exists; if fido2 starts skipping such
    # frames itself, the wrapper can go.
    with pytest.raises(ConnectionFailure):
        CtapHidDevice(Descriptor(), Wire())


def test_frames_of_other_channels_and_foreign_init_responses_are_skipped():
    wire = Wire()
    dev = SharedHidDevice(Descriptor(), wire)
    assert dev._channel_id == OWN
    assert dev.device_version == (5, 7, 4)
    assert dev.ping(b"hello") == b"hello"
    dev.close()
    assert wire.closed


def test_one_key_failing_to_open_does_not_hide_the_others(monkeypatch):
    good, bad = Descriptor(), Descriptor()
    bad.path = "broken"
    wires = {"fake-hid": Wire(noise=0), "broken": Wire(noise=0)}

    def broken_read():
        raise OSError("device gone")

    wires["broken"].read_packet = broken_read
    monkeypatch.setattr(devices, "list_descriptors", lambda: [bad, good])
    monkeypatch.setattr(devices, "open_connection", lambda d: wires[d.path])

    found = devices._list_hid()

    assert [d.descriptor.path for d in found] == ["fake-hid"]
    assert wires["broken"].closed
