"""Bulk enrollment page: import a user list, enroll key after key, export PINs."""

from __future__ import annotations

from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import bulk
from ..bulk import BulkRow
from ..fido.enroll import EnrollCancelled
from ..handover import Handover
from ..i18n import tr
from ..providers import AuthRequired
from .common import AppContext, SortItem, error_text, fit_columns, make_table, paused_sorting
from .dialogs import ExportDialog, ResultDialog
from .profile_form import profile_summary
from .theme import Card
from .workers import BulkWorker, PinPrompt, ResolveWorker, answer_prompt

COL_USER, COL_NAME, COL_STATUS, COL_SERIAL, COL_PIN, COL_MESSAGE = range(6)
MASK = "••••••"


class BulkPage(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self.rows: list[BulkRow] = []
        self._instance_id: str | None = None  # tenant the list was imported for
        self._worker: BulkWorker | ResolveWorker | None = None
        self._running = False
        self._unexported = False
        self._provider_label = ""

        # user list
        self.load = QPushButton(tr("Load from file…"))
        self.load.clicked.connect(self._load_file)
        self.clear = QPushButton(tr("Clear list"))
        self.clear.clicked.connect(self._clear)
        self.summary = QLabel()
        self.summary.setObjectName("hint")
        self.show_pins = QCheckBox(tr("Show PINs in the list"))
        self.show_pins.toggled.connect(self._refresh_all)
        list_buttons = QHBoxLayout()
        list_buttons.addWidget(self.load)
        list_buttons.addWidget(self.clear)
        list_buttons.addSpacing(10)
        list_buttons.addWidget(self.show_pins)
        list_buttons.addStretch(1)
        list_buttons.addWidget(self.summary)
        self.table = make_table(
            [
                tr("User"),
                tr("Display name"),
                tr("Status"),
                tr("Serial number"),
                tr("Temporary PIN"),
                tr("Message"),
            ],
            scrollable=True,
        )
        self.table.itemSelectionChanged.connect(self._update_state)
        list_card = Card(
            tr("User list"),
            tr(
                "Text or CSV file with one user per line: user name, login or e-mail. "
                "In a CSV with several columns, name the user column 'username'."
            ),
        )
        list_card.body.addLayout(list_buttons)
        list_card.body.addWidget(self.table, 1)

        # options
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._show_profile)
        self.profile_info = QLabel()
        self.profile_info.setObjectName("hint")
        self.profile_info.setWordWrap(True)
        self.key_name = QLineEdit()
        self.key_name.setPlaceholderText(tr("e.g. YubiKey 5 NFC"))
        self.key_name.setMaxLength(60)
        self.append_serial = QCheckBox(tr("Add the serial number to the key name"))
        self.append_serial.setChecked(True)
        self.profile_combo.setMinimumWidth(170)
        options = QHBoxLayout()
        options.setSpacing(10)
        options.addWidget(QLabel(tr("Profile")))
        options.addWidget(self.profile_combo)
        options.addSpacing(10)
        options.addWidget(QLabel(tr("Key display name")))
        options.addWidget(self.key_name, 1)
        options.addSpacing(10)
        options.addWidget(self.append_serial)
        options_card = Card(tr("Enrollment options"))
        options_card.body.addLayout(options)
        options_card.body.addWidget(self.profile_info)

        # actions
        self.start = QPushButton(tr("Start"))
        self.start.setObjectName("primary")
        self.start.clicked.connect(self._start)
        self.stop = QPushButton(tr("Stop"))
        self.stop.clicked.connect(self._stop)
        self.retry = QPushButton(tr("Retry failed"))
        self.retry.clicked.connect(self._retry_failed)
        self.export = QPushButton(tr("Export results…"))
        self.export.clicked.connect(self._export)
        self.handover = QPushButton(tr("Message for the user…"))
        self.handover.setToolTip(
            tr("Select an enrolled user to copy, e-mail or save the hand-over message.")
        )
        self.handover.clicked.connect(self._hand_over)
        self.step = QLabel()
        self.step.setObjectName("step")
        self.step.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        buttons = QHBoxLayout()
        for b in (self.start, self.stop, self.retry):
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(self.handover)
        buttons.addWidget(self.export)
        action_card = Card()
        action_card.body.addLayout(buttons)
        action_card.body.addWidget(self.step)
        action_card.body.addWidget(self.progress)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(options_card)
        layout.addWidget(list_card, 1)
        layout.addWidget(action_card)

        ctx.profiles_changed.connect(self._reload_profiles)
        ctx.active_changed.connect(self._reload_profiles)
        ctx.active_changed.connect(self._update_state)
        ctx.session_changed.connect(self._update_state)
        ctx.busy_changed.connect(lambda _: self._update_state())
        self._reload_profiles()
        self._update_state()

    # -- state -------------------------------------------------------------

    def is_running(self) -> bool:
        return self._worker is not None

    def has_unexported_pins(self) -> bool:
        return self._unexported

    def _foreign_list(self) -> bool:
        """The list was imported for another instance than the active one."""
        return bool(self.rows) and self._instance_id != self.ctx.config.active_instance_id

    def _update_state(self) -> None:
        counts = Counter(r.status for r in self.rows)
        idle = self._worker is None and not self.ctx.busy
        foreign = self._foreign_list()
        self.load.setEnabled(idle)
        self.clear.setEnabled(idle and bool(self.rows))
        self.start.setEnabled(idle and counts[bulk.READY] > 0 and not foreign)
        self.stop.setVisible(self._running)
        self.stop.setEnabled(self._running)
        self.retry.setEnabled(idle and counts[bulk.FAILED] > 0 and not foreign)
        self.export.setEnabled(bool(self.rows) and not self._running)
        selected = self._selected_row()
        self.handover.setEnabled(selected is not None and selected.status == bulk.DONE)
        for widget in (self.profile_combo, self.key_name, self.append_serial):
            widget.setEnabled(idle)

        parts = [
            tr("{count} ready", count=counts[bulk.READY] + counts[bulk.RUNNING]),
            tr("{count} enrolled", count=counts[bulk.DONE]),
        ]
        if counts[bulk.FAILED]:
            parts.append(tr("{count} failed", count=counts[bulk.FAILED]))
        if counts[bulk.NOT_FOUND]:
            parts.append(tr("{count} not found", count=counts[bulk.NOT_FOUND]))
        self.summary.setText(" · ".join(parts) if self.rows else "")

        total = sum(counts[s] for s in (bulk.READY, bulk.RUNNING, bulk.DONE, bulk.FAILED))
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(counts[bulk.DONE])
        if foreign and not self._running:
            self.step.setText(
                tr("This list belongs to another instance. Export the results and clear it.")
            )
        elif not self.rows:
            self.step.setText(tr("Load a user list to begin."))

    # -- profiles ----------------------------------------------------------

    def _reload_profiles(self) -> None:
        current = self.profile_combo.currentData()
        instance = self.ctx.config.active_instance
        preferred = (instance.default_profile if instance else None) or current
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for p in self.ctx.config.profiles:
            self.profile_combo.addItem(p.name, p.name)
        self.profile_combo.setCurrentIndex(max(0, self.profile_combo.findData(preferred)))
        self.profile_combo.blockSignals(False)
        self._show_profile()

    def _profile(self):
        return self.ctx.config.profile(self.profile_combo.currentData())

    def _show_profile(self) -> None:
        profile = self._profile()
        self.profile_info.setText(profile_summary(profile) if profile else "")

    # -- table -------------------------------------------------------------

    # The table can be sorted, so a row's position says nothing about which
    # user it shows: every row carries the index of its entry in self.rows.

    def _table_row(self, index: int) -> int:
        for position in range(self.table.rowCount()):
            item = self.table.item(position, COL_USER)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == index:
                return position
        return -1

    def _write_row(self, position: int, index: int) -> None:
        row = self.rows[index]
        user = row.user
        pin = row.pin or ""
        if pin and not self.show_pins.isChecked():
            pin = MASK
        values = [
            user.username if user else row.identifier,
            user.display_name if user else "",
            tr(bulk.STATUS_LABELS[row.status]),
            str(row.serial) if row.serial else "",
            pin,
            row.message_text,
        ]
        for col, value in enumerate(values):
            item = self.table.item(position, col)
            if item is None:
                item = SortItem()
                self.table.setItem(position, col, item)
            item.setText(value)
            item.setToolTip(value if col != COL_PIN else "")
        self.table.item(position, COL_USER).setData(Qt.ItemDataRole.UserRole, index)

    def _refresh_row(self, index: int) -> None:
        with paused_sorting(self.table):
            position = self._table_row(index)
            if position < 0:
                return
            self._write_row(position, index)
        if self.rows[index].status == bulk.RUNNING:
            position = self._table_row(index)  # sorting may have moved it
            self.table.scrollToItem(self.table.item(position, COL_USER))
            self.table.selectRow(position)

    def _refresh_all(self) -> None:
        selected = self._selected_index()
        with paused_sorting(self.table):
            self.table.setRowCount(0)
            self.table.setRowCount(len(self.rows))
            for index in range(len(self.rows)):
                self._write_row(index, index)
        if selected is not None and selected < len(self.rows):
            self.table.selectRow(self._table_row(selected))
        fit_columns(self.table)
        self._update_state()

    def _on_row_changed(self, index: int) -> None:
        row = self.rows[index]
        if row.status == bulk.DONE and row.pin:
            self._unexported = True
        self._refresh_row(index)
        fit_columns(self.table)
        self._update_state()

    def _selected_index(self) -> int | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self.table.item(selected[0].row(), COL_USER)
        index = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        return index if isinstance(index, int) and index < len(self.rows) else None

    def _selected_row(self) -> BulkRow | None:
        index = self._selected_index()
        return self.rows[index] if index is not None else None

    # -- import ------------------------------------------------------------

    def _confirm_discard(self) -> bool:
        if not self._unexported:
            return True
        answer = QMessageBox.question(
            self,
            tr("Unsaved PINs"),
            tr("The temporary PINs have not been exported and will be lost. Continue?"),
        )
        return answer == QMessageBox.StandardButton.Yes

    def _load_file(self) -> None:
        provider = self.ctx.provider
        if provider is None:
            QMessageBox.information(
                self, tr("No instance"), tr("Add an identity provider instance first.")
            )
            return
        if not provider.has_session():
            QMessageBox.information(
                self, tr("Not signed in"), tr("Sign in to the identity provider first.")
            )
            return
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Load user list"), "", tr("User lists (*.csv *.txt);;All files (*)")
        )
        if not path:
            return
        try:
            identifiers = bulk.read_identifiers(path)
        except OSError as e:
            QMessageBox.warning(self, tr("Error"), str(e))
            return
        if not identifiers:
            QMessageBox.information(
                self, tr("Load user list"), tr("No users were found in this file.")
            )
            return
        self.rows = [BulkRow(identifier) for identifier in identifiers]
        self._instance_id = self.ctx.config.active_instance_id
        self._provider_label = provider.label
        self._unexported = False
        self._refresh_all()
        self._resolve()

    def _resolve(self) -> None:
        provider = self.ctx.provider
        if provider is None or not any(r.status == bulk.NEW for r in self.rows):
            return
        self.step.setText(tr("Looking up users in the directory…"))
        worker = ResolveWorker(provider, self.rows)
        worker.row_changed.connect(self._on_row_changed)
        worker.succeeded.connect(lambda _: self._resolved(None))
        worker.failed.connect(self._resolved)
        self._begin(worker, running=False)

    def _resolved(self, exc) -> None:
        self._end()
        if exc is not None:
            self._report(exc)
        else:
            self.step.setText(tr("Ready. Insert the first security key and press Start."))

    def _clear(self) -> None:
        if not self._confirm_discard():
            return
        self.rows = []
        self._instance_id = None
        self._unexported = False
        self._refresh_all()

    def _retry_failed(self) -> None:
        for row in self.rows:
            if row.status == bulk.FAILED:
                row.status = bulk.READY if row.user else bulk.NEW
                row.message, row.message_params = "", {}
        self._refresh_all()
        self._resolve()

    # -- run ---------------------------------------------------------------

    def _begin(self, worker, running: bool) -> None:
        self._worker = worker
        self._running = running
        self.ctx.set_busy(True)
        self._update_state()
        worker.start()

    def _end(self) -> None:
        self._worker = None
        self._running = False
        self.ctx.set_busy(False)
        self._update_state()

    def _start(self) -> None:
        provider = self.ctx.provider
        profile = self._profile()
        if provider is None or profile is None:
            return
        if not provider.has_session():
            QMessageBox.information(
                self, tr("Not signed in"), tr("Sign in to the identity provider first.")
            )
            return
        ready = sum(1 for r in self.rows if r.status == bulk.READY)
        lines = [tr("{count} security key(s) will be enrolled, one per user.", count=ready)]
        lines.append(profile_summary(profile))
        if profile.reset:
            lines.append("")
            lines.append(
                tr("Every inserted key will be factory reset. All FIDO credentials on it will be erased.")
            )
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning if profile.reset else QMessageBox.Icon.Question)
        box.setWindowTitle(tr("Start bulk enrollment"))
        box.setText("\n".join(lines))
        proceed = box.addButton(tr("Start"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not proceed:
            return

        worker = BulkWorker(
            self.ctx.source,
            provider,
            profile,
            self.rows,
            self.key_name.text().strip(),
            self.append_serial.isChecked(),
        )
        worker.status.connect(self._on_status)
        worker.prompt.connect(self._on_prompt)
        worker.row_changed.connect(self._on_row_changed)
        worker.succeeded.connect(lambda _: self._finished(None))
        worker.failed.connect(self._finished)
        self._begin(worker, running=True)

    def _stop(self) -> None:
        if self._worker:
            self._worker.cancel.set()
            self.stop.setEnabled(False)
            self.step.setText(tr("Cancelling…"))

    def _on_status(self, template: str, params: dict) -> None:
        self.step.setText(tr(template, **params))

    def _on_prompt(self, prompt: PinPrompt) -> None:
        answer_prompt(self, prompt)

    def _finished(self, exc) -> None:
        self._end()
        if exc is not None:
            self._report(exc)

    def _report(self, exc) -> None:
        text = error_text(exc)
        self.step.setText(text)
        if isinstance(exc, AuthRequired):
            self.ctx.session_changed.emit()
        if not isinstance(exc, EnrollCancelled):
            QMessageBox.warning(self, tr("Bulk enrollment paused"), text)

    # -- export and hand-over ----------------------------------------------

    def _export(self) -> None:
        dialog = ExportDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export results"),
            "keyenroll-enrolled.csv" if dialog.enrolled_only else "keyenroll-results.csv",
            tr("CSV files (*.csv)"),
        )
        if not path:
            return
        try:
            bulk.write_results(
                path, self.rows, dialog.delimiter, dialog.include_pins, dialog.enrolled_only
            )
        except OSError as e:
            QMessageBox.warning(self, tr("Error"), str(e))
            return
        if dialog.include_pins:  # every enrolled user is in both kinds of export
            self._unexported = False
        self.step.setText(tr("Results exported to {path}", path=path))

    def _hand_over(self) -> None:
        row = self._selected_row()
        if row is None or row.status != bulk.DONE or row.user is None:
            return
        handover = Handover(
            user=row.user,
            key_name=row.key_name,
            serial=row.serial,
            pin=row.pin,
            pin_changed=True,
            must_change_pin=row.must_change_pin,
            provider=self._provider_label,
        )
        ResultDialog(handover, self.ctx.config, self).exec()

    def shutdown(self) -> None:
        if self._worker:
            self._worker.cancel.set()
            self._worker.wait(5000)
