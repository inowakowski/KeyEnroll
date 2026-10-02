"""Background work must never take the process down with it."""

from __future__ import annotations

import gc
import os
import threading
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import shiboken6
from PySide6.QtWidgets import QApplication, QWidget

from keyenroll.ui.common import Background, run_task
from keyenroll.ui.workers import _Worker


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def pump(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return True
        time.sleep(0.005)
    return False


def test_result_and_error_are_delivered_on_the_ui_thread(app):
    owner = QWidget()
    main = threading.current_thread()
    seen = []

    run_task(owner, lambda: 41 + 1, lambda r: seen.append(("ok", r, threading.current_thread())))

    def boom():
        raise ValueError("nope")

    run_task(owner, boom, None, lambda e: seen.append(("err", e, threading.current_thread())))
    assert pump(lambda: len(seen) == 2)
    by_kind = {kind: (value, thread) for kind, value, thread in seen}
    assert by_kind["ok"] == (42, main)
    assert isinstance(by_kind["err"][0], ValueError) and by_kind["err"][1] is main


def test_window_closed_while_work_is_running(app):
    """Used to abort the process: 'QThread: Destroyed while thread is still running'."""
    release = threading.Event()
    called = []
    for _ in range(20):
        owner = QWidget()
        run_task(owner, lambda: release.wait(5), called.append, called.append)
        shiboken6.delete(owner)  # the window is destroyed while the work runs
        del owner
    gc.collect()
    QApplication.processEvents()
    release.set()
    assert pump(lambda: not Background._alive)
    assert called == []  # nobody is left to receive the results


def test_worker_reports_failures_and_results(app):
    class Failing(_Worker):
        def job(self):
            raise RuntimeError("key unplugged")

    class Working(_Worker):
        def job(self):
            return "done"

    got = []
    bad, good = Failing(), Working()
    bad.failed.connect(lambda e: got.append(str(e)))
    good.succeeded.connect(got.append)
    bad.start()
    good.start()
    assert pump(lambda: len(got) == 2)
    assert sorted(got) == ["done", "key unplugged"]
    assert bad.wait(1000) and good.wait(1000)
    assert pump(lambda: bad not in Background._alive and good not in Background._alive)
