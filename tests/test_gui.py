"""Drives the real windows (offscreen) against a fake provider and fake key."""

from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
)

from fake_authenticator import FakeAuthenticator
from keyenroll import DOCS_URL, PROJECT_URL, bulk, i18n
from keyenroll.config import ConfigStore, Instance
from keyenroll.fido import enroll
from keyenroll.handover import Handover
from keyenroll.providers.base import AuthRequired, Credential, DirectoryUser
from keyenroll.secrets_store import TokenStore
from keyenroll.ui import common, dialogs
from keyenroll.ui.common import AppContext
from keyenroll.ui.main_window import PAGE_BULK, PAGE_INSTANCES, PAGE_SETTINGS, MainWindow
from test_enroll import FakeProvider, FakeSource

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


def labels_of(dialog):
    return [w.text() for w in dialog.findChildren(QLabel)]


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
        QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (str(out), ""))
    )
    choices = {"everyone": True, "pins": True}
    seen = []

    def choose(dialog):
        seen.append(dialog)
        assert dialog.enrolled.isChecked() and dialog.pins.isChecked()  # the defaults
        assert not dialog.warning.isHidden()  # the operator is warned about plain-text PINs
        dialog.everyone.setChecked(choices["everyone"])
        dialog.pins.setChecked(choices["pins"])
        dialog.format.setCurrentIndex(dialog.format.findData(";"))
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(dialogs.ExportDialog, "exec", choose)

    # A report without PINs can be shared, but does not count as saving them.
    choices.update(everyone=False, pins=False)
    page.export.click()
    report = out.read_text(encoding="utf-8-sig")
    assert keys[0].pin not in report and "ghost@example.com" not in report
    assert report.count("\n") == 3 and "alice@example.com" in report and "bob@example.com" in report
    assert page.has_unexported_pins()

    choices.update(everyone=True, pins=True)
    page.export.click()
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


# -- hand-over after an enrollment ---------------------------------------


def make_handover(**kw):
    values = dict(
        user=USERS[0], key_name="Finance 23456789", serial=23456789, pin="482915",
        must_change_pin=True, provider="Okta",
    )
    values.update(kw)
    return Handover(**values)


def test_result_dialog_copies_emails_and_saves_the_message(gui, tmp_path, monkeypatch):
    window, ctx, key, source, shown = gui
    dialog = dialogs.ResultDialog(make_handover(), ctx.config, window)
    clipboard = QGuiApplication.clipboard()

    dialog.copy_pin.click()
    assert clipboard.text() == "482915"
    assert "cleared" in dialog.feedback.text()

    dialog.copy_message.click()
    text = clipboard.text()
    assert "Alice Example" in text and "482915" in text and "23456789" in text
    assert "set your own PIN" in text

    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", staticmethod(lambda url: opened.append(url) or True))
    dialog.email.click()
    url = opened[0]
    assert isinstance(url, QUrl) and url.scheme() == "mailto" and url.path() == "alice@example.com"
    assert "482915" in url.toString() and "draft" in dialog.feedback.text()

    monkeypatch.setattr(QDesktopServices, "openUrl", staticmethod(lambda url: False))
    dialog.email.click()
    assert "No e-mail program" in dialog.feedback.text()

    target = tmp_path / "alice.txt"
    suggested = []

    def save_as(parent, title, name, *a):
        suggested.append(name)
        return str(target), ""

    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(save_as))
    dialog.save.click()
    assert suggested == ["keyenroll-alice@example.com.txt"]
    saved = target.read_text(encoding="utf-8-sig")
    assert saved.startswith("Your security key\n\nHello Alice Example") and "482915" in saved
    assert str(target) in dialog.feedback.text()


def test_result_dialog_without_a_generated_pin(gui):
    window, ctx, key, source, shown = gui
    dialog = dialogs.ResultDialog(
        make_handover(pin=None, pin_changed=False, must_change_pin=False), ctx.config, window
    )
    assert not hasattr(dialog, "copy_pin")
    assert "The PIN of the key was not changed." in labels_of(dialog)
    dialog.copy_message.click()
    assert "(provided separately)" in QGuiApplication.clipboard().text()


