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
    select_row_where,
    selected_data,
    show_error,
)
from .key_owners import KeyOwners, KeyWatcher, OwnerBanner, owner_text
from .theme import Card


class CredentialsPage(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._load_id = 0

        self.picker = UserPicker(ctx, browse=True)
        self.picker.selection_changed.connect(self._load)
        # Who the plugged-in keys belong to, where the provider keeps serial numbers.
        self.owner_banner = OwnerBanner()
        self.owner_banner.open_user.connect(self.show_user)
        user_card = Card(tr("User"))
        user_card.body.addWidget(self.picker, 1)
        self._keys: list = []  # connected keys with a serial number
        self._owners = KeyOwners(ctx, self)
        self._owners.changed.connect(self._update_owner_banner)
        self._watcher = KeyWatcher(ctx, self)
        self._watcher.keys_changed.connect(self._on_keys)

        self.table = make_table(
            [tr("Name"), tr("Serial number"), tr("Created"), tr("Details"), tr("ID")], scrollable=True
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
        layout.addWidget(self.owner_banner)
        layout.addWidget(user_card, 1)
        layout.addWidget(creds_card, 1)

        ctx.active_changed.connect(self._on_instance)
        ctx.session_changed.connect(self._load_users)
        self._on_instance()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._load_users()
        self._watcher.start()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._watcher.stop()

    # -- connected keys and their owners -----------------------------------

    def _on_keys(self, infos) -> None:
        self._keys = [info for info in infos if info.serial]
        self._owners.lookup(info.serial for info in self._keys)
        self._update_owner_banner()
        self._select_connected()

    def _update_owner_banner(self) -> None:
        rows = []
        if self._owners.available:
            for info in self._keys:
                found = self._owners.ownership(info.serial)
                if found is not None:
                    rows.append((owner_text(found, info.serial), found.users))
                elif self._owners.pending(info.serial):
                    text = tr(
                        "Connected key S/N {serial}: looking for its owner…", serial=info.serial
                    )
                    rows.append((text, []))
        self.owner_banner.set_rows(rows)

    def show_user(self, user) -> None:
        """Selects the user; their credentials load, the one on a plugged-in
        key selected."""
        self.picker.show_user(user)

    def _select_connected(self) -> None:
        """Selects the credential on a plugged-in key, ready to be deleted."""
        serials = {str(info.serial) for info in self._keys}
        if serials and selected_data(self.table) is None:
            select_row_where(self.table, lambda c: c.serial in serials)

    def _load_users(self) -> None:
        """Lists all users when the page is shown, so that searching is optional."""
        provider = self.ctx.provider
        if not (self.isVisible() and provider and provider.supports_credential_list):
            return
        if not provider.has_session():
            # Signed out: the list of the previous session goes too.
            self.picker.clear()
            self.picker.hint.setText(tr("Sign in to the identity provider first."))
        elif not self.picker.loaded:
            self.picker.load_all(quiet=True)

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
        self._load_users()

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
                fill_row(self.table, [c.name, c.serial, c.created, c.detail, c.id], c)
            fit_columns(self.table)
            self._select_connected()
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
                name=(
                    f"{cred.name or cred.id} (S/N {cred.serial})"
                    if cred.serial
                    else cred.name or cred.id
                ),
                user=user.display_name or user.username,
            )
        )
        confirm = box.addButton(tr("Delete"), QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not confirm:
            return
        self.delete.setEnabled(False)

        def deleted(_) -> None:
            # Recorded so that the key is no longer suggested as this user's.
            self.ctx.journal(provider, "").deleted(user, cred)
            index = self.ctx.key_index()
            if index is not None:
                index.remove(cred.serial, user)
            self._owners.reset()
            self._watcher.rescan()
            self._load(user)

        run_task(
            self,
            lambda: provider.delete_credential(user, cred.id),
            deleted,
            lambda exc: (show_error(self, self.ctx, exc), self._update_buttons()),
        )
