"""Minimal translation layer. English strings are the message keys."""

from __future__ import annotations

import locale

# Shown in the language selector, each in its own language.
LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "fr": "Français",
    "it": "Italiano",
    "pl": "Polski",
}

# Windows names locales in English ("German_Germany") rather than by ISO code.
_LOCALE_NAMES = {
    "english": "en",
    "german": "de",
    "spanish": "es",
    "french": "fr",
    "italian": "it",
    "polish": "pl",
}

_lang = "en"
_catalog: dict[str, str] = {}


def N_(text: str) -> str:
    """Marks a string for translation without translating it here."""
    return text


def catalog(lang: str) -> dict[str, str]:
    """Translations of one language. The imports are spelled out so that the
    packaged application is known to contain every one of them."""
    if lang == "de":
        from .translations_de import DE as table
    elif lang == "es":
        from .translations_es import ES as table
    elif lang == "fr":
        from .translations_fr import FR as table
    elif lang == "it":
        from .translations_it import IT as table
    elif lang == "pl":
        from .translations_pl import PL as table
    else:
        table = {}
    return table


def match_language(name: str) -> str | None:
    """'de_AT.UTF-8', 'de-AT' and 'German_Austria' are all 'de'; None if the
    language has no translation."""
    head = name.strip().lower().replace("-", "_").split(".", 1)[0].split("_", 1)[0]
    if head in LANGUAGES:
        return head
    return _LOCALE_NAMES.get(head)


def system_languages() -> list[str]:
    """Locale names of the languages the user prefers, most preferred first."""
    names: list[str] = []
    try:
        from PySide6.QtCore import QLocale

        # The display languages chosen in the system settings. Python's locale
        # module does not see them in an application started from the macOS
        # Finder or a Linux desktop launcher.
        names += QLocale.system().uiLanguages()
    except Exception:
        pass
    try:
        names.append(locale.getlocale()[0] or "")
    except ValueError:
        pass
    return names


def detect_language(names: list[str] | None = None) -> str:
    """The first preferred language that has a translation, else English."""
    for name in system_languages() if names is None else names:
        code = match_language(name)
        if code:
            return code
    return "en"


def set_language(lang: str) -> None:
    global _lang, _catalog
    if lang == "auto":
        lang = detect_language()
    _lang = lang if lang in LANGUAGES else "en"
    _catalog = catalog(_lang)


def current_language() -> str:
    return _lang


def tr(text: str, **params) -> str:
    text = _catalog.get(text, text)
    return text.format(**params) if params else text
