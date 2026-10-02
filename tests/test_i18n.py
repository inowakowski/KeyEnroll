from __future__ import annotations

import ast
import string
from pathlib import Path

from keyenroll import i18n
from keyenroll.translations_pl import PL

SRC = Path(__file__).parent.parent / "src" / "keyenroll"


def source_strings() -> set[str]:
    """All literals passed to tr() or N_() anywhere in the application."""
    found = set()
    for path in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in ("tr", "N_")
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                found.add(node.args[0].value)
    return found


def placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_every_string_has_a_polish_translation():
    missing = sorted(source_strings() - set(PL))
    assert not missing, f"untranslated: {missing}"


def test_no_stale_translations():
    stale = sorted(set(PL) - source_strings())
    assert not stale, f"unused: {stale}"


def test_translations_keep_placeholders():
    for english, polish in PL.items():
        assert placeholders(english) == placeholders(polish), english


def test_tr_switches_language_and_formats():
    try:
        i18n.set_language("pl")
        assert i18n.tr("Cancel") == "Anuluj"
        assert "7" in i18n.tr("Attempts remaining: {retries}", retries=7)
        assert i18n.tr("not a known string") == "not a known string"
        i18n.set_language("en")
        assert i18n.tr("Cancel") == "Cancel"
        i18n.set_language("xx")
        assert i18n.current_language() == "en"
    finally:
        i18n.set_language("en")
