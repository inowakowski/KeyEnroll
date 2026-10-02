"""Storage for refresh tokens, backed by the OS credential store."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SERVICE = "KeyEnroll"

# Windows Credential Manager caps a secret at 2560 bytes (stored as UTF-16),
# which Entra ID refresh tokens exceed, so values are split across entries.
_CHUNK = 1000


class TokenStore:
    """In-memory store; base class and fallback when no OS keyring is usable."""

    persistent = False

    def __init__(self):
        self._mem: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._mem.get(key)

    def set(self, key: str, value: str) -> None:
        self._mem[key] = value

    def delete(self, key: str) -> None:
        self._mem.pop(key, None)


class KeyringTokenStore(TokenStore):
    persistent = True

    def __init__(self, backend=None):
        super().__init__()
        if backend is None:
            import keyring

            backend = keyring
        self._kr = backend

    def _count(self, key: str) -> int:
        raw = self._kr.get_password(SERVICE, f"{key}:n")
        try:
            return int(raw) if raw else 0
        except ValueError:
            return 0

    def get(self, key: str) -> str | None:
        n = self._count(key)
        if not n:
            return None
        parts = [self._kr.get_password(SERVICE, f"{key}:{i}") for i in range(n)]
        if any(p is None for p in parts):
            return None
        return "".join(parts)

    def set(self, key: str, value: str) -> None:
        old = self._count(key)
        chunks = [value[i : i + _CHUNK] for i in range(0, len(value), _CHUNK)]
        for i, chunk in enumerate(chunks):
            self._kr.set_password(SERVICE, f"{key}:{i}", chunk)
        self._kr.set_password(SERVICE, f"{key}:n", str(len(chunks)))
        for i in range(len(chunks), old):
            self._delete_entry(f"{key}:{i}")

    def delete(self, key: str) -> None:
        for i in range(self._count(key)):
            self._delete_entry(f"{key}:{i}")
        self._delete_entry(f"{key}:n")

    def _delete_entry(self, name: str) -> None:
        try:
            self._kr.delete_password(SERVICE, name)
        except Exception:  # entry already gone
            pass


def default_store() -> TokenStore:
    """Returns the OS keyring store, or an in-memory store if none works."""
    try:
        store = KeyringTokenStore()
        store._kr.get_password(SERVICE, "probe")
        return store
    except Exception as e:
        logger.warning("No usable OS keyring (%s); sign-ins will not persist", e)
        return TokenStore()
