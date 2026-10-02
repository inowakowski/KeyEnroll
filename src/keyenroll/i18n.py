"""Minimal translation layer. English strings are the message keys."""

from __future__ import annotations

import locale

LANGUAGES = {"en": "English", "pl": "Polski"}

_lang = "en"


def N_(text: str) -> str:
    """Marks a string for translation without translating it here."""
    return text


def detect_language() -> str:
    try:
        code = (locale.getlocale()[0] or "").lower()
    except ValueError:
        code = ""
    return "pl" if code.startswith(("pl", "polish")) else "en"


def set_language(lang: str) -> None:
    global _lang
    if lang == "auto":
        lang = detect_language()
    _lang = lang if lang in LANGUAGES else "en"


def current_language() -> str:
    return _lang


def tr(text: str, **params) -> str:
    if _lang == "pl":
        from .translations_pl import PL

        text = PL.get(text, text)
    return text.format(**params) if params else text