def test_copied_pin_leaves_the_clipboard_after_a_while(gui, monkeypatch):
    monkeypatch.setattr(common, "CLIPBOARD_CLEAR_MS", 30)
    clipboard = QGuiApplication.clipboard()
    common.copy_sensitive("482915")
    assert clipboard.text() == "482915"
    wait_until(lambda: clipboard.text() == "")

    # Something the operator copied afterwards is not wiped.
    common.copy_sensitive("135790")
    clipboard.setText("unrelated")
    time.sleep(0.08)
    QApplication.processEvents()
    assert clipboard.text() == "unrelated"


def test_enrollment_result_reaches_the_dialog_with_provider_and_key_name(gui):
    window, ctx, key, source, shown = gui
    key.serial = 23456789
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    rescan(page)
    pick_user(page, "Alice")
    page.form.force_change.setChecked(True)
    page.start.click()
    wait_until(lambda: not page.is_running())

    handed = shown["results"][0].handover
    assert handed.user.username == "alice@example.com" and handed.pin == key.pin
    assert handed.serial == 23456789 and handed.must_change_pin
    assert handed.provider == ctx.provider.label
    assert handed.key_name  # falls back to the product name when no name was typed


# -- settings page ---------------------------------------------------------


def test_settings_have_their_own_page(gui):
    window, ctx, key, source, shown = gui
    titles = [window.nav.item(i).text() for i in range(window.nav.count())]
    assert titles == ["Enroll", "Bulk enrollment", "Credentials", "Profiles", "Instances", "Settings"]
    window.nav.setCurrentRow(PAGE_INSTANCES)
    assert not hasattr(window.pages.currentWidget(), "theme")
    window.nav.setCurrentRow(PAGE_SETTINGS)
    page = window.pages.currentWidget()
    assert page.theme.currentData() == "yubico"
    # "Same as the system" and every offered language, each named in itself.
    offered = [page.language.itemText(i) for i in range(1, page.language.count())]
    assert offered == list(i18n.LANGUAGES.values())
    assert {"Deutsch", "Español", "Français", "Italiano", "Polski"} <= set(offered)
    assert window.page_title.text() == "Settings"


def test_message_template_can_be_customised_and_restored(gui):
    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(PAGE_SETTINGS)
    page = window.pages.currentWidget()
    assert page.subject.text() == "Your security key"
    assert "{pin}" in page.body.toPlainText()

    page.save_message.click()  # unchanged text is not frozen into the settings
    assert (ctx.config.message_subject, ctx.config.message_body) == ("", "")

    page.subject.setText("Key for {name}")
    page.body.setPlainText("PIN: {pin}\nSerial: {serial}")
    page.save_message.click()
    stored = ConfigStore(ctx.config.path)
    assert stored.message_subject == "Key for {name}"
    assert stored.message_body == "PIN: {pin}\nSerial: {serial}\n"

    dialog = dialogs.ResultDialog(make_handover(), ctx.config, window)
    dialog.copy_message.click()
    assert QGuiApplication.clipboard().text() == "PIN: 482915\nSerial: 23456789\n"

    page.reset_message.click()
    assert ConfigStore(ctx.config.path).message_body == ""
    assert "Hello {name}" in page.body.toPlainText()


def test_about_links_to_the_documentation(gui):
    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(PAGE_SETTINGS)
    links = [text for text in labels_of(window.pages.currentWidget()) if "href" in text]
    assert any(f'href="{DOCS_URL}"' in text for text in links)
    # No host of the site is built in: the project page says where it is.
    assert DOCS_URL.startswith(PROJECT_URL)


