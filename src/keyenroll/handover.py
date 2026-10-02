"""Handing an enrolled key over to its user: message text, e-mail draft, file."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

from .i18n import N_, current_language, tr
from .providers import DirectoryUser

# Placeholders available in the message templates.
PLACEHOLDERS = (
    "name",
    "username",
    "email",
    "key_name",
    "serial",
    "pin",
    "provider",
    "change_note",
)

DEFAULT_SUBJECT = {
    "en": "Your security key",
    "pl": "Twój klucz bezpieczeństwa",
}

DEFAULT_BODY = {
    "en": (
        "Hello {name},\n"
        "\n"
        "your security key is ready.\n"
        "\n"
        "Key: {key_name}\n"
        "Serial number: {serial}\n"
        "Temporary PIN: {pin}\n"
        "\n"
        "{change_note}\n"
        "\n"
        "Use the key and the PIN to sign in to {provider} as {username}. "
        "Do not share the PIN with anyone.\n"
    ),
    "pl": (
        "Dzień dobry {name},\n"
        "\n"
        "Twój klucz bezpieczeństwa jest gotowy.\n"
        "\n"
        "Klucz: {key_name}\n"
        "Numer seryjny: {serial}\n"
        "Tymczasowy PIN: {pin}\n"
        "\n"
        "{change_note}\n"
        "\n"
        "Użyj klucza i PIN-u, aby zalogować się do {provider} jako {username}. "
        "Nie udostępniaj PIN-u nikomu.\n"
    ),
}


@dataclass
class Handover:
    """What the operator passes on to the user after an enrollment."""

    user: DirectoryUser
    key_name: str = ""
    serial: int | None = None
    pin: str | None = None  # None: the operator chose it, or it was not changed
    pin_changed: bool = True
    must_change_pin: bool = False
    provider: str = ""
    warnings: list[tuple[str, dict]] = field(default_factory=list)

    @property
    def recipient(self) -> str:
        """E-mail address of the user, if the directory knows one."""
        user = self.user
        if user.email:
            return user.email
        return user.username if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", user.username) else ""

    def values(self) -> dict[str, str]:
        user = self.user
        return {
            "name": user.display_name or user.username,
            "username": user.username,
            "email": user.email,
            "key_name": self.key_name or tr(N_("security key")),
            "serial": str(self.serial) if self.serial else "—",
            "pin": self.pin or tr(N_("(provided separately)")),
            "provider": self.provider,
            "change_note": (
                tr(N_("You will be asked to set your own PIN the first time you use the key."))
                if self.must_change_pin
                else ""
            ),
        }


def default_subject() -> str:
    return DEFAULT_SUBJECT.get(current_language(), DEFAULT_SUBJECT["en"])


def default_body() -> str:
    return DEFAULT_BODY.get(current_language(), DEFAULT_BODY["en"])


def render(template: str, handover: Handover) -> str:
    """Fills ``{placeholders}``. Unknown ones and stray braces are left as they
    are, so a typo in a custom template never breaks the hand-over."""
    values = handover.values()
    text = re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), template)
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)
    # An empty placeholder on its own line leaves a gap: close it.
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def message(handover: Handover, subject: str = "", body: str = "") -> tuple[str, str]:
    """Returns (subject, body), using the built-in templates when none are set."""
    return (
        render(subject or default_subject(), handover).strip(),
        render(body or default_body(), handover),
    )


def mailto_url(recipient: str, subject: str, body: str) -> str:
    """A mailto: link (RFC 6068) opening a draft in the default mail program."""
    crlf_body = body.replace("\r\n", "\n").replace("\n", "\r\n")
    return (
        f"mailto:{quote(recipient, safe='@')}"
        f"?subject={quote(subject, safe='')}&body={quote(crlf_body, safe='')}"
    )


def default_filename(handover: Handover) -> str:
    stem = re.sub(r"[^\w.@-]+", "_", handover.user.username or "user").strip("._") or "user"
    return f"keyenroll-{stem}.txt"


def save_text(path: str | Path, subject: str, body: str) -> None:
    """Writes the message to a text file readable by the owner only."""
    data = f"{subject}\n\n{body}".encode("utf-8-sig")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
