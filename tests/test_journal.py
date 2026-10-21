from __future__ import annotations

import base64
import csv
import json
import os
import sys
from datetime import datetime, timezone

import pytest

from fake_authenticator import FakeAuthenticator
from keyenroll import bulk, journal, oauth
from keyenroll.bulk import BulkRow, BulkRunner
from keyenroll.config import Profile
from keyenroll.fido import enroll
from keyenroll.fido.devices import KeyInfo
from keyenroll.fido.enroll import EnrollError, EnrollResult
from keyenroll.journal import FIELDS, Journal, JournalContext
from keyenroll.providers.base import DirectoryUser
from test_enroll import FakeProvider, FakeSource

USER = DirectoryUser("u1", "alice@example.com", "Alice Example", "alice@example.com")
KEY = KeyInfo(
    key="usb:1", transport="usb", name="YubiKey 5 NFC", serial=23456789,
    firmware="5.7.1", aaguid="cb69481e-8ff7-4039-93ec-0a2729a154a8",
)  # fmt: skip


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(enroll, "POLL_INTERVAL", 0.01)


def read(folder):
    files = sorted(folder.glob("deployments-*.csv"))
    assert len(files) == 1
    raw = files[0].read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf") and raw.count(b"\xef\xbb\xbf") == 1
    return files[0], list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))


def make_journal(folder, **context):
    return Journal(
        folder,
        JournalContext(
            instance=context.get("instance", "Prod"),
            provider="Microsoft Entra ID",
            operator="admin@example.com",
            profile="default",
            mode=context.get("mode", "single"),
        ),
    )


def test_enrollments_and_failures_are_appended_without_the_pin(tmp_path):
    log = make_journal(tmp_path)
    result = EnrollResult(
        user=USER, key=KEY, pin="482913", pin_changed=True, display_name="YubiKey 23456789",
        warnings=[("The firmware {x} is odd.", {"x": "5.7.1"})],
    )  # fmt: skip

    assert log.enrolled(result)
    assert log.failed(USER, KEY, EnrollError("The key was not touched in time."))

    path, rows = read(tmp_path)
    assert list(rows[0]) == list(FIELDS)
    assert rows[0]["result"] == "enrolled" and rows[1]["result"] == "failed"
    assert rows[0]["operator"] == "admin@example.com"
    assert rows[0]["serial"] == "23456789" and rows[0]["aaguid"] == KEY.aaguid
    assert rows[0]["key_name"] == "YubiKey 23456789" and rows[0]["pin_changed"] == "yes"
    assert rows[0]["message"] == "The firmware 5.7.1 is odd."
    assert rows[1]["message"] == "The key was not touched in time."
    assert "482913" not in path.read_text(encoding="utf-8-sig")
    assert path.name == f"deployments-{datetime.now(timezone.utc):%Y-%m}.csv"
    if sys.platform != "win32":
        assert os.stat(path).st_mode & 0o777 == 0o600


def test_cells_cannot_become_spreadsheet_formulas(tmp_path):
    user = DirectoryUser("u2", "=HYPERLINK(1)", "+Mallory", "")
    make_journal(tmp_path).failed(user, None, RuntimeError("@boom"))
    _, rows = read(tmp_path)
    assert rows[0]["username"] == "'=HYPERLINK(1)"
    assert rows[0]["display_name"] == "'+Mallory"


def test_a_disabled_or_unwritable_log_never_breaks_an_enrollment(tmp_path):
    log = Journal(tmp_path, JournalContext("Prod", "Okta"), enabled=False)
    assert not log.failed(USER, None, RuntimeError("x"))
    assert list(tmp_path.iterdir()) == []

    blocked = tmp_path / "file"
    blocked.write_text("not a folder")
    assert not Journal(blocked / "journal", JournalContext("Prod", "Okta")).failed(
        USER, None, RuntimeError("x")
    )


def test_old_months_are_deleted(tmp_path):
    for name in ("deployments-2025-09.csv", "deployments-2025-10.csv",
                 "deployments-2026-10.csv", "notes.txt"):  # fmt: skip
        (tmp_path / name).write_text("x")

    removed = journal.prune(tmp_path, 12, today=datetime(2026, 10, 20, tzinfo=timezone.utc))

    assert [p.name for p in removed] == ["deployments-2025-09.csv"]
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "deployments-2025-10.csv", "deployments-2026-10.csv", "notes.txt"
    ]  # fmt: skip
    assert journal.prune(tmp_path / "missing", 12) == []


def _id_token(claims: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"eyJhbGciOiJub25lIn0.{body}.signature"


def test_the_operator_is_read_from_the_id_token():
    assert oauth.signed_in_as(_id_token({"preferred_username": "admin@x", "sub": "1"})) == "admin@x"
    assert oauth.signed_in_as(_id_token({"sub": "00u1"})) == "00u1"
    assert oauth.signed_in_as("not a token") == ""
    assert oauth.signed_in_as(None) == ""


def test_the_operator_survives_a_refresh_without_an_id_token(http, store):
    from keyenroll.providers.okta import OktaProvider

    p = OktaProvider("i1", {"domain": "x.okta.com", "client_id": "c"}, store, http)
    p._set_tokens(oauth.TokenSet("A", 9e9, "R", _id_token({"preferred_username": "admin@x"})))
    p._set_tokens(oauth.TokenSet("B", 9e9, "R"))
    assert p.operator == "admin@x"


def test_bulk_runner_logs_each_user(tmp_path):
    key = FakeAuthenticator()
    key.serial = 111
    key.fresh = True
    source = FakeSource(key)
    rows = [BulkRow("alice@example.com", user=USER, status=bulk.READY)]

    class UI:
        def status(self, template, **params):
            pass

        def row_changed(self, index):
            pass

        def ask_current_pin(self, retries, wrong):
            return None

        def ask_new_pin(self, min_length, rejected):
            return None

    log = make_journal(tmp_path, mode="bulk")
    BulkRunner(FakeProvider(), Profile(), rows, "Key", True, UI(), source=source, journal=log).run()

    _, entries = read(tmp_path)
    assert [(e["result"], e["mode"], e["serial"]) for e in entries] == [("enrolled", "bulk", "111")]
    assert rows[0].pin and rows[0].pin not in str(entries)
