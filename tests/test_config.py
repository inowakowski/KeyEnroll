from __future__ import annotations

import json

import pytest

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


def test_allowed_key_models_are_stored_and_cleaned(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    store.upsert_profile(
        Profile(
            name="yubikeys",
            allowed_models=[{"aaguid": "CB69481E-8FF7-4039-93EC-0A2729A154A8", "name": "YubiKey 5"}],
            min_firmware="5.7",
            unknown_firmware="warn",
        )
    )
    raw = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    entry = next(p for p in raw["profiles"] if p["name"] == "yubikeys")
    entry["allowed_models"].append({"aaguid": "not an aaguid"})
    entry["allowed_models"].append("garbage")
    entry["unknown_firmware"] = "explode"
    (tmp_path / "config.json").write_text(json.dumps(raw), encoding="utf-8")

    loaded = ConfigStore(tmp_path / "config.json").profile("yubikeys")
    assert loaded.allowed_models == [
        {"aaguid": "cb69481e-8ff7-4039-93ec-0a2729a154a8", "name": "YubiKey 5"}
    ]
    assert (loaded.min_firmware, loaded.unknown_firmware) == ("5.7", "refuse")


# -- moving the configuration to another workstation ---------------------------

from keyenroll.config import (  # noqa: E402
    ImportProblem,
    apply_import,
    export_config,
    parse_import,
)

KINDS = {"entra", "okta", "pingone", "pingone_aic"}


def exported_store(tmp_path):
    store = ConfigStore(tmp_path / "a" / "config.json")
    store.upsert_profile(Profile(name="strict", min_pin_length=8, random_pin_length=8))
    store.upsert_instance(
        Instance(name="Prod", kind="entra", settings={"tenant_id": "t", "client_id": "c"},
                 default_profile="strict")
    )  # fmt: skip
    store.ui["window_geometry"] = "xyz"
    store.message_subject = "Your key"
    store.save()
    return store


def test_export_holds_no_ids_layout_or_secrets_and_imports_with_new_ids(tmp_path):
    source = exported_store(tmp_path)
    data = export_config(source)
    text = json.dumps(data)
    assert data["format"] == "keyenroll-config" and data["version"] == 1
    assert source.instances[0].id not in text and "window_geometry" not in text
    assert "token" not in text.lower()

    target = ConfigStore(tmp_path / "b" / "config.json")
    imported = parse_import(json.dumps(data).encode(), KINDS)
    outcome = apply_import(target, imported)

    assert (outcome.added, outcome.replaced, outcome.skipped) == (3, 0, 0)  # 2 profiles + 1
    reloaded = ConfigStore(target.path)
    prod = reloaded.instances[0]
    assert prod.name == "Prod" and prod.id != source.instances[0].id
    assert reloaded.active_instance_id == prod.id
    # "default" existed on both sides and was added under a new name; the
    # instance still points at the profile it had.
    assert [p.name for p in reloaded.profiles] == ["default", "default (2)", "strict"]
    assert prod.default_profile == "strict"
    assert reloaded.message_subject == "Your key"


def test_name_clashes_are_kept_replaced_or_renamed(tmp_path):
    data = json.dumps(export_config(exported_store(tmp_path))).encode()

    def target(name):
        store = ConfigStore(tmp_path / name / "config.json")
        store.upsert_instance(Instance(name="Prod", kind="okta", settings={"domain": "old"}))
        return store

    kept = target("skip")
    old_id = kept.instances[0].id
    apply_import(kept, parse_import(data, KINDS), clash="skip", profiles=False)
    assert [(i.name, i.kind) for i in kept.instances] == [("Prod", "okta")]

    replaced = target("replace")
    old_id = replaced.instances[0].id
    outcome = apply_import(replaced, parse_import(data, KINDS), clash="replace")
    (prod,) = replaced.instances
    assert (prod.id, prod.kind, prod.settings["tenant_id"]) == (old_id, "entra", "t")
    assert outcome.replaced_instances == [(old_id, True)]  # provider type changed

    renamed = target("rename")
    apply_import(renamed, parse_import(data, KINDS), clash="rename")
    assert [i.name for i in renamed.instances] == ["Prod", "Prod (2)"]


@pytest.mark.parametrize(
    "raw, message",
    [
        (b"not json", "not a KeyEnroll configuration"),
        (b'{"format": "something-else", "version": 1}', "not a KeyEnroll configuration"),
        (b'{"format": "keyenroll-config", "version": 99}', "newer version"),
        (b"{" + b" " * 1_000_001 + b"}", "too large"),
    ],
    ids=["not-json", "other-format", "newer-version", "too-large"],
)
def test_files_that_are_not_an_export_are_refused(raw, message):
    with pytest.raises(ImportProblem, match=message):
        parse_import(raw, KINDS)


def test_unusable_entries_are_left_out_and_named(tmp_path):
    raw = json.dumps({
        "format": "keyenroll-config", "version": 1,
        "instances": [
            {"name": "Ok", "kind": "okta", "settings": {"domain": "x"}},
            {"name": "Odd", "kind": "unknown-idp", "settings": {}},
            {"name": "Broken", "kind": "okta", "settings": "no"},
        ],
        "profiles": [{"name": "bad", "min_pin_length": "eight"}, {"name": "", "reset": True}],
    }).encode()  # fmt: skip
    imported = parse_import(raw, KINDS)
    assert [i.name for i in imported.instances] == ["Ok"]
    assert imported.skipped == ["Odd", "Broken", "bad", "?"]
