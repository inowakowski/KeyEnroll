"""Dialogs: provider instance editor, PIN prompts, enrollment result, export options."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from .. import handover as handover_text
from ..config import ConfigStore, Instance
from ..handover import Handover
from ..i18n import current_language, tr
from ..providers import PROVIDERS
from .common import copy_sensitive


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
    """Shows the outcome of an enrollment and helps passing the key and the
    temporary PIN on to the user: copy, e-mail draft or text file."""

    def __init__(self, handover: Handover, config: ConfigStore, parent: QWidget):
        super().__init__(parent)
        self.handover = handover
        self.config = config
        self.setWindowTitle(tr("Enrollment complete"))
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel(tr("The security key has been enrolled."))
        title.setObjectName("title")
        layout.addWidget(title)

        form = QFormLayout()
        user = handover.user
        form.addRow(tr("User"), QLabel(user.display_name or user.username))
        if user.display_name and user.username:
            form.addRow(tr("Username"), QLabel(user.username))
        if handover.serial:
            serial = QLabel(str(handover.serial))
            serial.setObjectName("value")
            serial.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(tr("Serial number"), serial)
        if handover.key_name:
            form.addRow(tr("Key name"), QLabel(handover.key_name))
        layout.addLayout(form)

        if handover.pin:
            layout.addWidget(QLabel(tr("Temporary PIN:")))
            pin = QLabel(handover.pin)
            font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
            font.setPointSize(22)
            font.setWeight(QFont.Weight.Bold)
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
            pin.setFont(font)
            pin.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            pin.setObjectName("pin")
            self.copy_pin = QPushButton(tr("Copy PIN"))
            self.copy_pin.clicked.connect(lambda: self._copy(handover.pin))
            row = QHBoxLayout()
            row.addWidget(pin, 1)
            row.addWidget(self.copy_pin)
            layout.addLayout(row)
            note = QLabel(tr("The PIN is not stored anywhere. It is shown only in this window."))
            note.setObjectName("hint")
            note.setWordWrap(True)
            layout.addWidget(note)
        elif handover.pin_changed:
            layout.addWidget(QLabel(tr("The PIN you entered has been set on the key.")))
        else:
            layout.addWidget(QLabel(tr("The PIN of the key was not changed.")))

        if handover.must_change_pin:
            layout.addWidget(QLabel(tr("The user must change the PIN before first use.")))

        for template, params in handover.warnings:
            warning = QLabel(tr(template, **params))
            warning.setWordWrap(True)
            warning.setObjectName("error")
            layout.addWidget(warning)

        # hand-over
        section = QLabel(tr("Pass it on to the user"))
        section.setObjectName("cardTitle")
        layout.addSpacing(6)
        layout.addWidget(section)
        advice = QLabel(
            tr(
                "The message contains the PIN. Send it through a different channel "
                "than the key itself."
            )
        )
        advice.setObjectName("hint")
        advice.setWordWrap(True)
        layout.addWidget(advice)

        self.copy_message = QPushButton(tr("Copy message"))
        self.copy_message.clicked.connect(self._copy_message)
        self.email = QPushButton(tr("E-mail draft…"))
        self.email.setToolTip(handover.recipient or tr("No e-mail address is known for this user."))
        self.email.clicked.connect(self._email)
        self.save = QPushButton(tr("Save to file…"))
        self.save.clicked.connect(self._save)
        actions = QHBoxLayout()
        for button in (self.copy_message, self.email, self.save):
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.feedback = QLabel()
        self.feedback.setObjectName("hint")
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(tr("Close"))
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

    def _message(self) -> tuple[str, str]:
        return handover_text.message(
            self.handover, self.config.message_subject, self.config.message_body
        )

    def _copy(self, text: str) -> None:
        copy_sensitive(text)
        self.feedback.setText(tr("Copied. The clipboard will be cleared in one minute."))

    def _copy_message(self) -> None:
        self._copy(self._message()[1])

    def _email(self) -> None:
        subject, body = self._message()
        url = handover_text.mailto_url(self.handover.recipient, subject, body)
        if QDesktopServices.openUrl(QUrl(url)):
            self.feedback.setText(tr("A draft was opened in your e-mail program. Review it and send it."))
        else:
            self.feedback.setText(tr("No e-mail program is available. Copy the message instead."))

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Save message"),
            handover_text.default_filename(self.handover),
            tr("Text files (*.txt)"),
        )
        if not path:
            return
        subject, body = self._message()
        try:
            handover_text.save_text(path, subject, body)
        except OSError as e:
            QMessageBox.warning(self, tr("Error"), str(e))
            return
        self.feedback.setText(tr("Saved to {path}. The file contains the PIN.", path=path))


class ExportDialog(QDialog):
    """Options for exporting the bulk enrollment results."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle(tr("Export results"))
        self.setMinimumWidth(460)

        self.enrolled = QRadioButton(tr("Enrolled users only"))
        self.everyone = QRadioButton(tr("All users on the list, with their status"))
        self.enrolled.setChecked(True)
        self.pins = QCheckBox(tr("Include temporary PINs"))
        self.pins.setChecked(True)
        self.warning = QLabel(
            tr(
                "The file will contain the temporary PINs in plain text. Store it "
                "securely and delete it once the keys have been handed out."
            )
        )
        self.warning.setObjectName("error")
        self.warning.setWordWrap(True)
        self.pins.toggled.connect(self.warning.setVisible)

        self.format = QComboBox()
        self.format.addItem(tr("CSV, semicolon separated"), ";")
        self.format.addItem(tr("CSV, comma separated"), ",")
        # Spreadsheets in countries that write decimals with a comma expect
        # semicolons; that is every language offered except English.
        self.format.setCurrentIndex(1 if current_language() == "en" else 0)
        form = QFormLayout()
        form.addRow(tr("Format"), self.format)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        export = buttons.button(QDialogButtonBox.StandardButton.Ok)
        export.setText(tr("Export"))
        export.setObjectName("primary")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("Cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self.enrolled)
        layout.addWidget(self.everyone)
        layout.addSpacing(6)
        layout.addWidget(self.pins)
        layout.addWidget(self.warning)
        layout.addLayout(form)
        layout.addWidget(buttons)

    @property
    def enrolled_only(self) -> bool:
        return self.enrolled.isChecked()

    @property
    def include_pins(self) -> bool:
        return self.pins.isChecked()

    @property
    def delimiter(self) -> str:
        return self.format.currentData()
