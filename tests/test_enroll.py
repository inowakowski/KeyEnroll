from __future__ import annotations

import os
import threading

import pytest
from fido2.utils import sha256

from fake_authenticator import FakeAuthenticator
from keyenroll.config import Profile
from keyenroll.fido import enroll
from keyenroll.fido.devices import DeviceSource
from keyenroll.fido.enroll import (
    EnrollCancelled,
    Enroller,
    EnrollError,
    compose_key_name,
)
from keyenroll.providers.base import (
    DirectoryUser,
    Registration,
    b64url_decode,
    b64url_encode,
)

RP_ID = "example.com"
ORIGIN = "https://login.example.com"
USER = DirectoryUser(id="u1", username="alice@example.com", display_name="Alice")


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(enroll, "POLL_INTERVAL", 0.01)


class FakeSource(DeviceSource):
    def __init__(self, *devices):
        self.devices = list(devices)
        self.present = True

    def list(self):
        return list(self.devices) if self.present else []

    def describe(self, dev):
        info = super().describe(dev)
        info.serial = getattr(dev, "serial", None)  # the fake has no HID vendor command
        return info


class FakeUI:
    """Plays the operator: re-inserts the key when asked, answers PIN prompts."""

    def __init__(self, source=None, current_pins=(), new_pins=()):
        self.source = source
        self.messages: list[str] = []
        self.current_pins = list(current_pins)
        self.new_pins = list(new_pins)
        self.pin_prompts: list[tuple] = []

    def status(self, template, **params):
        self.messages.append(template.format(**params) if params else template)
        if self.source is None:
            return
        if "remove the security key" in template:
            self.source.present = False
        elif "insert the security key" in template:
            self.source.present = True
            for dev in self.source.devices:
                dev.fresh = True

    def ask_current_pin(self, retries, wrong):
        self.pin_prompts.append(("current", retries, wrong))
        return self.current_pins.pop(0) if self.current_pins else None

    def ask_new_pin(self, min_length, rejected):
        self.pin_prompts.append(("new", min_length, rejected))
        return self.new_pins.pop(0) if self.new_pins else None


class FakeProvider:
    label = "Fake"
    max_display_name = None

    def __init__(self, exclude=(), attestation="direct"):
        self.exclude = list(exclude)
        self.attestation = attestation
        self.events: list[str] = []
        self.completed = None
        self.fail_complete = False

    def preflight(self, user):
        self.events.append("preflight")

    def begin_registration(self, user):
        self.events.append("begin")
        self.challenge = os.urandom(32)
        options = {
            "rp": {"id": RP_ID, "name": "Example"},
            "user": {
                "id": b64url_encode(user.id.encode()),
                "name": user.username,
                "displayName": user.display_name,
            },
            "challenge": b64url_encode(self.challenge),
            "pubKeyCredParams": [{"type": "public-key", "alg": -7}],
            "timeout": 60000,
            "attestation": self.attestation,
            "authenticatorSelection": {
                "authenticatorAttachment": "cross-platform",
                "requireResidentKey": True,
                "userVerification": "required",
            },
        }
        if self.exclude:
            options["excludeCredentials"] = [
                {"type": "public-key", "id": b64url_encode(c)} for c in self.exclude
            ]
        return Registration(options=options, origin=ORIGIN, state={})

    def complete_registration(self, registration, response, display_name):
        self.events.append("complete")
        if self.fail_complete:
            raise RuntimeError("server said no")
        client_data = response.response.client_data
        assert client_data.type == "webauthn.create"
        assert client_data.challenge == self.challenge
        assert client_data.origin == ORIGIN
        auth_data = response.response.attestation_object.auth_data
        assert auth_data.rp_id_hash == sha256(RP_ID.encode())
        assert auth_data.is_user_verified()
        assert auth_data.credential_data.credential_id == response.raw_id
        self.completed = (response, display_name)

    def cancel_registration(self, registration):
        self.events.append("cancel")


