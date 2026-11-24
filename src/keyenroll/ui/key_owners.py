"""Which user a connected security key is registered to, by its serial number."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from ..fido.devices import KeyInfo, close
from ..providers import DirectoryUser
from .common import AppContext, run_task

logger = logging.getLogger(__name__)

KEY_POLL_MS = 2000


def owner_names(users: list[DirectoryUser]) -> str:
    return ", ".join(u.display_name or u.username for u in users)


class KeyOwners(QObject):
    """Asks the provider, in the background, who has the key with a given
    serial number. Only providers that keep serial numbers (Okta with a
    profile attribute) can answer; for the others nothing is looked up."""

    changed = Signal()

    def __init__(self, ctx: AppContext, parent: QObject | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._owners: dict[int, list[DirectoryUser]] = {}
        self._pending: set[int] = set()
        self._generation = 0
        ctx.active_changed.connect(self.reset)
        ctx.instances_changed.connect(self.reset)

    @property
    def available(self) -> bool:
        provider = self.ctx.provider
        return provider is not None and bool(getattr(provider, "records_keys", False))

    def reset(self) -> None:
        """Forgets every answer, e.g. after an enrollment changed one."""
        self._generation += 1
        self._owners.clear()
        self._pending.clear()
        self.changed.emit()

    def owners(self, serial: int | None) -> list[DirectoryUser] | None:
        """The users listed for the key; None while unknown."""
        return self._owners.get(serial) if serial else None

    def pending(self, serial: int | None) -> bool:
        return serial in self._pending

    def find(self, user_id: str) -> DirectoryUser | None:
        for users in self._owners.values():
            for user in users:
                if user.id == user_id:
                    return user
        return None

    def lookup(self, serials) -> None:
        if not self.available:
            return
        provider = self.ctx.provider
        generation = self._generation
        for serial in serials:
            if not serial or serial in self._owners or serial in self._pending:
                continue
            self._pending.add(serial)
            run_task(
                self,
                lambda s=serial: provider.users_with_key(str(s)),
                lambda users, s=serial: self._done(generation, s, users),
                lambda exc, s=serial: self._failed(generation, s, exc),
            )

    def _done(self, generation: int, serial: int, users) -> None:
        if generation != self._generation:
            return
        self._pending.discard(serial)
        self._owners[serial] = list(users)
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
