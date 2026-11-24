"""Who a security key belongs to, by its serial number, with any provider.

Okta can keep the serial numbers in the user profile and answers itself.
Entra ID and PingOne keep them in the names of the keys; neither can search
those across the directory, so every user's keys are read once into an index.
Where that does not find the key, the deployment log of this computer says
who it was last enrolled for, and the provider is asked whether that user
still has it.
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from .journal import last_key_owner
from .providers import DirectoryUser, Provider, ProviderError

logger = logging.getLogger(__name__)


INDEX_MAX_AGE = 15 * 60  # seconds; keys enrolled elsewhere show up after that
INDEX_WORKERS = 8


@dataclass
class KeyOwnership:
    users: list[DirectoryUser] = field(default_factory=list)
    # The provider confirms it; otherwise only this computer's log says so.
    confirmed: bool = False
    # The provider keeps serial numbers, so "nobody" is its answer too.
    provider_records: bool = False
    # Every user's keys were searched at the provider, without a match.
    searched_provider: bool = False


class KeyIndex:
    """Serial number -> users, from the names of every user's keys at the
    provider. Read once (it takes a request per user) and reused by every
    lookup until it is old; enrollments and deletions made here update it."""

    def __init__(self, provider: Provider, max_age: float = INDEX_MAX_AGE):
        self.provider = provider
        self.max_age = max_age
        self._lock = threading.Lock()
        self._owners: dict[str, list[DirectoryUser]] | None = None
        self._built = 0.0

    def owners(self, serial) -> list[DirectoryUser]:
        with self._lock:
            if self._owners is None or time.monotonic() - self._built > self.max_age:
                self._owners = self._scan()
                self._built = time.monotonic()
            return list(self._owners.get(str(serial), []))

    def add(self, serial, user: DirectoryUser) -> None:
        with self._lock:
            if self._owners is not None and serial:
                users = self._owners.setdefault(str(serial), [])
                if all(u.id != user.id for u in users):
                    users.append(user)

    def remove(self, serial, user: DirectoryUser) -> None:
        with self._lock:
            if self._owners is not None and serial:
                users = self._owners.get(str(serial), [])
                users[:] = [u for u in users if u.id != user.id]

    def forget(self) -> None:
        with self._lock:
            self._owners = None

    def _scan(self) -> dict[str, list[DirectoryUser]]:
        provider = self.provider
        users = provider.list_users()

        def keys_of(user):
            try:
                return user, provider.list_credentials(user)
            except ProviderError as e:
                logger.info("Reading the keys of %s failed: %s", user.username, e)
                return user, []

        owners: dict[str, list[DirectoryUser]] = {}
        with ThreadPoolExecutor(INDEX_WORKERS) as pool:
            for user, credentials in pool.map(keys_of, users):
                for credential in credentials:
                    if credential.serial:
                        owners.setdefault(credential.serial, []).append(user)
        logger.info("Read the keys of %d users: %d serial numbers", len(users), len(owners))
        return owners


def find_owners(
    provider: Provider,
    journal_folder: Path,
    instance: str,
    serial,
    index: KeyIndex | None = None,
) -> KeyOwnership:
    serial = str(serial)
    records = bool(getattr(provider, "records_keys", False))
    if records:
        users = provider.users_with_key(serial)
        if users:
            return KeyOwnership(users, confirmed=True, provider_records=True)
        # Keys enrolled before the attribute was set up are only in the log.
    searched = False
    if index is not None:
        users = index.owners(serial)
        if users:
            return KeyOwnership(users, confirmed=True)
        searched = True
    user = last_key_owner(journal_folder, instance, serial)
    if user is None:
        return KeyOwnership(provider_records=records, searched_provider=searched)
    if not getattr(provider, "supports_credential_list", False):
        return KeyOwnership([user], provider_records=records, searched_provider=searched)
    try:
        credentials = provider.list_credentials(user)
    except ProviderError as e:
        # The user may be gone; the log alone is not enough then.
        logger.info("Checking the log's owner of key %s failed: %s", serial, e)
        return KeyOwnership(provider_records=records, searched_provider=searched)
    if any(c.serial == serial for c in credentials):
        return KeyOwnership([user], confirmed=True, provider_records=records)
    if all(c.serial for c in credentials):
        # Every key of the user is known and this is not one of them, or the
        # user has none left: the key changed hands outside KeyEnroll.
        return KeyOwnership(provider_records=records, searched_provider=searched)
    # A key without a known serial number may be this one.
    return KeyOwnership([user], provider_records=records, searched_provider=searched)