@pytest.mark.parametrize("lang", sorted(i18n.LANGUAGES))
def test_window_builds_in_every_language(app, tmp_path, lang):
    config = ConfigStore(tmp_path / "config.json")
    config.upsert_instance(Instance(name="Prod", kind="entra"))
    ctx = AppContext(
        config,
        TokenStore(),
        source=FakeSource(FakeAuthenticator("Fake Key")),
        provider_factory=lambda instance, tokens: GuiProvider(instance),
    )
    try:
        i18n.set_language(lang)
        window = MainWindow(ctx)
        titles = []
        for row in range(window.nav.count()):
            window.nav.setCurrentRow(row)
            QApplication.processEvents()
            titles.append(window.page_title.text())
        assert titles[PAGE_SETTINGS] == i18n.tr("Settings")
        assert len(set(titles)) == len(titles) and all(titles)
        if lang != "en":
            assert "Settings" not in titles and "Enroll" not in titles
        # Semicolons are what a spreadsheet expects wherever decimals use a comma.
        assert dialogs.ExportDialog(window).format.currentData() == ("," if lang == "en" else ";")
        handed = dialogs.ResultDialog(make_handover(), config, window)
        assert i18n.tr("Copy PIN") in [b.text() for b in handed.findChildren(QPushButton)]
        window.enroll_page.shutdown()
        window.bulk_page.shutdown()
        window.close()
    finally:
        i18n.set_language("en")


# -- layout of the enrollment page ------------------------------------------


def test_user_list_scrolls_sideways_instead_of_cutting_text(gui):
    window, ctx, key, source, shown = gui
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    long_user = DirectoryUser(
        "u9", "a.very.long.user.principal.name@subsidiary.example-corporation.com",
        "Aleksandra Konstantynopolitańczykowianka-Brzęczyszczykiewicz",
        "a.very.long.user.principal.name@subsidiary.example-corporation.com",
    )
    USERS.append(long_user)
    try:
        page.picker.query.setText("Aleksandra")
        page.picker.search()
        wait_until(lambda: page.picker.table.rowCount() == 1)
    finally:
        USERS.remove(long_user)
    table = page.picker.table
    header = table.horizontalHeader()
    assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive  # draggable
    metrics = table.fontMetrics()
    assert table.columnWidth(0) >= metrics.horizontalAdvance(long_user.display_name)
    assert table.columnWidth(1) >= metrics.horizontalAdvance(long_user.username)
    QApplication.processEvents()
    assert header.length() > table.viewport().width()
    assert table.horizontalScrollBar().maximum() > 0


def test_panes_are_resizable_and_the_layout_is_remembered(gui):
    window, ctx, key, source, shown = gui
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    QApplication.processEvents()
    assert page.splitter.count() == 2 and not page.splitter.childrenCollapsible()
    # The main action is large and sits with the options, not in the status bar.
    assert page.splitter.widget(1).isAncestorOf(page.start)
    assert page.start.minimumHeight() >= 48 and page.start.property("big") is True

    total = sum(page.splitter.sizes())
    page.splitter.setSizes([total - 460, 460])
    QApplication.processEvents()
    sizes = page.splitter.sizes()
    window.close()

    stored = ConfigStore(ctx.config.path)
    assert stored.ui["enroll_splitter"] == ",".join(str(v) for v in sizes)
    assert stored.ui["window_geometry"]

    again = MainWindow(AppContext(stored, TokenStore(), source=FakeSource()))
    again.show()
    # The test screen is smaller than the window, so Qt shrinks the restored
    # geometry; give the new window the old size before comparing the panes.
    again.resize(window.size())
    QApplication.processEvents()
    again.enroll_page._restore_splitter()
    QApplication.processEvents()
    assert again.enroll_page.splitter.sizes() == sizes
    again.close()

    # Nonsense in the settings file is ignored rather than applied.
    stored.ui["enroll_splitter"] = "abc,-5"
    broken = MainWindow(AppContext(stored, TokenStore(), source=FakeSource()))
    assert all(size >= 0 for size in broken.enroll_page.splitter.sizes())
    broken.close()


# -- bulk: hand-over for one user -------------------------------------------


