"""Who a security key belongs to, by its serial number, with any provider.

Okta can keep the serial numbers in the user profile and answers itself. For
every other case the deployment log of this computer says who the key was
last enrolled for, and the provider is asked whether that user still has it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from .journal import last_key_owner
from .providers import DirectoryUser, Provider, ProviderError

logger = logging.getLogger(__name__)


@dataclass
class KeyOwnership:
    users: list[DirectoryUser] = field(default_factory=list)
    # The provider confirms it; otherwise only this computer's log says so.
    confirmed: bool = False
    # The provider keeps serial numbers, so "nobody" is its answer too.
    provider_records: bool = False


def find_owners(
    provider: Provider, journal_folder: Path, instance: str, serial
) -> KeyOwnership:
    serial = str(serial)
    records = bool(getattr(provider, "records_keys", False))
    if records:
        users = provider.users_with_key(serial)
        if users:
            return KeyOwnership(users, confirmed=True, provider_records=True)
        # Keys enrolled before the attribute was set up are only in the log.
    user = last_key_owner(journal_folder, instance, serial)
    if user is None:
        return KeyOwnership(provider_records=records)
    if not getattr(provider, "supports_credential_list", False):
        return KeyOwnership([user], provider_records=records)
    try:
        credentials = provider.list_credentials(user)
    except ProviderError as e:
        # The user may be gone; the log alone is not enough then.
        logger.info("Checking the log's owner of key %s failed: %s", serial, e)
        return KeyOwnership(provider_records=records)
    if any(c.serial == serial for c in credentials):
        return KeyOwnership([user], confirmed=True, provider_records=records)
    if all(c.serial for c in credentials):
        # Every key of the user is known and this is not one of them, or the
        # user has none left: the key changed hands outside KeyEnroll.
        return KeyOwnership(provider_records=records)
    # A key without a known serial number may be this one.
    return KeyOwnership([user], provider_records=records)
