"""Start-up plumbing: logging and reporting of unexpected errors."""

from __future__ import annotations

import logging
import os
import sys
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from keyenroll import app as app_module


@pytest.fixture(scope="module")
def qt():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def clean_logging():
    root = logging.getLogger()
    before, level = list(root.handlers), root.level
    yield root
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            handler.close()
    root.setLevel(level)


@pytest.fixture
def hooks():
    saved = sys.excepthook, threading.excepthook
    yield
    sys.excepthook, threading.excepthook = saved


def test_log_goes_to_a_file_next_to_the_settings_by_default(tmp_path, monkeypatch, clean_logging):
    monkeypatch.setenv("KEYENROLL_HOME", str(tmp_path))
    app_module.configure_logging("INFO", None)
    logging.getLogger("keyenroll.test").info("hello from the test")
    for handler in clean_logging.handlers:
        handler.flush()
    path = tmp_path / "logs" / "keyenroll.log"
    assert path == app_module.log_path()
    assert "INFO keyenroll.test: hello from the test" in path.read_text(encoding="utf-8")


def test_explicit_log_file_and_level(tmp_path, clean_logging):
    target = tmp_path / "custom.log"
    app_module.configure_logging("WARNING", str(target))
    logging.getLogger("keyenroll.test").info("too quiet")
    logging.getLogger("keyenroll.test").warning("loud enough")
    for handler in clean_logging.handlers:
        handler.flush()
    text = target.read_text(encoding="utf-8")
    assert "loud enough" in text and "too quiet" not in text


def test_unwritable_log_location_does_not_stop_the_app(tmp_path, clean_logging):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    app_module.configure_logging("INFO", str(blocker / "nested" / "app.log"))  # not a directory
    logging.getLogger("keyenroll.test").info("still running")


def test_unexpected_error_is_logged_and_shown_once(qt, hooks, monkeypatch, caplog):
    shown = []
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda p, t, text: shown.append(text)))
    app_module.install_excepthooks()

    try:
        raise RuntimeError("boom in a slot")
    except RuntimeError:
        with caplog.at_level(logging.CRITICAL):
            sys.excepthook(*sys.exc_info())

    assert len(shown) == 1 and "RuntimeError: boom in a slot" in shown[0]
    assert any("Unexpected error" in r.message and r.exc_info for r in caplog.records)


def test_error_in_a_background_thread_is_logged_without_a_dialog(qt, hooks, monkeypatch, caplog):
    shown = []
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda p, t, text: shown.append(text)))
    app_module.install_excepthooks()

    def work():
        raise ValueError("boom in a thread")

    with caplog.at_level(logging.CRITICAL):
        thread = threading.Thread(target=work)
        thread.start()
        thread.join()

    assert shown == []  # widgets must not be touched off the UI thread
    assert any(r.exc_info and "boom in a thread" in str(r.exc_info[1]) for r in caplog.records)


def test_ctrl_c_is_left_alone(qt, hooks, monkeypatch):
    shown = []
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda p, t, text: shown.append(text)))
    passed_on = []
    monkeypatch.setattr(sys, "__excepthook__", lambda *a: passed_on.append(a[0]))
    app_module.install_excepthooks()
    sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
    assert shown == [] and passed_on == [KeyboardInterrupt]
