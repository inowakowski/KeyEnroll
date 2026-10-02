from __future__ import annotations

import os
import stat
import sys
from urllib.parse import parse_qs, unquote, urlsplit

from keyenroll import handover, i18n
from keyenroll.handover import Handover
from keyenroll.providers.base import DirectoryUser

ALICE = DirectoryUser("u1", "alice@example.com", "Alice Example", "alice@example.com")


def make(**kw) -> Handover:
    defaults = dict(
        user=ALICE, key_name="YubiKey 5 NFC 23456789", serial=23456789, pin="482915",
        must_change_pin=True, provider="Okta",
    )
    defaults.update(kw)
    return Handover(**defaults)


def test_default_message_contains_everything_the_user_needs():
    subject, body = handover.message(make())
    assert subject == "Your security key"
    for expected in ("Alice Example", "YubiKey 5 NFC 23456789", "23456789", "482915", "Okta",
                     "alice@example.com", "set your own PIN"):
        assert expected in body
    assert "{" not in body and "\n\n\n" not in body


def test_note_about_changing_the_pin_only_when_it_applies():
    _, body = handover.message(make(must_change_pin=False))
    assert "set your own PIN" not in body
    assert "\n\n\n" not in body  # the empty placeholder leaves no gap


def test_missing_pin_and_serial_are_worded_not_left_blank():
    _, body = handover.message(make(pin=None, serial=None, key_name=""))
    assert "Temporary PIN: (provided separately)" in body
    assert "Serial number: —" in body
    assert "Key: security key" in body


def test_custom_template_with_typos_and_braces_survives():
    h = make()
    text = handover.render("PIN {pin} for {nmae} {} {serial:>10} {{x}} 100%", h)
    assert text == "PIN 482915 for {nmae} {} {serial:>10} {{x}} 100%\n"
    subject, body = handover.message(h, "Key for {username}", "Hi {name}\nPIN: {pin}")
    assert subject == "Key for alice@example.com" and body == "Hi Alice Example\nPIN: 482915\n"


def test_polish_defaults_follow_the_language():
    try:
        i18n.set_language("pl")
        subject, body = handover.message(make())
        assert subject == "Twój klucz bezpieczeństwa"
        assert "Tymczasowy PIN: 482915" in body and "własnego PIN-u" in body
    finally:
        i18n.set_language("en")


def test_mailto_link_round_trips_through_a_mail_client():
    subject, body = "Klucz & PIN?", "Dzień dobry Żaneta,\nPIN: 482915 + #1\n100% & more"
    url = handover.mailto_url("zaneta.los@example.com", subject, body)
    parts = urlsplit(url)
    assert parts.scheme == "mailto" and parts.path == "zaneta.los@example.com"
    assert " " not in url and "\n" not in url
    query = parse_qs(parts.query, keep_blank_values=True, strict_parsing=True)
    assert query["subject"] == [subject]
    assert query["body"] == [body.replace("\n", "\r\n")]
    # '+' must not be used for spaces: mail programs would show it literally.
    assert unquote(parts.query.split("body=")[1]).startswith("Dzień dobry")
    assert "+" not in parts.query.replace("%2B", "")


def test_recipient_falls_back_to_an_email_like_username():
    assert make().recipient == "alice@example.com"
    assert make(user=DirectoryUser("1", "bob@x.com", "Bob", "")).recipient == "bob@x.com"
    assert make(user=DirectoryUser("1", "bob", "Bob", "")).recipient == ""
    assert handover.mailto_url("", "s", "b").startswith("mailto:?subject=")


def test_saved_file_is_private_and_named_after_the_user(tmp_path):
    h = make(user=DirectoryUser("1", "CORP\\alice smith", "Alice", ""))
    name = handover.default_filename(h)
    assert name == "keyenroll-CORP_alice_smith.txt"
    path = tmp_path / name
    handover.save_text(path, "Subject", "Body ż\n")
    assert path.read_text(encoding="utf-8-sig") == "Subject\n\nBody ż\n"
    if sys.platform != "win32":
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
