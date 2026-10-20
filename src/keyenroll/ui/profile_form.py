"""Controls for the enrollment options of a profile."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config import MAX_PIN, MIN_PIN, Profile, normalize_aaguid
from ..fido.devices import DeviceSource, KeyInfo, close
from ..i18n import tr
from .common import run_task


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

        # Allowed key models are edited on the Profiles page only; they are
        # carried along so that a one-off change of options keeps them.
        self._models: list[dict[str, str]] = []
        self._min_firmware = ""
        self._unknown_firmware = "refuse"

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
        self._models = [dict(m) for m in p.allowed_models]
        self._min_firmware = p.min_firmware
        self._unknown_firmware = p.unknown_firmware
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
            allowed_models=[dict(m) for m in self._models],
            min_firmware=self._min_firmware,
            unknown_firmware=self._unknown_firmware,
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
    if p.allowed_models:
        parts.append(tr("only {count} allowed key model(s)", count=len(p.allowed_models)))
    if p.min_firmware:
        parts.append(tr("firmware {version} or newer", version=p.min_firmware))
    return " · ".join(parts)


def model_label(model: dict[str, str]) -> str:
    name = model.get("name") or tr("Unnamed model")
    return f"{name} · {model['aaguid']}"


class ModelDialog(QDialog):
    """Asks for an AAGUID and a name to recognise it by."""

    def __init__(self, parent: QWidget, aaguid: str = "", name: str = ""):
        super().__init__(parent)
        self.setWindowTitle(tr("Allowed key model"))
        self.setMinimumWidth(460)
        self.aaguid = QLineEdit(aaguid)
        self.aaguid.setPlaceholderText("cb69481e-8ff7-4039-93ec-0a2729a154a8")
        self.aaguid.setReadOnly(bool(aaguid))
        self.name = QLineEdit(name)
        self.name.setPlaceholderText(tr("e.g. YubiKey 5 NFC"))
        self.name.setMaxLength(60)
        self.message = QLabel()
        self.message.setObjectName("error")
        form = QFormLayout()
        form.addRow("AAGUID", self.aaguid)
        form.addRow(tr("Name"), self.name)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.message)
        layout.addWidget(buttons)

    def accept(self) -> None:
        if normalize_aaguid(self.aaguid.text()) is None:
            self.message.setText(tr("This is not an AAGUID."))
            return
        super().accept()

    def value(self) -> dict[str, str]:
        return {
            "aaguid": normalize_aaguid(self.aaguid.text()) or "",
            "name": self.name.text().strip(),
        }


class KeyModelsEditor(QWidget):
    """Which key models a profile accepts, and the minimum firmware."""

    def __init__(self, source: DeviceSource, parent: QWidget | None = None):
        super().__init__(parent)
        self.source = source
        self.list = QListWidget()
        # A handful of models at most: no need to take the whole page.
        self.list.setFixedHeight(120)
        self.list.itemSelectionChanged.connect(self._update_buttons)
        self.list.itemDoubleClicked.connect(self._rename)
        self.add_connected = QPushButton(tr("Add the connected key"))
        self.add_connected.setToolTip(tr("Reads the model of the security key that is plugged in."))
        self.add_connected.clicked.connect(self._add_connected)
        self.add_manual = QPushButton(tr("Add AAGUID…"))
        self.add_manual.clicked.connect(self._add)
        self.remove = QPushButton(tr("Remove from the list"))
        self.remove.clicked.connect(self._remove)
        buttons = QHBoxLayout()
        for b in (self.add_connected, self.add_manual, self.remove):
            buttons.addWidget(b)
        buttons.addStretch(1)

        self.min_firmware = QLineEdit()
        self.min_firmware.setPlaceholderText(tr("e.g. 5.7 (empty: any)"))
        self.min_firmware.setMaxLength(20)
        self.min_firmware.textChanged.connect(self._update_buttons)
        self.unknown = QComboBox()
        self.unknown.addItem(tr("Refuse the key"), "refuse")
        self.unknown.addItem(tr("Only warn"), "warn")
        self.unknown.setToolTip(
            tr(
                "The firmware version is read from YubiKeys over USB only. This "
                "decides what happens with other keys and keys on an NFC reader."
            )
        )
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow(tr("Minimum firmware"), self.min_firmware)
        form.addRow(tr("If the version cannot be read"), self.unknown)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)
        layout.addLayout(buttons)
        layout.addLayout(form)
        self._update_buttons()

    def set_profile(self, p: Profile) -> None:
        self.list.clear()
        for model in p.allowed_models:
            self._append(model)
        self.min_firmware.setText(p.min_firmware)
        self.unknown.setCurrentIndex(max(0, self.unknown.findData(p.unknown_firmware)))
        self._update_buttons()

    def apply(self, p: Profile) -> Profile:
        """Returns ``p`` with the restrictions shown in the editor."""
        p.allowed_models = [
            dict(self.list.item(row).data(Qt.ItemDataRole.UserRole))
            for row in range(self.list.count())
        ]
        p.min_firmware = self.min_firmware.text().strip()
        p.unknown_firmware = self.unknown.currentData()
        return p

    def _append(self, model: dict[str, str]) -> None:
        item = QListWidgetItem(model_label(model))
        item.setData(Qt.ItemDataRole.UserRole, dict(model))
        self.list.addItem(item)

    def _known(self) -> set[str]:
        return {
            self.list.item(row).data(Qt.ItemDataRole.UserRole)["aaguid"]
            for row in range(self.list.count())
        }

    def _update_buttons(self) -> None:
        self.remove.setEnabled(bool(self.list.selectedItems()))
        self.unknown.setEnabled(bool(self.min_firmware.text().strip()))

    def _add(self, aaguid: str = "", name: str = "") -> None:
        if aaguid in self._known():
            return  # the connected key is on the list already
        dialog = ModelDialog(self, aaguid, name)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        model = dialog.value()
        if model["aaguid"] in self._known():
            QMessageBox.information(
                self, tr("Allowed key model"), tr("This model is already on the list.")
            )
            return
        self._append(model)

    def _add_connected(self) -> None:
        source = self.source
        self.add_connected.setEnabled(False)

        def scan() -> list[KeyInfo]:
            infos = []
            for dev in source.list():
                try:
                    infos.append(source.describe(dev))
                finally:
                    close(dev)
            return infos

        def done(infos: list[KeyInfo]) -> None:
            self.add_connected.setEnabled(True)
            models = [i for i in infos if i.aaguid]
            if not models:
                QMessageBox.information(
                    self,
                    tr("Allowed key model"),
                    tr("No connected security key reports its model. Insert a key and try again."),
                )
                return
            for info in models:
                self._add(info.aaguid, info.name)

        def failed(exc) -> None:
            self.add_connected.setEnabled(True)
            QMessageBox.warning(self, tr("Error"), str(exc))

        run_task(self, scan, done, failed)

    def _rename(self, item: QListWidgetItem) -> None:
        model = item.data(Qt.ItemDataRole.UserRole)
        dialog = ModelDialog(self, model["aaguid"], model.get("name", ""))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            model = dialog.value()
            item.setData(Qt.ItemDataRole.UserRole, model)
            item.setText(model_label(model))

    def _remove(self) -> None:
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
        self._update_buttons()
