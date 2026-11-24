"""Configuration lock codes of the profiles.

A lock code keeps the user of a key from enabling applications the
administrator switched off. It is 16 random bytes, kept in the OS credential
store (never in the configuration file, never exported), under an ID the
profile carries. Without it the locked keys can no longer be changed, so the
administrator should also keep a copy in a password manager.
"""

from __future__ import annotations

import os
import re
import uuid

from .config import Profile
from .fido.management import CLEAR_LOCK, LOCK_CODE_LENGTH
from .secrets_store import TokenStore

_PREFIX = "lock-code:"
_HEX = re.compile(r"^[0-9a-fA-F]{32}$")


def generate() -> bytes:
    while True:
        code = os.urandom(LOCK_CODE_LENGTH)
        if code != CLEAR_LOCK:
            return code


def parse(text: str) -> bytes | None:
    """A code typed or pasted as 32 hex digits, spaces and dashes allowed."""
    cleaned = re.sub(r"[\s:-]", "", text)
    if not _HEX.match(cleaned):
        return None
    code = bytes.fromhex(cleaned)
    return None if code == CLEAR_LOCK else code


def to_text(code: bytes) -> str:
    return code.hex()


def get(store: TokenStore, profile: Profile) -> bytes | None:
    if not profile.lock_code_id:
        return None
    value = store.get(_PREFIX + profile.lock_code_id)
    return parse(value) if value else None


def put(store: TokenStore, profile: Profile, code: bytes) -> None:
    """Stores the code for the profile; the caller saves the profile."""
    if not profile.lock_code_id:
        profile.lock_code_id = uuid.uuid4().hex
    store.set(_PREFIX + profile.lock_code_id, to_text(code))


def forget(store: TokenStore, profile: Profile) -> None:
    if profile.lock_code_id:
        store.delete(_PREFIX + profile.lock_code_id)
    profile.lock_code_id = ""
