"""YubiKey applications and configuration lock.

Which applications (OTP, PIV, OATH, ...) a YubiKey offers over USB and NFC,
and the lock code that keeps a user from changing that. Uses the YubiKey
management commands over the FIDO HID interface, as Yubico's yubikey-manager
does (yubikit/management.py, 5.5.1); firmware 5.0 or newer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import IntFlag

from fido2.ctap import CtapDevice, CtapError

from ..i18n import N_
from .enroll import EnrollError

logger = logging.getLogger(__name__)

CTAP_READ_CONFIG = 0x42
CTAP_WRITE_CONFIG = 0x43

TAG_USB_SUPPORTED = 0x01
TAG_SERIAL = 0x02
TAG_USB_ENABLED = 0x03
TAG_VERSION = 0x05
TAG_CONFIG_LOCK = 0x0A
TAG_UNLOCK = 0x0B
TAG_NFC_SUPPORTED = 0x0D
TAG_NFC_ENABLED = 0x0E
TAG_MORE_DATA = 0x10

LOCK_CODE_LENGTH = 16
CLEAR_LOCK = bytes(LOCK_CODE_LENGTH)  # writing it as the new code removes the lock
MIN_FIRMWARE = (5, 0, 0)
_MAX_PAGES = 8


class Capability(IntFlag):
    OTP = 0x01
    U2F = 0x02
    OPENPGP = 0x08
    PIV = 0x10
    OATH = 0x20
    HSMAUTH = 0x100
    FIDO2 = 0x200


# In the order they are shown; FIDO2 stays on, enrollment depends on it.
APPLICATIONS: list[tuple[Capability, str]] = [
    (Capability.FIDO2, N_("FIDO2 (passkeys, sign-in with the identity provider)")),
    (Capability.U2F, N_("FIDO U2F (older two-step sign-in)")),
    (Capability.OTP, N_("OTP (Yubico OTP, challenge-response, static password)")),
    (Capability.OATH, N_("OATH (one-time codes in Yubico Authenticator)")),
    (Capability.PIV, N_("PIV (smart card, certificates)")),
    (Capability.OPENPGP, N_("OpenPGP")),
    (Capability.HSMAUTH, N_("YubiHSM Auth")),
]
REQUIRED = Capability.FIDO2


class ManagementError(EnrollError):
    """A key that cannot be configured, or refused the change."""


@dataclass
class DeviceConfig:
    serial: int | None = None
    version: tuple[int, int, int] | None = None
    usb_supported: int = 0
    usb_enabled: int = 0
    nfc_supported: int = 0
    nfc_enabled: int = 0
    locked: bool = False

    @property
    def firmware(self) -> str:
        return ".".join(str(v) for v in self.version) if self.version else ""


def parse_tlvs(data: bytes) -> dict[int, bytes]:
    out: dict[int, bytes] = {}
    i = 0
    while i + 2 <= len(data):
        tag, length = data[i], data[i + 1]
        out[tag] = bytes(data[i + 2 : i + 2 + length])
        i += 2 + length
    return out


def _caps(value: bytes | None) -> int:
    return int.from_bytes(value, "big") if value else 0


def read_config(dev: CtapDevice) -> DeviceConfig:
    """Keys on an NFC reader and keys of other vendors do not answer."""
    tlvs: dict[int, bytes] = {}
    for page in range(_MAX_PAGES):
        try:
            data = bytes(dev.call(CTAP_READ_CONFIG, bytes([page])))
        except Exception as e:
            raise ManagementError(
                N_("This security key does not support managing its applications.")
            ) from e
        if not data or data[0] != len(data) - 1:
            raise ManagementError(N_("The security key sent an invalid configuration."))
        found = parse_tlvs(data[1:])
        tlvs.update(found)
        if found.get(TAG_MORE_DATA) != b"\x01":
            break
    version = tlvs.get(TAG_VERSION)
    config = DeviceConfig(
        serial=int.from_bytes(tlvs[TAG_SERIAL], "big") if TAG_SERIAL in tlvs else None,
        version=tuple(version) if version and len(version) == 3 else None,
        usb_supported=_caps(tlvs.get(TAG_USB_SUPPORTED)),
        usb_enabled=_caps(tlvs.get(TAG_USB_ENABLED)),
        nfc_supported=_caps(tlvs.get(TAG_NFC_SUPPORTED)),
        nfc_enabled=_caps(tlvs.get(TAG_NFC_ENABLED)),
        locked=tlvs.get(TAG_CONFIG_LOCK) == b"\x01",
    )
    return config


def _tlv(tag: int, value: bytes = b"") -> bytes:
    return bytes([tag, len(value)]) + value


def config_bytes(
    usb_enabled: int | None,
    nfc_enabled: int | None,
    cur_lock: bytes | None = None,
    new_lock: bytes | None = None,
) -> bytes:
    """The payload of the write command, in yubikey-manager's order."""
    for code in (cur_lock, new_lock):
        if code is not None and len(code) != LOCK_CODE_LENGTH:
            raise ValueError("A lock code is 16 bytes")
    buf = b""
    if cur_lock:
        buf += _tlv(TAG_UNLOCK, cur_lock)
    if usb_enabled is not None:
        buf += _tlv(TAG_USB_ENABLED, usb_enabled.to_bytes(2, "big"))
    if nfc_enabled is not None:
        buf += _tlv(TAG_NFC_ENABLED, nfc_enabled.to_bytes(2, "big"))
    if new_lock:
        buf += _tlv(TAG_CONFIG_LOCK, new_lock)
    return bytes([len(buf)]) + buf


def check_supported(config: DeviceConfig) -> None:
    if config.version is None or config.version < MIN_FIRMWARE:
        raise ManagementError(
            N_("Managing applications needs a YubiKey with firmware 5.0 or newer.")
        )


def write_config(
    dev: CtapDevice,
    config: DeviceConfig,
    usb_enabled: int,
    nfc_enabled: int | None,
    cur_lock: bytes | None = None,
    new_lock: bytes | None = None,
) -> None:
    """Writes the enabled applications; they take effect once the key is
    plugged in again. FIDO2 is always kept on."""
    check_supported(config)
    usb_enabled = (usb_enabled | REQUIRED) & config.usb_supported
    if config.nfc_supported and nfc_enabled is not None:
        nfc_enabled = (nfc_enabled | REQUIRED) & config.nfc_supported
    else:
        nfc_enabled = None
    if config.locked and not cur_lock:
        raise ManagementError(
            N_("The configuration of this key is locked. Choose the lock code it was locked with.")
        )
    try:
        dev.call(CTAP_WRITE_CONFIG, config_bytes(usb_enabled, nfc_enabled, cur_lock, new_lock))
    except CtapError as e:
        logger.info("Writing the key configuration failed: %s", e)
        if config.locked:
            raise ManagementError(
                N_("The security key refused the change. The lock code does not match.")
            ) from e
        raise ManagementError(
            N_("The security key reported an error: {detail}"), detail=e.code.name
        ) from e