def test_bulk_message_button_opens_the_hand_over_for_an_enrolled_user(gui, tmp_path, monkeypatch):
    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(PAGE_BULK)
    page = window.bulk_page
    users_file = tmp_path / "users.txt"
    users_file.write_text("alice@example.com\nghost@example.com\n")
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(users_file), ""))
    )
    page.load.click()
    wait_until(lambda: not page.is_running() and page.table.rowCount() == 2)
    key.serial, key.fresh = 777, True
    page.start.click()
    wait_until(lambda: not page.is_running())
    assert page.rows[0].status == bulk.DONE

    page.table.selectRow(1)  # not enrolled
    assert not page.handover.isEnabled()
    page.table.selectRow(0)
    assert page.handover.isEnabled()
    page.handover.click()

    handed = shown["results"][-1].handover
    assert (handed.user.username, handed.pin, handed.serial) == ("alice@example.com", key.pin, 777)
    assert handed.provider == ctx.provider.label


# -- sortable tables --------------------------------------------------------


def column(table, col):
    return [table.item(r, col).text() for r in range(table.rowCount())]


def test_natural_compare_reads_like_a_person():
    names = ["user10", "Bob", "user2", "alice", "User1", "", "bob2"]
    import functools

    ordered = sorted(names, key=functools.cmp_to_key(common.natural_compare))
    assert ordered == ["", "alice", "Bob", "bob2", "User1", "user2", "user10"]
    assert common.natural_compare("Key 9", "key 10") < 0
    assert common.natural_compare("ALICE", "alice") == 0
    assert common.natural_compare("a", "a1") < 0 < common.natural_compare("a1", "a")


def test_user_list_sorts_by_clicking_a_column(gui):
    window, ctx, key, source, shown = gui
    page = window.enroll_page
    window.nav.setCurrentRow(0)
    extra = [
        DirectoryUser("s1", "user10@example.com", "zoe Example", "z@example.com"),
        DirectoryUser("s2", "user2@example.com", "Adam Example", "m@example.com"),
        DirectoryUser("s3", "User1@example.com", "bartek Example", "a@example.com"),
    ]
    USERS.extend(extra)
    try:
        page.picker.query.setText("Example")
        page.picker.search()
        wait_until(lambda: page.picker.table.rowCount() == 5)
        table = page.picker.table
        header = table.horizontalHeader()
        assert table.isSortingEnabled() and header.sortIndicatorSection() == -1
        # Until a header is clicked the provider's order is kept.
        assert column(table, 0)[:2] == ["Alice Example", "Bob Example"]

        table.sortItems(0, Qt.SortOrder.AscendingOrder)
        assert column(table, 0) == [
            "Adam Example", "Alice Example", "bartek Example", "Bob Example", "zoe Example"
        ]
        table.sortItems(1, Qt.SortOrder.AscendingOrder)  # numbers inside names count as numbers
        assert column(table, 1)[-3:] == [
            "User1@example.com", "user2@example.com", "user10@example.com"
        ]
        table.sortItems(1, Qt.SortOrder.DescendingOrder)
        assert column(table, 1)[0] == "user10@example.com"

        # The row still belongs to the same user after sorting.
        table.selectRow(0)
        assert page.picker.selected().id == "s1"

        # A new search keeps the chosen order.
        header.setSortIndicator(0, Qt.SortOrder.DescendingOrder)
        page.picker.search()
        wait_until(lambda: page.picker.table.rowCount() == 5 and page.picker.button.isEnabled())
        assert column(table, 0)[0] == "zoe Example" and column(table, 0)[-1] == "Adam Example"
    finally:
        for user in extra:
            USERS.remove(user)


