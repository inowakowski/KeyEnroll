"""Drives the real windows (offscreen) against a fake provider and fake key."""

from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox

from fake_authenticator import FakeAuthenticator
from test_enroll import FakeProvider, FakeSource
from keyenroll.config import ConfigStore, Instance, Profile
from keyenroll.fido import enroll
from keyenroll.providers.base import AuthRequired, Credential, DirectoryUser
from keyenroll.secrets_store import TokenStore
from keyenroll import bulk
from keyenroll.ui import dialogs
from keyenroll.ui.common import AppContext
from keyenroll.ui.main_window import MainWindow

USERS = [
    DirectoryUser("u1", "alice@example.com", "Alice Example", "alice@example.com"),
    DirectoryUser("u2", "bob@example.com", "Bob Example", "bob@example.com"),
]


class GuiProvider(FakeProvider):
    supports_credential_list = True
    supports_credential_delete = True

    def __init__(self, instance):
        super().__init__()
        self.label = instance.kind
        self.instance = instance
        self.session = True
        self.credentials = [Credential("c1", "Old key", "2026-01-01", "YubiKey 5")]

    def has_session(self):
        return self.session

    def search_users(self, query):
        if not self.session:
            raise AuthRequired("Not signed in. Sign in to the identity provider first.")
        return [u for u in USERS if query.lower() in u.display_name.lower()]

    def find_user(self, identifier):
        return next((u for u in USERS if u.username == identifier), None)

    def list_credentials(self, user):
        return list(self.credentials)

    def delete_credential(self, user, credential_id):
        self.credentials = [c for c in self.credentials if c.id != credential_id]

    def logout(self):
        self.session = False


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def wait_until(condition, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError("condition not met in time")


@pytest.fixture
def gui(app, tmp_path, monkeypatch):
    monkeypatch.setattr(enroll, "POLL_INTERVAL", 0.01)
    config = ConfigStore(tmp_path / "config.json")
    config.upsert_instance(Instance(name="Prod", kind="entra", default_profile="default"))
    config.upsert_instance(Instance(name="Lab", kind="okta"))
    key = FakeAuthenticator("Fake Key")
    source = FakeSource(key)
    providers = {}

    def factory(instance, tokens):
        return providers.setdefault(instance.id, GuiProvider(instance))

    ctx = AppContext(config, TokenStore(), source=source, provider_factory=factory)
    window = MainWindow(ctx)
    window.show()

    # Modal dialogs: confirm message boxes, capture the result dialog.
    shown = {"boxes": [], "results": []}

    def confirm(box):
        shown["boxes"].append(box.text())
        accepting = (
            QMessageBox.ButtonRole.AcceptRole,
            QMessageBox.ButtonRole.DestructiveRole,
            QMessageBox.ButtonRole.YesRole,
        )
        for button in box.buttons():
            if box.buttonRole(button) in accepting:
                button.click()
                break
        return 0

    monkeypatch.setattr(QMessageBox, "exec", confirm)
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda p, t, text, *a: shown["boxes"].append(text))
    )
    monkeypatch.setattr(
        QMessageBox, "information", staticmethod(lambda p, t, text, *a: shown["boxes"].append(text))
    )

    def question(parent, title, text, *a):
        shown["boxes"].append(text)
        return QMessageBox.StandardButton.Yes

    monkeypatch.setattr(QMessageBox, "question", staticmethod(question))

    def capture(dialog):
        shown["results"].append(dialog)
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(dialogs.ResultDialog, "exec", capture)

    # The operator: unplugs and re-inserts the key when the app asks for it.
    page = window.enroll_page
    original = page._on_status

    def operator(template, params):
        original(template, params)
        if "remove the security key" in template:
            source.present = False
        elif "insert the security key" in template:
            source.present = True
            key.fresh = True

    page._on_status = operator

    yield window, ctx, key, source, shown
    page.shutdown()
    window.close()


