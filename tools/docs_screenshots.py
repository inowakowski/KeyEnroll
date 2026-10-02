"""Renders the screenshots used by the documentation.

    python tools/docs_screenshots.py            # every documentation language
    python tools/docs_screenshots.py pl         # one language

The application runs against the fake identity provider and the software
security key of the test suite, so no tenant and no hardware are involved and
the pictures contain made-up people only. Nothing is shown on screen. Run it
again after changing the user interface, on a machine with a desktop session
(the fonts come from the system).
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "windows")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication, QScrollArea

from fake_authenticator import FakeAuthenticator
from keyenroll import DOCS_LANGUAGES, bulk, i18n
from keyenroll.bulk import BulkRow
from keyenroll.config import ConfigStore, Instance, Profile
from keyenroll.handover import Handover
from keyenroll.providers.base import Credential, DirectoryUser
from keyenroll.secrets_store import TokenStore
from keyenroll.ui import dialogs, main_window
from keyenroll.ui.common import AppContext
from keyenroll.ui.theme import apply_theme
from test_enroll import FakeSource
from test_gui import GuiProvider

OUT = ROOT / "docs" / "assets" / "screenshots"
THEME = "yubico"
SIZE = (1180, 800)

PEOPLE = [
    DirectoryUser(str(i), f"{login}@example.com", name, f"{login}@example.com")
    for i, (login, name) in enumerate(
        [
            ("alice.martin", "Alice Martin"),
            ("bob.novak", "Bob Novak"),
            ("carol.jensen", "Carol Jensen"),
            ("david.rossi", "David Rossi"),
            ("emma.schmidt", "Emma Schmidt"),
        ]
    )
]
LABELS = {"entra": "Microsoft Entra ID", "okta": "Okta"}


class Provider(GuiProvider):
    def __init__(self, instance):
        super().__init__(instance)
        self.label = LABELS[instance.kind]
        self.max_display_name = 30 if instance.kind == "entra" else None
        self.credentials = [
            Credential("c1", "YubiKey 5 NFC 23456789", "2026-09-14 10:32", "YubiKey 5 Series with NFC"),
            Credential("c2", "YubiKey 5C 19874410", "2025-03-02 08:15", "YubiKey 5 Series"),
        ]

    def search_users(self, query):
        return [u for u in PEOPLE if query.lower() in u.display_name.lower()]


class Source(FakeSource):
    def describe(self, dev):
        info = super().describe(dev)
        info.firmware = "5.7.1"
        return info


def pump(seconds: float = 0.4) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)
        time.sleep(0.01)


def render(app: QApplication, lang: str) -> list[str]:
    out = OUT / lang
    out.mkdir(parents=True, exist_ok=True)
    i18n.set_language(lang)
    made = []

    def shot(widget, name: str) -> None:
        pump(0.2)
        widget.grab().save(str(out / f"{name}.png"))
        made.append(name)

    config = ConfigStore(Path(tempfile.mkdtemp()) / "config.json")
    config.theme = THEME
    config.append_serial = True
    config.upsert_profile(
        Profile(name="high-security", min_pin_length=8, random_pin_length=8,
                force_pin_change=True, require_always_uv=True)
    )
    config.upsert_instance(
        Instance(name="Example Corp", kind="entra", default_profile="high-security",
                 settings={"tenant_id": "0000", "client_id": "1111"})
    )
    config.upsert_instance(Instance(name="Example Lab", kind="okta"))

    providers: dict[str, Provider] = {}
    key = FakeAuthenticator("YubiKey 5 NFC")
    key.serial = 23456789
    ctx = AppContext(
        config,
        TokenStore(),
        source=Source(key),
        provider_factory=lambda inst, tokens: providers.setdefault(inst.id, Provider(inst)),
    )
    window = main_window.MainWindow(ctx)
    window.resize(*SIZE)

    # -- enroll --------------------------------------------------------------
    page = window.enroll_page
    window.nav.setCurrentRow(main_window.PAGE_ENROLL)
    page.refresh_keys()
    page.picker.search()
    pump()
    page.picker.table.selectRow(0)
    page.display_name.setText("YubiKey 5 NFC")
    shot(window, "enroll")
    page._set_running(True)
    for step in (
        "Checking sign-in and permissions…",
        "Factory reset: remove the security key now…",
        "Factory reset: insert the security key again…",
        "Factory reset: touch the security key to confirm…",
    ):
        page._on_status(step, {})
    shot(window, "enroll-progress")
    page._set_running(False)

    handover = Handover(
        user=PEOPLE[0], key_name="YubiKey 5 NFC 23456789", serial=23456789, pin="48291537",
        must_change_pin=True, provider=LABELS["entra"],
    )
    shot(dialogs.ResultDialog(handover, config, window), "result")
    shot(dialogs.NewPinDialog(8, False, window), "new-pin")
    shot(dialogs.CurrentPinDialog(8, False, window), "current-pin")

    # -- bulk ----------------------------------------------------------------
    window.nav.setCurrentRow(main_window.PAGE_BULK)
    bulk_page = window.bulk_page
    states = [
        (bulk.DONE, 23456789, "48153729"),
        (bulk.DONE, 23456790, "90274615"),
        (bulk.RUNNING, None, None),
        (bulk.READY, None, None),
    ]
    bulk_page.rows = [
        BulkRow(user.username, user=user, status=status, serial=serial, pin=pin,
                key_name=f"YubiKey 5 NFC {serial}" if serial else "",
                finished="2026-10-02 09:41:07" if serial else "", must_change_pin=True)
        for user, (status, serial, pin) in zip(PEOPLE, states, strict=False)
    ]
    bulk_page.rows.append(BulkRow("frank.ghost@example.com", status=bulk.NOT_FOUND))
    bulk_page._instance_id = config.active_instance_id
    bulk_page.key_name.setText("YubiKey 5 NFC")
    bulk_page._refresh_all()
    # A batch in the middle of its run, waiting for the third key.
    bulk_page._worker, bulk_page._running = object(), True
    bulk_page._update_state()
    bulk_page._on_status(
        "Remove the previous key, then insert the key for {user}…", {"user": PEOPLE[2].username}
    )
    bulk_page.table.selectRow(0)
    shot(window, "bulk")
    shot(dialogs.ExportDialog(window), "export")
    bulk_page._worker, bulk_page._running = None, False
    bulk_page.rows = []  # nothing left to warn about when the window closes
    bulk_page._refresh_all()
    bulk_page._update_state()

    # -- credentials -----------------------------------------------------------
    window.nav.setCurrentRow(main_window.PAGE_CREDENTIALS)
    credentials = window.pages.currentWidget()
    credentials.picker.search()
    pump()
    credentials.picker.table.selectRow(0)
    pump()
    credentials.table.selectRow(0)
    shot(window, "credentials")

    # -- profiles --------------------------------------------------------------
    window.nav.setCurrentRow(main_window.PAGE_PROFILES)
    profiles = window.pages.currentWidget()
    profiles.list.setCurrentRow(1)
    shot(window, "profiles")

    # -- instances -------------------------------------------------------------
    window.nav.setCurrentRow(main_window.PAGE_INSTANCES)
    instances = window.pages.currentWidget()
    instances.table.selectRow(1)
    shot(window, "instances")
    dialog = dialogs.InstanceDialog(config, None, window)
    dialog.name.setText("Example Corp")
    dialog.profile.setCurrentIndex(dialog.profile.findData("high-security"))
    dialog._inputs["tenant_id"].setText("3f2b9a6e-1c4d-4e8a-9b7f-5d6c0a1e2f34")
    dialog._inputs["client_id"].setText("a81c5d2e-7f30-4b96-8e21-c4d9b0f6a753")
    shot(dialog, "instance-dialog")

    # -- settings --------------------------------------------------------------
    window.nav.setCurrentRow(main_window.PAGE_SETTINGS)
    settings = window.pages.currentWidget()
    shot(window, "settings")
    bar = settings.findChild(QScrollArea).verticalScrollBar()
    bar.setValue(bar.maximum())
    shot(window, "settings-about")

    page.shutdown()
    bulk_page.shutdown()
    window.close()
    window.deleteLater()
    pump(0.1)
    return made


def main(argv: list[str]) -> int:
    languages = argv or list(DOCS_LANGUAGES)
    unknown = [lang for lang in languages if lang not in i18n.LANGUAGES]
    if unknown:
        print(f"unknown language: {', '.join(unknown)}", file=sys.stderr)
        return 2
    # The yellow "restart as administrator" banner is not part of the pictures.
    main_window.is_admin = lambda: True
    app = QApplication([])
    apply_theme(app, THEME)
    for lang in languages:
        names = render(app, lang)
        print(f"{lang}: {len(names)} screenshots in {OUT / lang}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
