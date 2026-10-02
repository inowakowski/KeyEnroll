"""Instances page: identity provider configurations and app settings."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..i18n import LANGUAGES, tr
from ..providers import PROVIDERS
from .common import AppContext, fill_row, make_table, selected_data
from .dialogs import InstanceDialog
from .theme import PRESETS, Card, apply_theme


class InstancesPage(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx

        self.table = make_table(
            [tr("Name"), tr("Identity provider"), tr("Default profile"), tr("Session")]
        )
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.doubleClicked.connect(lambda _: self._edit())

        self.add = QPushButton(tr("Add instance"))
        self.add.setObjectName("primary")
        self.add.clicked.connect(self._add)
        self.edit = QPushButton(tr("Edit"))
        self.edit.clicked.connect(self._edit)
        self.activate = QPushButton(tr("Set as active"))
        self.activate.clicked.connect(self._activate)
        self.delete = QPushButton(tr("Delete"))
        self.delete.setObjectName("danger")
        self.delete.clicked.connect(self._delete)
        buttons = QHBoxLayout()
        for b in (self.add, self.edit, self.activate, self.delete):
            buttons.addWidget(b)
        buttons.addStretch(1)

        box = Card(
            tr("Identity provider instances"),
            tr(
                "Each instance is one tenant of an identity provider. Add as many as "
                "you need and switch between them with the selector at the top."
            ),
        )
        box.body.addWidget(self.table, 1)
        box.body.addLayout(buttons)

        self.language = QComboBox()
        self.language.addItem(tr("System default"), "auto")
        for code, label in LANGUAGES.items():
            self.language.addItem(label, code)
        self.language.setCurrentIndex(max(0, self.language.findData(ctx.config.language)))
        self.language.currentIndexChanged.connect(self._set_language)
        labels = {"light": tr("Light"), "dark": tr("Dark"), "yubico": "Yubico"}
        self.theme = QComboBox()
        self.theme.addItem(tr("System default"), "auto")
        for preset in PRESETS:
            self.theme.addItem(labels[preset], preset)
        self.theme.addItem(tr("Custom"), "custom")
        self.theme.setCurrentIndex(max(0, self.theme.findData(ctx.config.theme)))
        self.theme.currentIndexChanged.connect(self._set_theme)

        # custom scheme: light or dark base plus any accent colour
        self.custom_base = QComboBox()
        self.custom_base.addItem(tr("Light"), "light")
        self.custom_base.addItem(tr("Dark"), "dark")
        self.custom_base.setCurrentIndex(
            max(0, self.custom_base.findData(ctx.config.custom_base))
        )
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
        self.language_note = QLabel()
        self.language_note.setObjectName("hint")
        settings = Card(tr("Settings"))
        settings_form = QFormLayout()
        settings_form.addRow(tr("Language"), self.language)
        settings_form.addRow(tr("Appearance"), self.theme)
        settings_form.addRow(self.custom_label, self.custom_row)
        self._show_custom()
        settings.body.addLayout(settings_form)
        settings.body.addWidget(self.language_note)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(box, 1)
        layout.addWidget(settings)

        for signal in (ctx.instances_changed, ctx.active_changed, ctx.session_changed,
                       ctx.profiles_changed):
            signal.connect(self.reload)
        ctx.busy_changed.connect(lambda _: self._update_buttons())
        self.reload()

    def reload(self) -> None:
        selected = selected_data(self.table)
        self.table.setRowCount(0)
        config = self.ctx.config
        for inst in config.instances:
            cls = PROVIDERS.get(inst.kind)
            name = inst.name + ("  ✓" if inst.id == config.active_instance_id else "")
            try:
                session = self.ctx.provider_for(inst).has_session()
            except Exception:
                session = False
            fill_row(
                self.table,
                [
                    name,
                    cls.label if cls else inst.kind,
                    inst.default_profile or "",
                    tr("Signed in") if session else tr("Not signed in"),
                ],
                inst.id,
            )
            if inst.id == selected:
                self.table.selectRow(self.table.rowCount() - 1)
        self._update_buttons()

    def _selected(self):
        return self.ctx.config.instance(selected_data(self.table))

    def _update_buttons(self) -> None:
        inst = self._selected()
        idle = not self.ctx.busy
        self.add.setEnabled(idle)
        self.edit.setEnabled(idle and inst is not None)
        self.delete.setEnabled(idle and inst is not None)
        self.activate.setEnabled(
            idle and inst is not None and inst.id != self.ctx.config.active_instance_id
        )

    def _add(self) -> None:
        dialog = InstanceDialog(self.ctx.config, None, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        had_active = self.ctx.config.active_instance_id is not None
        self.ctx.config.upsert_instance(dialog.instance)
        self.ctx.instances_changed.emit()
        if not had_active:
            self.ctx.active_changed.emit()

    def _edit(self) -> None:
        inst = self._selected()
        if inst is None or self.ctx.busy:
            return
        dialog = InstanceDialog(self.ctx.config, inst, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.ctx.config.upsert_instance(dialog.instance)
        # Endpoints may have changed: rebuild the provider with new settings.
        self.ctx.forget_provider(inst.id)
        self.ctx.instances_changed.emit()
        if inst.id == self.ctx.config.active_instance_id:
            self.ctx.active_changed.emit()

    def _activate(self) -> None:
        inst = self._selected()
        if inst is None:
            return
        self.ctx.config.set_active(inst.id)
        self.ctx.active_changed.emit()

    def _delete(self) -> None:
        inst = self._selected()
        if inst is None:
            return
        answer = QMessageBox.question(
            self,
            tr("Delete instance"),
            tr("Delete instance '{name}' and its saved sign-in?", name=inst.name),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        was_active = inst.id == self.ctx.config.active_instance_id
        self.ctx.tokens.delete(inst.id)
        self.ctx.forget_provider(inst.id)
        self.ctx.config.delete_instance(inst.id)
        self.ctx.instances_changed.emit()
        if was_active:
            self.ctx.active_changed.emit()

    def _set_language(self) -> None:
        self.ctx.config.language = self.language.currentData()
        self.ctx.config.save()
        self.language_note.setText(tr("Restart the application to apply the change."))

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
