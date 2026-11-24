"""Which user a connected security key is registered to, by its serial number."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..fido.devices import KeyInfo, close
from ..i18n import tr
from ..key_lookup import KeyOwnership
from ..providers import DirectoryUser
from .common import AppContext, owner_search, run_task

logger = logging.getLogger(__name__)

KEY_POLL_MS = 2000


def owner_names(users: list[DirectoryUser]) -> str:
    return ", ".join(u.display_name or u.username for u in users)


def owner_text(found: KeyOwnership, serial: int | None = None) -> str:
    """What to tell the operator about a key; ``serial`` names it when
    several keys may be connected."""
    users = owner_names(found.users)
    if serial is None:
        if found.confirmed:
            return tr("This key is registered to: {users}", users=users)
        return tr("According to the deployment log, this key is registered to: {users}", users=users)
    if found.users:
        if found.confirmed:
            return tr(
                "Connected key S/N {serial} belongs to: {users}", serial=serial, users=users
            )
        return tr(
            "According to the deployment log, connected key S/N {serial} belongs to: {users}",
            serial=serial,
            users=users,
        )
    if found.provider_records:
        return tr("Connected key S/N {serial} is not assigned to any user.", serial=serial)
    return tr(
        "Connected key S/N {serial} is not in the deployment log of this computer.",
        serial=serial,
    )


class KeyOwners(QObject):
    """Finds out, in the background, who has the key with a given serial
    number: from the provider where it keeps serial numbers (Okta), else from
    this computer's deployment log, checked against the provider."""

    changed = Signal()

    def __init__(self, ctx: AppContext, parent: QObject | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._owners: dict[int, KeyOwnership] = {}
        self._pending: set[int] = set()
        self._generation = 0
        ctx.active_changed.connect(self.reset)
        ctx.instances_changed.connect(self.reset)

    @property
    def available(self) -> bool:
        return self.ctx.provider is not None

    def reset(self) -> None:
        """Forgets every answer, e.g. after an enrollment changed one."""
        self._generation += 1
        self._owners.clear()
        self._pending.clear()
        self.changed.emit()

    def ownership(self, serial: int | None) -> KeyOwnership | None:
        """What is known about the key; None while unknown."""
        return self._owners.get(serial) if serial else None

    def owners(self, serial: int | None) -> list[DirectoryUser] | None:
        found = self.ownership(serial)
        return None if found is None else found.users

    def pending(self, serial: int | None) -> bool:
        return serial in self._pending

    def find(self, user_id: str) -> DirectoryUser | None:
        for found in self._owners.values():
            for user in found.users:
                if user.id == user_id:
                    return user
        return None

    def lookup(self, serials) -> None:
        if not self.available:
            return
        search = owner_search(self.ctx)
        generation = self._generation
        for serial in serials:
            if not serial or serial in self._owners or serial in self._pending:
                continue
            self._pending.add(serial)
            run_task(
                self,
                lambda s=serial: search(s),
                lambda found, s=serial: self._done(generation, s, found),
                lambda exc, s=serial: self._failed(generation, s, exc),
            )

    def _done(self, generation: int, serial: int, found: KeyOwnership) -> None:
        if generation != self._generation:
            return
        self._pending.discard(serial)
        self._owners[serial] = found
        self.changed.emit()

    def _failed(self, generation: int, serial: int, exc: BaseException) -> None:
        if generation != self._generation:
            return
        # Only a hint: not signed in, or the directory could not be read.
        self._pending.discard(serial)
        logger.info("Looking up the owner of key %s failed: %s", serial, exc)
        self.changed.emit()


class KeyWatcher(QObject):
    """Notices security keys being plugged in or taken out while a page is
    shown, and reads their serial numbers. Stays away from the keys while an
    enrollment owns them."""

    keys_changed = Signal(list)  # list[KeyInfo]

    def __init__(self, ctx: AppContext, parent: QObject | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._paths: set[str] | None = None
        self._scanning = False
        self._timer = QTimer(self)
        self._timer.setInterval(KEY_POLL_MS)
        self._timer.timeout.connect(self.poll)

    def start(self) -> None:
        self._timer.start()
        self.poll()

    def stop(self) -> None:
        self._timer.stop()

    def rescan(self) -> None:
        self._paths = None
        self.poll()

    def poll(self) -> None:
        if self.ctx.busy or self._scanning:
            return
        try:
            from fido2.hid import list_descriptors

            paths = {str(d.path) for d in list_descriptors()}
        except Exception:
            return
        if paths == self._paths:
            return
        self._paths = paths
        self._scanning = True
        source = self.ctx.source

        def scan() -> list[KeyInfo]:
            infos = []
            for dev in source.list():
                try:
                    infos.append(source.describe(dev))
                except Exception:
                    logger.debug("Reading a security key failed", exc_info=True)
                finally:
                    close(dev)
            return infos

        def done(infos) -> None:
            self._scanning = False
            self.keys_changed.emit(infos)

        def failed(exc) -> None:
            self._scanning = False
            self._paths = None  # try again on the next tick

        run_task(self, scan, done, failed)


class OwnerBanner(QFrame):
    """A banner that stands out: who the connected keys belong to, with a
    button per user that opens the user's credentials."""

    open_user = Signal(object)  # DirectoryUser

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("banner")
        self._rows = QVBoxLayout(self)
        self._rows.setContentsMargins(14, 10, 14, 10)
        self._rows.setSpacing(8)
        self.setVisible(False)

    def texts(self) -> list[str]:
        return [label.text() for label in self.findChildren(QLabel)]

    def buttons(self) -> list[QPushButton]:
        return self.findChildren(QPushButton)

    def set_rows(self, rows: list[tuple[str, list[DirectoryUser]]]) -> None:
        """One line per key: its text and the users to offer a button for."""
        while self._rows.count():
            widget = self._rows.takeAt(0).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        for text, users in rows:
            line = QWidget()
            row = QHBoxLayout(line)
            row.setContentsMargins(0, 0, 0, 0)
            label = QLabel(text)
            label.setWordWrap(True)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            row.addWidget(label, 1)
            for user in users:
                name = user.display_name or user.username
                button = QPushButton(
                    tr("Show the keys of {user}", user=name) if len(users) > 1
                    else tr("Show the user's keys")
                )
                button.clicked.connect(lambda _=False, u=user: self.open_user.emit(u))
                row.addWidget(button)
            self._rows.addWidget(line)
        self.setVisible(bool(rows))
