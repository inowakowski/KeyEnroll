from __future__ import annotations

import argparse
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

import PySide6
from PySide6.QtCore import QLibraryInfo, QTimer, QTranslator
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_NAME, __version__
from .config import ConfigStore, config_dir, private_dir
from .i18n import current_language, set_language, tr
from .secrets_store import default_store
from .ui.common import AppContext
from .ui.main_window import MainWindow
from .ui.theme import apply_theme

logger = logging.getLogger(__name__)

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def log_path() -> Path:
    return config_dir() / "logs" / "keyenroll.log"


def configure_logging(level: str, log_file: str | None) -> None:
    """Logs to ``log_file`` if given, otherwise to a small rotating file next
    to the settings, so that a problem report can include what happened."""
    handler: logging.Handler
    try:
        if log_file:
            handler = logging.FileHandler(log_file, encoding="utf-8")
        else:
            path = log_path()
            private_dir(config_dir())
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
            )
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def install_excepthooks() -> None:
    """Unexpected errors are logged and reported instead of vanishing: in a
    windowed build there is no console to print a traceback to."""
    showing = threading.Event()

    def on_error(exc_type, exc, tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        logger.critical("Unexpected error", exc_info=(exc_type, exc, tb))
        on_ui_thread = threading.current_thread() is threading.main_thread()
        if QApplication.instance() is None or not on_ui_thread or showing.is_set():
            return
        showing.set()
        try:
            QMessageBox.critical(
                None,
                APP_NAME,
                tr("An unexpected error occurred:")
                + f"\n\n{exc_type.__name__}: {exc}\n\n"
                + tr("Details were written to the log: {path}", path=str(log_path())),
            )
        finally:
            showing.clear()

    sys.excepthook = on_error
    threading.excepthook = lambda args: on_error(
        args.exc_type, args.exc_value, args.exc_traceback
    )


def install_qt_translation(app: QApplication, language: str) -> bool:
    """Makes Qt's own texts (Yes/No buttons, the colour dialog) follow the
    language of the application. Returns False if Qt has no such translation."""
    if language == "en":
        return True
    translator = QTranslator(app)
    # Where Qt says they are, and where a packaged build keeps them.
    folders = [
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
        str(Path(PySide6.__file__).parent / "translations"),
    ]
    for folder in folders:
        if translator.load(f"qtbase_{language}", folder):
            logger.info("Qt translation for %s loaded from %s", language, folder)
            return app.installTranslator(translator)
    translator.deleteLater()
    logger.warning("No Qt translation for %s in %s", language, " or ".join(folders))
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="keyenroll")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "-l",
        "--log-level",
        default="INFO",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        help="logging verbosity (default: INFO)",
    )
    parser.add_argument(
        "--log-file", help="write the log to this file instead of the default location"
    )
    args, qt_args = parser.parse_known_args(sys.argv[1:] if argv is None else argv)

    configure_logging(args.log_level, args.log_file)
    install_excepthooks()

    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)

    config = ConfigStore()
    set_language(config.language)
    install_qt_translation(app, current_language())
    theme = apply_theme(app, config.theme, config.custom_base, config.custom_accent)
    window = MainWindow(AppContext(config, default_store()))
    window.show()
    logger.info("Started %s %s (%s theme)", APP_NAME, __version__, theme)

    if config.unreadable_backup is not None:
        backup = config.unreadable_backup
        QTimer.singleShot(
            0,
            lambda: QMessageBox.warning(
                window,
                APP_NAME,
                tr(
                    "The settings file could not be read and was set aside as {path}. "
                    "KeyEnroll started with default settings.",
                    path=str(backup),
                ),
            ),
        )
    return app.exec()
