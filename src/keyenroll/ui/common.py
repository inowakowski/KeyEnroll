"""Shared UI plumbing: application context, background tasks, user picker."""

from __future__ import annotations

import atexit
import logging
import re
import sys
import threading
from contextlib import contextmanager
from itertools import zip_longest
from typing import Callable

from PySide6.QtCore import QCollator, QMimeData, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from ..config import ConfigStore, Instance
from ..fido.devices import DeviceSource
from ..fido.enroll import EnrollError
from ..i18n import tr
from ..oauth import OAuthError
from ..providers import AuthRequired, DirectoryUser, Provider, ProviderError, create_provider
from ..secrets_store import TokenStore

logger = logging.getLogger(__name__)


def error_text(exc: BaseException) -> str:
    if isinstance(exc, EnrollError):
        return tr(exc.template, **exc.params)
    if isinstance(exc, (ProviderError, OAuthError)):
        return tr(str(exc))
    return f"{type(exc).__name__}: {exc}"


class AppContext(QObject):
    """State shared by all pages."""

    instances_changed = Signal()
    profiles_changed = Signal()
    active_changed = Signal()
    session_changed = Signal()
    busy_changed = Signal(bool)
    theme_changed = Signal()

    def __init__(
        self,
        config: ConfigStore,
        tokens: TokenStore,
        source: DeviceSource | None = None,
        provider_factory: Callable[[Instance, TokenStore], Provider] = create_provider,
    ):
        super().__init__()
        self.config = config
        self.tokens = tokens
        self.source = source or DeviceSource()
        self._factory = provider_factory
        self._providers: dict[str, Provider] = {}
        self._busy = False

    def provider_for(self, instance: Instance) -> Provider:
        provider = self._providers.get(instance.id)
        if provider is None:
            provider = self._providers[instance.id] = self._factory(instance, self.tokens)
        return provider

    @property
    def provider(self) -> Provider | None:
        instance = self.config.active_instance
        return self.provider_for(instance) if instance else None

    def forget_provider(self, instance_id: str) -> None:
        self._providers.pop(instance_id, None)

    @property
    def busy(self) -> bool:
        return self._busy

    def set_busy(self, busy: bool) -> None:
        if busy != self._busy:
            self._busy = busy
            self.busy_changed.emit(busy)


class Background(QObject):
    """Base for work done off the UI thread.

    The work runs on a daemon Python thread rather than a QThread owned by a
    widget: Qt aborts the whole process when a QThread object is destroyed
    while still running, which happens when a window is closed in the middle
    of a search, a sign-in or a key scan. Everything the work reports is
    marshalled to the UI thread with ``post``.
    """

    _post = Signal(object)
    _alive: set = set()  # keeps instances referenced until their work is done

    def __init__(self):
        super().__init__()
        self._post.connect(self._run_posted, Qt.ConnectionType.QueuedConnection)
        self._thread = threading.Thread(target=self._main, daemon=True, name="keyenroll-bg")

    def start(self) -> None:
        Background._alive.add(self)
        self._thread.start()

    def wait(self, msecs: int) -> bool:
        self._thread.join(msecs / 1000)
        return not self._thread.is_alive()

    def post(self, fn) -> None:
        """Runs ``fn`` on the UI thread. Safe to call from the worker thread."""
        try:
            self._post.emit(fn)
        except RuntimeError:  # the application is shutting down
            pass

    def _run_posted(self, fn) -> None:
        fn()

    def _main(self) -> None:
        try:
            self.work()
        finally:
            self.post(lambda: Background._alive.discard(self))

    def work(self) -> None:
        raise NotImplementedError


class Task(Background):
    """Runs a callable off the UI thread; callbacks run on the UI thread,
    unless the widget that asked for the result is gone by then."""

    def __init__(self, fn, on_ok, on_err, owner: QObject):
        super().__init__()
        self._fn = fn
        self._on_ok = on_ok
        self._on_err = on_err
        self._owner = owner

    def work(self) -> None:
        try:
            result = self._fn()
        except Exception as e:
            logger.info("Background task failed", exc_info=True)
            # Bound as a default: the name ``e`` is gone once the block ends.
            self.post(lambda exc=e: self._deliver(self._on_err, exc))
        else:
            self.post(lambda: self._deliver(self._on_ok, result))

    def _deliver(self, callback, value) -> None:
        if callback and isValid(self._owner):
            callback(value)


