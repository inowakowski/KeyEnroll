"""Application look: colour tokens, palette, style sheet and icons.

One style (Fusion plus this sheet) is used on every platform so the app looks
the same on Windows, macOS and Linux, in a light and a dark variant.
"""

from __future__ import annotations

import atexit
import re
import shutil
import tempfile
from pathlib import Path
from string import Template

from PySide6 import QtSvg  # noqa: F401  (keeps the SVG plugins in frozen builds)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout, QWidget

THEMES = {
    "light": dict(
        bg="#f4f5f7",
        sidebar="#ffffff",
        card="#ffffff",
        input="#ffffff",
        border="#e1e4ea",
        border_strong="#c4c9d4",
        text="#1b1f27",
        muted="#667085",
        disabled="#a3aab8",
        hover="#eef0f4",
        button="#ffffff",
        accent="#4f5bd5",
        accent_hover="#434ec0",
        accent_soft="#e8eafc",
        accent_text="#3a45b0",
        accent_disabled="#b9bfee",
        on_accent="#ffffff",
        danger="#d13438",
        danger_soft="#fdecec",
        success="#1a7f47",
        banner_bg="#fff5d6",
        banner_border="#f0cf7a",
        banner_text="#5b4300",
    ),
    "dark": dict(
        bg="#0f1116",
        sidebar="#14171e",
        card="#191d26",
        input="#11141a",
        border="#272c38",
        border_strong="#3a4152",
        text="#e7e9ee",
        muted="#939bad",
        disabled="#5b6375",
        hover="#222734",
        button="#1f2430",
        accent="#7480f6",
        accent_hover="#8d97f8",
        accent_soft="#262b4d",
        accent_text="#aab2fb",
        accent_disabled="#3a3f66",
        on_accent="#ffffff",
        danger="#f0686c",
        danger_soft="#3a1e21",
        success="#4cc38a",
        banner_bg="#3a2f10",
        banner_border="#6b5518",
        banner_text="#f3dc9b",
    ),
}

# Colour schemes offered in the settings, besides "auto" and "custom".
PRESETS = ("light", "dark", "yubico")
YUBICO_ACCENT = "#9aca3c"
DEFAULT_CUSTOM_ACCENT = "#4f5bd5"


def _rgb(color: str) -> tuple[int, int, int]:
    return tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))


def _mix(color: str, other: str, amount: float) -> str:
    """Blends ``amount`` (0..1) of ``other`` into ``color``."""
    return "#" + "".join(
        f"{round(a + (b - a) * amount):02x}" for a, b in zip(_rgb(color), _rgb(other), strict=True)
    )


