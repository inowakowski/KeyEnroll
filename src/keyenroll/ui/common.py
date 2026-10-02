"""Shared UI plumbing: application context, background tasks, user picker."""

from __future__ import annotations

import logging
import threading
from typing import Callable

from PySide6.QtCore import QObject, Qt, QTimer, Signal
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


def copy_sensitive(text: str) -> None:
    """Copies a PIN (or a message containing one) and removes it from the
    clipboard after a minute, unless something else was copied meanwhile."""
    clipboard = QGuiApplication.clipboard()
    clipboard.setText(text)

    def clear() -> None:
        if clipboard.text() == text:
            clipboard.clear()

    QTimer.singleShot(CLIPBOARD_CLEAR_MS, clear)


def make_table(headers: list[str], scrollable: bool = False) -> QTableWidget:
    """A read-only, row-selecting table.

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
    return table


def fit_columns(table: QTableWidget) -> None:
    """Sizes the columns of a scrollable table to their contents."""
    header = table.horizontalHeader()
    table.resizeColumnsToContents()
    for col in range(table.columnCount() - 1):
        width = max(table.columnWidth(col) + 16, header.sectionSizeHint(col) + 16)
        table.setColumnWidth(col, min(width, MAX_COLUMN_WIDTH))


def fill_row(table: QTableWidget, values: list[str], data=None) -> None:
    row = table.rowCount()
    table.insertRow(row)
    for col, value in enumerate(values):
        item = QTableWidgetItem(value)
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
