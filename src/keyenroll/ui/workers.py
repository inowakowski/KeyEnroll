"""Background work running enrollments, bridged to the UI thread."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QWidget

from ..bulk import BulkRunner, resolve_rows
from ..fido.enroll import Enroller
from .common import Background
from .dialogs import CurrentPinDialog, NewPinDialog


@dataclass
class PinPrompt:
    kind: str  # "current" or "new"
    retries: int | None = None
    wrong: bool = False
    min_length: int = 4
    rejected: bool = False
    answer: str | None = None
    done: threading.Event = field(default_factory=threading.Event)


def answer_prompt(parent: QWidget, prompt: PinPrompt) -> None:
    """Shows the PIN dialog for a prompt raised by a worker (UI thread)."""
    if prompt.kind == "current":
        dialog = CurrentPinDialog(prompt.retries, prompt.wrong, parent)
    else:
        dialog = NewPinDialog(prompt.min_length, prompt.rejected, parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        prompt.answer = dialog.value()
    prompt.done.set()


class _Worker(Background):
    """Signals are always emitted on the UI thread."""

    status = Signal(str, dict)
    prompt = Signal(object)
    row_changed = Signal(int)
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self):
        super().__init__()
        self.cancel = threading.Event()

    def job(self):
        raise NotImplementedError

    def work(self) -> None:
        try:
            result = self.job()
        except Exception as e:
            # Bound as a default: the name ``e`` is gone once the block ends.
            self.post(lambda exc=e: self.failed.emit(exc))
        else:
            self.post(lambda: self.succeeded.emit(result))


class _Bridge:
    """EnrollUI/BulkUI implementation called on the worker thread."""

    def __init__(self, worker: _Worker):
        self.w = worker

    def status(self, template, **params):
        self.w.post(lambda: self.w.status.emit(template, params))

    def row_changed(self, index):
        self.w.post(lambda: self.w.row_changed.emit(index))

    def _ask(self, prompt: PinPrompt) -> str | None:
        self.w.post(lambda: self.w.prompt.emit(prompt))
        while not prompt.done.wait(0.2):
            if self.w.cancel.is_set():
                return None
        return prompt.answer

    def ask_current_pin(self, retries, wrong):
        return self._ask(PinPrompt("current", retries=retries, wrong=wrong))

    def ask_new_pin(self, min_length, rejected):
        return self._ask(PinPrompt("new", min_length=min_length, rejected=rejected))


class EnrollWorker(_Worker):
    def __init__(self, source, provider, profile, user, name, key, append_serial):
        super().__init__()
        self._enroller = Enroller(
            provider,
            profile,
            user,
            name,
            key,
            _Bridge(self),
            source=source,
            cancel=self.cancel,
            append_serial=append_serial,
        )

    def job(self):
        return self._enroller.run()


class BulkWorker(_Worker):
    def __init__(self, source, provider, profile, rows, name, append_serial):
        super().__init__()
        self._runner = BulkRunner(
            provider,
            profile,
            rows,
            name,
            append_serial,
            _Bridge(self),
            source=source,
            cancel=self.cancel,
        )

    def job(self):
        return self._runner.run()


class ResolveWorker(_Worker):
    """Looks up imported user identifiers in the directory."""

    def __init__(self, provider, rows):
        super().__init__()
        self._provider = provider
        self._rows = rows

    def job(self):
        resolve_rows(self._provider, self._rows, _Bridge(self).row_changed, self.cancel)
