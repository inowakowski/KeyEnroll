__version__ = "0.5.0"

APP_NAME = "KeyEnroll"
PROJECT_URL = "https://github.com/inowakowski/KeyEnroll"
DOCS_URL = "https://inowakowski.github.io/KeyEnroll/"
# Languages the documentation is written in; other languages get the English one.
DOCS_LANGUAGES = ("en", "pl")


def docs_url(language: str = "en") -> str:
    if language != "en" and language in DOCS_LANGUAGES:
        return f"{DOCS_URL}{language}/"
    return DOCS_URL
