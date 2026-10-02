"""Settings page: appearance, language, hand-over message, about."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, PROJECT_URL, __version__, handover, updates
from ..config import config_dir
from ..i18n import LANGUAGES, tr
from .common import AppContext, run_task
from .theme import PRESETS, Card, apply_theme


class SettingsPage(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        config = ctx.config

        # -- appearance ----------------------------------------------------
        labels = {"light": tr("Light"), "dark": tr("Dark"), "yubico": "Yubico"}
        self.theme = QComboBox()
        for preset in PRESETS:
            self.theme.addItem(labels[preset], preset)
        self.theme.addItem(tr("Same as the system (light or dark)"), "auto")
        self.theme.addItem(tr("Custom"), "custom")
        self.theme.setCurrentIndex(max(0, self.theme.findData(config.theme)))
        self.theme.currentIndexChanged.connect(self._set_theme)

        self.custom_base = QComboBox()
        self.custom_base.addItem(tr("Light"), "light")
        self.custom_base.addItem(tr("Dark"), "dark")
        self.custom_base.setCurrentIndex(max(0, self.custom_base.findData(config.custom_base)))
        self.custom_base.currentIndexChanged.connect(self._set_theme)
        self.accent_swatch = QLabel()
        self.accent_swatch.setFixedSize(34, 34)
        self.accent_button = QPushButton(tr("Accent colour…"))
        self.accent_button.clicked.connect(self._pick_accent)
        self.custom_row = QWidget()
        custom = QHBoxLayout(self.custom_row)
        custom.setContentsMargins(0, 0, 0, 0)
        custom.addWidget(self.custom_base)
        custom.addWidget(self.accent_swatch)
        custom.addWidget(self.accent_button)
        custom.addStretch(1)
        self.custom_label = QLabel(tr("Custom colours"))

        appearance = Card(tr("Appearance"))
        appearance_form = QFormLayout()
        appearance_form.addRow(tr("Colour scheme"), self.theme)
        appearance_form.addRow(self.custom_label, self.custom_row)
        appearance.body.addLayout(appearance_form)

        # -- language ------------------------------------------------------
        self.language = QComboBox()
        self.language.addItem(tr("Same as the system"), "auto")
        for code, label in LANGUAGES.items():
            self.language.addItem(label, code)
        self.language.setCurrentIndex(max(0, self.language.findData(config.language)))
        self.language.currentIndexChanged.connect(self._set_language)
        self.language_note = QLabel()
        self.language_note.setObjectName("hint")
        self.language_note.setVisible(False)
        language = Card(tr("Language"))
        language_form = QFormLayout()
        language_form.addRow(tr("Language"), self.language)
        language.body.addLayout(language_form)
        language.body.addWidget(self.language_note)

        # -- hand-over message --------------------------------------------
        self.subject = QLineEdit()
        self.body = QPlainTextEdit()
        self.body.setMinimumHeight(190)
        self.body.setTabChangesFocus(True)
        self.save_message = QPushButton(tr("Save"))
        self.save_message.setObjectName("primary")
        self.save_message.clicked.connect(self._save_message)
        self.reset_message = QPushButton(tr("Restore the default text"))
        self.reset_message.clicked.connect(self._reset_message)
        self.message_note = QLabel()
        self.message_note.setObjectName("hint")
        message_buttons = QHBoxLayout()
        message_buttons.addWidget(self.save_message)
        message_buttons.addWidget(self.reset_message)
        message_buttons.addWidget(self.message_note, 1)
        message = Card(
            tr("Message for the user"),
            tr(
                "Used after an enrollment for the e-mail draft, the copied message and "
                "the saved file. Placeholders: {placeholders}.",
                placeholders=", ".join("{%s}" % name for name in handover.PLACEHOLDERS),
            ),
        )
        message_form = QFormLayout()
        message_form.addRow(tr("Subject"), self.subject)
        message_form.addRow(tr("Text"), self.body)
        message.body.addLayout(message_form)
        message.body.addLayout(message_buttons)
        self._load_message()

        # -- about ---------------------------------------------------------
        about = Card(tr("About"))
        about_form = QFormLayout()
        about_form.addRow(tr("Version"), QLabel(f"{APP_NAME} {__version__}"))
        about_form.addRow(tr("License"), QLabel("MIT"))
        link = QLabel(f'<a href="{PROJECT_URL}">{PROJECT_URL}</a>')
        link.setOpenExternalLinks(True)
        link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        about_form.addRow(tr("Project page"), link)
        about.body.addLayout(about_form)
        disclaimer = QLabel(
            tr(
                "KeyEnroll is an independent open-source project. It is not affiliated "
                "with or endorsed by Yubico, Microsoft, Okta or Ping Identity."
            )
        )
        disclaimer.setObjectName("hint")
        disclaimer.setWordWrap(True)
        about.body.addWidget(disclaimer)
        self.check_updates = QPushButton(tr("Check for updates"))
        self.check_updates.clicked.connect(self._check_updates)
        self.download_update = QPushButton(tr("Open the download page"))
        self.download_update.setObjectName("primary")
        self.download_update.setVisible(False)
        self.download_update.clicked.connect(self._open_release)
        self.update_note = QLabel()
        self.update_note.setObjectName("hint")
        self.update_note.setWordWrap(True)
        self.update_note.setVisible(False)
        self._release_url = ""
        self.open_logs = QPushButton(tr("Open the folder with settings and logs"))
        self.open_logs.clicked.connect(self._open_data_folder)
        about_buttons = QHBoxLayout()
        about_buttons.addWidget(self.check_updates)
        about_buttons.addWidget(self.download_update)
        about_buttons.addWidget(self.open_logs)
        about_buttons.addStretch(1)
        about.body.addLayout(about_buttons)
        about.body.addWidget(self.update_note)

        host = QWidget()
        column = QVBoxLayout(host)
        column.setContentsMargins(0, 0, 6, 0)
        column.setSpacing(14)
        for card in (appearance, language, message, about):
            column.addWidget(card)
        column.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName("plain")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(host)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self._show_custom()

    # -- appearance --------------------------------------------------------

    def _show_custom(self) -> None:
        custom = self.theme.currentData() == "custom"
        self.custom_label.setVisible(custom)
        self.custom_row.setVisible(custom)
        accent = self.ctx.config.custom_accent
        self.accent_swatch.setStyleSheet(
            f"background: {accent}; border-radius: 8px; border: 1px solid palette(mid);"
        )
        self.accent_swatch.setToolTip(accent)

    def _set_theme(self) -> None:
        config = self.ctx.config
        config.theme = self.theme.currentData()
        config.custom_base = self.custom_base.currentData()
        config.save()
        self._show_custom()
        app = QApplication.instance()
        if app is not None:  # takes effect immediately
            apply_theme(app, config.theme, config.custom_base, config.custom_accent)
        self.ctx.theme_changed.emit()

    def _pick_accent(self) -> None:
        color = QColorDialog.getColor(
            QColor(self.ctx.config.custom_accent), self, tr("Choose the accent colour")
        )
        if color.isValid():
            self.ctx.config.custom_accent = color.name()
            self._set_theme()

    # -- language ----------------------------------------------------------

    def _set_language(self) -> None:
        self.ctx.config.language = self.language.currentData()
        self.ctx.config.save()
        self.language_note.setText(tr("Restart the application to apply the change."))
        self.language_note.setVisible(True)

    # -- message -----------------------------------------------------------

    def _load_message(self) -> None:
        config = self.ctx.config
        self.subject.setText(config.message_subject or handover.default_subject())
        self.body.setPlainText(config.message_body or handover.default_body())

    def _save_message(self) -> None:
        config = self.ctx.config
        subject = self.subject.text().strip()
        body = self.body.toPlainText().strip() + "\n"
        # Text equal to the built-in default is not stored, so that it keeps
        # following the language of the application.
        config.message_subject = "" if subject == handover.default_subject() else subject
        config.message_body = "" if body == handover.default_body() else body
        config.save()
        self.message_note.setText(tr("Saved."))

    def _reset_message(self) -> None:
        config = self.ctx.config
        config.message_subject = config.message_body = ""
        config.save()
        self._load_message()
        self.message_note.setText(tr("The default text has been restored."))

    # -- about -------------------------------------------------------------

    def _check_updates(self) -> None:
        self.check_updates.setEnabled(False)
        self.download_update.setVisible(False)
        self._show_update_note(tr("Checking for updates…"))
        run_task(self, updates.check, self._update_checked, self._update_failed)

    def _show_update_note(self, text: str) -> None:
        self.update_note.setText(text)
        self.update_note.setVisible(True)

    def _update_checked(self, info: updates.UpdateInfo) -> None:
        self.check_updates.setEnabled(True)
        if info.newer:
            self._release_url = info.url
            self.download_update.setVisible(True)
            self._show_update_note(
                tr(
                    "Version {latest} is available (you have {current}).",
                    latest=info.latest,
                    current=info.current,
                )
            )
        else:
            self._show_update_note(
                tr("You have the latest version ({current}).", current=info.current)
            )

    def _update_failed(self, exc: Exception) -> None:
        self.check_updates.setEnabled(True)
        if isinstance(exc, updates.UpdateError):
            self._show_update_note(tr(str(exc)))
        else:
            self._show_update_note(tr("The update server returned an unexpected answer."))

    def _open_release(self) -> None:
        if self._release_url:
            QDesktopServices.openUrl(QUrl(self._release_url))

    def _open_data_folder(self) -> None:
        folder = config_dir()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
