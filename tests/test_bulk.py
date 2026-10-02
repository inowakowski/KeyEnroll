from __future__ import annotations

import csv
import io
import os
import stat
import sys
import threading

import pytest

from fake_authenticator import FakeAuthenticator
from keyenroll import bulk, i18n
from keyenroll.bulk import BulkRow, BulkRunner, parse_identifiers
from keyenroll.config import Profile
from keyenroll.fido import enroll
from keyenroll.fido.enroll import EnrollCancelled, EnrollError
from keyenroll.providers.base import AuthRequired, DirectoryUser, ProviderError
from test_enroll import FakeProvider, FakeSource, FakeUI


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch):
    monkeypatch.setattr(enroll, "POLL_INTERVAL", 0.01)


# -- import -----------------------------------------------------------------


def test_plain_list_one_user_per_line():
    text = "alice@x.com\n\n  bob@x.com  \n# a comment\nALICE@x.com\ncarol\n"
    assert parse_identifiers(text) == ["alice@x.com", "bob@x.com", "carol"]


def test_csv_with_named_user_column():
    text = "Name;Department;UserPrincipalName\nAlice A;IT;alice@x.com\nBob B;HR;bob@x.com\n"
    assert parse_identifiers(text) == ["alice@x.com", "bob@x.com"]


def test_csv_without_header_uses_first_column():
    text = 'alice@x.com,"Example, Alice"\nbob@x.com,Bob\n'
    assert parse_identifiers(text) == ["alice@x.com", "bob@x.com"]


def test_polish_header_and_tabs():
    text = "Nazwa użytkownika\tDział\nala@x.pl\tIT\n"
    assert parse_identifiers(text) == ["ala@x.pl"]


def test_empty_and_short_rows():
    assert parse_identifiers("") == []
    assert parse_identifiers("# nothing\n\n") == []
    assert parse_identifiers("name;login\nAlice\nBob;bob\n") == ["bob"]


def test_file_encodings(tmp_path):
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "cp1250"):
        path = tmp_path / f"{encoding}.csv"
        path.write_bytes("login\nżaneta.łoś@x.pl\n".encode(encoding))
        assert bulk.read_identifiers(path) == ["żaneta.łoś@x.pl"], encoding


# -- lookup -----------------------------------------------------------------


class Directory:
    def __init__(self, users):
        self.users = {u.username: u for u in users}
        self.fail = set()

    def find_user(self, identifier):
        if identifier in self.fail:
            raise ProviderError("Fake: HTTP 500")
        return self.users.get(identifier)


def users(*names):
    return [DirectoryUser(f"id-{n}", f"{n}@x.com", n.title(), f"{n}@x.com") for n in names]


def test_resolve_marks_ready_not_found_and_failed():
    directory = Directory(users("alice", "bob"))
    directory.fail.add("broken@x.com")
    rows = [BulkRow(i) for i in ("alice@x.com", "ghost@x.com", "broken@x.com", "bob@x.com")]
    changed = []

    bulk.resolve_rows(directory, rows, changed.append)

    assert [r.status for r in rows] == [bulk.READY, bulk.NOT_FOUND, bulk.FAILED, bulk.READY]
    assert rows[0].user.display_name == "Alice" and "500" in rows[2].message
    assert changed == [0, 1, 2, 3]


def test_resolve_stops_on_expired_session_and_on_cancel():
    class Expired:
        def find_user(self, identifier):
            raise AuthRequired("Not signed in. Sign in to the identity provider first.")

    rows = [BulkRow("a"), BulkRow("b")]
    with pytest.raises(AuthRequired):
        bulk.resolve_rows(Expired(), rows, lambda i: None)
    assert [r.status for r in rows] == [bulk.NEW, bulk.NEW]

    cancel = threading.Event()
    cancel.set()
    bulk.resolve_rows(Directory([]), rows, lambda i: None, cancel)
    assert [r.status for r in rows] == [bulk.NEW, bulk.NEW]


# -- batch run --------------------------------------------------------------


class Operator(FakeUI):
    """Swaps keys on request: takes the next key from the pile each time the
    app asks for one, removes it when told to."""

    def __init__(self, source, pile):
        super().__init__(source)
        self.pile = list(pile)
        self.changed: list[int] = []

    def row_changed(self, index):
        self.changed.append(index)

    def status(self, template, **params):
        self.messages.append(template.format(**params) if params else template)
        if template.startswith("Remove the previous key"):
            self.source.devices = []
        elif template.startswith("Insert the security key for"):
            key = self.pile.pop(0)
            key.fresh = True
            self.source.devices = [key]
        elif "remove the security key" in template:
            self.source.present = False
        elif "insert the security key" in template:
            self.source.present = True
            for dev in self.source.devices:
                dev.fresh = True