def make(profile, key, ui=None, provider=None, source=None):
    source = source or FakeSource(key)
    ui = ui or FakeUI(source)
    ui.source = source
    provider = provider or FakeProvider()
    enroller = Enroller(provider, profile, USER, "Alice's key", None, ui, source=source)
    return enroller, ui, provider


def test_default_profile_resets_sets_random_pin_and_registers():
    key = FakeAuthenticator()
    key.pin = "oldpin"
    enroller, ui, provider = make(Profile(), key)

    result = enroller.run()

    assert result.pin is not None and len(result.pin) == 6 and result.pin.isdigit()
    assert key.pin == result.pin
    assert result.pin_changed
    assert len(key.credentials) == 1
    assert key.credentials[0]["rp_id"] == RP_ID
    assert key.credentials[0]["user"]["id"] == b"u1"
    assert provider.events == ["preflight", "begin", "complete"]
    assert provider.completed[1] == "Alice's key"
    assert ui.pin_prompts == []
    assert not key.force_pin_change
    # The reset has to happen before anything is written to the key.
    assert key.log.index("reset") < key.log.index("client_pin")
    assert key.closed >= 1


def test_all_options_are_applied_in_a_working_order():
    key = FakeAuthenticator()
    profile = Profile(
        min_pin_length=8,
        require_always_uv=True,
        require_ea=True,
        force_pin_change=True,
        reset=True,
        random_pin=True,
        random_pin_length=6,  # shorter than the minimum: must be raised to 8
    )
    enroller, ui, provider = make(profile, key, provider=FakeProvider(attestation="none"))

    result = enroller.run()

    assert len(result.pin) == 8
    assert key.min_pin_length == 8
    assert key.always_uv
    assert key.ep
    assert key.credentials[0]["enterprise"] == 1
    # Forcing the PIN change last, otherwise no token could be obtained for
    # creating the credential.
    assert key.force_pin_change
    assert provider.completed is not None
    assert result.warnings == []


def test_no_reset_keeps_existing_pin_after_verifying_it():
    key = FakeAuthenticator()
    key.pin = "123456"
    profile = Profile(reset=False, random_pin=False)
    ui = FakeUI(current_pins=["000000", "123456"])
    enroller, ui, provider = make(profile, key, ui=ui)

    result = enroller.run()

    assert key.pin == "123456"
    assert result.pin is None and not result.pin_changed
    assert [p[0] for p in ui.pin_prompts] == ["current", "current"]
    assert ui.pin_prompts[1][2] is True  # second prompt reports the wrong PIN
    assert "reset" not in key.log
    assert len(key.credentials) == 1


def test_no_reset_with_random_pin_changes_existing_pin():
    key = FakeAuthenticator()
    key.pin = "123456"
    profile = Profile(reset=False, random_pin=True, random_pin_length=10)
    enroller, ui, provider = make(profile, key, ui=FakeUI(current_pins=["123456"]))

    result = enroller.run()

    assert result.pin == key.pin and len(key.pin) == 10
    assert len(key.credentials) == 1


def test_operator_chosen_pin_on_blank_key():
    key = FakeAuthenticator()
    key.reject_pins = {"111111"}
    profile = Profile(reset=False, random_pin=False, min_pin_length=6)
    ui = FakeUI(new_pins=["123", "111111", "246813"])
    enroller, ui, provider = make(profile, key, ui=ui)

    result = enroller.run()

    assert key.pin == "246813"
    assert result.pin is None  # operator-chosen PINs are not echoed back
    assert result.pin_changed
    assert ui.pin_prompts == [("new", 6, False), ("new", 6, True), ("new", 6, True)]
    assert key.min_pin_length == 6


def test_key_with_pending_pin_change_gets_a_new_pin():
    key = FakeAuthenticator()
    key.pin = "123456"
    key.force_pin_change = True
    profile = Profile(reset=False, random_pin=False)
    ui = FakeUI(current_pins=["123456"], new_pins=["654321"])
    enroller, ui, provider = make(profile, key, ui=ui)

    enroller.run()

    assert key.pin == "654321"
    assert not key.force_pin_change
    assert len(key.credentials) == 1