def _luminance(color: str) -> float:
    """Relative luminance as defined by WCAG."""
    channels = [c / 255 for c in _rgb(color)]
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two colours (1..21)."""
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def valid_color(color: str) -> bool:
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", color or ""))


def with_accent(base: str, accent: str) -> dict[str, str]:
    """A light or dark scheme recoloured around an arbitrary accent."""
    t = dict(THEMES[base])
    toward = "#ffffff" if base == "dark" else "#000000"
    t["accent"] = accent.lower()
    t["accent_hover"] = _mix(accent, toward, 0.14)
    t["accent_soft"] = _mix(t["card"], accent, 0.22 if base == "dark" else 0.14)
    t["accent_text"] = _mix(accent, toward, 0.30)
    t["accent_disabled"] = _mix(t["card"], accent, 0.40)
    # Light accents (such as the Yubico green) need dark text on top:
    # use whichever of the two is easier to read.
    t["on_accent"] = max("#ffffff", "#11151c", key=lambda c: contrast(c, accent))
    return t


def build_tokens(
    setting: str, custom_base: str = "dark", custom_accent: str = DEFAULT_CUSTOM_ACCENT
) -> tuple[str, dict[str, str]]:
    """Returns the name of the scheme in effect and its colour tokens."""
    if setting == "yubico":
        return "yubico", with_accent("dark", YUBICO_ACCENT)
    if setting == "custom":
        base = custom_base if custom_base in THEMES else "dark"
        accent = custom_accent if valid_color(custom_accent) else DEFAULT_CUSTOM_ACCENT
        return "custom", with_accent(base, accent)
    name = resolve_theme(setting)
    return name, dict(THEMES[name])


_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
    'stroke-linejoin="round">{body}</svg>'
)

ICONS = {
    "key": '<circle cx="8" cy="15.5" r="4"/><path d="M11 12.5 19.5 4M16.5 7l2.5 2.5M14 9.5l2 2"/>',
    "users": (
        '<circle cx="9" cy="8" r="3.3"/><path d="M2.8 20c0-3.4 2.8-6 6.2-6s6.2 2.6 6.2 6"/>'
        '<path d="M16 4.9a3.3 3.3 0 0 1 0 6.2M18 14.4c1.9.9 3.2 2.9 3.2 5.6"/>'
    ),
    "shield": '<path d="M12 3l7.5 3v5.2c0 4.4-3 8-7.5 9.8-4.5-1.8-7.5-5.4-7.5-9.8V6z"/><path d="M8.8 12l2.3 2.3 4.2-4.4"/>',
    "sliders": (
        '<path d="M4 7h9M18 7h2M4 17h3M12 17h8"/>'
        '<circle cx="15.5" cy="7" r="2.3"/><circle cx="9.5" cy="17" r="2.3"/>'
    ),
    "layers": '<path d="M12 3.5l8.5 4.5-8.5 4.5L3.5 8z"/><path d="M3.5 12.5l8.5 4.5 8.5-4.5M3.5 16.5 12 21l8.5-4.5"/>',
    "gear": (
        '<circle cx="12" cy="12" r="3.2"/>'
        '<path d="M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.9 1.9M16.6 16.6l1.9 1.9'
        'M18.5 5.5l-1.9 1.9M7.4 16.6l-1.9 1.9"/>'
    ),
    "chevron-down": '<path d="M6 9.5l6 6 6-6"/>',
    "chevron-up": '<path d="M6 14.5l6-6 6 6"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "grip": '<path d="M12 7v.01M12 12v.01M12 17v.01"/>',
}

APP_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect x="4" y="4" width="56" height="56" rx="14" fill="#4f5bd5"/>'
    '<g fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round" '
    'stroke-linejoin="round"><circle cx="24" cy="40" r="9"/>'
    '<path d="M31 33 48 16M42 22l6 6M36 28l4.5 4.5"/></g></svg>'
)

_QSS = Template(
    """
QMainWindow, QDialog, QMessageBox { background: $bg; }
QToolTip { background: $card; color: $text; border: 1px solid $border; padding: 4px 8px; }

QFrame#sidebar { background: $sidebar; border-right: 1px solid $border; }
QLabel#brand { font-size: ${title}pt; font-weight: 700; }
QLabel#version { color: $muted; font-size: ${small}pt; }
QListWidget#nav { background: transparent; border: none; outline: 0; }
QListWidget#nav::item { padding: 10px 12px; margin: 2px 10px; border-radius: 8px; color: $muted; }
QListWidget#nav::item:hover { background: $hover; color: $text; }
QListWidget#nav::item:selected { background: $accent_soft; color: $accent_text; font-weight: 600; }

QLabel#pageTitle { font-size: ${page}pt; font-weight: 700; }
QLabel#cardTitle { font-size: ${title}pt; font-weight: 600; }
QLabel#hint { color: $muted; }
QLabel#error { color: $danger; font-weight: 600; }
QLabel#title { font-size: ${page}pt; font-weight: 700; }
QLabel#step { font-size: ${title}pt; font-weight: 600; }
QLabel#value { font-weight: 600; }
QLabel#pin { padding: 10px 14px; border: 1px solid $border; border-radius: 10px; background: $input; }
QLabel#chip { padding: 4px 10px; border-radius: 11px; background: $hover; color: $muted; }
QLabel#chip[state="on"] { background: $accent_soft; color: $accent_text; }

QFrame#card { background: $card; border: 1px solid $border; border-radius: 12px; }
QFrame#banner { background: $banner_bg; border: 1px solid $banner_border; border-radius: 10px; }
QFrame#banner QLabel { color: $banner_text; }

