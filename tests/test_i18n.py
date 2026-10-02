from __future__ import annotations

import ast
import string
from pathlib import Path

import pytest

from keyenroll import handover, i18n

SRC = Path(__file__).parent.parent / "src" / "keyenroll"
TRANSLATED = sorted(set(i18n.LANGUAGES) - {"en"})


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


def test_english_needs_no_catalog_and_unknown_languages_have_none():
    assert i18n.catalog("en") == {}
    assert i18n.catalog("xx") == {}


@pytest.mark.parametrize("lang", TRANSLATED)
def test_every_string_is_translated(lang):
    missing = sorted(source_strings() - set(i18n.catalog(lang)))
    assert not missing, f"untranslated in {lang}: {missing}"


@pytest.mark.parametrize("lang", TRANSLATED)
def test_no_stale_translations(lang):
    stale = sorted(set(i18n.catalog(lang)) - source_strings())
    assert not stale, f"unused in {lang}: {stale}"


@pytest.mark.parametrize("lang", TRANSLATED)
def test_translations_keep_placeholders(lang):
    for english, translated in i18n.catalog(lang).items():
        assert placeholders(english) == placeholders(translated), english


@pytest.mark.parametrize("lang", TRANSLATED)
def test_translations_are_not_empty_and_keep_the_ellipsis(lang):
    for english, translated in i18n.catalog(lang).items():
        assert translated.strip(), english
        # A trailing ellipsis marks "opens a dialog" or "in progress".
        assert english.endswith("…") == translated.endswith("…"), english


@pytest.mark.parametrize("lang", TRANSLATED)
def test_file_dialog_filters_keep_their_patterns(lang):
    for english, translated in i18n.catalog(lang).items():
        if "(*" in english:
            patterns = [part[part.index("(") :] for part in english.split(";;")]
            assert [part[part.index("(") :] for part in translated.split(";;")] == patterns


@pytest.mark.parametrize("lang", sorted(i18n.LANGUAGES))
def test_every_language_has_a_hand_over_message(lang):
    assert handover.DEFAULT_SUBJECT[lang].strip()
    body = handover.DEFAULT_BODY[lang]
    assert placeholders(body) == placeholders(handover.DEFAULT_BODY["en"])
    assert placeholders(body) <= set(handover.PLACEHOLDERS)


def test_tr_switches_language_and_formats():
    try:
        i18n.set_language("pl")
        assert i18n.tr("Cancel") == "Anuluj"
        assert "7" in i18n.tr("Attempts remaining: {retries}", retries=7)
        assert i18n.tr("not a known string") == "not a known string"
        i18n.set_language("de")
        assert i18n.tr("Cancel") == "Abbrechen"
        i18n.set_language("en")
        assert i18n.tr("Cancel") == "Cancel"
        i18n.set_language("xx")
        assert i18n.current_language() == "en"
        assert i18n.tr("Cancel") == "Cancel"
    finally:
        i18n.set_language("en")


@pytest.mark.parametrize(
    "name, expected",
    [
        ("pl_PL", "pl"),
        ("pl-PL", "pl"),
        ("Polish_Poland", "pl"),
        ("de_AT.UTF-8", "de"),
        ("German_Switzerland", "de"),
        ("fr", "fr"),
        ("French_Canada", "fr"),
        ("es-419", "es"),
        ("Spanish_Mexico", "es"),
        ("it_CH", "it"),
        ("en-GB", "en"),
        ("English_United States", "en"),
        ("ja_JP", None),
        ("C", None),
        ("", None),
    ],
)
def test_locale_names_are_matched_to_languages(name, expected):
    assert i18n.match_language(name) == expected


def test_first_preferred_language_with_a_translation_wins():
    assert i18n.detect_language(["de-CH", "en-US"]) == "de"
    # Japanese is not offered: the next choice of the user is.
    assert i18n.detect_language(["ja-JP", "fr-FR", "en-US"]) == "fr"
    assert i18n.detect_language(["en-US", "pl-PL"]) == "en"
    assert i18n.detect_language(["ja-JP", "C", ""]) == "en"
    assert i18n.detect_language([]) == "en"


def test_system_language_is_always_one_that_is_offered():
    assert i18n.detect_language() in i18n.LANGUAGES
    try:
        i18n.set_language("auto")
        assert i18n.current_language() in i18n.LANGUAGES
    finally:
        i18n.set_language("en")
