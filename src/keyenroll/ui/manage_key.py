"""Manage key: which applications a YubiKey offers, and the optional lock."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .. import lock_codes
from ..fido.devices import KeyInfo, close, device_key
from ..fido.management import (
    APPLICATIONS,
    CLEAR_LOCK,
    REQUIRED,
    Capability,
    DeviceConfig,
    ManagementError,
    check_supported,
    read_config,
    write_config,
)
from ..i18n import N_, tr
from ..journal import Journal, JournalContext, journal_dir
from .common import AppContext, error_text, run_task
from .dialogs import check_key_apps

logger = logging.getLogger(__name__)


def describe_change(usb: int, nfc: int | None, locked: bool) -> str:
    """For the deployment log, in English."""

    def names(caps: int) -> str:
        return ", ".join(c.name for c, _ in APPLICATIONS if caps & c) or "none"

    text = f"USB: {names(usb)}"
    if nfc is not None:
        text += f"; NFC: {names(nfc)}"
    return text + ("; configuration locked" if locked else "")


class ManageKeyDialog(QDialog):
    """Reads the key when opened; writes only on Apply. Optional: nothing in
    the enrollment depends on it."""

    def __init__(self, ctx: AppContext, key: KeyInfo, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self.key = key
        self.config: DeviceConfig | None = None
        self.applied = False
        self.setWindowTitle(tr("Manage key"))
        self.setMinimumWidth(560)

        title = QLabel(key.label)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)
        self.state = QLabel(tr("Reading the security key…"))
        self.state.setObjectName("hint")
        self.state.setWordWrap(True)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(18)
        self.usb_boxes: dict[Capability, QCheckBox] = {}
        self.nfc_boxes: dict[Capability, QCheckBox] = {}

        self.code_choice = QComboBox()
        self.lock = QCheckBox(tr("Lock the configuration with this code"))
        self.lock.setToolTip(
            tr("The user cannot enable the applications again, for example in Yubico Authenticator.")
        )
        self.code_choice.currentIndexChanged.connect(self._update_lock)
        self.lock.toggled.connect(self._update_lock)
        lock_form = QFormLayout()
        lock_form.addRow(tr("Lock code"), self.code_choice)
        lock_form.addRow(self.lock)
        self.lock_note = QLabel()
        self.lock_note.setObjectName("hint")
        self.lock_note.setWordWrap(True)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel
        )
        self.apply = self.buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.apply.setText(tr("Apply"))
        self.apply.setObjectName("primary")
        self.apply.setEnabled(False)
        self.apply.clicked.connect(self._apply)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Cancel"))
        self.buttons.rejected.connect(self.reject)

        self.options = QWidget()
        options = QVBoxLayout(self.options)
        options.setContentsMargins(0, 0, 0, 0)
        heading = QLabel(tr("Enabled applications"))
        heading.setObjectName("step")
        options.addWidget(heading)
        options.addLayout(self.grid)
        options.addSpacing(8)
        options.addLayout(lock_form)
        options.addWidget(self.lock_note)
        self.options.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.state)
        layout.addWidget(self.options)
        layout.addStretch(1)
        layout.addWidget(self.buttons)
        self._fill_codes()
        self._read()

    # -- the key -------------------------------------------------------------

    def _with_device(self, action):
        """Opens the key this dialog is about, runs ``action(dev)``, closes it."""
        source = self.ctx.source
        wanted = self.key.key

        def run():
            devices = source.list()
            chosen = None
            for dev in devices:
                if chosen is None and device_key(dev) == wanted:
                    chosen = dev
                else:
                    close(dev)
            if chosen is None:
                raise ManagementError(
                    N_("The selected security key is no longer connected. Refresh the list.")
                )
            try:
                return action(chosen)
            finally:
                close(chosen)

        return run

    def _read(self) -> None:
        def done(config: DeviceConfig) -> None:
            self.config = config
            self._show(config)

        def failed(exc) -> None:
            self.state.setText(error_text(exc))

        def read(dev) -> DeviceConfig:
            config = read_config(dev)
            check_supported(config)
            return config

        run_task(self, self._with_device(read), done, failed)

    def _show(self, config: DeviceConfig) -> None:
        nfc = bool(config.nfc_supported)
        self.grid.addWidget(QLabel(tr("Application")), 0, 0)
        center = Qt.AlignmentFlag.AlignCenter
        self.grid.addWidget(QLabel("USB"), 0, 1, center)
        if nfc:
            self.grid.addWidget(QLabel("NFC"), 0, 2, center)
        row = 1
        for cap, label in APPLICATIONS:
            if not (config.usb_supported | config.nfc_supported) & cap:
                continue
            self.grid.addWidget(QLabel(tr(label)), row, 0)
            for column, (supported, enabled, boxes) in enumerate(
                (
                    (config.usb_supported, config.usb_enabled, self.usb_boxes),
                    (config.nfc_supported, config.nfc_enabled, self.nfc_boxes),
                ),
                start=1,
            ):
                if column == 2 and not nfc:
                    continue
                box = QCheckBox()
                box.setChecked(bool(enabled & cap))
                box.setEnabled(bool(supported & cap) and cap != REQUIRED)
                if cap == REQUIRED:
                    box.setChecked(True)
                    box.setToolTip(tr("Always on: KeyEnroll enrolls keys with it."))
                box.setVisible(bool(supported & cap))
                boxes[cap] = box
                self.grid.addWidget(box, row, column, Qt.AlignmentFlag.AlignCenter)
            row += 1
        if config.locked:
            self.state.setText(
                tr("The configuration is locked. Choose the profile whose lock code it was locked with.")
            )
            self.lock.setChecked(True)
        else:
            self.state.setText(tr("The configuration is not locked."))
        self.options.setVisible(True)
        self.apply.setEnabled(True)
        self._update_lock()

    # -- lock codes ----------------------------------------------------------

    def _fill_codes(self) -> None:
        self.code_choice.addItem(tr("No lock code"), None)
        for profile in self.ctx.config.profiles:
            if lock_codes.get(self.ctx.tokens, profile) is not None:
                self.code_choice.addItem(tr("Profile: {name}", name=profile.name), profile.name)

    def _code(self) -> bytes | None:
        name = self.code_choice.currentData()
        profile = self.ctx.config.profile(name) if name else None
        return lock_codes.get(self.ctx.tokens, profile) if profile else None

    def _update_lock(self, *_args) -> None:
        has_code = self._code() is not None
        self.lock.setEnabled(has_code)
        if not has_code:
            self.lock.setChecked(False)
        locked = bool(self.config and self.config.locked)
        if locked and not has_code:
            note = tr("Changing a locked key needs its lock code.")
        elif locked and not self.lock.isChecked():
            note = tr("Applying removes the lock.")
        elif not self.ctx.config.profiles or self.code_choice.count() == 1:
            note = tr("To lock keys, create a lock code on the Profiles page.")
        else:
            note = ""
        self.lock_note.setText(note)
        self.lock_note.setVisible(bool(note))

    # -- writing ---------------------------------------------------------------

    @staticmethod
    def _caps(boxes: dict[Capability, QCheckBox]) -> int:
        return sum(int(cap) for cap, box in boxes.items() if box.isChecked())

    def _apply(self) -> None:
        config = self.config
        if config is None:
            return
        usb = self._caps(self.usb_boxes) | REQUIRED
        nfc = (self._caps(self.nfc_boxes) | REQUIRED) if config.nfc_supported else None
        code = self._code()
        keep_locked = self.lock.isChecked() and code is not None
        if config.locked and code is None:
            QMessageBox.warning(self, tr("Manage key"), tr("Changing a locked key needs its lock code."))
            return
        cur_lock = code if config.locked else None
        if config.locked:
            new_lock = None if keep_locked else CLEAR_LOCK
        else:
            new_lock = code if keep_locked else None
        if config.locked and not keep_locked:
            answer = QMessageBox.question(
                self,
                tr("Manage key"),
                tr("Remove the lock? The user will be able to change the applications again."),
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        if not check_key_apps(self):
            return

        self.apply.setEnabled(False)
        self.state.setText(tr("Writing the configuration…"))
        self.ctx.set_busy(True)

        def write(dev) -> None:
            fresh = read_config(dev)  # the key may have changed since it was read
            write_config(dev, fresh, usb, nfc, cur_lock, new_lock)

        def done(_) -> None:
            self.ctx.set_busy(False)
            self.applied = True
            self._log(describe_change(usb, nfc, keep_locked))
            QMessageBox.information(
                self,
                tr("Manage key"),
                tr("Saved. Remove the security key and insert it again for the changes to take effect."),
            )
            self.accept()

        def failed(exc) -> None:
            self.ctx.set_busy(False)
            self.apply.setEnabled(True)
            self.state.setText(error_text(exc))

        run_task(self, self._with_device(write), done, failed)

    def _log(self, message: str) -> None:
        instance = self.ctx.config.active_instance
        provider = self.ctx.provider
        context = JournalContext(
            instance=instance.name if instance else "",
            provider=provider.label if provider else "",
            operator=getattr(provider, "operator", "") if provider else "",
            profile=self.code_choice.currentData() or "",
        )
        Journal(journal_dir(self.ctx.config.path), context, self.ctx.config.journal_enabled).configured(
            self.key, message
        )