def test_credentials_list_is_sortable(gui):
    window, ctx, key, source, shown = gui
    ctx.provider.credentials = [
        Credential("c2", "Spare key", "2026-03-01", "YubiKey 5C"),
        Credential("c1", "main key", "2026-01-15", "YubiKey 5 NFC"),
        Credential("c3", "Backup", "2026-02-10", "Security Key"),
    ]
    window.nav.setCurrentRow(2)
    page = window.pages.currentWidget()
    pick_user(page, "Alice")
    wait_until(lambda: page.table.rowCount() == 3)
    assert column(page.table, 0) == ["Spare key", "main key", "Backup"]
    page.table.sortItems(0, Qt.SortOrder.AscendingOrder)
    assert column(page.table, 0) == ["Backup", "main key", "Spare key"]
    page.table.sortItems(1, Qt.SortOrder.DescendingOrder)  # newest first
    assert column(page.table, 1) == ["2026-03-01", "2026-02-10", "2026-01-15"]

    page.table.selectRow(2)  # the oldest one, "main key"
    page.delete.click()
    wait_until(lambda: page.table.rowCount() == 2)
    assert sorted(c.id for c in ctx.provider.credentials) == ["c2", "c3"]


def test_sorted_bulk_list_keeps_rows_tied_to_their_users(gui, tmp_path, monkeypatch):
    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(PAGE_BULK)
    page = window.bulk_page
    users_file = tmp_path / "users.txt"
    users_file.write_text("alice@example.com\nghost@example.com\nbob@example.com\n")
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (str(users_file), ""))
    )
    page.load.click()
    wait_until(lambda: not page.is_running() and page.table.rowCount() == 3)

    # Sorted Z to A: bob is not on top of the list but is still enrolled second.
    page.table.sortItems(0, Qt.SortOrder.DescendingOrder)
    assert column(page.table, 0) == ["ghost@example.com", "bob@example.com", "alice@example.com"]

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
    page.start.click()
    wait_until(lambda: not page.is_running())

    by_user = {
        page.table.item(r, 0).text(): (page.table.item(r, 2).text(), page.table.item(r, 3).text())
        for r in range(3)
    }
    assert by_user == {
        "alice@example.com": ("Enrolled", "501"),
        "bob@example.com": ("Enrolled", "502"),
        "ghost@example.com": ("Not found", ""),
    }
    assert column(page.table, 0) == ["ghost@example.com", "bob@example.com", "alice@example.com"]

    page.table.selectRow(1)  # bob, wherever sorting put him
    page.handover.click()
    assert shown["results"][-1].handover.user.username == "bob@example.com"
    assert shown["results"][-1].handover.pin == keys[1].pin

    # Sorting by status regroups the rows; the data follows.
    page.table.sortItems(3, Qt.SortOrder.DescendingOrder)
    assert column(page.table, 3) == ["502", "501", ""]
    page.show_pins.setChecked(True)
    assert column(page.table, 4) == [keys[1].pin, keys[0].pin, ""]


# -- update check -----------------------------------------------------------


def test_update_check_button(gui, monkeypatch):
    from keyenroll import updates

    window, ctx, key, source, shown = gui
    window.nav.setCurrentRow(PAGE_SETTINGS)
    page = window.pages.currentWidget()
    assert page.download_update.isHidden() and page.update_note.isHidden()

    newer = updates.UpdateInfo("0.3.0", "0.4.0", "https://github.com/inowakowski/KeyEnroll/releases/tag/v0.4.0")
    monkeypatch.setattr(updates, "check", lambda: newer)
    page.check_updates.click()
    assert not page.check_updates.isEnabled()  # no double clicks while it runs
    wait_until(lambda: page.check_updates.isEnabled())
    assert "0.4.0" in page.update_note.text() and not page.download_update.isHidden()

    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", staticmethod(lambda url: opened.append(url.toString()) or True))
    page.download_update.click()
    assert opened == ["https://github.com/inowakowski/KeyEnroll/releases/tag/v0.4.0"]

    monkeypatch.setattr(updates, "check", lambda: updates.UpdateInfo("0.3.0", "0.3.0", "x"))
    page.check_updates.click()
    wait_until(lambda: page.check_updates.isEnabled())
    assert "latest version" in page.update_note.text() and page.download_update.isHidden()

    def unavailable():
        raise updates.UpdateError("No published release was found.")

    monkeypatch.setattr(updates, "check", unavailable)
    page.check_updates.click()
    wait_until(lambda: page.check_updates.isEnabled())
    assert page.update_note.text() == "No published release was found."
    assert page.download_update.isHidden()
