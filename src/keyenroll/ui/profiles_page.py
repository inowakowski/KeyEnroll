"""Profiles page: presets of enrollment options."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import lock_codes
from ..config import Profile
from ..i18n import N_, tr
from .common import AppContext
from .lock_code import LockCodeEditor
from .profile_form import KeyModelsEditor, ProfileForm
from .theme import Card


class ProfilesPage(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self._editing: str | None = None  # name of the stored profile being edited

        self.list = QListWidget()
        self.list.currentTextChanged.connect(self._select)
        self.new = QPushButton(tr("New profile"))
        self.new.clicked.connect(self._new)
        left = Card(tr("Profiles"))
        left.body.addWidget(self.list, 1)
        left.body.addWidget(self.new)

        self.name = QLineEdit()
        self.name.setMaxLength(40)
        self.form = ProfileForm()
        self.save = QPushButton(tr("Save"))
        self.save.setObjectName("primary")
        self.save.clicked.connect(self._save)
        self.delete = QPushButton(tr("Delete"))
        self.delete.setObjectName("danger")
        self.delete.clicked.connect(self._delete)
        name_form = QFormLayout()
        name_form.addRow(tr("Profile name"), self.name)
        buttons = QHBoxLayout()
        buttons.addWidget(self.save)
        buttons.addWidget(self.delete)
        buttons.addStretch(1)
        box = Card(tr("Profile settings"))
        box.body.addLayout(name_form)
        box.body.addWidget(self.form)

        self.models = KeyModelsEditor(ctx.source)
        models_box = Card(
            tr("Allowed security keys"),
            tr(
                "Leave the list empty to accept every model. The key is checked "
                "before it is reset, so a key that is not allowed stays as it is."
            ),
        )
        models_box.body.addWidget(self.models)

        self.lock_code = LockCodeEditor(ctx)
        self.lock_code.changed.connect(self.form.set_lock_code_id)
        lock_box = Card(
            tr("Configuration lock code"),
            tr(
                "Optional. In Manage key, it locks which applications are enabled on "
                "a key, so that its user cannot change them. Keep a copy in a password "
                "manager: without the code, locked keys can no longer be changed."
            ),
        )
        lock_box.body.addWidget(self.lock_code)

        # Both cards can be taller than a small window: let them scroll.
        right_host = QWidget()
        right = QVBoxLayout(right_host)
        right.setContentsMargins(0, 0, 6, 0)
        right.setSpacing(14)
        right.addWidget(box)
        right.addWidget(models_box)
        right.addWidget(lock_box)
        right.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName("plain")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(right_host)
        right_column = QWidget()
        column = QVBoxLayout(right_column)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(12)
        column.addWidget(scroll, 1)
        column.addLayout(buttons)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(left, 1)
        layout.addWidget(right_column, 2)

        self._reload()

    def _reload(self, select: str | None = None) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        names = [p.name for p in self.ctx.config.profiles]
        self.list.addItems(names)
        self.list.blockSignals(False)
        target = select if select in names else names[0]
        self.list.setCurrentRow(names.index(target))
        self._select(target)

    def _select(self, name: str) -> None:
        profile = self.ctx.config.profile(name)
        if profile is None:
            return
        self._editing = name
        self.name.setText(profile.name)
        self.form.set_profile(profile)
        self.models.set_profile(profile)
        self.lock_code.set_profile(profile.name)
        self.delete.setEnabled(True)

    def _new(self) -> None:
        self._editing = None
        self.list.blockSignals(True)
        self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self.name.setText("")
        self.form.set_profile(Profile())
        self.models.set_profile(Profile())
        self.lock_code.set_profile(None)
        self.delete.setEnabled(False)
        self.name.setFocus()

    def _save(self) -> None:
        profile = self.models.apply(self.form.profile(self.name.text().strip()))
        problems = profile.problems()
        clash = self.ctx.config.profile(profile.name)
        if clash is not None and profile.name != self._editing:
            problems.append(N_("A profile with this name already exists."))
        if problems:
            QMessageBox.warning(self, tr("Error"), "\n".join(tr(p) for p in problems))
            return
        self.ctx.config.upsert_profile(profile, old_name=self._editing)
        self._reload(profile.name)
        self.ctx.profiles_changed.emit()

    def _delete(self) -> None:
        if self._editing is None:
            return
        profile = self.ctx.config.profile(self._editing)
        text = tr("Delete profile '{name}'?", name=self._editing)
        if profile is not None and profile.lock_code_id:
            text += "\n\n" + tr(
                "Its lock code is removed from this computer too. Keys locked with it "
                "can then only be changed if you kept a copy."
            )
        answer = QMessageBox.question(self, tr("Delete profile"), text)
        if answer != QMessageBox.StandardButton.Yes:
            return
        if profile is not None:
            lock_codes.forget(self.ctx.tokens, profile)
        self.ctx.config.delete_profile(self._editing)
        self._reload()
        self.ctx.profiles_changed.emit()
