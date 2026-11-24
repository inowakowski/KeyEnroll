"""The optional configuration lock code of a profile, on the Profiles page."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import lock_codes
from ..config import Profile
from ..i18n import tr
from .common import AppContext, copy_sensitive


class LockCodeEditor(QWidget):
    """Works on the stored profile: the code is saved at once, apart from
    the other settings of the form."""

    changed = Signal(str)  # the profile's new lock_code_id

    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._name: str | None = None
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.generate = QPushButton(tr("Generate"))
        self.enter = QPushButton(tr("Enter…"))
        self.copy = QPushButton(tr("Copy"))
        self.remove = QPushButton(tr("Remove"))
        self.remove.setObjectName("danger")
        self.generate.clicked.connect(self._generate)
        self.enter.clicked.connect(self._enter)
        self.copy.clicked.connect(self._copy)
        self.remove.clicked.connect(self._remove)
        buttons = QHBoxLayout()
        for button in (self.generate, self.enter, self.copy, self.remove):
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.status)
        layout.addLayout(buttons)
        self.set_profile(None)

    def _profile(self) -> Profile | None:
        return self.ctx.config.profile(self._name) if self._name else None

    def _code(self) -> bytes | None:
        profile = self._profile()
        return lock_codes.get(self.ctx.tokens, profile) if profile else None

    def set_profile(self, name: str | None) -> None:
        """The stored profile to work on; None for one not saved yet."""
        self._name = name
        profile = self._profile()
        code = self._code()
        if profile is None:
            text = tr("Save the profile first.")
        elif code is not None:
            text = tr("A lock code is stored on this computer.")
        elif profile.lock_code_id:
            text = tr(
                "This profile has a lock code, but it is not stored on this computer. "
                "Enter it to use it here."
            )
        else:
            text = tr("No lock code. Keys are configured without a lock.")
        self.status.setText(text)
        for button in (self.generate, self.enter):
            button.setEnabled(profile is not None)
        self.copy.setEnabled(code is not None)
        self.remove.setEnabled(bool(profile and profile.lock_code_id))

    def _store(self, code: bytes | None) -> None:
        profile = self._profile()
        if profile is None:
            return
        if code is None:
            lock_codes.forget(self.ctx.tokens, profile)
        else:
            lock_codes.put(self.ctx.tokens, profile, code)
        self.ctx.config.upsert_profile(profile, old_name=profile.name)
        self.changed.emit(profile.lock_code_id)
        self.set_profile(profile.name)

    def _replacing_ok(self) -> bool:
        profile = self._profile()
        if not (profile and profile.lock_code_id):
            return True
        answer = QMessageBox.question(
            self,
            tr("Replace the lock code"),
            tr(
                "Keys locked with the current code can then only be changed with "
                "that code. Replace it anyway?"
            ),
        )
        return answer == QMessageBox.StandardButton.Yes

    def _generate(self) -> None:
        if not self._replacing_ok():
            return
        code = lock_codes.generate()
        self._store(code)
        self._show_new(code)

    def _show_new(self, code: bytes) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(tr("Lock code"))
        box.setText(
            tr(
                "Keep a copy of the lock code in your password manager. Without it, "
                "keys locked with it can no longer be changed.\n\n{code}",
                code=lock_codes.to_text(code),
            )
        )
        copy = box.addButton(tr("Copy"), QMessageBox.ButtonRole.ActionRole)
        box.addButton(tr("Close"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()
        if box.clickedButton() is copy:
            copy_sensitive(lock_codes.to_text(code))

    def _enter(self) -> None:
        if not self._replacing_ok():
            return
        text, ok = QInputDialog.getText(
            self,
            tr("Lock code"),
            tr("Lock code (32 hexadecimal characters):"),
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        code = lock_codes.parse(text)
        if code is None:
            QMessageBox.warning(
                self, tr("Error"), tr("A lock code is 32 hexadecimal characters (0-9, a-f).")
            )
            return
        self._store(code)

    def _copy(self) -> None:
        code = self._code()
        if code is not None:
            copy_sensitive(lock_codes.to_text(code))

    def _remove(self) -> None:
        answer = QMessageBox.question(
            self,
            tr("Remove the lock code"),
            tr(
                "Remove the lock code from this profile and this computer? Keys locked "
                "with it can then only be changed if you kept a copy."
            ),
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._store(None)
