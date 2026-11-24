"""YubiKey applications and the configuration lock (fido/management.py)."""

from __future__ import annotations

import pytest

from fake_authenticator import FakeAuthenticator
from keyenroll import lock_codes
from keyenroll.config import Profile
from keyenroll.fido.management import (
    CLEAR_LOCK,
    Capability,
    ManagementError,
    config_bytes,
    read_config,
    write_config,
)
from keyenroll.secrets_store import TokenStore

CODE = bytes(range(1, 17))
ALL = 0x23B


def test_the_configuration_is_read_from_the_key():
    key = FakeAuthenticator()
    key.serial = 32445513
    key.nfc_enabled = ALL & ~Capability.PIV
    config = read_config(key)
    assert config.serial == 32445513 and config.firmware == "5.7.4"
    assert config.usb_enabled == ALL and not config.nfc_enabled & Capability.PIV
    assert not config.locked


def test_the_write_payload_follows_yubikey_manager():
    # yubikit 5.5.1 DeviceConfig.get_bytes: UNLOCK, USB_ENABLED, NFC_ENABLED,
    # CONFIG_LOCK, each a TLV, the whole prefixed with its length.
    payload = config_bytes(0x0201, 0x0200, cur_lock=CODE, new_lock=CLEAR_LOCK)
    body = (
        bytes([0x0B, 16]) + CODE
        + bytes([0x03, 2, 0x02, 0x01])
        + bytes([0x0E, 2, 0x02, 0x00])
        + bytes([0x0A, 16]) + CLEAR_LOCK
    )  # fmt: skip
    assert payload == bytes([len(body)]) + body
    with pytest.raises(ValueError):
        config_bytes(1, None, cur_lock=b"short")


def test_applications_are_switched_off_and_fido2_stays_on():
    key = FakeAuthenticator()
    config = read_config(key)
    write_config(key, config, usb_enabled=Capability.OATH, nfc_enabled=0)
    assert key.usb_enabled == Capability.OATH | Capability.FIDO2
    assert key.nfc_enabled == Capability.FIDO2


def test_the_configuration_is_locked_and_unlocked_with_the_code():
    key = FakeAuthenticator()
    write_config(key, read_config(key), ALL & ~Capability.PIV, None, new_lock=CODE)
    assert key.lock_code == CODE and read_config(key).locked

    locked = read_config(key)
    with pytest.raises(ManagementError, match="locked"):
        write_config(key, locked, ALL, None)  # no code
    with pytest.raises(ManagementError, match="does not match"):
        write_config(key, locked, ALL, None, cur_lock=bytes(range(2, 18)))
    assert not key.usb_enabled & Capability.PIV

    write_config(key, locked, ALL, None, cur_lock=CODE)  # changed, still locked
    assert key.usb_enabled & Capability.PIV and key.lock_code == CODE
    write_config(key, read_config(key), ALL, None, cur_lock=CODE, new_lock=CLEAR_LOCK)
    assert key.lock_code is None


def test_old_firmware_and_keys_without_management_are_refused():
    key = FakeAuthenticator()
    key.version = (4, 3, 7)
    with pytest.raises(ManagementError, match="5.0"):
        write_config(key, read_config(key), ALL, None)
    key.management = False
    with pytest.raises(ManagementError, match="does not support"):
        read_config(key)


def test_lock_codes_are_kept_in_the_credential_store_not_the_profile():
    store = TokenStore()
    profile = Profile(name="high-security")
    assert lock_codes.get(store, profile) is None
    code = lock_codes.generate()
    assert len(code) == 16 and code != CLEAR_LOCK
    lock_codes.put(store, profile, code)
    assert profile.lock_code_id and lock_codes.get(store, profile) == code
    assert code.hex() not in str(vars(profile))
    lock_codes.forget(store, profile)
    assert profile.lock_code_id == "" and lock_codes.get(store, profile) is None


def test_lock_codes_typed_in_are_checked():
    assert lock_codes.parse("0102 0304-0506 0708 090a 0b0c 0d0e 0f10") == CODE
    assert lock_codes.parse("00" * 16) is None  # that would remove a lock
    assert lock_codes.parse("xyz") is None