def rescan(page):
    """Scans for keys again, after a test changed the state of the fake key."""
    wait_until(lambda: not page._refreshing)
    page.refresh_keys()
    wait_until(lambda: not page._refreshing and page.key_combo.currentData() is not None)


def pick_user(page, name):
    page.picker.query.setText(name)
    page.picker.search()
    wait_until(lambda: page.picker.table.rowCount() == 1)
    assert page.picker.selected().display_name.startswith(name)


def test_full_enrollment_through_the_window(gui):
    window, ctx, key, source, shown = gui
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    wait_until(lambda: page.key_combo.currentData() is not None)
    assert "Fake Key" in page.key_combo.currentText()
    pick_user(page, "Alice")
    page.display_name.setText("Alice's YubiKey")

    page.start.click()
    assert ctx.busy and not window.instance_combo.isEnabled()
    wait_until(lambda: not page.is_running())

    assert not ctx.busy and window.instance_combo.isEnabled()
    assert "factory reset" in shown["boxes"][0]  # the destructive step was confirmed
    result = shown["results"][0]
    provider = ctx.provider
    assert provider.completed[1] == "Alice's YubiKey"
    assert len(key.credentials) == 1 and key.pin is not None
    # The temporary PIN shown to the operator is the one now on the key.
    pin_label = result.findChild(type(page.step), "pin")
    assert pin_label.text() == key.pin
    log = [page.log.item(i).text() for i in range(page.log.count())]
    assert any("remove the security key" in line for line in log)
    assert any("Touch the security key" in line for line in log)


def test_pin_prompt_and_per_enrollment_overrides(gui, monkeypatch):
    window, ctx, key, source, shown = gui
    key.pin = "135790"
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    rescan(page)
    assert "PIN is set" in page.key_info.text()
    pick_user(page, "Bob")
    # Override the profile for this enrollment only.
    page.form.reset.setChecked(False)
    page.form.random_pin.setChecked(False)

    answers = iter(["000000", "135790"])
    prompts = []

    def answer(dialog):
        prompts.append(dialog)
        dialog.pin.setText(next(answers))
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(dialogs.CurrentPinDialog, "exec", answer)

    page.start.click()
    wait_until(lambda: not page.is_running())

    assert len(prompts) == 2
    assert key.pin == "135790" and "reset" not in key.log
    assert len(key.credentials) == 1
    assert shown["results"][0].findChild(type(page.step), "pin") is None
    assert ctx.config.profile("default").reset is True  # stored profile untouched


def test_cancel_during_reset_leaves_key_alone(gui):
    window, ctx, key, source, shown = gui
    key.pin = "135790"
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    wait_until(lambda: page.key_combo.currentData() is not None)
    pick_user(page, "Alice")
    page._on_status = lambda template, params: (
        page.cancel.click() if "remove the security key" in template else None
    )

    page.start.click()
    wait_until(lambda: not page.is_running())

    assert key.pin == "135790" and key.credentials == []
    assert shown["results"] == []
    assert page.start.isEnabled() and not ctx.busy


def test_validation_messages_before_starting(gui):
    window, ctx, key, source, shown = gui
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    wait_until(lambda: page.key_combo.currentData() is not None)

    page.start.click()
    assert "select one from the list" in shown["boxes"][-1]

    pick_user(page, "Alice")
    ctx.provider.session = False
    page.start.click()
    assert "Sign in to the identity provider first" in shown["boxes"][-1]
    assert not page.is_running() and key.log.count("reset") == 0


