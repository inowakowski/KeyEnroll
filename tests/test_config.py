from __future__ import annotations

import json

from keyenroll.config import ConfigStore, Instance, Profile
from keyenroll.fido.pin import generate_pin, is_trivial
from keyenroll.secrets_store import KeyringTokenStore


def test_first_run_has_default_profile(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    assert [p.name for p in store.profiles] == ["default"]
    p = store.profiles[0]
    # Same defaults as the YubiEnroll CLI.
    assert (p.min_pin_length, p.reset, p.random_pin, p.random_pin_length) == (4, True, True, 6)
    assert not (p.require_always_uv or p.require_ea or p.force_pin_change)
    assert store.active_instance is None


def test_instances_persist_and_switch(tmp_path):
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    a = Instance(name="Prod Entra", kind="entra", settings={"tenant_id": "t"})
    b = Instance(name="Okta dev", kind="okta", settings={"domain": "d"})
    store.upsert_instance(a)
    store.upsert_instance(b)
    assert store.active_instance.id == a.id  # first one becomes active
    store.set_active(b.id)

    reloaded = ConfigStore(path)
    assert [i.name for i in reloaded.instances] == ["Prod Entra", "Okta dev"]
    assert (reloaded.theme, reloaded.append_serial) == ("yubico", False)  # the default scheme
    reloaded.theme, reloaded.append_serial = "dark", True
    reloaded.save()
    again = ConfigStore(path)
    assert (again.theme, again.append_serial) == ("dark", True)
    assert reloaded.active_instance.kind == "okta"
    assert reloaded.instances[0].settings == {"tenant_id": "t"}

    reloaded.delete_instance(b.id)
    assert reloaded.active_instance.id == a.id
    assert "token" not in path.read_text().lower()


def test_profile_rename_updates_instance_default(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    store.upsert_instance(Instance(name="x", kind="okta", default_profile="default"))
    store.upsert_profile(Profile(name="strict", min_pin_length=8, random_pin_length=8), old_name="default")
    assert store.instances[0].default_profile == "strict"
    assert [p.name for p in store.profiles] == ["strict"]
    store.delete_profile("strict")
    assert store.instances[0].default_profile is None
    assert [p.name for p in store.profiles] == ["default"]  # never left empty


def test_configuration_from_before_the_rename_is_carried_over(tmp_path):
    old = tmp_path / "YubiEnrollGUI" / "config.json"
    old.parent.mkdir()
    legacy = ConfigStore(old)
    legacy.upsert_instance(Instance(name="Okta lab", kind="okta", settings={"domain": "d"}))
    new = tmp_path / "KeyEnroll" / "config.json"

    store = ConfigStore(new, legacy_path=old)
    assert [i.name for i in store.instances] == ["Okta lab"]
    assert not new.exists()  # nothing is written until something changes

    store.theme = "yubico"
    store.save()
    assert new.exists()
    # From now on the new file wins, the old one is left untouched.
    legacy.delete_instance(legacy.instances[0].id)
    assert [i.name for i in ConfigStore(new, legacy_path=old).instances] == ["Okta lab"]


def test_legacy_location_matches_the_platform(monkeypatch, tmp_path):
    from keyenroll import config

    monkeypatch.delenv("KEYENROLL_HOME", raising=False)
    current, legacy = config.config_dir(), config.legacy_config_dir()
    assert legacy.parent == current.parent
    assert legacy.name in ("YubiEnrollGUI", "yubienroll-gui") and legacy != current
    monkeypatch.setenv("KEYENROLL_HOME", str(tmp_path))
    assert config.legacy_config_dir() is None  # explicit location: no fallback


def test_unknown_keys_in_file_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"profiles": [{"name": "p", "future_option": 1}], "instances": []}))
    assert ConfigStore(path).profiles[0].name == "p"


def test_profile_validation():
    assert Profile().problems() == []
    assert Profile(min_pin_length=3).problems()
    assert Profile(min_pin_length=8, random_pin_length=6).problems()
    assert Profile(min_pin_length=8, random_pin=False, random_pin_length=6).problems() == []
    assert Profile(name=" ").problems()


def test_generated_pins_are_numeric_and_not_trivial():
    for length in (4, 6, 12):
        for _ in range(200):
            pin = generate_pin(length)
            assert len(pin) == length and pin.isdigit() and not is_trivial(pin)
            assert pin[0] != "0"  # survives a round trip through a spreadsheet
    for weak in ("123456", "654321", "000000", "111122", "890123"):
        assert is_trivial(weak)
    assert not is_trivial("482915")


class FakeKeyring:
    def __init__(self):
        self.items = {}

    def get_password(self, service, name):
        return self.items.get((service, name))

    def set_password(self, service, name, value):
        assert len(value) <= 1000, "exceeds what Windows Credential Manager accepts"
        self.items[(service, name)] = value

    def delete_password(self, service, name):
        del self.items[(service, name)]


def test_long_tokens_are_chunked_for_the_os_keyring():
    backend = FakeKeyring()
    store = KeyringTokenStore(backend)
    long_token = "x" * 2500 + "end"
    store.set("inst", long_token)
    assert store.get("inst") == long_token
    assert store.get("other") is None

    store.set("inst", "short")  # leftover chunks of the long value must go
    assert store.get("inst") == "short"
    assert len(backend.items) == 2

    store.delete("inst")
    assert backend.items == {} and store.get("inst") is None


def test_damaged_file_is_set_aside_and_the_app_still_starts(tmp_path):
    path = tmp_path / "config.json"
    for damaged in ('{"instances": [', '[1, 2, 3]', '{"instances": [{"kind": "okta"}]}', '{"profiles": 5}'):
        path.write_text(damaged)
        store = ConfigStore(path)
        assert store.instances == [] and [p.name for p in store.profiles] == ["default"]
        backup = store.unreadable_backup
        assert backup is not None and backup != path and backup.read_text() == damaged
        assert not path.exists()
        backup.unlink()
        store.upsert_instance(Instance(name="New", kind="okta"))
        assert ConfigStore(path).unreadable_backup is None


def test_message_templates_and_layout_state_persist(tmp_path):
    path = tmp_path / "config.json"
    store = ConfigStore(path)
    assert (store.message_subject, store.message_body, store.ui) == ("", "", {})
    store.message_subject, store.message_body = "Key for {name}", "PIN {pin}"
    store.ui["enroll_splitter"] = "400,500"
    store.save()
    again = ConfigStore(path)
    assert (again.message_subject, again.message_body) == ("Key for {name}", "PIN {pin}")
    assert again.ui == {"enroll_splitter": "400,500"}
