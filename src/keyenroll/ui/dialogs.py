"""Dialogs: provider instance editor, PIN prompts, enrollment result."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import ConfigStore, Instance
from ..fido.enroll import EnrollResult
from ..i18n import tr
from ..providers import PROVIDERS


class InstanceDialog(QDialog):
    """Adds or edits a named identity provider configuration."""

    def __init__(self, config: ConfigStore, instance: Instance | None, parent: QWidget):
        super().__init__(parent)
        self.config = config
        self.instance = instance
        self.setWindowTitle(tr("Edit instance") if instance else tr("Add instance"))
        self.setMinimumWidth(520)

        self.name = QLineEdit(instance.name if instance else "")
        self.name.setPlaceholderText(tr("e.g. Production tenant"))
        self.kind = QComboBox()
        for kind, cls in PROVIDERS.items():
            self.kind.addItem(cls.label, kind)
        if instance:
            self.kind.setCurrentIndex(self.kind.findData(instance.kind))
            self.kind.setEnabled(False)
        self.profile = QComboBox()
        self.profile.addItem(tr("(none)"), None)
        for p in config.profiles:
            self.profile.addItem(p.name, p.name)
        if instance and instance.default_profile:
            self.profile.setCurrentIndex(max(0, self.profile.findData(instance.default_profile)))

        # One form so that all labels share a column; the provider-specific
        # rows live between the fixed head and tail rows.
        self._form = QFormLayout()
        self._form.addRow(tr("Instance name"), self.name)
        self._form.addRow(tr("Identity provider"), self.kind)
        self._form.addRow(tr("Default profile"), self.profile)
        self._inputs: dict[str, QLineEdit | QComboBox] = {}

        note = QLabel(
            tr(
                "Use the values of the application registered for YubiEnroll at the "
                "identity provider. The redirect URI must match the registration exactly."
            )
        )
        note.setWordWrap(True)
        note.setObjectName("hint")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("Save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Cancel"))
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(self._form)
        layout.addWidget(note)
        layout.addWidget(buttons)

        self.kind.currentIndexChanged.connect(self._build_fields)
        self._build_fields()

    def _build_fields(self) -> None:
        head, tail = 2, 1
        while self._form.rowCount() > head + tail:
            self._form.removeRow(head)
        self._inputs.clear()
        cls = PROVIDERS[self.kind.currentData()]
        saved = self.instance.settings if self.instance else {}
        for spec in cls.fields:
            value = saved.get(spec.key) or spec.default
            if spec.choices:
                widget: QLineEdit | QComboBox = QComboBox()
                for choice, label in spec.choices:
                    widget.addItem(label, choice)
                widget.setCurrentIndex(max(0, widget.findData(value)))
            else:
                widget = QLineEdit(value)
                widget.setPlaceholderText(spec.placeholder)
            if spec.help:
                widget.setToolTip(tr(spec.help))
            label = tr(spec.label) + ("" if spec.required else " " + tr("(optional)"))
            self._form.insertRow(head + len(self._inputs), label, widget)
            self._inputs[spec.key] = widget
        self.adjustSize()

    def _settings(self) -> dict[str, str]:
        out = {}
        for key, widget in self._inputs.items():
            if isinstance(widget, QComboBox):
                out[key] = widget.currentData()
            else:
                out[key] = widget.text().strip()
        return out

    def _save(self) -> None:
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("Error"), tr("Instance name cannot be empty."))
            return
        own_id = self.instance.id if self.instance else None
        if any(i.name == name and i.id != own_id for i in self.config.instances):
            QMessageBox.warning(
                self, tr("Error"), tr("An instance with this name already exists.")
            )
            return
        kind = self.kind.currentData()
        settings = self._settings()
        missing = PROVIDERS[kind].missing_settings(settings)
        if missing:
            QMessageBox.warning(
                self,
                tr("Error"),
                tr("Required field is empty: {field}", field=tr(missing[0].label)),
            )
            return
        redirect = settings.get("redirect_uri", "")
        if not redirect.startswith("http://localhost"):
            QMessageBox.warning(
                self, tr("Error"), tr("The redirect URI must start with http://localhost.")
            )
            return
        if self.instance:
            self.instance.name = name
            self.instance.settings = settings
            self.instance.default_profile = self.profile.currentData()
        else:
            self.instance = Instance(
                name=name,
                kind=kind,
                settings=settings,
                default_profile=self.profile.currentData(),
            )
        self.accept()


def _pin_field() -> QLineEdit:
    field = QLineEdit()
    field.setEchoMode(QLineEdit.EchoMode.Password)
    field.setMaxLength(63)
    return field


def _show_toggle(*fields: QLineEdit) -> QCheckBox:
    toggle = QCheckBox(tr("Show PIN"))

    def apply(checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        for f in fields:
            f.setEchoMode(mode)

    toggle.toggled.connect(apply)
    return toggle


def _ok_cancel(dialog: QDialog) -> QDialogButtonBox:
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Cancel"))
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    return buttons


class CurrentPinDialog(QDialog):
    def __init__(self, retries: int | None, wrong: bool, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle(tr("Security key PIN"))
        self.pin = _pin_field()
        layout = QVBoxLayout(self)
        if wrong:
            warning = QLabel(tr("Wrong PIN."))
            warning.setObjectName("error")
            layout.addWidget(warning)
        layout.addWidget(QLabel(tr("Enter the current PIN of the security key:")))
        layout.addWidget(self.pin)
        if retries is not None:
            layout.addWidget(QLabel(tr("Attempts remaining: {retries}", retries=retries)))
        layout.addWidget(_show_toggle(self.pin))
        layout.addWidget(_ok_cancel(self))

    def value(self) -> str:
        return self.pin.text()


class NewPinDialog(QDialog):
    def __init__(self, min_length: int, rejected: bool, parent: QWidget):
        super().__init__(parent)
        self.min_length = min_length
        self.setWindowTitle(tr("New PIN"))
        self.pin = _pin_field()
        self.confirm = _pin_field()
        self.message = QLabel()
        self.message.setObjectName("error")
        if rejected:
            self.message.setText(
                tr("The security key rejected this PIN (too short or too simple).")
            )
        form = QFormLayout()
        form.addRow(tr("New PIN"), self.pin)
        form.addRow(tr("Repeat PIN"), self.confirm)
        layout = QVBoxLayout(self)
        layout.addWidget(self.message)
        layout.addWidget(
            QLabel(tr("Choose a PIN of at least {length} characters.", length=min_length))
        )
        layout.addLayout(form)
        layout.addWidget(_show_toggle(self.pin, self.confirm))
        layout.addWidget(_ok_cancel(self))

    def accept(self) -> None:
        if len(self.pin.text()) < self.min_length:
            self.message.setText(tr("The PIN is too short."))
        elif self.pin.text() != self.confirm.text():
            self.message.setText(tr("The PINs do not match."))
        else:
            super().accept()

    def value(self) -> str:
        return self.pin.text()


class ResultDialog(QDialog):
    def __init__(self, result: EnrollResult, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle(tr("Enrollment complete"))
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)

        title = QLabel(tr("The security key has been enrolled."))
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        user = result.user
        form.addRow(tr("User"), QLabel(user.display_name or user.username))
        if user.display_name and user.username:
            form.addRow(tr("Username"), QLabel(user.username))
        form.addRow(tr("Security key"), QLabel(result.key.name))
        if result.key.serial:
            serial = QLabel(str(result.key.serial))
            serial.setObjectName("value")
            serial.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(tr("Serial number"), serial)
        if result.display_name:
            form.addRow(tr("Key name"), QLabel(result.display_name))
        layout.addLayout(form)

        if result.pin:
            layout.addWidget(QLabel(tr("Temporary PIN:")))
            pin = QLabel(result.pin)
            font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
            font.setPointSize(22)
            font.setWeight(QFont.Weight.Bold)
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
            pin.setFont(font)
            pin.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            pin.setObjectName("pin")
            copy = QPushButton(tr("Copy"))
            copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(result.pin))
            row = QHBoxLayout()
            row.addWidget(pin, 1)
            row.addWidget(copy)
            layout.addLayout(row)
            note = QLabel(
                tr(
                    "The PIN is shown only once. Hand it over to the user together "
                    "with the security key."
                )
            )
            note.setWordWrap(True)
            layout.addWidget(note)
        elif result.pin_changed:
            layout.addWidget(QLabel(tr("The PIN you entered has been set on the key.")))
        else:
            layout.addWidget(QLabel(tr("The PIN of the key was not changed.")))

        if result.key.force_pin_change:
            layout.addWidget(QLabel(tr("The user must change the PIN before first use.")))

        for template, params in result.warnings:
            warning = QLabel(tr(template, **params))
            warning.setWordWrap(True)
            warning.setObjectName("error")
            layout.addWidget(warning)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(tr("Close"))
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