def run_task(owner: QObject, fn, on_ok=None, on_err=None) -> Task:
    task = Task(fn, on_ok, on_err, owner)
    task.start()
    return task


def show_error(parent: QWidget, ctx: AppContext, exc: BaseException) -> None:
    if isinstance(exc, AuthRequired):
        ctx.session_changed.emit()
    QMessageBox.warning(parent, tr("Error"), error_text(exc))


CLIPBOARD_CLEAR_MS = 60_000
MAX_COLUMN_WIDTH = 900  # beyond this a cell is elided; the tooltip has the full text


def sensitive_mime(text: str, platform: str = sys.platform) -> QMimeData:
    """Text marked as a secret for the programs that record the clipboard.

    Clearing the clipboard does not remove what a clipboard history has
    already kept, so the history is asked not to take it in the first place:
    the Windows clipboard history and its cloud sync, clipboard managers on
    macOS, and KDE's Klipper all honour these markers.
    """
    mime = QMimeData()
    mime.setText(text)
    if platform == "win32":
        mime.setData("ExcludeClipboardContentFromMonitorProcessing", b"1")
        mime.setData("CanIncludeInClipboardHistory", bytes(4))  # DWORD 0
        mime.setData("CanUploadToCloudClipboard", bytes(4))  # DWORD 0
    elif platform == "darwin":
        mime.setData("application/x-nspasteboard-concealed-type", text.encode())
    else:
        mime.setData("x-kde-passwordManagerHint", b"secret")
    return mime


_copied: set[str] = set()  # secrets of ours that may still be on the clipboard
_exit_hooks = False


def forget_copied(only: str | None = None) -> None:
    """Takes a copied secret off the clipboard again, unless something else
    has been copied since. Without ``only``, any secret of ours is removed."""
    wanted = _copied if only is None else _copied & {only}
    if wanted and QGuiApplication.instance() is not None:
        clipboard = QGuiApplication.clipboard()
        if clipboard.text() in wanted:
            clipboard.clear()
    _copied.difference_update(set(wanted))


def copy_sensitive(text: str) -> None:
    """Copies a PIN (or a message containing one) and removes it from the
    clipboard after a minute, or when the application closes, unless
    something else was copied meanwhile."""
    global _exit_hooks
    if not _exit_hooks:
        # A PIN must not outlive the application on the clipboard. The
        # interpreter-exit hook is for a process that ends without the event
        # loop quitting: Qt would otherwise destroy our clipboard data after
        # Python is gone, which crashes.
        QGuiApplication.instance().aboutToQuit.connect(lambda: forget_copied())
        atexit.register(forget_copied)
        _exit_hooks = True
    _copied.add(text)
    QGuiApplication.clipboard().setMimeData(sensitive_mime(text))
    QTimer.singleShot(CLIPBOARD_CLEAR_MS, lambda: forget_copied(text))


_collator: QCollator | None = None
_DIGITS = re.compile(r"(\d+)")


def natural_compare(a: str, b: str) -> int:
    """Three-way comparison for sorting text the way people read it.

    Case is ignored and runs of digits compare as numbers; both are done here
    rather than by QCollator, whose support for them depends on how Qt was
    built. The collator only supplies the alphabet order of the system
    language.
    """
    global _collator
    if _collator is None:
        _collator = QCollator()
    for x, y in zip_longest(_DIGITS.split(a.casefold()), _DIGITS.split(b.casefold())):
        if x is None or y is None:
            return -1 if x is None else 1
        if x.isdigit() and y.isdigit():
            if int(x) != int(y):
                return -1 if int(x) < int(y) else 1
            continue
        order = _collator.compare(x, y)
        if order:
            return order
    return 0


