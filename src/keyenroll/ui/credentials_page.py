"""Credentials page: list and delete a user's FIDO credentials."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..i18n import tr
from .common import (
    AppContext,
    UserPicker,
    fill_row,
    fit_columns,
    make_table,
    run_task,
    selected_data,
    show_error,
)
from .theme import Card


class CredentialsPage(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._load_id = 0

        self.picker = UserPicker(ctx)
        self.picker.selection_changed.connect(self._load)
        user_card = Card(tr("User"))
        user_card.body.addWidget(self.picker, 1)

        self.table = make_table(
            [tr("Name"), tr("Created"), tr("Details"), tr("ID")], scrollable=True
        )
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.notice = QLabel()
        self.notice.setObjectName("hint")
        self.notice.setWordWrap(True)
        self.refresh = QPushButton(tr("Refresh"))
        self.refresh.clicked.connect(lambda: self._load(self.picker.selected()))
        self.delete = QPushButton(tr("Delete selected"))
        self.delete.setObjectName("danger")
        self.delete.clicked.connect(self._delete)
        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh)
        buttons.addWidget(self.delete)
        buttons.addStretch(1)

        creds_card = Card(tr("FIDO credentials of the selected user"))
        creds_card.body.addWidget(self.notice)
        creds_card.body.addWidget(self.table, 1)
        creds_card.body.addLayout(buttons)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(user_card, 1)
        layout.addWidget(creds_card, 1)

        ctx.active_changed.connect(self._on_instance)
        self._on_instance()

    def _on_instance(self) -> None:
        self._load_id += 1
        self.table.setRowCount(0)
        provider = self.ctx.provider
        supported = provider is None or provider.supports_credential_list
        self.notice.setText(
            ""
            if supported
            else tr(
                "{provider} does not offer an API for listing or deleting "
                "credentials. Manage them in the provider's admin console.",
                provider=provider.label,
            )
        )
        self.notice.setVisible(not supported)
        self.table.setEnabled(supported)
        self._update_buttons()

    def _update_buttons(self) -> None:
        provider = self.ctx.provider
        user = self.picker.selected()
        can_list = bool(provider and provider.supports_credential_list and user)
        self.refresh.setEnabled(can_list)
        self.delete.setEnabled(
            bool(
                can_list
                and provider.supports_credential_delete
                and selected_data(self.table) is not None
            )
        )

    def _load(self, user) -> None:
        self._load_id += 1
        load_id = self._load_id
        self.table.setRowCount(0)
        self._update_buttons()
        provider = self.ctx.provider
        if user is None or provider is None or not provider.supports_credential_list:
            return

        def done(creds):
            if load_id != self._load_id:
                return
            for c in creds:
                fill_row(self.table, [c.name, c.created, c.detail, c.id], c)
            fit_columns(self.table)
            self._update_buttons()

        def failed(exc):
            if load_id == self._load_id:
                show_error(self, self.ctx, exc)

        run_task(self, lambda: provider.list_credentials(user), done, failed)

    def _delete(self) -> None:
        provider = self.ctx.provider
        user = self.picker.selected()
        cred = selected_data(self.table)
        if not (provider and user and cred):
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("Delete credential"))
        box.setText(
            tr(
                "Delete credential '{name}' of {user}? The user will no longer be "
                "able to sign in with this key.",
                name=cred.name or cred.id,
                user=user.display_name or user.username,
            )
        )
        confirm = box.addButton(tr("Delete"), QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not confirm:
            return
        self.delete.setEnabled(False)
        run_task(
            self,
            lambda: provider.delete_credential(user, cred.id),
            lambda _: self._load(user),
            lambda exc: (show_error(self, self.ctx, exc), self._update_buttons()),
        )
