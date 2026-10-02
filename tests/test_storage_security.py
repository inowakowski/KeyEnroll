"""What is kept where, and who can get at it: the settings folder, files that
contain PINs, the credential store, and the clipboard."""

from __future__ import annotations

import json
import os
import stat
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from keyenroll import bulk, config, handover, secrets_store
from keyenroll.bulk import BulkRow
from keyenroll.config import ConfigStore, Instance
from keyenroll.providers.base import DirectoryUser
from keyenroll.ui import common

posix_only = pytest.mark.skipif(os.name != "posix", reason="POSIX file modes")
PIN = "482915"


def mode(path) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


# -- the settings folder -------------------------------------------------------


@posix_only
def test_settings_folder_is_closed_to_other_accounts(tmp_path, monkeypatch):
    monkeypatch.delenv("KEYENROLL_HOME", raising=False)
    folder = tmp_path / "keyenroll"
    folder.mkdir(mode=0o755)  # as an earlier version left it
    monkeypatch.setattr(config, "config_dir", lambda: folder)
    store = ConfigStore(folder / "config.json")
    store.upsert_instance(Instance(name="Prod", kind="okta"))
    assert mode(folder) == 0o700


@posix_only
def test_a_folder_chosen_by_the_operator_keeps_its_permissions(tmp_path, monkeypatch):
    folder = tmp_path / "shared"
    folder.mkdir(mode=0o755)
    monkeypatch.setenv("KEYENROLL_HOME", str(folder))
    ConfigStore().upsert_instance(Instance(name="Prod", kind="okta"))
    assert (folder / "config.json").exists() and mode(folder) == 0o755


def test_settings_never_contain_tokens_or_pins(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    store.upsert_instance(
        Instance(name="Prod", kind="okta", settings={"domain": "example.okta.com", "client_id": "abc"})
    )
    text = (tmp_path / "config.json").read_text(encoding="utf-8")
    for word in ("token", "secret", "password"):
        assert word not in text.lower(), word

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key, value
                yield from walk(value)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)

    # The only PIN-related entries are profile options: lengths and switches.
    about_pins = {k: v for k, v in walk(json.loads(text)) if "pin" in k.lower()}
    assert about_pins and all(isinstance(v, (bool, int)) for v in about_pins.values())


# -- files that contain PINs -----------------------------------------------------


def exported_files(tmp_path):
    user = DirectoryUser("1", "alice@x.com", "Alice", "alice@x.com")
    rows = [BulkRow("alice@x.com", user=user, status=bulk.DONE, serial=1000, pin=PIN)]
    results, message = tmp_path / "results.csv", tmp_path / "message.txt"
    for path in (results, message):
        path.write_text("an older, longer file that everyone could read " * 40)
        if os.name == "posix":
            os.chmod(path, 0o644)
    bulk.write_results(results, rows)
    handover.save_text(message, "Your key", f"PIN: {PIN}\n")
    return results, message


def test_files_with_pins_replace_what_was_there(tmp_path):
    for path in exported_files(tmp_path):
        data = path.read_bytes()
        assert PIN.encode() in data and b"an older" not in data


@posix_only
def test_files_with_pins_are_readable_by_the_owner_only(tmp_path):
    # Also when the file existed before with wider permissions.
    for path in exported_files(tmp_path):
        assert mode(path) == 0o600, path.name


# -- the credential store ----------------------------------------------------------


def backend_from(module: str, **attrs):
    return type("Backend", (), {"__module__": module, **attrs})()


def test_only_stores_of_the_operating_system_are_trusted():
    trusted = secrets_store.protected_by_os
    assert trusted(backend_from("keyring.backends.Windows"))
    assert trusted(backend_from("keyring.backends.macOS"))
    assert trusted(backend_from("keyring.backends.SecretService"))
    # keyrings.alt keeps secrets in a file, in clear text or lightly encrypted.
    assert not trusted(backend_from("keyrings.alt.file"))
    chain = backend_from(
        "keyring.backends.chainer",
        backends=[backend_from("keyring.backends.SecretService"), backend_from("keyrings.alt.file")],
    )
    assert not trusted(chain)


def test_sign_in_is_not_remembered_rather_than_written_to_a_plain_file(monkeypatch, caplog):
    import keyring

    stored = {}
    plain = backend_from(
        "keyrings.alt.file",
        get_password=lambda self, s, n: stored.get(n),
        set_password=lambda self, s, n, v: stored.__setitem__(n, v),
    )
    monkeypatch.setattr(keyring, "get_keyring", lambda: plain)
    store = secrets_store.default_store()
    assert not store.persistent and "not an OS credential store" in caplog.text
    store.set("inst", "refresh-token")
    assert store.get("inst") == "refresh-token" and stored == {}


# -- the clipboard -------------------------------------------------------------------


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    "platform, markers",
    [
        (
            "win32",
            {
                "ExcludeClipboardContentFromMonitorProcessing": b"1",
                "CanIncludeInClipboardHistory": b"\0\0\0\0",
                "CanUploadToCloudClipboard": b"\0\0\0\0",
            },
        ),
        ("darwin", {"application/x-nspasteboard-concealed-type": PIN.encode()}),
        ("linux", {"x-kde-passwordManagerHint": b"secret"}),
    ],
)
def test_copied_pin_is_marked_as_a_secret_for_clipboard_histories(app, platform, markers):
    mime = common.sensitive_mime(PIN, platform)
    assert mime.text() == PIN
    for name, value in markers.items():
        assert mime.hasFormat(name) and bytes(mime.data(name)) == value, name


def test_copying_goes_through_the_marked_form(app):
    common.copy_sensitive(PIN)
    mime = QGuiApplication.clipboard().mimeData()
    assert mime.text() == PIN
    expected = common.sensitive_mime(PIN, sys.platform).formats()
    assert set(expected) <= set(mime.formats())
