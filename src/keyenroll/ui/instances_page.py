"""Instances page: identity provider configurations."""

from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import (
    MAX_IMPORT_BYTES,
    ImportProblem,
    apply_import,
    export_config,
    parse_import,
    write_private,
)
from ..i18n import tr
from ..providers import PROVIDERS
from .common import AppContext, fill_row, make_table, selected_data
from .dialogs import ExportConfigDialog, ImportConfigDialog, InstanceDialog
from .theme import Card


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
        self.export = QPushButton(tr("Export…"))
        self.export.setToolTip(tr("Saves instances and profiles for another computer."))
        self.export.clicked.connect(self._export)
        self.import_ = QPushButton(tr("Import…"))
        self.import_.setToolTip(tr("Adds instances and profiles exported on another computer."))
        self.import_.clicked.connect(self._import)
        buttons = QHBoxLayout()
        for b in (self.add, self.edit, self.activate, self.delete):
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(self.export)
        buttons.addWidget(self.import_)

        box = Card(
            tr("Identity provider instances"),
            tr(
                "Each instance is one tenant of an identity provider. Add as many as "
                "you need and switch between them with the selector at the top."
            ),
        )
        box.body.addWidget(self.table, 1)
        box.body.addLayout(buttons)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(box, 1)

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
        self.import_.setEnabled(idle)
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

    def _export(self) -> None:
        dialog = ExportConfigDialog(self.ctx.config, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export configuration"),
            "keyenroll-config.json",
            tr("KeyEnroll configuration (*.json)"),
        )
        if not path:
            return
        data = export_config(
            self.ctx.config,
            instances=dialog.instances.isChecked(),
            profiles=dialog.profiles.isChecked(),
            message=dialog.message.isChecked(),
        )
        try:
            write_private(path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
        except OSError as e:
            QMessageBox.warning(self, tr("Error"), str(e))
            return
        QMessageBox.information(
            self, tr("Export configuration"), tr("Saved to {path}.", path=path)
        )

    def _import(self) -> None:
        if self.ctx.busy:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Import configuration"),
            "",
            tr("KeyEnroll configuration (*.json);;All files (*)"),
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                raw = f.read(MAX_IMPORT_BYTES + 1)  # enough to tell it is too large
            imported = parse_import(raw, set(PROVIDERS))
        except OSError as e:
            QMessageBox.warning(self, tr("Error"), str(e))
            return
        except ImportProblem as e:
            QMessageBox.warning(self, tr("Import configuration"), tr(str(e)))
            return
        dialog = ImportConfigDialog(imported, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        config = self.ctx.config
        had_active = config.active_instance_id is not None
        outcome = apply_import(
            config,
            imported,
            clash=dialog.clash.currentData(),
            instances=dialog.instances.isChecked(),
            profiles=dialog.profiles.isChecked(),
            message=dialog.message.isChecked(),
        )
        for instance_id, kind_changed in outcome.replaced_instances:
            # New settings: rebuild the provider; another provider type
            # cannot use the old sign-in.
            if kind_changed:
                self.ctx.tokens.delete(instance_id)
            self.ctx.forget_provider(instance_id)
        self.ctx.profiles_changed.emit()
        self.ctx.instances_changed.emit()
        replaced_active = any(
            i == config.active_instance_id for i, _ in outcome.replaced_instances
        )
        if not had_active or replaced_active:
            self.ctx.active_changed.emit()
        QMessageBox.information(
            self,
            tr("Import configuration"),
            tr(
                "Added: {added} · replaced: {replaced} · kept as they were: {skipped}.",
                added=outcome.added,
                replaced=outcome.replaced,
                skipped=outcome.skipped,
            ),
        )

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
