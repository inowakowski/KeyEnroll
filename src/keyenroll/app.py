from __future__ import annotations

import argparse
import logging
import sys

from PySide6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .config import ConfigStore
from .i18n import set_language
from .secrets_store import default_store
from .ui.common import AppContext
from .ui.main_window import MainWindow
from .ui.theme import apply_theme


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="keyenroll")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "-l",
        "--log-level",
        default="WARNING",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        help="logging verbosity (written to stderr or --log-file)",
    )
    parser.add_argument("--log-file", help="write the log to this file")
    args, qt_args = parser.parse_known_args(sys.argv[1:] if argv is None else argv)

    logging.basicConfig(
        level=args.log_level,
        filename=args.log_file,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)

    config = ConfigStore()
    set_language(config.language)
    theme = apply_theme(app, config.theme, config.custom_base, config.custom_accent)
    window = MainWindow(AppContext(config, default_store()))
    window.show()
    logging.getLogger(__name__).info("Started %s %s (%s theme)", APP_NAME, __version__, theme)
    return app.exec()
