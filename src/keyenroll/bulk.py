"""Bulk enrollment: user list import, the batch run and result export."""

from __future__ import annotations

import csv
import io
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .config import Profile, write_private
from .fido import enroll
from .fido.devices import DeviceSource, close, device_key
from .fido.enroll import EnrollCancelled, Enroller, EnrollError, EnrollUI
from .i18n import N_, tr
from .providers import AuthRequired, DirectoryUser, Provider, ProviderError

logger = logging.getLogger(__name__)

KEY_WAIT_TIMEOUT = 30 * 60

NEW = "new"  # imported, not looked up yet
READY = "ready"
NOT_FOUND = "not_found"
RUNNING = "running"
DONE = "done"
FAILED = "failed"

STATUS_LABELS = {
    NEW: N_("Checking…"),
    READY: N_("Ready"),
    NOT_FOUND: N_("Not found"),
    RUNNING: N_("In progress"),
    DONE: N_("Enrolled"),
    FAILED: N_("Failed"),
}

_HEADER_NAMES = {
    "username", "user", "login", "upn", "userprincipalname", "email", "e-mail", "mail",
    "nazwa użytkownika", "nazwa uzytkownika", "użytkownik", "uzytkownik",
    "benutzername", "benutzer", "anmeldename",
    "nombre de usuario", "usuario", "correo electrónico", "correo",
    "nom d’utilisateur", "nom d'utilisateur", "utilisateur", "identifiant", "courriel",
    "nome utente", "utente",
}  # fmt: skip
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


@dataclass
class BulkRow:
    identifier: str
    user: DirectoryUser | None = None
    status: str = NEW
    message: str = ""
    message_params: dict = field(default_factory=dict)
    serial: int | None = None
    key_name: str = ""
    pin: str | None = None
    must_change_pin: bool = False
    finished: str = ""

    @property
    def message_text(self) -> str:
        return tr(self.message, **self.message_params) if self.message else ""


