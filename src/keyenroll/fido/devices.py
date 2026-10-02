"""Security key discovery over USB (HID) and NFC (PC/SC)."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from fido2.ctap import CtapDevice
from fido2.ctap2 import Ctap2
from fido2.hid import CtapHidDevice

logger = logging.getLogger(__name__)

# YubiKey management over the FIDO HID interface (vendor command).
_CTAP_READ_CONFIG = 0x42
_TAG_SERIAL = 0x02
_TAG_VERSION = 0x05


@dataclass
class KeyInfo:
    key: str
    transport: str  # "usb" or "nfc"
    name: str
    serial: int | None = None
    firmware: str | None = None
    ctap2: bool = True
    has_pin: bool = False
    min_pin_length: int = 4
    always_uv: bool | None = None  # None: not supported
    enterprise_attestation: bool | None = None  # None: not supported
    force_pin_change: bool = False
    supports_config: bool = False

    @property
    def label(self) -> str:
        parts = [self.name]
        if self.serial:
            parts.append(f"S/N {self.serial}")
        if self.firmware:
            parts.append(f"FW {self.firmware}")
        if self.transport == "nfc":
            parts.append("NFC")
        return " · ".join(parts)


def device_key(dev: CtapDevice) -> str:
    """Identifier that stays the same when a key is re-inserted in the same port."""
    descriptor = getattr(dev, "descriptor", None)
    if descriptor is not None:
        path = descriptor.path
        return "usb:" + (path.decode(errors="replace") if isinstance(path, bytes) else str(path))
    return "nfc:" + getattr(dev, "_name", repr(dev))


def _list_pcsc() -> list[CtapDevice]:
    try:
        from fido2.pcsc import CtapPcscDevice
    except Exception:  # pyscard not installed
        return []
    try:
        devices = list(CtapPcscDevice.list_devices())
    except Exception:
        logger.debug("PC/SC listing failed", exc_info=True)
        return []
    out = []
    for dev in devices:
        # A YubiKey plugged in over USB also shows up as a CCID reader.
        if "yubikey" in getattr(dev, "_name", "").lower():
            close(dev)
        else:
            out.append(dev)
    return out


def close(dev: CtapDevice) -> None:
    try:
        dev.close()
    except Exception:
        logger.debug("Closing device failed", exc_info=True)


class DeviceSource:
    """Enumerates connected security keys. Returned devices are open."""

    def list(self) -> list[CtapDevice]:
        devices: list[CtapDevice] = []
        try:
            devices.extend(CtapHidDevice.list_devices())
        except Exception:
            logger.debug("HID listing failed", exc_info=True)
        devices.extend(_list_pcsc())
        return devices

    def describe(self, dev: CtapDevice) -> KeyInfo:
        return describe(dev)


def _read_yubikey_config(dev: CtapDevice) -> tuple[int | None, str | None]:
    """Reads serial number and firmware version of a YubiKey over HID."""
    if not isinstance(dev, CtapHidDevice):
        return None, None
    try:
        data = dev.call(_CTAP_READ_CONFIG, b"\x00")
    except Exception:
        try:
            data = dev.call(_CTAP_READ_CONFIG)
        except Exception:
            return None, None
    serial = version = None
    try:
        body = data[1 : 1 + data[0]]
        while len(body) >= 2:
            tag, length, body = body[0], body[1], body[2:]
            value, body = body[:length], body[length:]
            if tag == _TAG_SERIAL:
                serial = int.from_bytes(value, "big")
            elif tag == _TAG_VERSION and len(value) == 3:
                version = ".".join(str(b) for b in value)
    except IndexError:
        pass
    return serial, version


def describe(dev: CtapDevice) -> KeyInfo:
    key = device_key(dev)
    transport = "usb" if key.startswith("usb:") else "nfc"
    name = getattr(dev, "product_name", None) or (
        getattr(dev, "_name", None) if transport == "nfc" else None
    ) or "FIDO security key"
    info = KeyInfo(key=key, transport=transport, name=name)
    info.serial, info.firmware = _read_yubikey_config(dev)
    if info.firmware is None and isinstance(dev, CtapHidDevice):
        version = dev.device_version
        if any(version):
            info.firmware = ".".join(str(v) for v in version)
    try:
        ctap_info = Ctap2(dev).info
    except Exception:
        info.ctap2 = False
        return info
    options = ctap_info.options
    info.has_pin = bool(options.get("clientPin"))
    info.min_pin_length = ctap_info.min_pin_length
    info.always_uv = options.get("alwaysUv")
    info.enterprise_attestation = options.get("ep")
    info.force_pin_change = ctap_info.force_pin_change
    info.supports_config = bool(options.get("authnrCfg"))
    return info


def is_admin() -> bool:
    """Windows only lets elevated processes talk to FIDO HID devices."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    """Starts a new elevated instance of the app. Returns True if started."""
    if sys.platform != "win32":
        return False
    import ctypes
    import subprocess

    if getattr(sys, "frozen", False):
        exe, args = sys.executable, sys.argv[1:]
    else:
        exe, args = sys.executable, ["-m", "keyenroll", *sys.argv[1:]]
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, subprocess.list2cmdline(args), None, 1
    )
    return result > 32