def test_switching_instances_changes_provider_and_clears_selection(gui):
    window, ctx, key, source, shown = gui
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    pick_user(page, "Alice")
    first = ctx.provider
    assert window.instance_combo.count() == 2

    window.instance_combo.setCurrentIndex(1)

    assert ctx.config.active_instance.name == "Lab"
    assert ctx.provider is not first and ctx.provider.instance.kind == "okta"
    assert page.picker.table.rowCount() == 0  # users of the other tenant are gone
    # Each instance keeps its own session.
    ctx.provider.session = False
    ctx.session_changed.emit()
    assert window.session_button.text() == "Sign in"
    window.instance_combo.setCurrentIndex(0)
    assert window.session_button.text() == "Sign out"
    assert ConfigStore(ctx.config.path).active_instance.name == "Prod"


def test_credentials_page_lists_and_deletes(gui):
    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(2)
    page = window.pages.currentWidget()
    pick_user(page, "Alice")
    wait_until(lambda: page.table.rowCount() == 1)
    assert not page.delete.isEnabled()
    page.table.selectRow(0)
    assert page.delete.isEnabled()

    page.delete.click()
    wait_until(lambda: page.table.rowCount() == 0)

    assert ctx.provider.credentials == []
    assert "Old key" in shown["boxes"][-1]


def test_profiles_page_saves_and_enroll_page_follows(gui):
    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(3)
    page = window.pages.currentWidget()
    page.new.click()
    page.name.setText("strict")
    page.form.min_pin.setValue(8)
    page.form.random_len.setValue(6)
    page.save.click()
    assert "cannot be shorter" in shown["boxes"][-1]  # invalid combination refused
    assert ctx.config.profile("strict") is None

    page.form.random_len.setValue(10)
    page.form.always_uv.setChecked(True)
    page.save.click()

    stored = ConfigStore(ctx.config.path).profile("strict")
    assert (stored.min_pin_length, stored.random_pin_length, stored.require_always_uv) == (8, 10, True)
    combo = window.enroll_page.profile_combo
    assert [combo.itemText(i) for i in range(combo.count())] == ["default", "strict"]
    combo.setCurrentIndex(1)
    assert window.enroll_page.form.profile().min_pin_length == 8


def test_first_run_opens_instances_page(app, tmp_path):
    ctx = AppContext(ConfigStore(tmp_path / "c.json"), TokenStore(), source=FakeSource())
    window = MainWindow(ctx)
    assert window.nav.currentRow() == 4
    assert window.page_title.text() == "Instances"
    assert not window.session_button.isEnabled()
    window.close()


def test_serial_number_is_shown_and_added_to_the_key_name(gui):
    window, ctx, key, source, shown = gui
    key.serial = 23456789
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    rescan(page)
    assert page.key_serial.text() == "23456789"
    assert "S/N 23456789" in page.key_combo.currentText()
    pick_user(page, "Alice")
    page.display_name.setText("Finance")
    assert not page.name_preview.isVisible()

    page.append_serial.setChecked(True)
    assert "Finance 23456789" in page.name_preview.text()
    assert ConfigStore(ctx.config.path).append_serial is True  # remembered

    page.start.click()
    wait_until(lambda: not page.is_running())

    assert "Finance 23456789" in shown["boxes"][0]  # confirmation names the key
    assert ctx.provider.completed[1] == "Finance 23456789"
    labels = [w.text() for w in shown["results"][0].findChildren(type(page.step))]
    assert "23456789" in labels and "Finance 23456789" in labels