def _decode(data: bytes) -> str:
    # UTF-16 only when marked as such: almost any byte string "decodes" as it.
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    for encoding in ("utf-8-sig", "cp1250"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return data.decode("latin-1")


def parse_identifiers(text: str) -> list[str]:
    """Extracts user identifiers from a text or CSV file.

    One identifier per line, or a CSV whose user column is either named
    (username, login, UPN, e-mail…) or the first one. Lines starting with '#'
    are comments. Duplicates are dropped, order is kept.
    """
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        return []
    delimiter = max(";,\t", key=lines[0].count)
    if lines[0].count(delimiter) == 0:
        delimiter = ","
    rows = [r for r in csv.reader(lines, delimiter=delimiter) if r]

    column = 0
    header = [c.strip().lower() for c in rows[0]]
    named = [i for i, name in enumerate(header) if name in _HEADER_NAMES]
    if named:
        column = named[0]
        rows = rows[1:]

    seen: set[str] = set()
    out = []
    for row in rows:
        if column >= len(row):
            continue
        value = row[column].strip()
        if value and value.lower() not in seen:
            seen.add(value.lower())
            out.append(value)
    return out


def read_identifiers(path: str | Path) -> list[str]:
    return parse_identifiers(_decode(Path(path).read_bytes()))


def _safe_cell(value) -> str:
    """Neutralises values a spreadsheet would run as a formula."""
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


def results_csv(
    rows: list[BulkRow],
    delimiter: str = ",",
    include_pins: bool = True,
    enrolled_only: bool = False,
) -> str:
    """The batch as CSV.

    ``enrolled_only`` keeps just the users who received a key (a deployment
    report); ``include_pins=False`` leaves the PIN column out so the file can
    be shared or archived.
    """
    out = io.StringIO()
    writer = csv.writer(out, delimiter=delimiter, lineterminator="\r\n")
    header = [
        tr("Username"),
        tr("Display name"),
        tr("E-mail"),
        tr("Status"),
        tr("Serial number"),
        tr("Key name"),
        tr("Temporary PIN"),
        tr("Enrolled at"),
        tr("Message"),
    ]
    pin_column = header.index(tr("Temporary PIN"))
    if not include_pins:
        del header[pin_column]
    writer.writerow(header)
    for row in rows:
        if enrolled_only and row.status != DONE:
            continue
        user = row.user
        cells = [
            user.username if user else row.identifier,
            user.display_name if user else "",
            user.email if user else "",
            tr(STATUS_LABELS[row.status]),
            row.serial or "",
            row.key_name,
            row.pin or "",
            row.finished,
            row.message_text,
        ]
        if not include_pins:
            del cells[pin_column]
        writer.writerow(_safe_cell(v) for v in cells)
    return out.getvalue()


def write_results(
    path: str | Path,
    rows: list[BulkRow],
    delimiter: str = ",",
    include_pins: bool = True,
    enrolled_only: bool = False,
) -> None:
    """Writes the result list, readable by the owner only."""
    text = results_csv(rows, delimiter, include_pins, enrolled_only)
    write_private(path, text.encode("utf-8-sig"))  # BOM: Excel needs it


def resolve_rows(
    provider: Provider,
    rows: list[BulkRow],
    on_change,
    cancel: threading.Event | None = None,
) -> None:
    """Looks up every imported identifier in the directory."""
    for index, row in enumerate(rows):
        if cancel is not None and cancel.is_set():
            return
        if row.status != NEW:
            continue
        try:
            row.user = provider.find_user(row.identifier)
        except AuthRequired:
            raise
        except ProviderError as e:
            row.status, row.message, row.message_params = FAILED, str(e), {}
        else:
            row.status = READY if row.user else NOT_FOUND
        on_change(index)


class BulkUI(EnrollUI, Protocol):
    def row_changed(self, index: int) -> None: ...


class BulkRunner:
    """Enrolls one key per ready row, asking the operator to swap keys."""

    def __init__(
        self,
        provider: Provider,
        profile: Profile,
        rows: list[BulkRow],
        key_name: str,
        append_serial: bool,
        ui: BulkUI,
        source: DeviceSource | None = None,
        cancel: threading.Event | None = None,
    ):
        self.provider = provider
        self.profile = profile
        self.rows = rows
        self.key_name = key_name
        self.append_serial = append_serial
        self.ui = ui
        self.source = source or DeviceSource()
        self.cancel = cancel or threading.Event()

    def _keys(self) -> list[str]:
        devices = self.source.list()
        keys = [device_key(d) for d in devices]
        for dev in devices:
            close(dev)
        return keys

    def _wait(self, predicate):
        deadline = time.monotonic() + KEY_WAIT_TIMEOUT
        while time.monotonic() < deadline:
            if self.cancel.is_set():
                raise EnrollCancelled()
            result = predicate()
            if result is not None:
                return result
            self.cancel.wait(enroll.POLL_INTERVAL)
        raise EnrollError(N_("Timed out waiting for the security key."))

    def _next_key(self, user: DirectoryUser, swap: bool) -> str:
        """Returns the key to enroll for ``user``.

        ``swap`` is set once a key has been processed in this batch: the
        operator then has to remove it before the next one is accepted, so
        that one key can never be enrolled (and reset) for two users.
        """
        name = user.display_name or user.username
        if swap:
            self.ui.status(
                N_("Remove the previous key, then insert the key for {user}…"), user=name
            )
            self._wait(lambda: True if not self._keys() else None)
        else:
            keys = self._keys()
            if len(keys) == 1:
                return keys[0]
            if len(keys) > 1:
                raise EnrollError(
                    N_("Several security keys are connected. Leave only one connected.")
                )
        self.ui.status(N_("Insert the security key for {user}…"), user=name)

        def one_key():
            keys = self._keys()
            return keys[0] if len(keys) == 1 else None

        return self._wait(one_key)

    def run(self) -> None:
        """Processes ready rows in order; stops at the first failure so the
        operator can decide what to do with that user and key."""
        used = {r.serial for r in self.rows if r.status == DONE and r.serial}
        swap = any(r.status in (DONE, FAILED) for r in self.rows)
        for index, row in enumerate(self.rows):
            if row.status != READY or row.user is None:
                continue
            if self.cancel.is_set():
                raise EnrollCancelled()
            row.status, row.message, row.message_params = RUNNING, "", {}
            self.ui.row_changed(index)
            try:
                key = self._next_key(row.user, swap)
                result = Enroller(
                    self.provider,
                    self.profile,
                    row.user,
                    self.key_name,
                    key,
                    self.ui,
                    source=self.source,
                    cancel=self.cancel,
                    append_serial=self.append_serial,
                    try_reset_first=True,
                    used_serials=used,
                ).run()
            except (EnrollCancelled, AuthRequired):
                row.status = READY
                self.ui.row_changed(index)
                raise
            except Exception as e:
                logger.info("Bulk enrollment of %s failed", row.identifier, exc_info=True)
                row.status = FAILED
                if isinstance(e, EnrollError):
                    row.message, row.message_params = e.template, e.params
                else:
                    row.message, row.message_params = str(e) or type(e).__name__, {}
                self.ui.row_changed(index)
                raise
            row.status = DONE
            row.serial = result.key.serial
            row.key_name = result.display_name
            row.pin = result.pin
            row.must_change_pin = result.key.force_pin_change
            row.finished = time.strftime("%Y-%m-%d %H:%M:%S")
            if result.warnings:
                row.message, row.message_params = result.warnings[0]
            if row.serial:
                used.add(row.serial)
            swap = True
            self.ui.row_changed(index)
        self.ui.status(N_("Batch finished."))