def test_existing_pin_shorter_than_profile_minimum_is_refused():
    key = FakeAuthenticator()
    key.pin = "1234"
    profile = Profile(reset=False, random_pin=False, min_pin_length=8)
    enroller, ui, provider = make(profile, key, ui=FakeUI(current_pins=["1234"]))

    with pytest.raises(EnrollError, match="shorter than the minimum"):
        enroller.run()
    assert key.min_pin_length == 4
    assert "begin" not in provider.events


def test_unsupported_options_fail_before_the_key_is_reset():
    key = FakeAuthenticator(supports_config=False)
    key.pin = "123456"
    enroller, ui, provider = make(Profile(require_always_uv=True), key)

    with pytest.raises(EnrollError, match="always UV"):
        enroller.run()
    assert "reset" not in key.log
    assert key.pin == "123456"


def test_key_without_config_support_works_with_basic_profile():
    key = FakeAuthenticator(supports_config=False)
    enroller, ui, provider = make(Profile(), key)

    result = enroller.run()

    assert key.pin == result.pin
    assert len(key.credentials) == 1


def test_already_registered_key_is_reported_and_cleaned_up():
    key = FakeAuthenticator()
    existing = os.urandom(32)
    profile = Profile(reset=False, random_pin=False)

    class Source(FakeSource):
        pass

    source = Source(key)
    key.pin = "123456"
    key.credentials.append({"id": existing, "rp_id": RP_ID, "user": {}, "enterprise": None})
    provider = FakeProvider(exclude=[existing])
    enroller, ui, provider = make(
        profile, key, ui=FakeUI(current_pins=["123456"]), provider=provider, source=source
    )

    with pytest.raises(EnrollError, match="already registered"):
        enroller.run()
    assert provider.events == ["preflight", "begin", "cancel"]
    assert len(key.credentials) == 1


def test_provider_failure_cancels_the_pending_registration():
    key = FakeAuthenticator()
    provider = FakeProvider()
    provider.fail_complete = True
    enroller, ui, provider = make(Profile(), key, provider=provider)

    with pytest.raises(RuntimeError, match="server said no"):
        enroller.run()
    assert provider.events == ["preflight", "begin", "complete", "cancel"]
    assert key.closed >= 1


def test_reset_is_retried_when_the_key_refuses_it():
    key = FakeAuthenticator()
    source = FakeSource(key)

    class SlowOperator(FakeUI):
        attempts = 0

        def status(self, template, **params):
            super().status(template, **params)
            if "insert the security key" in template:
                self.attempts += 1
                if self.attempts == 1:
                    key.fresh = False  # too slow the first time

    enroller, ui, provider = make(Profile(), key, ui=SlowOperator(), source=source)

    result = enroller.run()

    assert ui.attempts == 2
    assert key.log.count("reset") == 2
    assert key.pin == result.pin


def test_cancel_while_waiting_for_reinsertion():
    key = FakeAuthenticator()
    source = FakeSource(key)
    cancel = threading.Event()

    class Canceller(FakeUI):
        def status(self, template, **params):
            self.messages.append(template)
            if "remove the security key" in template:
                cancel.set()

    provider = FakeProvider()
    enroller = Enroller(
        provider, Profile(), USER, "", None, Canceller(), source=source, cancel=cancel
    )

    with pytest.raises(EnrollCancelled):
        enroller.run()
    assert "reset" not in key.log
    assert "begin" not in provider.events


def test_no_key_connected():
    source = FakeSource()
    enroller = Enroller(FakeProvider(), Profile(), USER, "", None, FakeUI(), source=source)
    with pytest.raises(EnrollError, match="No security key detected"):
        enroller.run()


