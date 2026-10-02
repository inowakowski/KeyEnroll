"""Common identity provider interface and OAuth session handling."""

from __future__ import annotations

import base64
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Iterable

import requests

from .. import oauth
from ..i18n import N_
from ..secrets_store import TokenStore

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class AuthRequired(ProviderError):
    """No valid session; the operator has to sign in (again)."""


@dataclass
class FieldSpec:
    """One setting of a provider configuration, rendered as a form field."""

    key: str
    label: str
    required: bool = True
    default: str = ""
    placeholder: str = ""
    help: str = ""
    choices: list[tuple[str, str]] | None = None  # (value, label)


@dataclass
class DirectoryUser:
    id: str
    username: str
    display_name: str = ""
    email: str = ""


@dataclass
class Credential:
    id: str
    name: str = ""
    created: str = ""
    detail: str = ""


@dataclass
class Registration:
    """A pending WebAuthn registration ceremony.

    ``options`` is a PublicKeyCredentialCreationOptions dict in the WebAuthn
    JSON form (binary values base64url encoded without padding).
    """

    options: dict[str, Any]
    origin: str
    state: dict[str, Any] = field(default_factory=dict)


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode()


def to_b64url(value: Any) -> str:
    """Normalizes a binary value sent as base64/base64url text or a byte array.

    Byte arrays may use signed values (Java/JS Int8Array serialization).
    """
    if isinstance(value, str):
        return value.replace("+", "-").replace("/", "_").rstrip("=")
    if isinstance(value, (bytes, bytearray)):
        return b64url_encode(bytes(value))
    if isinstance(value, Iterable):
        return b64url_encode(bytes(int(b) & 0xFF for b in value))
    raise ProviderError(f"Unsupported binary value: {value!r}")


def clean_host(value: str) -> str:
    """Accepts 'https://host/path' or 'host' and returns the bare host."""
    value = value.strip()
    if "://" in value:
        value = value.split("://", 1)[1]
    return value.split("/", 1)[0].strip().lower()


class Provider:
    kind: ClassVar[str]
    label: ClassVar[str]
    fields: ClassVar[list[FieldSpec]]
    supports_credential_list: ClassVar[bool] = True
    supports_credential_delete: ClassVar[bool] = True
    max_display_name: ClassVar[int | None] = None  # limit for credential names

    def __init__(
        self,
        instance_id: str,
        settings: dict[str, str],
        token_store: TokenStore,
        http: requests.Session | None = None,
    ):
        self.instance_id = instance_id
        self.settings = {
            f.key: (settings.get(f.key) or f.default).strip() for f in self.fields
        }
        self._store = token_store
        self._http = http or requests.Session()
        self._tokens: oauth.TokenSet | None = None
        self._lock = threading.RLock()

    # -- configuration -----------------------------------------------------

    @classmethod
    def missing_settings(cls, settings: dict[str, str]) -> list[FieldSpec]:
        return [
            f
            for f in cls.fields
            if f.required and not (settings.get(f.key) or f.default).strip()
        ]

    def oauth_config(self) -> oauth.OAuthConfig:
        raise NotImplementedError

    # -- session -----------------------------------------------------------

    def login(
        self,
        open_browser: Callable[[str], None],
        cancel: threading.Event | None = None,
    ) -> None:
        tokens = oauth.authorize(
            self.oauth_config(), open_browser, cancel, http=self._http
        )
        self._set_tokens(tokens)

    def _set_tokens(self, tokens: oauth.TokenSet) -> None:
        with self._lock:
            self._tokens = tokens
            if tokens.refresh_token:
                self._store.set(self.instance_id, tokens.refresh_token)

    def has_session(self) -> bool:
        """Cheap check without network access."""
        with self._lock:
            if self._tokens and self._tokens.expires_at > time.time():
                return True
            return self._store.get(self.instance_id) is not None

    def logout(self) -> None:
        with self._lock:
            refresh_token = self._store.get(self.instance_id)
            if refresh_token:
                oauth.revoke(self.oauth_config(), refresh_token, self._http)
            self._store.delete(self.instance_id)
            self._tokens = None

    def access_token(self, force_refresh: bool = False) -> str:
        with self._lock:
            tokens = self._tokens
            if tokens and not force_refresh and tokens.expires_at - 60 > time.time():
                return tokens.access_token
            refresh_token = (tokens and tokens.refresh_token) or self._store.get(
                self.instance_id
            )
            if not refresh_token:
                self._tokens = None
                raise AuthRequired(N_("Not signed in. Sign in to the identity provider first."))
            try:
                new = oauth.refresh(self.oauth_config(), refresh_token, self._http)
            except oauth.OAuthError as e:
                logger.info("Token refresh failed: %s", e)
                self._tokens = None
                self._store.delete(self.instance_id)
                raise AuthRequired(
                    N_("The session has expired. Sign in to the identity provider again.")
                ) from e
            self._set_tokens(new)
            return new.access_token

    # -- HTTP --------------------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json: Any = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        ok: tuple[int, ...] = (200, 201, 202, 204),
        retry_auth: bool = True,
    ) -> requests.Response:
        hdrs = {"Accept": "application/json", **(headers or {})}
        resp = None
        for attempt in (0, 1) if retry_auth else (0,):
            hdrs["Authorization"] = f"Bearer {self.access_token(force_refresh=attempt == 1)}"
            try:
                resp = self._http.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    data=data,
                    headers=hdrs,
                    timeout=oauth.HTTP_TIMEOUT,
                )
            except requests.RequestException as e:
                raise ProviderError(f"{self.label}: {e}") from e
            if resp.status_code != 401:
                break
        assert resp is not None
        if resp.status_code not in ok:
            raise ProviderError(
                f"{self.label}: {self._error_message(resp)}", resp.status_code
            )
        return resp

    def _error_message(self, resp: requests.Response) -> str:
        try:
            body = resp.json()
        except ValueError:
            body = None
        detail = self._error_detail(body) if isinstance(body, dict) else None
        return f"HTTP {resp.status_code}" + (f" – {detail}" if detail else "")

    def _error_detail(self, body: dict) -> str | None:
        return body.get("message") or body.get("error_description") or body.get("error")

    # -- directory and credentials ----------------------------------------

    def search_users(self, query: str) -> list[DirectoryUser]:
        raise NotImplementedError

    def find_user(self, identifier: str) -> DirectoryUser | None:
        """Exact lookup by username, e-mail or ID, for imported user lists."""
        wanted = identifier.strip().lower()
        for user in self.search_users(identifier):
            if wanted in (user.username.lower(), user.email.lower(), user.id.lower()):
                return user
        return None

    def preflight(self, user: DirectoryUser) -> None:
        """Verifies, without side effects, that enrollment can be attempted."""
        self.access_token()

    def begin_registration(self, user: DirectoryUser) -> Registration:
        raise NotImplementedError

    def complete_registration(
        self, registration: Registration, response, display_name: str
    ) -> None:
        """``response`` is a fido2.webauthn.RegistrationResponse."""
        raise NotImplementedError

    def cancel_registration(self, registration: Registration) -> None:
        """Cleans up server-side state of a ceremony that was not completed."""

    def list_credentials(self, user: DirectoryUser) -> list[Credential]:
        raise NotImplementedError

    def delete_credential(self, user: DirectoryUser, credential_id: str) -> None:
        raise NotImplementedError