def make_keys(count):
    keys = []
    for n in range(count):
        key = FakeAuthenticator(f"key{n}")
        key.serial = 1000 + n
        keys.append(key)
    return keys


def ready_rows(*names):
    return [BulkRow(u.username, user=u, status=bulk.READY) for u in users(*names)]


def runner(rows, pile, provider=None, profile=None, **kw):
    source = FakeSource()
    ui = Operator(source, pile)
    provider = provider or FakeProvider()
    r = BulkRunner(provider, profile or Profile(), rows, "Corp key", True, ui, source=source, **kw)
    return r, ui, provider, source


def test_batch_enrolls_one_key_per_user():
    keys = make_keys(3)
    rows = ready_rows("alice", "bob", "carol")
    r, ui, provider, source = runner(rows, keys)

    r.run()

    assert [row.status for row in rows] == [bulk.DONE] * 3
    assert [row.serial for row in rows] == [1000, 1001, 1002]
    assert [row.key_name for row in rows] == ["Corp key 1000", "Corp key 1001", "Corp key 1002"]
    for row, key in zip(rows, keys, strict=True):
        assert row.pin == key.pin and len(row.pin) == 6
        assert len(key.credentials) == 1
        assert key.credentials[0]["user"]["id"] == row.user.id.encode()
        assert row.finished
    assert len({row.pin for row in rows}) == 3
    # Freshly inserted keys are reset without asking for a re-insertion.
    assert not any("remove the security key now" in m for m in ui.messages)
    assert sum(m.startswith("Remove the previous key") for m in ui.messages) == 2
    assert ui.messages[-1] == "Batch finished."


def test_rows_not_ready_are_skipped():
    keys = make_keys(1)
    rows = ready_rows("alice", "bob", "carol")
    rows[0].status = bulk.NOT_FOUND
    rows[2].status = bulk.DONE
    rows[2].serial = 999
    r, ui, provider, source = runner(rows, keys)

    r.run()

    assert [row.status for row in rows] == [bulk.NOT_FOUND, bulk.DONE, bulk.DONE]
    assert rows[1].serial == 1000
    # A key was already processed in this batch: the operator must swap first.
    assert ui.messages[0].startswith("Remove the previous key")


def test_same_key_is_never_enrolled_for_two_users():
    key = make_keys(1)[0]
    rows = ready_rows("alice", "bob")
    r, ui, provider, source = runner(rows, [key, key])  # operator re-inserts Alice's key

    with pytest.raises(EnrollError, match="already enrolled in this batch"):
        r.run()

    assert [row.status for row in rows] == [bulk.DONE, bulk.FAILED]
    assert key.pin == rows[0].pin  # Alice's key was not reset again
    assert key.log.count("reset") == 1 and len(key.credentials) == 1
    assert "1000" in rows[1].message_text


def test_failure_pauses_the_batch_and_can_be_resumed():
    keys = make_keys(3)
    rows = ready_rows("alice", "bob", "carol")

    class Flaky(FakeProvider):
        def begin_registration(self, user):
            if user.username == "bob@x.com" and "retry" not in self.events:
                raise ProviderError("Fake: HTTP 403 – policy")
            return super().begin_registration(user)

    provider = Flaky()
    r, ui, provider, source = runner(rows, keys, provider=provider)
    with pytest.raises(ProviderError):
        r.run()
    assert [row.status for row in rows] == [bulk.DONE, bulk.FAILED, bulk.READY]
    assert "403" in rows[1].message

    # The operator retries Bob with a new key, then the batch goes on.
    provider.events.append("retry")
    rows[1].status = bulk.READY
    spare = make_keys(4)[3]
    r2 = BulkRunner(provider, Profile(), rows, "Corp key", True, ui, source=source)
    ui.pile = [spare, keys[2]]
    r2.run()

    assert [row.status for row in rows] == [bulk.DONE] * 3
    assert [row.serial for row in rows] == [1000, 1003, 1002]
    assert rows[1].message == ""


def test_cancel_returns_the_row_to_ready():
    rows = ready_rows("alice")
    cancel = threading.Event()
    r, ui, provider, source = runner(rows, [], cancel=cancel)

    def status(template, **params):
        ui.messages.append(template)
        cancel.set()

    ui.status = status
    with pytest.raises(EnrollCancelled):
        r.run()
    assert rows[0].status == bulk.READY


