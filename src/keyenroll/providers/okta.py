"""Okta, using the User Factors API (factorType webauthn)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote

from .. import oauth
from ..i18n import N_
from .base import (
    GROUPS_FIELD,
    Credential,
    DirectoryGroup,
    DirectoryUser,
    FieldSpec,
    Provider,
    ProviderError,
    ProviderNotice,
    Registration,
    b64_encode,
    b64url_decode,
    b64url_encode,
    clean_host,
    to_b64url,
)

logger = logging.getLogger(__name__)

# One entry per security key in the profile attribute, readable in the admin
# console: "32445513 · 2026-11-24 10:41 UTC · fwf1k3xwer1B09yTH358".
ENTRY_SEPARATOR = " · "
UNKNOWN_SERIAL = "unknown"
_ATTRIBUTE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_OKTA_ID = re.compile(r"^[A-Za-z0-9]{20}$")


def key_entry(serial: int | None, factor_id: str, when: datetime) -> str:
    stamp = when.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return ENTRY_SEPARATOR.join((str(serial) if serial else UNKNOWN_SERIAL, stamp, factor_id))


def parse_entry(entry: str) -> tuple[str, str] | None:
    """(serial, factor ID) of an entry written by KeyEnroll; None for
    anything else an administrator may have put in the attribute."""
    parts = [p.strip() for p in str(entry).split(ENTRY_SEPARATOR.strip())]
    if len(parts) < 2 or not _OKTA_ID.match(parts[-1]):
        return None
    return parts[0], parts[-1]


def _user_handle(user_id: str) -> str:
    """Okta sends the WebAuthn user handle as base64url text.

    Browsers decode it before passing it to the authenticator; falls back to
    the raw characters if the value is not valid base64url.
    """
    try:
        return b64url_encode(b64url_decode(user_id))
    except ValueError:
        return b64url_encode(user_id.encode())


class OktaProvider(Provider):
    kind = "okta"
    label = "Okta"
    supports_groups = True
    fields = [
        FieldSpec(
            "domain",
            N_("Okta domain"),
            placeholder="example.okta.com",
            help=N_("FIDO2 credentials are registered per domain (default or custom)."),
        ),
        FieldSpec("client_id", N_("Client ID")),
        FieldSpec(
            "redirect_uri",
            N_("Redirect URI"),
            default="http://localhost:8080/yubienroll-redirect",
        ),
        GROUPS_FIELD,
        FieldSpec(
            "key_attribute",
            N_("Profile attribute for key serial numbers"),
            required=False,
            placeholder="securityKeys",
            help=N_(
                "Variable name of a string array attribute in the Okta user profile. "
                "KeyEnroll writes the serial number of every key it enrolls into it, "
                "so that you can tell the keys of a user apart and find who has a "
                "key. Empty: off."
            ),
        ),
    ]
    # Writing the serial numbers changes where nothing is sent.
    session_neutral = Provider.session_neutral | {"key_attribute"}

    @property
    def _domain(self) -> str:
        return clean_host(self.settings["domain"])

    @property
    def _base(self) -> str:
        return f"https://{self._domain}"

    def oauth_config(self) -> oauth.OAuthConfig:
        return oauth.OAuthConfig(
            authorize_url=f"{self._base}/oauth2/v1/authorize",
            token_url=f"{self._base}/oauth2/v1/token",
            revoke_url=f"{self._base}/oauth2/v1/revoke",
            client_id=self.settings["client_id"],
            redirect_uri=self.settings["redirect_uri"],
            scopes=[
                "openid",
                "offline_access",
                "okta.users.read",
                "okta.users.manage",
                *(["okta.groups.read"] if self.groups_enabled else []),
            ],
        )

    def _error_detail(self, body: dict) -> str | None:
        summary = body.get("errorSummary")
        causes = [
            c.get("errorSummary") for c in body.get("errorCauses") or [] if c.get("errorSummary")
        ]
        if summary and causes:
            return f"{summary} ({'; '.join(causes)})"
        return summary or super()._error_detail(body)

    def _factors_url(self, user_id: str) -> str:
        return f"{self._base}/api/v1/users/{quote(user_id)}/factors"

    def search_users(self, query: str) -> list[DirectoryUser]:
        params = {"limit": "25"}
        if query.strip():
            params["q"] = query.strip()
        data = self._request("GET", f"{self._base}/api/v1/users", params=params).json()
        users = [self._to_user(u) for u in data]
        if self.records_keys and query.strip().isdigit():
            # A number may be the serial number of a key: its owner comes first.
            owners = self.users_with_key(query.strip())
            known = {u.id for u in owners}
            users = owners + [u for u in users if u.id not in known]
        return users

    # -- serial numbers of the keys in the user profile --------------------

    @property
    def _key_attribute(self) -> str:
        return self.settings.get("key_attribute", "")

    @property
    def records_keys(self) -> bool:
        return bool(self._key_attribute)

    def _checked_attribute(self) -> str:
        attribute = self._key_attribute
        if not _ATTRIBUTE_NAME.match(attribute):
            raise ProviderError(
                f"{self.label}: '{attribute}' is not a valid profile attribute name"
            )
        return attribute

    def _key_entries(self, user_id: str) -> list[str]:
        attribute = self._checked_attribute()
        data = self._request("GET", f"{self._base}/api/v1/users/{quote(user_id)}").json()
        value = (data.get("profile") or {}).get(attribute)
        if isinstance(value, str):
            value = [value]
        return [str(v) for v in value or []]

    def _write_entries(self, user_id: str, entries: list[str]) -> None:
        attribute = self._checked_attribute()
        try:
            # POST updates only the attributes it names.
            self._request(
                "POST",
                f"{self._base}/api/v1/users/{quote(user_id)}",
                json={"profile": {attribute: entries}},
            )
        except ProviderError as e:
            if e.status == 400 and "not defined in profile" in str(e).lower():
                raise ProviderNotice(
                    N_(
                        "The credential was registered, but Okta does not know the profile "
                        "attribute '{attribute}' for this user, so the serial number was not "
                        "saved. Add the attribute in Profile Editor, to the profile of the "
                        "user's type, with exactly this variable name (it is case-sensitive)."
                    ),
                    e.status,
                    attribute=attribute,
                ) from e
            raise

    def _webauthn_factor_ids(self, user_id: str) -> set[str]:
        data = self._request("GET", self._factors_url(user_id)).json()
        return {f["id"] for f in data if f.get("factorType") == "webauthn"}

    def _current_entries(self, user_id: str, entries: list[str], drop: str = "") -> list[str]:
        """Leaves out entries of keys removed in the meantime (also in the
        admin console) and of ``drop``; other text is kept as it is."""
        factors = self._webauthn_factor_ids(user_id)
        kept = []
        for entry in entries:
            parsed = parse_entry(entry)
            if parsed is None or (parsed[1] in factors and parsed[1] != drop):
                kept.append(entry)
        return kept

    def record_key(self, user, registration, serial) -> None:
        if not self.records_keys:
            return
        factor_id = registration.state["factor_id"]
        entries = self._current_entries(user.id, self._key_entries(user.id), drop=factor_id)
        entries.append(key_entry(serial, factor_id, datetime.now(timezone.utc)))
        self._write_entries(user.id, entries)

    def users_with_key(self, serial: str) -> list[DirectoryUser]:
        """Users whose profile lists a key with this serial number.

        Okta's search cannot match a part of an array element, so the users
        that have the attribute at all are read and compared here."""
        attribute = self._checked_attribute()
        found = self._collect(
            f"{self._base}/api/v1/users",
            {"search": f"profile.{attribute} pr", "limit": "200"},
            self._page,
        )
        out = []
        for u in found:
            value = (u.get("profile") or {}).get(attribute) or []
            entries = [value] if isinstance(value, str) else value
            if any((parse_entry(e) or ("", ""))[0] == serial for e in entries):
                out.append(self._to_user(u))
        return out

    @staticmethod
    def _to_user(u: dict) -> DirectoryUser:
        profile = u.get("profile") or {}
        name = " ".join(p for p in (profile.get("firstName"), profile.get("lastName")) if p)
        return DirectoryUser(
            id=u["id"],
            username=profile.get("login") or "",
            display_name=name,
            email=profile.get("email") or "",
        )

    def find_user(self, identifier: str) -> DirectoryUser | None:
        identifier = identifier.strip()
        try:
            # Accepts a user ID, a login or an unambiguous short login.
            data = self._request(
                "GET", f"{self._base}/api/v1/users/{quote(identifier, safe='')}"
            ).json()
        except ProviderError as e:
            if e.status == 404:
                return None
            raise
        return self._to_user(data)

    def begin_registration(self, user: DirectoryUser) -> Registration:
        factor = self._request(
            "POST",
            self._factors_url(user.id),
            json={"factorType": "webauthn", "provider": "FIDO"},
        ).json()
        state = {"user_id": user.id, "factor_id": factor.get("id")}
        activation = (factor.get("_embedded") or {}).get("activation")
        if not activation or not state["factor_id"]:
            raise ProviderError(f"{self.label}: no activation data returned")

        rp = dict(activation.get("rp") or {})
        rp.setdefault("name", self._domain)
        rp.setdefault("id", self._domain)
        okta_user = dict(activation["user"])
        okta_user["id"] = _user_handle(okta_user["id"])
        options = {
            "rp": rp,
            "user": okta_user,
            "challenge": to_b64url(activation["challenge"]),
            "pubKeyCredParams": activation["pubKeyCredParams"],
        }
        for key in ("attestation", "authenticatorSelection"):
            if activation.get(key):
                options[key] = activation[key]
        exclude = [
            {**c, "id": to_b64url(c["id"])} for c in activation.get("excludeCredentials") or []
        ]
        if exclude:
            options["excludeCredentials"] = exclude
        return Registration(options=options, origin=self._base, state=state)

    def complete_registration(self, registration, response, display_name) -> None:
        state = registration.state
        self._request(
            "POST",
            f"{self._factors_url(state['user_id'])}/{quote(state['factor_id'])}/lifecycle/activate",
            json={
                "attestation": b64_encode(response.response.attestation_object),
                "clientData": b64_encode(response.response.client_data),
            },
        )

    def cancel_registration(self, registration: Registration) -> None:
        state = registration.state
        self._request(
            "DELETE", f"{self._factors_url(state['user_id'])}/{quote(state['factor_id'])}"
        )

    def list_credentials(self, user: DirectoryUser) -> list[Credential]:
        data = self._request("GET", self._factors_url(user.id)).json()
        serials: dict[str, str] = {}
        if self.records_keys:
            try:
                for entry in self._key_entries(user.id):
                    parsed = parse_entry(entry)
                    if parsed and parsed[0] != UNKNOWN_SERIAL:
                        serials[parsed[1]] = parsed[0]
            except ProviderError:
                logger.warning("Reading the key serial numbers failed", exc_info=True)
        return [
            Credential(
                id=f["id"],
                name=(f.get("profile") or {}).get("authenticatorName") or "",
                created=f.get("created") or "",
                detail=f.get("status") or "",
                serial=serials.get(f["id"], ""),
            )
            for f in data
            if f.get("factorType") == "webauthn"
        ]

    @staticmethod
    def _page(resp) -> tuple[list, str | None, None]:
        # Okta pages with a Link header: <https://…/users?after=…>; rel="next"
        links = getattr(resp, "links", None) or {}
        return resp.json(), (links.get("next") or {}).get("url"), None

    def search_groups(self, query: str) -> list[DirectoryGroup]:
        params = {"limit": "25"}
        if query.strip():
            params["q"] = query.strip()
        data = self._request("GET", f"{self._base}/api/v1/groups", params=params).json()
        return [
            DirectoryGroup(
                g["id"],
                (g.get("profile") or {}).get("name") or "",
                (g.get("profile") or {}).get("description") or "",
            )
            for g in data
        ]

    def group_members(self, group: DirectoryGroup, nested: bool = False) -> list[DirectoryUser]:
        users = self._collect(
            f"{self._base}/api/v1/groups/{quote(group.id)}/users", {"limit": "200"}, self._page
        )
        return [self._to_user(u) for u in users]

    def delete_credential(self, user: DirectoryUser, credential_id: str) -> None:
        self._request("DELETE", f"{self._factors_url(user.id)}/{quote(credential_id)}")
        if not self.records_keys:
            return
        try:
            entries = self._key_entries(user.id)
            kept = self._current_entries(user.id, entries, drop=credential_id)
            if kept != entries:
                self._write_entries(user.id, kept)
        except ProviderError as e:
            raise ProviderError(
                f"{self.label}: the key was removed, but its serial number is still "
                f"listed in the user profile ({e})"
            ) from e
