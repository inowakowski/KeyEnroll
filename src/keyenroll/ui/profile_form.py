"""Controls for the enrollment options of a profile."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QFormLayout, QSpinBox, QWidget

from ..config import MAX_PIN, MIN_PIN, Profile
from ..i18n import tr


class ProfileForm(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.min_pin = QSpinBox()
        self.min_pin.setRange(MIN_PIN, MAX_PIN)
        self.reset = QCheckBox(tr("Factory reset the security key"))
        self.reset.setToolTip(tr("Erases all FIDO credentials and the PIN on the key."))
        self.random_pin = QCheckBox(tr("Set new random PIN"))
        self.random_len = QSpinBox()
        self.random_len.setRange(MIN_PIN, MAX_PIN)
        self.force_change = QCheckBox(tr("Force PIN change before use"))
        self.always_uv = QCheckBox(tr("Require always UV"))
        self.always_uv.setToolTip(tr("The key asks for the PIN on every use."))
        self.ea = QCheckBox(tr("Require Enterprise Attestation"))

        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow(self.reset)
        form.addRow(self.random_pin)
        form.addRow(tr("Random PIN length"), self.random_len)
        form.addRow(tr("Minimum PIN length"), self.min_pin)
        form.addRow(self.force_change)
        form.addRow(self.always_uv)
        form.addRow(self.ea)

        self.random_pin.toggled.connect(self.random_len.setEnabled)
        for box in (self.reset, self.random_pin, self.force_change, self.always_uv, self.ea):
            box.toggled.connect(self.changed)
        for spin in (self.min_pin, self.random_len):
            spin.valueChanged.connect(self.changed)
        self.set_profile(Profile())

    def set_profile(self, p: Profile) -> None:
        self.blockSignals(True)
        self.min_pin.setValue(p.min_pin_length)
        self.reset.setChecked(p.reset)
        self.random_pin.setChecked(p.random_pin)
        self.random_len.setValue(p.random_pin_length)
        self.random_len.setEnabled(p.random_pin)
        self.force_change.setChecked(p.force_pin_change)
        self.always_uv.setChecked(p.require_always_uv)
        self.ea.setChecked(p.require_ea)
        self.blockSignals(False)

    def profile(self, name: str = "") -> Profile:
        return Profile(
            name=name,
            min_pin_length=self.min_pin.value(),
            require_always_uv=self.always_uv.isChecked(),
            require_ea=self.ea.isChecked(),
            force_pin_change=self.force_change.isChecked(),
            reset=self.reset.isChecked(),
            random_pin=self.random_pin.isChecked(),
            random_pin_length=self.random_len.value(),
        )


def profile_summary(p: Profile) -> str:
    """One-line description of what a profile does to a key."""
    parts = [tr("factory reset") if p.reset else tr("no factory reset")]
    if p.random_pin:
        length = max(p.random_pin_length, p.min_pin_length)
        parts.append(tr("random PIN of {length} digits", length=length))
    else:
        parts.append(tr("PIN entered by the operator"))
    parts.append(tr("minimum PIN length {length}", length=p.min_pin_length))
    if p.force_pin_change:
        parts.append(tr("forced PIN change"))
    if p.require_always_uv:
        parts.append(tr("always UV"))
    if p.require_ea:
        parts.append(tr("Enterprise Attestation"))
    return " · ".join(parts)