def test_several_connected_keys_are_refused():
    rows = ready_rows("alice")
    r, ui, provider, source = runner(rows, [])
    source.devices = make_keys(2)
    with pytest.raises(EnrollError, match="Several security keys"):
        r.run()
    assert all("reset" not in k.log for k in source.devices)


def test_key_already_inserted_is_used_for_the_first_user():
    key = make_keys(1)[0]
    rows = ready_rows("alice")
    r, ui, provider, source = runner(rows, [])
    source.devices = [key]

    r.run()

    assert rows[0].status == bulk.DONE and rows[0].serial == 1000
    # It was not freshly inserted, so the reset needed a re-insertion.
    assert any("remove the security key now" in m for m in ui.messages)


# -- export -----------------------------------------------------------------


def finished_rows():
    rows = ready_rows("alice", "bob")
    rows[0].status, rows[0].serial, rows[0].pin = bulk.DONE, 1000, "482915"
    rows[0].key_name, rows[0].finished = "Corp key 1000", "2026-10-02 12:00:00"
    rows[1].status, rows[1].message = bulk.FAILED, "The key was not touched in time."
    rows.append(BulkRow("ghost@x.com", status=bulk.NOT_FOUND))
    return rows


def test_results_csv_contains_pins_serials_and_statuses():
    text = bulk.results_csv(finished_rows(), ";")
    table = list(csv.reader(io.StringIO(text), delimiter=";"))
    assert table[0][:7] == [
        "Username", "Display name", "E-mail", "Status", "Serial number", "Key name", "Temporary PIN"
    ]
    assert table[1][:8] == [
        "alice@x.com", "Alice", "alice@x.com", "Enrolled", "1000", "Corp key 1000", "482915",
        "2026-10-02 12:00:00",
    ]
    assert table[2][3] == "Failed" and table[2][6] == "" and "not touched" in table[2][8]
    assert table[3][0] == "ghost@x.com" and table[3][3] == "Not found"


def test_spreadsheet_formulas_are_neutralised():
    rows = [BulkRow("x", user=DirectoryUser("1", "=cmd|' /C calc'!A0", "+SUM(A1)", "@x"), status=bulk.READY)]
    table = list(csv.reader(io.StringIO(bulk.results_csv(rows))))
    assert table[1][0].startswith("'=") and table[1][1].startswith("'+") and table[1][2] == "'@x"


def test_written_file_opens_in_excel_and_is_private(tmp_path):
    path = tmp_path / "results.csv"
    path.write_text("old content that must be replaced entirely, longer than the new one" * 20)
    bulk.write_results(path, finished_rows(), ";")
    data = path.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")  # BOM so Excel reads UTF-8
    assert b"482915" in data and b"old content" not in data
    fresh = tmp_path / "fresh.csv"
    bulk.write_results(fresh, finished_rows())
    if sys.platform != "win32":
        assert stat.S_IMODE(os.stat(fresh).st_mode) == 0o600


def test_export_of_enrolled_users_only():
    table = list(csv.reader(io.StringIO(bulk.results_csv(finished_rows(), enrolled_only=True))))
    assert len(table) == 2 and table[1][0] == "alice@x.com" and table[1][6] == "482915"


def test_export_without_pins_drops_the_column_entirely():
    text = bulk.results_csv(finished_rows(), ";", include_pins=False)
    table = list(csv.reader(io.StringIO(text), delimiter=";"))
    assert "Temporary PIN" not in table[0] and len(table[0]) == 8
    assert "482915" not in text
    assert table[1][:6] == ["alice@x.com", "Alice", "alice@x.com", "Enrolled", "1000", "Corp key 1000"]
    assert all(len(row) == 8 for row in table)


@pytest.mark.parametrize("lang", sorted(i18n.LANGUAGES))
def test_exported_list_can_be_loaded_again_in_every_language(lang):
    try:
        i18n.set_language(lang)
        text = bulk.results_csv(finished_rows(), ";")
        header = text.splitlines()[0].split(";")
        assert header[0] == i18n.tr("Username") and len(set(header)) == len(header)
        # The translated header is recognised, not taken for a user.
        assert parse_identifiers(text) == ["alice@x.com", "bob@x.com", "ghost@x.com"]
    finally:
        i18n.set_language("en")


def test_forced_pin_change_is_recorded_for_the_hand_over():
    keys = make_keys(1)
    rows = ready_rows("alice")
    r, ui, provider, source = runner(rows, keys, profile=Profile(force_pin_change=True))
    r.run()
    assert rows[0].must_change_pin is True
