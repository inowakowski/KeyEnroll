"""Profiles page: presets of enrollment options."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QWidget,
)

from ..config import Profile
from ..i18n import N_, tr
from .common import AppContext
from .profile_form import ProfileForm
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
        box.body.addStretch(1)
        box.body.addLayout(buttons)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(left, 1)
        layout.addWidget(box, 2)

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
        self.delete.setEnabled(True)

    def _new(self) -> None:
        self._editing = None
        self.list.blockSignals(True)
        self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self.name.setText("")
        self.form.set_profile(Profile())
        self.delete.setEnabled(False)
        self.name.setFocus()

    def _save(self) -> None:
        profile = self.form.profile(self.name.text().strip())
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
        answer = QMessageBox.question(
            self, tr("Delete profile"), tr("Delete profile '{name}'?", name=self._editing)
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.ctx.config.delete_profile(self._editing)
        self._reload()
        self.ctx.profiles_changed.emit()
