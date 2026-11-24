"""Who a key belongs to, with any identity provider."""

from __future__ import annotations

import pytest

from keyenroll.fido.devices import KeyInfo
from keyenroll.fido.enroll import EnrollResult
from keyenroll.journal import Journal, JournalContext, last_key_owner, safe_cell
from keyenroll.key_lookup import find_owners
from keyenroll.providers.base import Credential, DirectoryUser, ProviderError

ALICE = DirectoryUser("u1", "alice@x", "Alice Example")
BOB = DirectoryUser("u2", "bob@x", "Bob Example")


def enrolled(folder, user, serial, instance="Prod"):
    log = Journal(folder, JournalContext(instance=instance, provider="Entra ID"))
    key = KeyInfo(key="usb:1", transport="usb", name="YubiKey", serial=serial)
    assert log.enrolled(EnrollResult(user=user, key=key, display_name=f"YubiKey {serial}"))


def deleted(folder, user, serial, instance="Prod"):
    log = Journal(folder, JournalContext(instance=instance, provider="Entra ID"))
    assert log.deleted(user, Credential("c1", f"YubiKey {serial}", serial=str(serial)))


class Provider:
    supports_credential_list = True
    records_keys = False

    def __init__(self, credentials=None, owners=(), fail=False):
        self.credentials = credentials or {}
        self.owners = list(owners)
        self.fail = fail

    def users_with_key(self, serial):
        return self.owners

    def list_credentials(self, user):
        if self.fail:
            raise ProviderError("HTTP 404 – user not found", 404)
        return self.credentials.get(user.id, [])


def test_the_latest_enrollment_of_a_key_names_its_owner(tmp_path):
    enrolled(tmp_path, ALICE, 32445513)
    enrolled(tmp_path, BOB, 32445513)  # reset and handed to Bob
    enrolled(tmp_path, ALICE, 11111111, instance="Lab")
    assert last_key_owner(tmp_path, "Prod", 32445513).id == "u2"
    assert last_key_owner(tmp_path, "Lab", 32445513) is None  # another tenant
    assert last_key_owner(tmp_path, "Prod", 99999999) is None
    assert last_key_owner(tmp_path / "missing", "Prod", 32445513) is None


def test_a_key_deleted_in_keyenroll_has_no_owner_any_more(tmp_path):
    enrolled(tmp_path, ALICE, 32445513)
    deleted(tmp_path, ALICE, 32445513)
    assert last_key_owner(tmp_path, "Prod", 32445513) is None


def test_names_written_as_safe_cells_are_read_back(tmp_path):
    odd = DirectoryUser("u3", "-dash@x", "=Formula Name")
    enrolled(tmp_path, odd, 32445513)
    assert safe_cell("=Formula Name") == "'=Formula Name"
    owner = last_key_owner(tmp_path, "Prod", 32445513)
    assert (owner.username, owner.display_name) == ("-dash@x", "=Formula Name")


def test_the_provider_confirms_the_log_by_the_serial_in_the_key_name(tmp_path):
    enrolled(tmp_path, ALICE, 32445513)
    provider = Provider({"u1": [Credential("m1", "YubiKey 32445513", serial="32445513")]})
    found = find_owners(provider, tmp_path, "Prod", 32445513)
    assert [u.id for u in found.users] == ["u1"] and found.confirmed


def test_the_log_alone_is_reported_as_such(tmp_path):
    enrolled(tmp_path, ALICE, 32445513)
    provider = Provider({"u1": [Credential("m1", "YubiKey 5 NFC")]})  # no serial in the name
    found = find_owners(provider, tmp_path, "Prod", 32445513)
    assert [u.id for u in found.users] == ["u1"] and not found.confirmed


@pytest.mark.parametrize(
    "credentials",
    [
        [],  # the user has no key left
        [Credential("m2", "YubiKey 22222222", serial="22222222")],  # only other keys
    ],
)
def test_a_key_the_user_no_longer_has_is_not_suggested(tmp_path, credentials):
    enrolled(tmp_path, ALICE, 32445513)
    found = find_owners(Provider({"u1": credentials}), tmp_path, "Prod", 32445513)
    assert found.users == []


