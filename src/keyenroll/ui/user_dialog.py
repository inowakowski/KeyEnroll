"""A user's profile with the security keys registered to them."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..i18n import tr
from ..providers import DirectoryUser
from .common import AppContext, error_text, fill_row, fit_columns, make_table, run_task


class UserProfileDialog(QDialog):
    """Who the user is and which keys they have, without leaving the page.
    Deleting a key is done on the Credentials page, one button away."""

    def __init__(self, ctx: AppContext, user: DirectoryUser, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self.user = user
        self.setWindowTitle(user.display_name or user.username)
        self.setMinimumWidth(640)

        title = QLabel(user.display_name or user.username)
        title.setObjectName("title")
        details = QFormLayout()
        for label, value in (
            (tr("Username"), user.username),
            (tr("E-mail"), user.email),
            (tr("ID"), user.id),
        ):
            field = QLabel(value or "—")
            field.setObjectName("value")
            field.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            details.addRow(label, field)

        self.table = make_table(
            [tr("Name"), tr("Serial number"), tr("Created"), tr("Details")], scrollable=True
        )
        self.table.setMinimumHeight(180)
        self.status = QLabel()
        self.status.setObjectName("hint")
        self.status.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(tr("Close"))
        buttons.rejected.connect(self.reject)
        self.open_credentials = buttons.addButton(
            tr("Open on the Credentials page"), QDialogButtonBox.ButtonRole.ActionRole
        )
        self.open_credentials.setToolTip(tr("There you can delete a key of the user."))
        self.open_credentials.clicked.connect(self._open_credentials)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(details)
        heading = QLabel(tr("Security keys"))
        heading.setObjectName("cardTitle")
        layout.addSpacing(8)
        layout.addWidget(heading)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status)
        layout.addWidget(buttons)
        self._load()

    def _load(self) -> None:
        provider = self.ctx.provider
        if provider is None or not provider.supports_credential_list:
            self.table.setVisible(False)
            self.open_credentials.setVisible(False)
            self.status.setText(
                tr(
                    "{provider} does not offer an API for listing or deleting "
                    "credentials. Manage them in the provider's admin console.",
                    provider=provider.label if provider else "",
                )
            )
            return
        self.status.setText(tr("Loading…"))
        user = self.user

        def done(credentials) -> None:
            for c in credentials:
                fill_row(self.table, [c.name, c.serial, c.created, c.detail], c)
            fit_columns(self.table)
            self.status.setText(
                tr("{count} FIDO method(s).", count=len(credentials))
                if credentials
                else tr("{name} has no FIDO method yet.", name=user.display_name or user.username)
            )

        def failed(exc) -> None:
            self.status.setText(error_text(exc))

        run_task(self, lambda: provider.list_credentials(user), done, failed)

    def _open_credentials(self) -> None:
        self.accept()
        self.ctx.open_user_credentials.emit(self.user)
