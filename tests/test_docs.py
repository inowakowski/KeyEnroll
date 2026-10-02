"""The documentation site: every page exists in each documentation language
and only refers to screenshots that are there. (Links between pages are
checked by ``mkdocs build --strict`` in the docs workflow.)"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from keyenroll import DOCS_LANGUAGES, DOCS_URL, PROJECT_URL, i18n

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
TRANSLATED = [lang for lang in DOCS_LANGUAGES if lang != "en"]


def pages(lang: str) -> dict[str, Path]:
    """Page name -> file, for one language (name.md is English, name.pl.md Polish)."""
    out = {}
    for path in DOCS.glob("*.md"):
        stem, _, suffix = path.stem.partition(".")
        if (suffix or "en") == lang:
            out[stem] = path
    return out


def test_documentation_languages_are_application_languages():
    assert DOCS_LANGUAGES[0] == "en" and set(DOCS_LANGUAGES) <= set(i18n.LANGUAGES)


def test_no_host_of_the_site_is_built_in():
    """The site may move to another host or domain; the application and the
    site configuration must keep working when it does."""
    assert DOCS_URL.startswith(PROJECT_URL + "#")
    anchor = DOCS_URL.split("#")[1]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    headings = [h.lower() for h in re.findall(r"^#+ (.+)$", readme, flags=re.M)]
    assert headings.count(anchor) == 1, "the README section the application links to"
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert re.search(r"^site_url: !ENV", config, flags=re.M)
    assert "github.io" not in config and "pages.dev" not in config


@pytest.mark.parametrize("lang", TRANSLATED)
def test_every_page_exists_in_every_documentation_language(lang):
    english = pages("en")
    assert "index" in english and len(english) >= 10
    assert sorted(pages(lang)) == sorted(english)


@pytest.mark.parametrize("lang", DOCS_LANGUAGES)
def test_pages_show_screenshots_of_their_own_language_that_exist(lang):
    seen = 0
    for path in pages(lang).values():
        for image in re.findall(r"\]\((assets/screenshots/[^)]+)\)", path.read_text(encoding="utf-8")):
            assert image.startswith(f"assets/screenshots/{lang}/"), f"{path.name}: {image}"
            assert (DOCS / image).is_file(), f"{path.name}: {image} is missing"
            seen += 1
    assert seen >= 10


@pytest.mark.parametrize("lang", TRANSLATED)
def test_translated_pages_keep_the_headings_other_pages_link_to(lang):
    """Links carry English anchors (page.md#some-heading); a translated page
    has to declare the same anchor explicitly on its translated heading."""
    linked: dict[str, set[str]] = {}
    for path in DOCS.glob("*.md"):
        for page, anchor in re.findall(r"\]\(([\w-]+)\.md#([\w-]+)\)", path.read_text(encoding="utf-8")):
            linked.setdefault(page, set()).add(anchor)
    translated = pages(lang)
    for page, anchors in linked.items():
        text = translated[page].read_text(encoding="utf-8")
        for anchor in anchors:
            # Either declared explicitly, or a heading that slugs to it unchanged.
            explicit = f"{{ #{anchor} }}" in text
            plain = any(
                re.sub(r"[^\w]+", "-", h.lower()).strip("-") == anchor
                for h in re.findall(r"^#+ (.+?)(?: \{.*\})?$", text, flags=re.M)
            )
            assert explicit or plain, f"{translated[page].name} lacks the anchor #{anchor}"