def test_a_user_the_provider_no_longer_knows_is_not_suggested(tmp_path):
    enrolled(tmp_path, ALICE, 32445513)
    assert find_owners(Provider(fail=True), tmp_path, "Prod", 32445513).users == []


def test_providers_without_a_credential_list_trust_the_log(tmp_path):
    enrolled(tmp_path, ALICE, 32445513)
    provider = Provider()
    provider.supports_credential_list = False
    found = find_owners(provider, tmp_path, "Prod", 32445513)
    assert [u.id for u in found.users] == ["u1"] and not found.confirmed


def test_okta_answers_itself_and_falls_back_to_the_log(tmp_path):
    okta = Provider(owners=[BOB])
    okta.records_keys = True
    found = find_owners(okta, tmp_path, "Prod", 32445513)
    assert found.users == [BOB] and found.confirmed and found.provider_records

    # A key enrolled before the profile attribute existed: Okta lists it
    # without a serial number, next to a newer key that has one.
    okta.owners = []
    okta.credentials = {
        "u1": [Credential("f1", "YubiKey 5 Series"), Credential("f2", "", serial="22222222")]
    }
    enrolled(tmp_path, ALICE, 32445513)
    found = find_owners(okta, tmp_path, "Prod", 32445513)
    assert [u.id for u in found.users] == ["u1"]

    unknown = find_owners(okta, tmp_path, "Prod", 1234567)
    assert unknown.users == [] and unknown.provider_records


# -- serial numbers in the key names (Entra ID, PingOne) -----------------------


class Directory(Provider):
    serials_in_key_names = True

    def __init__(self, credentials, fail_for=()):
        super().__init__(credentials)
        self.fail_for = set(fail_for)
        self.listed = 0
        self.read = []

    def list_users(self):
        self.listed += 1
        return [ALICE, BOB]

    def list_credentials(self, user):
        self.read.append(user.id)
        if user.id in self.fail_for:
            raise ProviderError("HTTP 403 – forbidden", 403)
        return super().list_credentials(user)


def test_the_index_finds_a_key_enrolled_anywhere(tmp_path):
    from keyenroll.key_lookup import KeyIndex

    provider = Directory({
        "u1": [Credential("m1", "YubiKey 5 NFC")],
        "u2": [Credential("m2", "Serial: 23851693", serial="23851693")],
    })  # fmt: skip
    index = KeyIndex(provider)
    found = find_owners(provider, tmp_path, "Prod", 23851693, index)  # nothing in the log
    assert found.users == [BOB] and found.confirmed

    # Read once, then reused.
    assert find_owners(provider, tmp_path, "Prod", 11111111, index).searched_provider
    assert provider.listed == 1 and sorted(provider.read) == ["u1", "u2"]


def test_the_index_is_read_again_when_old_and_follows_changes_made_here(tmp_path):
    from keyenroll.key_lookup import KeyIndex

    provider = Directory({"u2": [Credential("m2", "YubiKey 23851693", serial="23851693")]})
    index = KeyIndex(provider, max_age=3600)
    assert index.owners(23851693) == [BOB]
    index.remove(23851693, BOB)  # deleted on the Credentials page
    index.add(32445513, ALICE)  # enrolled on the Enroll page
    assert index.owners(23851693) == [] and index.owners(32445513) == [ALICE]
    assert provider.listed == 1

    index.max_age = -1  # too old now
    assert index.owners(23851693) == [BOB]
    assert provider.listed == 2


def test_a_user_whose_keys_cannot_be_read_does_not_stop_the_index(tmp_path):
    from keyenroll.key_lookup import KeyIndex

    provider = Directory(
        {"u2": [Credential("m2", "YubiKey 23851693", serial="23851693")]}, fail_for={"u1"}
    )
    assert KeyIndex(provider).owners(23851693) == [BOB]


def test_the_log_still_helps_when_the_name_has_no_serial(tmp_path):
    from keyenroll.key_lookup import KeyIndex

    provider = Directory({"u1": [Credential("m1", "Alice's key")]})
    enrolled(tmp_path, ALICE, 32445513)
    found = find_owners(provider, tmp_path, "Prod", 32445513, KeyIndex(provider))
    assert found.users == [ALICE] and not found.confirmed