def test_bulk_page_imports_enrolls_and_exports(gui, tmp_path, monkeypatch):
    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(1)
    page = window.bulk_page
    assert window.page_title.text() == "Bulk enrollment"
    assert not page.start.isEnabled()

    users_file = tmp_path / "users.csv"
    users_file.write_text(
        "username;department\nalice@example.com;IT\nghost@example.com;HR\nbob@example.com;HR\n"
    )
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(users_file), ""))
    )
    page.load.click()
    wait_until(lambda: not page.is_running() and page.table.rowCount() == 3)
    assert [r.status for r in page.rows] == [bulk.READY, bulk.NOT_FOUND, bulk.READY]
    assert page.table.item(1, 2).text() == "Not found"
    assert "2 ready" in page.summary.text() and "1 not found" in page.summary.text()

    keys = [FakeAuthenticator("k1"), FakeAuthenticator("k2")]
    keys[0].serial, keys[1].serial = 501, 502
    pile = list(keys)
    source.devices = []
    original = page._on_status

    def operator(template, params):
        original(template, params)
        if template.startswith("Remove the previous key"):
            source.devices = []
        elif template.startswith("Insert the security key for"):
            nxt = pile.pop(0)
            nxt.fresh = True
            source.devices = [nxt]

    page._on_status = operator
    page.key_name.setText("Corp")
    page.start.click()
    assert ctx.busy and not window.instance_combo.isEnabled()
    assert not window.enroll_page.start.isEnabled()  # the key is in use by the batch
    wait_until(lambda: not page.is_running())

    assert "factory reset" in shown["boxes"][-1] and "2 security key(s)" in shown["boxes"][-1]
    assert [r.status for r in page.rows] == [bulk.DONE, bulk.NOT_FOUND, bulk.DONE]
    assert [k.pin for k in keys] == [page.rows[0].pin, page.rows[2].pin]
    assert page.table.item(0, 3).text() == "501" and page.table.item(2, 3).text() == "502"
    assert page.table.item(0, 4).text() == "••••••"  # PINs are masked on screen
    page.show_pins.setChecked(True)
    assert page.table.item(0, 4).text() == keys[0].pin
    assert page.progress.value() == 2 and page.progress.maximum() == 2
    assert not ctx.busy and window.enroll_page.start.isEnabled()
    assert page.has_unexported_pins()

    out = tmp_path / "out.csv"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *a, **k: (str(out), "CSV, semicolon separated (*.csv)")),
    )
    page.export.click()
    assert "plain text" in shown["boxes"][-1]  # the operator is warned first
    lines = out.read_text(encoding="utf-8-sig").splitlines()
    assert lines[1].split(";")[:7] == [
        "alice@example.com", "Alice Example", "alice@example.com", "Enrolled", "501", "Corp 501",
        keys[0].pin,
    ]
    assert lines[2].split(";")[3] == "Not found"
    assert not page.has_unexported_pins()


def test_bulk_failure_pauses_and_retry_resets_the_row(gui, tmp_path, monkeypatch):
    window, ctx, key, source, shown = gui
    page = window.bulk_page
    users_file = tmp_path / "users.txt"
    users_file.write_text("alice@example.com\nbob@example.com\n")
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(users_file), ""))
    )
    page.load.click()
    wait_until(lambda: not page.is_running() and page.table.rowCount() == 2)

    ctx.provider.fail_complete = True
    key.fresh = True
    page.start.click()
    wait_until(lambda: not page.is_running())

    assert [r.status for r in page.rows] == [bulk.FAILED, bulk.READY]
    assert "server said no" in page.table.item(0, 5).text()
    assert "server said no" in shown["boxes"][-1]
    assert page.retry.isEnabled()
    page.retry.click()
    assert [r.status for r in page.rows] == [bulk.READY, bulk.READY]
    assert page.table.item(0, 5).text() == ""


def test_bulk_list_is_locked_to_its_instance(gui, tmp_path, monkeypatch):
    window, ctx, key, source, shown = gui
    page = window.bulk_page
    users_file = tmp_path / "users.txt"
    users_file.write_text("alice@example.com\n")
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(users_file), ""))
    )
    page.load.click()
    wait_until(lambda: not page.is_running() and page.table.rowCount() == 1)
    assert page.start.isEnabled()

    window.instance_combo.setCurrentIndex(1)  # users of another tenant
    assert not page.start.isEnabled()
    assert "another instance" in page.step.text()
    window.instance_combo.setCurrentIndex(0)
    assert page.start.isEnabled()
    page.clear.click()
    assert page.table.rowCount() == 0 and not page.start.isEnabled()
