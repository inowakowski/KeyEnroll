"""Enrollment page: pick a user, a key and options, then run the enrollment."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..config import Profile
from ..fido.devices import KeyInfo, close
from ..fido.enroll import EnrollCancelled, compose_key_name
from ..i18n import tr
from ..providers import AuthRequired
from .common import AppContext, UserPicker, error_text, run_task
from .dialogs import ResultDialog
from .profile_form import ProfileForm
from .theme import Card
from .workers import EnrollWorker, PinPrompt, answer_prompt

KEY_POLL_MS = 2000


class EnrollPage(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._worker: EnrollWorker | None = None
        self._keys: list[KeyInfo] = []
        self._refreshing = False
        self._last_paths: set | None = None

        # 1. user
        self.picker = UserPicker(ctx)
        user_card = Card(tr("1. User"))
        user_card.body.addWidget(self.picker, 1)

        # 2. key
        self.key_combo = QComboBox()
        # Key labels can be long; let the box shrink instead of widening the column.
        self.key_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.key_combo.setMinimumContentsLength(14)
        self.key_refresh = QPushButton(tr("Refresh"))
        self.key_refresh.clicked.connect(self.refresh_keys)
        self.key_combo.currentIndexChanged.connect(self._show_key_info)
        key_row = QHBoxLayout()
        key_row.addWidget(self.key_combo, 1)
        key_row.addWidget(self.key_refresh)
        self.key_serial = QLabel()
        self.key_serial.setObjectName("value")
        self.key_firmware = QLabel()
        self.key_firmware.setObjectName("value")
        self.key_details = QHBoxLayout()
        for caption, value in (
            (tr("Serial number"), self.key_serial),
            (tr("Firmware"), self.key_firmware),
        ):
            label = QLabel(caption)
            label.setObjectName("hint")
            self.key_details.addWidget(label)
            self.key_details.addWidget(value)
            self.key_details.addSpacing(18)
        self.key_details.addStretch(1)
        self.key_info = QLabel()
        self.key_info.setObjectName("hint")
        self.key_info.setWordWrap(True)
        key_card = Card(tr("2. Security key"))
        key_card.body.addLayout(key_row)
        key_card.body.addLayout(self.key_details)
        key_card.body.addWidget(self.key_info)

        # 3. options
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._load_profile)
        self.form = ProfileForm()
        self.display_name = QLineEdit()
        self.display_name.setPlaceholderText(tr("e.g. YubiKey 5 NFC"))
        self.display_name.setMaxLength(60)
        self.display_name.textChanged.connect(self._update_name_preview)
        self.append_serial = QCheckBox(tr("Add the serial number to the key name"))
        self.append_serial.setChecked(ctx.config.append_serial)
        self.append_serial.toggled.connect(self._serial_toggled)
        self.name_preview = QLabel()
        self.name_preview.setObjectName("hint")
        self.name_preview.setWordWrap(True)
        top_form = QFormLayout()
        top_form.addRow(tr("Profile"), self.profile_combo)
        top_form.addRow(tr("Key display name"), self.display_name)
        options_card = Card(tr("3. Enrollment options"))
        options_card.body.addLayout(top_form)
        options_card.body.addWidget(self.append_serial)
        options_card.body.addWidget(self.name_preview)
        options_card.body.addWidget(self.form)

        # action and progress
        self.start = QPushButton(tr("Enroll security key"))
        self.start.setObjectName("primary")
        self.start.clicked.connect(self._start)
        self.cancel = QPushButton(tr("Cancel"))
        self.cancel.clicked.connect(self._cancel)
        self.cancel.setVisible(False)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        self.step = QLabel(tr("Ready to enroll."))
        self.step.setObjectName("step")
        self.step.setWordWrap(True)
        self.log = QListWidget()
        self.log.setObjectName("log")
        self.log.setFixedHeight(64)

        action_row = QHBoxLayout()
        action_row.addWidget(self.start)
        action_row.addWidget(self.cancel)
        action_row.addSpacing(8)
        action_row.addWidget(self.step, 1)
        action_card = Card()
        action_card.body.addLayout(action_row)
        action_card.body.addWidget(self.progress)
        action_card.body.addWidget(self.log)

        # The options can be taller than a small screen: let them scroll
        # instead of forcing a minimum window height.
        right_host = QWidget()
        right = QVBoxLayout(right_host)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(14)
        right.addWidget(key_card)
        right.addWidget(options_card)
        right.addStretch(1)
        right_scroll = QScrollArea()
        right_scroll.setObjectName("plain")
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setWidget(right_host)
        right_scroll.setMinimumWidth(480)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        columns.addWidget(user_card, 1)
        columns.addWidget(right_scroll, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addLayout(columns, 1)
        layout.addWidget(action_card)

        ctx.profiles_changed.connect(self._reload_profiles)
        ctx.active_changed.connect(self._reload_profiles)
        ctx.busy_changed.connect(self._on_busy)
        self._reload_profiles()
        self._show_key_info()

        self._timer = QTimer(self)
        self._timer.setInterval(KEY_POLL_MS)
        self._timer.timeout.connect(self._poll_keys)

    # -- visibility --------------------------------------------------------

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._timer.start()
        if not self._keys:
            self.refresh_keys()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._timer.stop()

    def _on_busy(self, busy: bool) -> None:
        # Another page (bulk enrollment) owns the security key while busy.
        if self._worker is None:
            self.start.setEnabled(not busy)

    # -- profiles ----------------------------------------------------------

    def _reload_profiles(self) -> None:
        current = self.profile_combo.currentData()
        instance = self.ctx.config.active_instance
        preferred = (instance.default_profile if instance else None) or current
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for p in self.ctx.config.profiles:
            self.profile_combo.addItem(p.name, p.name)
        index = self.profile_combo.findData(preferred)
        self.profile_combo.setCurrentIndex(max(0, index))
        self.profile_combo.blockSignals(False)
        self._load_profile()
        self._update_name_preview()

    def _load_profile(self) -> None:
        profile = self.ctx.config.profile(self.profile_combo.currentData())
        if profile:
            self.form.set_profile(profile)

    # -- keys --------------------------------------------------------------

    def _poll_keys(self) -> None:
        """Cheap USB check; a full scan only runs when something changed."""
        if self.ctx.busy or self._refreshing:
            return
        try:
            from fido2.hid import list_descriptors

            paths = {str(d.path) for d in list_descriptors()}
        except Exception:
            return
        if paths != self._last_paths:
            self._last_paths = paths
            self.refresh_keys()

    def refresh_keys(self) -> None:
        if self.ctx.busy or self._refreshing:
            return
        self._refreshing = True
        self.key_refresh.setEnabled(False)
        source = self.ctx.source

        def scan() -> list[KeyInfo]:
            infos = []
            for dev in source.list():
                try:
                    infos.append(source.describe(dev))
                finally:
                    close(dev)
            return infos

        def done(infos: list[KeyInfo]) -> None:
            self._refreshing = False
            self.key_refresh.setEnabled(True)
            selected = self.key_combo.currentData()
            self._keys = infos
            self.key_combo.blockSignals(True)
            self.key_combo.clear()
            for info in infos:
                self.key_combo.addItem(info.label, info.key)
            if not infos:
                self.key_combo.addItem(tr("No security key detected"), None)
            index = self.key_combo.findData(selected)
            self.key_combo.setCurrentIndex(max(0, index))
            self.key_combo.blockSignals(False)
            self._show_key_info()

        def failed(exc) -> None:
            self._refreshing = False
            self.key_refresh.setEnabled(True)
            self.key_info.setText(error_text(exc))

        run_task(self, scan, done, failed)

    def _selected_key(self) -> KeyInfo | None:
        key = self.key_combo.currentData()
        return next((k for k in self._keys if k.key == key), None)

    def _show_key_info(self) -> None:
        info = self._selected_key()
        self.key_serial.setText(str(info.serial) if info and info.serial else "—")
        self.key_firmware.setText(info.firmware if info and info.firmware else "—")
        self._update_name_preview()
        if info is None:
            self.key_info.setText(tr("Insert a security key or place it on the NFC reader."))
            return
        if not info.ctap2:
            self.key_info.setText(tr("This security key does not support FIDO2."))
            return
        parts = [tr("PIN is set") if info.has_pin else tr("No PIN set")]
        parts.append(tr("minimum PIN length {length}", length=info.min_pin_length))
        if info.always_uv:
            parts.append(tr("always UV enabled"))
        if info.enterprise_attestation:
            parts.append(tr("Enterprise Attestation enabled"))
        if info.force_pin_change:
            parts.append(tr("PIN change required"))
        if not info.supports_config:
            parts.append(tr("no support for advanced options"))
        if not info.serial:
            parts.append(tr("serial number not readable"))
        self.key_info.setText(" · ".join(parts))

    # -- key name ----------------------------------------------------------

    def _serial_toggled(self, checked: bool) -> None:
        self.ctx.config.append_serial = checked
        self.ctx.config.save()
        self._update_name_preview()

    def _key_name(self, key: KeyInfo | None) -> str:
        base = self.display_name.text().strip()
        if not self.append_serial.isChecked():
            return base
        provider = self.ctx.provider
        limit = getattr(provider, "max_display_name", None)
        return compose_key_name(base, key.serial if key else None, limit)

    def _update_name_preview(self) -> None:
        name = self._key_name(self._selected_key())
        self.name_preview.setText(
            tr("Key will be registered as: {name}", name=name) if name else ""
        )
        self.name_preview.setVisible(bool(name) and self.append_serial.isChecked())

    # -- enrollment --------------------------------------------------------

    def is_running(self) -> bool:
        return self._worker is not None

    def _start(self) -> None:
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
        user = self.picker.selected()
        if user is None:
            QMessageBox.information(
                self, tr("No user"), tr("Search for a user and select one from the list.")
            )
            return
        key = self._selected_key()
        if key is None:
            QMessageBox.information(
                self, tr("No security key"), tr("No security key detected. Insert a key and try again.")
            )
            return
        profile: Profile = self.form.profile(self.profile_combo.currentData() or "")
        problems = profile.problems()
        if problems:
            QMessageBox.warning(self, tr("Error"), "\n".join(tr(p) for p in problems))
            return

        lines = [
            tr("User: {user}", user=user.display_name or user.username),
            tr("Security key: {key}", key=key.label),
        ]
        name = self._key_name(key)
        if name:
            lines.append(tr("Key name: {name}", name=name))
        if profile.reset:
            lines.append("")
            lines.append(
                tr("The key will be factory reset. All FIDO credentials on it will be erased.")
            )
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning if profile.reset else QMessageBox.Icon.Question)
        box.setWindowTitle(tr("Confirm enrollment"))
        box.setText("\n".join(lines))
        proceed = box.addButton(tr("Enroll"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not proceed:
            return

        self.log.clear()
        worker = EnrollWorker(
            self.ctx.source,
            provider,
            profile,
            user,
            self.display_name.text().strip(),
            key.key,
            self.append_serial.isChecked(),
        )
        worker.status.connect(self._on_status)
        worker.prompt.connect(self._on_prompt)
        worker.succeeded.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        self._worker = worker
        self._set_running(True)
        worker.start()

    def _cancel(self) -> None:
        if self._worker:
            self._worker.cancel.set()
            self.cancel.setEnabled(False)
            self._add_log(tr("Cancelling…"))

    def _set_running(self, running: bool) -> None:
        self.start.setEnabled(not running)
        self.cancel.setVisible(running)
        self.cancel.setEnabled(True)
        self.progress.setVisible(running)
        for widget in (self.picker, self.key_combo, self.key_refresh, self.profile_combo,
                       self.form, self.display_name, self.append_serial):
            widget.setEnabled(not running)
        self.ctx.set_busy(running)

    def _add_log(self, text: str) -> None:
        self.log.addItem(f"{time.strftime('%H:%M:%S')}  {text}")
        self.log.scrollToBottom()

    def _on_status(self, template: str, params: dict) -> None:
        text = tr(template, **params)
        self.step.setText(text)
        self._add_log(text)

    def _on_prompt(self, prompt: PinPrompt) -> None:
        answer_prompt(self, prompt)

    def _finish(self) -> None:
        self._worker = None
        self._set_running(False)
        self._last_paths = None  # the key state changed, rescan

    def _on_done(self, result) -> None:
        self._finish()
        self.step.setText(tr("The security key has been enrolled."))
        ResultDialog(result, self).exec()
        self.refresh_keys()

    def _on_failed(self, exc) -> None:
        self._finish()
        text = error_text(exc)
        self.step.setText(text)
        self._add_log(text)
        if isinstance(exc, AuthRequired):
            self.ctx.session_changed.emit()
        if not isinstance(exc, EnrollCancelled):
            QMessageBox.warning(self, tr("Enrollment failed"), text)
        self.refresh_keys()

    def shutdown(self) -> None:
        if self._worker:
            self._worker.cancel.set()
            self._worker.wait(5000)