class SortItem(QTableWidgetItem):
    """A cell that sorts the way people read: ignoring case, with the rules
    of the system language (ą after a, not after z) and digit runs compared
    as numbers (user2 before user10)."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        return natural_compare(self.text(), other.text()) < 0


@contextmanager
def paused_sorting(table: QTableWidget):
    """Rows are addressed by position while a table is being filled; with
    sorting switched on Qt would move them as soon as a cell changes."""
    enabled = table.isSortingEnabled()
    table.setSortingEnabled(False)
    try:
        yield
    finally:
        table.setSortingEnabled(enabled)


def make_table(headers: list[str], scrollable: bool = False) -> QTableWidget:
    """A read-only, row-selecting table, sortable by clicking a column header.

    By default the columns share the available width. A ``scrollable`` table
    sizes its columns to their contents instead (see ``fit_columns``), lets the
    user resize them and scrolls sideways when they do not fit.
    """
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(38)
    table.setShowGrid(False)
    header = table.horizontalHeader()
    header.setHighlightSections(False)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    if scrollable:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(90)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setWordWrap(False)
        fit_columns(table)
    else:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    # Unsorted until a header is clicked, so the provider's order is kept;
    # a third click on the same header clears the sorting again.
    header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
    header.setSortIndicatorClearable(True)
    table.setSortingEnabled(True)
    return table


def fit_columns(table: QTableWidget) -> None:
    """Sizes the columns of a scrollable table to their contents."""
    header = table.horizontalHeader()
    table.resizeColumnsToContents()
    for col in range(table.columnCount() - 1):
        width = max(table.columnWidth(col) + 16, header.sectionSizeHint(col) + 16)
        table.setColumnWidth(col, min(width, MAX_COLUMN_WIDTH))


def fill_row(table: QTableWidget, values: list[str], data=None) -> None:
    with paused_sorting(table):
        row = table.rowCount()
        table.insertRow(row)
        for col, value in enumerate(values):
            item = SortItem(value)
            item.setToolTip(value)
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, data)
            table.setItem(row, col, item)


def selected_data(table: QTableWidget):
    rows = table.selectionModel().selectedRows()
    if not rows:
        return None
    return table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)


class UserPicker(QWidget):
    """Directory search box with a result table."""

    selection_changed = Signal(object)

    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._search_id = 0

        self.query = QLineEdit()
        self.query.setPlaceholderText(tr("Name, username or e-mail"))
        self.query.setClearButtonEnabled(True)
        self.query.returnPressed.connect(self.search)
        self.button = QPushButton(tr("Search"))
        self.button.clicked.connect(self.search)

        top = QHBoxLayout()
        top.addWidget(self.query, 1)
        top.addWidget(self.button)

        self.table = make_table(
            [tr("Display name"), tr("Username"), tr("E-mail")], scrollable=True
        )
        self.table.itemSelectionChanged.connect(
            lambda: self.selection_changed.emit(self.selected())
        )
        self.hint = QLabel()
        self.hint.setObjectName("hint")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.hint)

        ctx.active_changed.connect(self.clear)

    def selected(self) -> DirectoryUser | None:
        return selected_data(self.table)

    def clear(self) -> None:
        self._search_id += 1  # drop results of a search still in flight
        self.table.setRowCount(0)
        self.hint.setText("")
        self.button.setEnabled(True)

    def search(self) -> None:
        provider = self.ctx.provider
        if provider is None:
            QMessageBox.information(
                self, tr("No instance"), tr("Add an identity provider instance first.")
            )
            return
        query = self.query.text()
        self._search_id += 1
        search_id = self._search_id
        self.button.setEnabled(False)
        self.hint.setText(tr("Searching…"))

        def done(users):
            if search_id != self._search_id:
                return
            self.button.setEnabled(True)
            self.table.setRowCount(0)
            for u in users:
                fill_row(self.table, [u.display_name, u.username, u.email], u)
            fit_columns(self.table)
            self.hint.setText(tr("{count} user(s) found", count=len(users)))
            if len(users) == 1:
                self.table.selectRow(0)

        def failed(exc):
            if search_id != self._search_id:
                return
            self.button.setEnabled(True)
            self.hint.setText("")
            show_error(self, self.ctx, exc)

        run_task(self, lambda: provider.search_users(query), done, failed)
