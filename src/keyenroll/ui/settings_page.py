"""Settings page: appearance, language, hand-over message, about."""

from __future__ import annotations

import logging
import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, DOCS_URL, PROJECT_URL, __version__, handover, journal, updates
from ..config import config_dir
from ..i18n import LANGUAGES, tr
from .common import AppContext, Background, run_task
from .theme import PRESETS, Card, apply_theme

logger = logging.getLogger(__name__)


class DownloadTask(Background):
    """Downloads and verifies an update off the UI thread."""

    progress = Signal(int, int)
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, info: updates.UpdateInfo, asset: updates.Asset, folder: Path):
        super().__init__()
        self.cancel = threading.Event()
        self._info, self._asset, self._folder = info, asset, folder
        self._shown = -1

    def _report(self, done: int, total: int) -> None:
        percent = done * 100 // total if total else 0
        if percent != self._shown:  # a signal per percent, not per chunk
            self._shown = percent
            self.post(lambda: self.progress.emit(done, total))

    def work(self) -> None:
        try:
            path = updates.download(
                self._info, self._asset, self._folder, progress=self._report, cancel=self.cancel
            )
        except Exception as e:
            self.post(lambda exc=e: self.failed.emit(exc))
        else:
            self.post(lambda: self.succeeded.emit(path))


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

        # -- deployment log ------------------------------------------------
        self.journal_enabled = QCheckBox(tr("Keep a deployment log"))
        self.journal_enabled.setChecked(config.journal_enabled)
        self.journal_enabled.toggled.connect(self._set_journal)
        self.journal_months = QSpinBox()
        self.journal_months.setRange(1, 120)
        self.journal_months.setValue(config.journal_months)
        self.journal_months.valueChanged.connect(self._set_journal)
        self.journal_months.setEnabled(config.journal_enabled)
        self.open_journal = QPushButton(tr("Open the deployment log folder"))
        self.open_journal.clicked.connect(self._open_journal)
        log = Card(
            tr("Deployment log"),
            tr(
                "One line per enrollment: who enrolled which key for whom, and when. "
                "PINs are never written to it. The log names people: keep it only as "
                "long as your organisation needs it."
            ),
        )
        log_form = QFormLayout()
        log_form.addRow(self.journal_enabled)
        log_form.addRow(tr("Keep entries for (months)"), self.journal_months)
        log.body.addLayout(log_form)
        log_buttons = QHBoxLayout()
        log_buttons.addWidget(self.open_journal)
        log_buttons.addStretch(1)
        log.body.addLayout(log_buttons)

        # -- about ---------------------------------------------------------
        about = Card(tr("About"))
        about_form = QFormLayout()
        about_form.addRow(tr("Version"), QLabel(f"{APP_NAME} {__version__}"))
        about_form.addRow(tr("License"), QLabel("MIT"))
        link = QLabel(f'<a href="{PROJECT_URL}">{PROJECT_URL}</a>')
        link.setOpenExternalLinks(True)
        link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        about_form.addRow(tr("Project page"), link)
        docs_link = QLabel(f'<a href="{DOCS_URL}">{DOCS_URL}</a>')
        docs_link.setOpenExternalLinks(True)
        docs_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        about_form.addRow(tr("Documentation"), docs_link)
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
        self.open_logs = QPushButton(tr("Open the folder with settings and logs"))
        self.open_logs.clicked.connect(self._open_data_folder)
        about_buttons = QHBoxLayout()
        about_buttons.addWidget(self.open_logs)
        about_buttons.addStretch(1)
        about.body.addLayout(about_buttons)

        # -- updates -------------------------------------------------------
        self.check_updates = QPushButton(tr("Check for updates"))
        self.check_updates.clicked.connect(self._check_updates)
        self.install_update = QPushButton()
        self.install_update.setObjectName("primary")
        self.install_update.setVisible(False)
        self.install_update.clicked.connect(self._install_update)
        self.download_update = QPushButton(tr("Open the download page"))
        self.download_update.setVisible(False)
        self.download_update.clicked.connect(self._open_release)
        self.update_note = QLabel()
        self.update_note.setObjectName("hint")
        self.update_note.setWordWrap(True)
        self.update_note.setVisible(False)
        self._release_url = ""
        self._update: updates.UpdateInfo | None = None
        self._asset: updates.Asset | None = None
        self._download: DownloadTask | None = None
        self.update_previews = QCheckBox(tr("Include preview versions"))
        self.update_previews.setToolTip(
            tr("Previews have the newest features before they were tested on real keys and tenants.")
        )
        self.update_previews.setChecked(config.update_previews)
        self.update_previews.toggled.connect(self._set_update_options)
        self.update_on_start = QCheckBox(tr("Check for updates when the application starts"))
        self.update_on_start.setChecked(config.update_on_start)
        self.update_on_start.toggled.connect(self._set_update_options)
        self.update_unexported = QComboBox()
        self.update_unexported.addItem(tr("Warn me; I can still update and lose them"), "warn")
        self.update_unexported.addItem(tr("Do not allow the update until they are exported"), "block")
        self.update_unexported.setCurrentIndex(max(0, self.update_unexported.findData(config.update_unexported)))
        self.update_unexported.currentIndexChanged.connect(self._set_update_options)
        update_card = Card(
            tr("Updates"),
            tr(
                "An update is installed only after you confirm it, and only if the "
                "downloaded file matches the published one."
            ),
        )
        update_buttons = QHBoxLayout()
        update_buttons.addWidget(self.check_updates)
        update_buttons.addWidget(self.install_update)
        update_buttons.addWidget(self.download_update)
        update_buttons.addStretch(1)
        update_card.body.addLayout(update_buttons)
        update_card.body.addWidget(self.update_note)
        update_form = QFormLayout()
        update_form.addRow(self.update_previews)
        update_form.addRow(self.update_on_start)
        update_form.addRow(tr("Temporary PINs not exported yet"), self.update_unexported)
        update_card.body.addLayout(update_form)

        host = QWidget()
        column = QVBoxLayout(host)
        column.setContentsMargins(0, 0, 6, 0)
        column.setSpacing(14)
        for card in (appearance, language, message, log, update_card, about):
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

    # -- deployment log ----------------------------------------------------

    def _set_journal(self) -> None:
        config = self.ctx.config
        config.journal_enabled = self.journal_enabled.isChecked()
        config.journal_months = self.journal_months.value()
        config.save()
        self.journal_months.setEnabled(config.journal_enabled)

    def _open_journal(self) -> None:
        folder = journal.journal_dir(self.ctx.config.path)
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    # -- updates -----------------------------------------------------------

    def _set_update_options(self) -> None:
        config = self.ctx.config
        config.update_previews = self.update_previews.isChecked()
        config.update_on_start = self.update_on_start.isChecked()
        config.update_unexported = self.update_unexported.currentData()
        config.save()

    def _check_updates(self) -> None:
        self.check_updates.setEnabled(False)
        self.download_update.setVisible(False)
        self.install_update.setVisible(False)
        self._show_update_note(tr("Checking for updates…"))
        previews = self.ctx.config.update_previews
        run_task(
            self,
            lambda: updates.check(previews=previews),
            self._update_checked,
            self._update_failed,
        )

    def _show_update_note(self, text: str) -> None:
        self.update_note.setText(text)
        self.update_note.setVisible(True)

    def show_update(self, info: updates.UpdateInfo) -> None:
        """Shows a release found by the check at start-up."""
        self._update_checked(info)

    def _update_checked(self, info: updates.UpdateInfo) -> None:
        self.check_updates.setEnabled(True)
        if info.newer:
            self._release_url = info.url
            self._update = info
            kind = updates.installer_kind()
            self._asset = updates.pick_asset(info, kind, updates.machine_arch())
            self.download_update.setVisible(True)
            if self._asset is not None:
                text = (
                    tr("Install version {version}", version=info.latest)
                    if kind == "windows"
                    else tr("Download version {version}", version=info.latest)
                )
                self.install_update.setText(text)
                self.install_update.setVisible(True)
            note = tr(
                "Version {latest} is available (you have {current}).",
                latest=info.latest,
                current=info.current,
            )
            if info.prerelease:
                note += " " + tr("It is a preview version.")
            self._show_update_note(note)
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

    def _may_update(self) -> bool:
        """Nothing in progress is lost without the operator knowing."""
        if self.ctx.busy:
            QMessageBox.information(
                self,
                tr("Updates"),
                tr("An enrollment is in progress. Finish or cancel it before updating."),
            )
            return False
        if not self.ctx.unexported_pins:
            return True
        if self.ctx.config.update_unexported == "block":
            QMessageBox.warning(
                self,
                tr("Updates"),
                tr(
                    "The bulk enrollment list has temporary PINs that were not exported. "
                    "Export them, or clear the list, before updating."
                ),
            )
            return False
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("Unsaved PINs"))
        box.setText(
            tr(
                "The bulk enrollment list has temporary PINs that were not exported. "
                "If you update now, they are lost for good and the keys concerned "
                "have to be enrolled again."
            )
        )
        lose = box.addButton(tr("Update and lose the PINs"), QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        return box.clickedButton() is lose

    def _install_update(self) -> None:
        info, asset = self._update, self._asset
        if info is None or asset is None or self._download is not None:
            return
        if not self._may_update():
            return
        kind = updates.installer_kind()
        if kind == "windows":
            folder = Path(tempfile.gettempdir()) / "KeyEnroll-update"
        else:
            downloads = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DownloadLocation
            )
            folder = Path(downloads or tempfile.gettempdir())
        progress = QProgressDialog(
            tr("Downloading version {version}…", version=info.latest), tr("Cancel"), 0, 100, self
        )
        progress.setWindowTitle(tr("Updates"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        task = DownloadTask(info, asset, folder)
        progress.canceled.connect(task.cancel.set)
        task.progress.connect(
            lambda done, total: progress.setValue(done * 100 // total if total else 0)
        )

        def finished() -> None:
            self._download = None
            progress.canceled.disconnect(task.cancel.set)
            progress.close()
            self.install_update.setEnabled(True)

        def failed(exc) -> None:
            finished()
            if isinstance(exc, updates.UpdateCancelled):
                return
            text = tr(str(exc)) if isinstance(exc, updates.UpdateError) else str(exc)
            QMessageBox.warning(self, tr("Updates"), text)

        def done(path: Path) -> None:
            finished()
            self._downloaded(path, kind, info)

        task.succeeded.connect(done)
        task.failed.connect(failed)
        self._download = task
        self.install_update.setEnabled(False)
        task.start()
        progress.show()

    def _downloaded(self, path: Path, kind: str | None, info: updates.UpdateInfo) -> None:
        if kind == "windows":
            try:
                updates.launch_windows_installer(path)
            except OSError as e:
                QMessageBox.warning(self, tr("Updates"), str(e))
                return
            logger.info("Installing version %s; closing", info.latest)
            self.ctx.closing_for_update = True
            self.window().close()
            return
        if kind == "macos":
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            text = tr(
                "The disk image is open. Quit KeyEnroll, drag the new KeyEnroll onto the "
                "Applications folder to replace the old one, and start it again."
            )
        elif kind == "deb":
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
            text = tr(
                "Saved to {path}. Quit KeyEnroll and install it with your package manager, "
                "for example: sudo apt install {path}",
                path=str(path),
            )
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
            text = tr(
                "Saved to {path}. Quit KeyEnroll and unpack the archive over the current "
                "installation.",
                path=str(path),
            )
        QMessageBox.information(self, tr("Updates"), text)

    # -- about -------------------------------------------------------------

    def _open_release(self) -> None:
        if self._release_url:
            QDesktopServices.openUrl(QUrl(self._release_url))

    def _open_data_folder(self) -> None:
        folder = config_dir()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
