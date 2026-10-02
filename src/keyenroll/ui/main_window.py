"""Main window: sidebar navigation, instance switcher and session controls."""

from __future__ import annotations

import threading
import webbrowser

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, __version__
from ..fido.devices import is_admin, relaunch_as_admin
from ..i18n import tr
from ..oauth import LoginCancelled
from ..providers import PROVIDERS
from .bulk_page import BulkPage
from .common import AppContext, error_text, run_task
from .credentials_page import CredentialsPage
from .enroll_page import EnrollPage
from .instances_page import InstancesPage
from .profiles_page import ProfilesPage
from .theme import app_icon, nav_icon

PAGE_ENROLL, PAGE_BULK, PAGE_CREDENTIALS, PAGE_PROFILES, PAGE_INSTANCES = range(5)


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 800)
        self.setMinimumSize(1080, 640)

        # sidebar
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(QSize(30, 30)))
        brand = QLabel(APP_NAME)
        brand.setObjectName("brand")
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(18, 18, 18, 14)
        brand_row.setSpacing(10)
        brand_row.addWidget(logo)
        brand_row.addWidget(brand, 1)

        self.enroll_page = EnrollPage(ctx)
        self.bulk_page = BulkPage(ctx)
        self.pages = QStackedWidget()
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setIconSize(QSize(20, 20))
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._titles = []
        self._icons = []
        for title, icon, page in (
            (tr("Enroll"), "key", self.enroll_page),
            (tr("Bulk enrollment"), "users", self.bulk_page),
            (tr("Credentials"), "shield", CredentialsPage(ctx)),
            (tr("Profiles"), "sliders", ProfilesPage(ctx)),
            (tr("Instances"), "layers", InstancesPage(ctx)),
        ):
            self.nav.addItem(QListWidgetItem(nav_icon(icon), title))
            self.pages.addWidget(page)
            self._titles.append(title)
            self._icons.append(icon)
        self.nav.currentRowChanged.connect(self._show_page)

        version = QLabel(tr("Version {version}", version=__version__))
        version.setObjectName("version")
        version.setContentsMargins(20, 0, 0, 14)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(0)
        side.addLayout(brand_row)
        side.addWidget(self.nav, 1)
        side.addWidget(version)

        # top bar: page title, instance switcher, session
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        self.instance_combo = QComboBox()
        self.instance_combo.setMinimumWidth(300)
        self.instance_combo.currentIndexChanged.connect(self._switch_instance)
        self.session_label = QLabel()
        self.session_label.setObjectName("chip")
        self.session_button = QPushButton()
        self.session_button.clicked.connect(self._toggle_session)
        topbar = QHBoxLayout()
        topbar.setSpacing(10)
        topbar.addWidget(self.page_title)
        topbar.addStretch(1)
        topbar.addWidget(self.instance_combo)
        topbar.addWidget(self.session_label)
        topbar.addWidget(self.session_button)

        content = QVBoxLayout()
        content.setContentsMargins(24, 18, 24, 22)
        content.setSpacing(14)
        content.addLayout(topbar)
        banner = self._admin_banner()
        if banner:
            content.addWidget(banner)
        content.addWidget(self.pages, 1)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar)
        layout.addLayout(content, 1)
        self.setCentralWidget(central)

        ctx.instances_changed.connect(self._reload_instances)
        ctx.active_changed.connect(self._reload_instances)
        ctx.session_changed.connect(self._update_session)
        ctx.busy_changed.connect(self._on_busy)
        ctx.theme_changed.connect(self._retint_icons)
        self._reload_instances()
        # First run: nothing to enroll against yet, start on the instances page.
        self.nav.setCurrentRow(PAGE_ENROLL if ctx.config.instances else PAGE_INSTANCES)

    def _retint_icons(self) -> None:
        for row, name in enumerate(self._icons):
            self.nav.item(row).setIcon(nav_icon(name))

    def _show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        self.page_title.setText(self._titles[index] if index >= 0 else "")

    # -- admin banner ------------------------------------------------------

    def _admin_banner(self) -> QFrame | None:
        if is_admin():
            return None
        banner = QFrame()
        banner.setObjectName("banner")
        text = QLabel(
            tr(
                "Windows only lets administrators access FIDO security keys directly. "
                "Restart the application as administrator to detect and enroll keys."
            )
        )
        text.setWordWrap(True)
        button = QPushButton(tr("Restart as administrator"))
        button.clicked.connect(self._elevate)
        row = QHBoxLayout(banner)
        row.setContentsMargins(14, 10, 10, 10)
        row.addWidget(text, 1)
        row.addWidget(button)
        return banner

    def _elevate(self) -> None:
        if relaunch_as_admin():
            QApplication.quit()

    # -- instances ---------------------------------------------------------

    def _reload_instances(self) -> None:
        config = self.ctx.config
        self.instance_combo.blockSignals(True)
        self.instance_combo.clear()
        for inst in config.instances:
            cls = PROVIDERS.get(inst.kind)
            self.instance_combo.addItem(
                f"{inst.name}  —  {cls.label if cls else inst.kind}", inst.id
            )
        if not config.instances:
            self.instance_combo.addItem(tr("(no instances configured)"), None)
        index = self.instance_combo.findData(config.active_instance_id)
        self.instance_combo.setCurrentIndex(max(0, index))
        self.instance_combo.blockSignals(False)
        self._update_session()

    def _switch_instance(self) -> None:
        instance_id = self.instance_combo.currentData()
        if instance_id and instance_id != self.ctx.config.active_instance_id:
            self.ctx.config.set_active(instance_id)
            self.ctx.active_changed.emit()

    def _on_busy(self, busy: bool) -> None:
        self.instance_combo.setEnabled(not busy)
        self.session_button.setEnabled(not busy and self.ctx.provider is not None)

    # -- session -----------------------------------------------------------

    def _update_session(self) -> None:
        provider = self.ctx.provider
        signed_in = False
        if provider is not None:
            try:
                signed_in = provider.has_session()
            except Exception:
                signed_in = False
        self.session_label.setVisible(provider is not None)
        self.session_label.setText(tr("Signed in") if signed_in else tr("Not signed in"))
        self.session_label.setProperty("state", "on" if signed_in else "off")
        self.session_label.style().unpolish(self.session_label)
        self.session_label.style().polish(self.session_label)
        self.session_button.setText(tr("Sign out") if signed_in else tr("Sign in"))
        self.session_button.setObjectName("" if signed_in else "primary")
        self.session_button.style().unpolish(self.session_button)
        self.session_button.style().polish(self.session_button)
        self.session_button.setEnabled(provider is not None and not self.ctx.busy)
        self._signed_in = signed_in

    def _toggle_session(self) -> None:
        provider = self.ctx.provider
        if provider is None:
            return
        if self._signed_in:
            self.session_button.setEnabled(False)
            run_task(self, provider.logout, lambda _: self.ctx.session_changed.emit(),
                     self._session_error)
            return

        cancel = threading.Event()
        progress = QProgressDialog(
            tr("Complete the sign-in in your browser…"), tr("Cancel"), 0, 0, self
        )
        progress.setWindowTitle(tr("Sign in"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.canceled.connect(cancel.set)

        def finished(exc=None) -> None:
            progress.canceled.disconnect(cancel.set)
            progress.close()
            self.ctx.session_changed.emit()
            if exc is not None and not isinstance(exc, LoginCancelled):
                QMessageBox.warning(self, tr("Sign-in failed"), error_text(exc))

        run_task(
            self,
            lambda: provider.login(webbrowser.open, cancel),
            lambda _: finished(),
            finished,
        )
        progress.show()

    def _session_error(self, exc) -> None:
        self.ctx.session_changed.emit()
        QMessageBox.warning(self, tr("Error"), error_text(exc))

    # -- shutdown ----------------------------------------------------------

    def closeEvent(self, event) -> None:
        if self.enroll_page.is_running() or self.bulk_page.is_running():
            answer = QMessageBox.question(
                self,
                tr("Enrollment in progress"),
                tr("An enrollment is in progress. Cancel it and quit?"),
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        if self.bulk_page.has_unexported_pins():
            answer = QMessageBox.question(
                self,
                tr("Unsaved PINs"),
                tr("The temporary PINs have not been exported and will be lost. Continue?"),
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self.enroll_page.shutdown()
        self.bulk_page.shutdown()
        event.accept()