QLineEdit, QComboBox, QSpinBox {
    background: $input; border: 1px solid $border_strong; border-radius: 8px;
    padding: 6px 10px; min-height: 20px; selection-background-color: $accent; selection-color: $on_accent;
}
QPlainTextEdit {
    background: $input; border: 1px solid $border_strong; border-radius: 8px; padding: 6px 8px;
    selection-background-color: $accent; selection-color: $on_accent;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus { border-color: $accent; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled { color: $disabled; border-color: $border; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow { image: url($chevron_down); width: 14px; height: 14px; }
QComboBox QAbstractItemView {
    background: $card; border: 1px solid $border; border-radius: 8px; padding: 4px; outline: 0;
    selection-background-color: $accent_soft; selection-color: $text;
}
QSpinBox::up-button, QSpinBox::down-button { border: none; width: 24px; background: transparent; }
QSpinBox::up-arrow { image: url($chevron_up); width: 11px; height: 11px; }
QSpinBox::down-arrow { image: url($chevron_down); width: 11px; height: 11px; }

QPushButton {
    background: $button; border: 1px solid $border_strong; border-radius: 8px;
    padding: 7px 16px; font-weight: 500;
}
QPushButton:hover { background: $hover; }
QPushButton:pressed { background: $border; }
QPushButton:disabled { color: $disabled; border-color: $border; }
QPushButton#primary { background: $accent; border-color: $accent; color: $on_accent; font-weight: 600; }
QPushButton#primary:hover { background: $accent_hover; border-color: $accent_hover; }
QPushButton#primary:disabled { background: $accent_disabled; border-color: $accent_disabled; color: $card; }
QPushButton#primary[big="true"] { padding: 13px 24px; font-size: ${title}pt; border-radius: 10px; }
QPushButton[big="true"] { padding: 13px 20px; border-radius: 10px; }
QPushButton#danger { color: $danger; }
QPushButton#danger:hover { background: $danger_soft; border-color: $danger; }
QPushButton#danger:disabled { color: $disabled; }
QFrame#banner QPushButton { background: $banner_text; color: $banner_bg; border: none; }

QCheckBox { spacing: 10px; padding: 3px 0; }
QCheckBox::indicator {
    width: 18px; height: 18px; border: 1px solid $border_strong; border-radius: 5px; background: $input;
}
QCheckBox::indicator:hover { border-color: $accent; }
QCheckBox::indicator:checked { background: $accent; border-color: $accent; image: url($check); }
QCheckBox::indicator:disabled { background: $hover; border-color: $border; }
QCheckBox::indicator:checked:disabled { background: $accent_disabled; border-color: $accent_disabled; }
QCheckBox:disabled { color: $disabled; }

QTableWidget, QListWidget { background: transparent; border: none; outline: 0; }
QTableWidget::item { padding: 7px 10px; border-bottom: 1px solid $border; }
QTableWidget::item:selected, QListWidget::item:selected { background: $accent_soft; color: $text; }
QListWidget::item { padding: 7px 10px; border-radius: 6px; }
QListWidget#log { font-size: ${small}pt; color: $muted; }
QListWidget#log::item { padding: 2px 4px; }
QHeaderView { background: transparent; }
QHeaderView::section {
    background: transparent; border: none; border-bottom: 1px solid $border;
    padding: 8px 10px; color: $muted; font-weight: 600;
}
QTableCornerButton::section { background: transparent; border: none; }

QSplitter::handle { background: transparent; }
QSplitter::handle:horizontal { width: 14px; image: url($grip); }
QSplitter::handle:horizontal:hover { background: $hover; border-radius: 4px; }

QRadioButton { spacing: 10px; padding: 3px 0; }
QRadioButton::indicator {
    width: 16px; height: 16px; border: 1px solid $border_strong; border-radius: 9px; background: $input;
}
QRadioButton::indicator:hover { border-color: $accent; }
QRadioButton::indicator:checked {
    width: 8px; height: 8px; border: 5px solid $accent; background: $input;
}

QScrollArea#plain { background: transparent; border: none; }
QScrollArea#plain > QWidget > QWidget { background: transparent; }

QProgressBar { background: $border; border: none; border-radius: 3px; max-height: 6px; min-height: 6px; }
QProgressBar::chunk { background: $accent; border-radius: 3px; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $border_strong; border-radius: 3px; min-height: 30px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: $border_strong; border-radius: 3px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""
)

_assets: Path | None = None
_tokens: dict[str, str] = dict(THEMES["light"])


def _asset_dir() -> Path:
    global _assets
    if _assets is None:
        _assets = Path(tempfile.mkdtemp(prefix="keyenroll-"))
        atexit.register(shutil.rmtree, _assets, ignore_errors=True)
    return _assets


def _svg_file(name: str, color: str, width: float = 2) -> str:
    """Writes a tinted icon and returns its path in the form Qt style sheets need."""
    path = _asset_dir() / f"{name}-{color.lstrip('#')}.svg"
    if not path.exists():
        path.write_text(
            _SVG.format(color=color, width=width, body=ICONS[name]), encoding="utf-8"
        )
    return path.as_posix()


def token(name: str) -> str:
    return _tokens[name]


def nav_icon(name: str) -> QIcon:
    icon = QIcon()
    size = QSize(20, 20)
    icon.addFile(_svg_file(name, _tokens["muted"], 1.8), size, QIcon.Mode.Normal)
    icon.addFile(_svg_file(name, _tokens["accent_text"], 1.8), size, QIcon.Mode.Selected)
    return icon


def app_icon() -> QIcon:
    path = _asset_dir() / "app.svg"
    if not path.exists():
        path.write_text(APP_ICON_SVG, encoding="utf-8")
    return QIcon(path.as_posix())


def resolve_theme(setting: str) -> str:
    if setting in THEMES:
        return setting
    scheme = QGuiApplication.styleHints().colorScheme()
    return "dark" if scheme == Qt.ColorScheme.Dark else "light"


def apply_theme(
    app: QApplication,
    setting: str = "auto",
    custom_base: str = "dark",
    custom_accent: str = DEFAULT_CUSTOM_ACCENT,
) -> str:
    """Applies style, palette and style sheet. Returns the scheme in effect."""
    global _tokens
    name, t = build_tokens(setting, custom_base, custom_accent)
    _tokens = t
    app.setStyle("Fusion")

    font = app.font()
    if font.pointSizeF() < 10:  # Windows defaults to 9pt, which reads small
        font.setPointSizeF(10)
        app.setFont(font)
    base = font.pointSizeF()

    palette = QPalette()
    roles = QPalette.ColorRole
    for role, key in (
        (roles.Window, "bg"),
        (roles.WindowText, "text"),
        (roles.Base, "input"),
        (roles.AlternateBase, "card"),
        (roles.Text, "text"),
        (roles.Button, "button"),
        (roles.ButtonText, "text"),
        (roles.ToolTipBase, "card"),
        (roles.ToolTipText, "text"),
        (roles.PlaceholderText, "muted"),
        (roles.Highlight, "accent"),
        (roles.Link, "accent"),
    ):
        palette.setColor(role, QColor(t[key]))
    palette.setColor(roles.HighlightedText, QColor(t["on_accent"]))
    for role in (roles.WindowText, roles.Text, roles.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(t["disabled"]))
    app.setPalette(palette)

    app.setStyleSheet(
        _QSS.substitute(
            t,
            small=round(base - 1, 1),
            title=round(base + 1.5, 1),
            page=round(base + 6, 1),
            chevron_down=_svg_file("chevron-down", t["muted"]),
            chevron_up=_svg_file("chevron-up", t["muted"]),
            check=_svg_file("check", t["on_accent"], 3),
            grip=_svg_file("grip", t["muted"], 2.6),
        )
    )
    app.setWindowIcon(app_icon())
    return name


class Card(QFrame):
    """A titled surface grouping related controls."""

    def __init__(self, title: str = "", hint: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(10)
        if title:
            label = QLabel(title)
            label.setObjectName("cardTitle")
            self.body.addWidget(label)
        if hint:
            note = QLabel(hint)
            note.setObjectName("hint")
            note.setWordWrap(True)
            self.body.addWidget(note)