def test_selected_key_is_used_when_several_are_connected():
    first, second = FakeAuthenticator("first"), FakeAuthenticator("second")
    source = FakeSource(first, second)
    ui = FakeUI(source)

    def status(template, **params):
        ui.messages.append(template)
        # Only the chosen key is unplugged and re-inserted.
        if "remove the security key" in template:
            source.devices = [first]
        elif "insert the security key" in template:
            source.devices = [first, second]
            second.fresh = True

    ui.status = status
    enroller = Enroller(
        FakeProvider(), Profile(), USER, "", "nfc:second", ui, source=source
    )

    result = enroller.run()

    assert second.pin == result.pin and len(second.credentials) == 1
    assert first.pin is None and first.credentials == []
    assert "reset" not in first.log


def test_user_handle_roundtrip():
    assert b64url_decode(b64url_encode(b"\x00\xff\x10")) == b"\x00\xff\x10"


def test_compose_key_name():
    assert compose_key_name("YubiKey 5 NFC", 12345678) == "YubiKey 5 NFC 12345678"
    assert compose_key_name("", 12345678) == "YubiKey 12345678"
    assert compose_key_name("  Spare  ", None) == "Spare"
    # A provider limit shortens the name, never the serial number.
    limited = compose_key_name("A very long descriptive key name", 12345678, 30)
    assert len(limited) <= 30 and limited.endswith(" 12345678")
    assert compose_key_name("x" * 40, None, 30) == "x" * 30


def test_serial_number_is_appended_to_the_registered_name():
    key = FakeAuthenticator()
    key.serial = 23456789
    source = FakeSource(key)
    ui = FakeUI(source)
    provider = FakeProvider()
    provider.max_display_name = 20
    enroller = Enroller(
        provider, Profile(), USER, "Finance YubiKey", None, ui, source=source, append_serial=True
    )

    result = enroller.run()

    assert provider.completed[1] == result.display_name == "Finance Yub 23456789"
    assert any("S/N 23456789" in m for m in ui.messages)  # shown during enrollment


def test_name_is_untouched_without_the_option_or_without_a_serial():
    key = FakeAuthenticator()
    key.serial = 23456789
    enroller, ui, provider = make(Profile(), key)
    assert enroller.run().display_name == "Alice's key"

    blank = FakeAuthenticator()
    source = FakeSource(blank)
    provider = FakeProvider()
    enroller = Enroller(
        provider, Profile(), USER, "Spare", None, FakeUI(source), source=source, append_serial=True
    )
    assert enroller.run().display_name == "Spare"


def test_freshly_inserted_key_is_reset_without_reinsertion():
    key = FakeAuthenticator()
    key.fresh = True  # just plugged in
    source = FakeSource(key)
    ui = FakeUI(source)
    enroller = Enroller(
        FakeProvider(), Profile(), USER, "", None, ui, source=source, try_reset_first=True
    )

    result = enroller.run()

    assert key.pin == result.pin
    assert not any("remove the security key" in m for m in ui.messages)


def test_reset_first_falls_back_to_reinsertion_when_refused():
    key = FakeAuthenticator()  # has been plugged in for a while
    source = FakeSource(key)
    ui = FakeUI(source)
    enroller = Enroller(
        FakeProvider(), Profile(), USER, "", None, ui, source=source, try_reset_first=True
    )

    result = enroller.run()

    assert key.log.count("reset") == 2 and key.pin == result.pin
    assert any("remove the security key" in m for m in ui.messages)


def test_key_already_used_in_the_batch_is_refused_before_any_change():
    key = FakeAuthenticator()
    key.serial = 111
    key.pin = "135790"
    key.fresh = True
    source = FakeSource(key)
    provider = FakeProvider()
    enroller = Enroller(
        provider, Profile(), USER, "", None, FakeUI(source), source=source,
        try_reset_first=True, used_serials={111},
    )

    with pytest.raises(EnrollError, match="already enrolled in this batch"):
        enroller.run()
    assert "reset" not in key.log and key.pin == "135790"
    assert "begin" not in provider.events
