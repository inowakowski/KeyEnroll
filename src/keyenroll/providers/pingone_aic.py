"""PingOne Advanced Identity Cloud, driving a WebAuthn registration journey.

The journey must prompt for the username once and then return the WebAuthn
registration challenge, as required by the YubiEnroll CLI. The operator's
access token is sent in the Authorization header of every journey call.
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any
from urllib.parse import quote

from .. import oauth
from ..i18n import N_
from .base import (
    DirectoryUser,
    FieldSpec,
    Provider,
    ProviderError,
    Registration,
    b64url_encode,
    clean_host,
    to_b64url,
)

JOURNEY_HEADERS = {
    "Accept-API-Version": "resource=2.1, protocol=1.0",
    "Content-Type": "application/json",
}
OUTCOME_ID = "webAuthnOutcome"


def _query_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _output(callback: dict, name: str) -> Any:
    for item in callback.get("output") or []:
        if item.get("name") == name:
            return item.get("value")
    return None


def _int_array(text: str) -> bytes:
    return bytes(int(n) & 0xFF for n in re.findall(r"-?\d+", text))


def _exclude_from_text(text: str) -> list[dict]:
    return [
        {"type": "public-key", "id": b64url_encode(_int_array(m))}
        for m in re.findall(r"Int8Array\(\[([^\]]*)\]\)", text or "")
    ]


def _loads_lenient(text: str, default: Any) -> Any:
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return default


def options_from_metadata(meta: dict, default_rp_id: str) -> dict:
    """Builds creation options from the WebAuthn MetadataCallback value."""
    rp_id = meta.get("_relyingPartyId")
    if not rp_id:
        m = re.search(r'id:\s*"([^"]+)"', meta.get("relyingPartyId") or "")
        rp_id = m.group(1) if m else default_rp_id

    params = meta.get("_pubKeyCredParams") or _loads_lenient(
        meta.get("pubKeyCredParams"), None
    )
    if not params:
        raise ProviderError("WebAuthn callback has no pubKeyCredParams")

    selection = meta.get("_authenticatorSelection") or _loads_lenient(
        meta.get("authenticatorSelection"), {}
    )

    if meta.get("_excludeCredentials") is not None:
        exclude = [
            {"type": c.get("type", "public-key"), "id": to_b64url(c["id"])}
            for c in meta["_excludeCredentials"]
        ]
    else:
        exclude = _exclude_from_text(meta.get("excludeCredentials"))

    options: dict[str, Any] = {
        "rp": {"id": rp_id, "name": meta.get("relyingPartyName") or rp_id},
        "user": {
            # AM passes the handle as text that browsers map char-by-char.
            "id": b64url_encode(str(meta["userId"]).encode("latin-1", "replace")),
            "name": meta.get("userName") or "",
            "displayName": meta.get("displayName") or meta.get("userName") or "",
        },
        "challenge": b64url_encode(base64.b64decode(meta["challenge"])),
        "pubKeyCredParams": params,
        "attestation": meta.get("attestationPreference") or "none",
    }
    if selection:
        options["authenticatorSelection"] = selection
    if exclude:
        options["excludeCredentials"] = exclude
    return options


def options_from_script(script: str, default_rp_id: str) -> dict:
    """Best-effort parsing of the legacy JavaScript form of the challenge."""

    def find(pattern: str) -> str | None:
        m = re.search(pattern, script, re.S)
        return m.group(1) if m else None

    challenge = find(r"challenge:\s*new Int8Array\(\[([^\]]*)\]\)")
    user_id = find(r'id:\s*Uint8Array\.from\("([^"]*)"')
    params = _loads_lenient(find(r"pubKeyCredParams:\s*(\[.*?\])\s*,"), None)
    if not (challenge and user_id and params):
        raise ProviderError(
            "Cannot parse the WebAuthn challenge. Disable 'Return challenge as "
            "JavaScript' in the journey's WebAuthn Registration Node."
        )
    options: dict[str, Any] = {
        "rp": {
            "id": find(r'rp:\s*\{[^}]*?id:\s*"([^"]+)"') or default_rp_id,
            "name": find(r'rp:\s*\{[^}]*?name:\s*"([^"]*)"') or default_rp_id,
        },
        "user": {
            "id": b64url_encode(user_id.encode("latin-1", "replace")),
            "name": find(r'user:\s*\{.*?name:\s*"([^"]*)"') or "",
            "displayName": find(r'displayName:\s*"([^"]*)"') or "",
        },
        "challenge": b64url_encode(_int_array(challenge)),
        "pubKeyCredParams": params,
        "attestation": find(r'attestation:\s*"(\w+)"') or "none",
    }
    selection = _loads_lenient(find(r"authenticatorSelection:\s*(\{.*?\})"), None)
    if selection:
        options["authenticatorSelection"] = selection
    exclude = _exclude_from_text(find(r"excludeCredentials:\s*(\[.*?\])\s*,") or "")
    if exclude:
        options["excludeCredentials"] = exclude
    return options


class PingOneAicProvider(Provider):
    kind = "pingone_aic"
    label = "PingOne Advanced Identity Cloud"
    supports_credential_list = False
    supports_credential_delete = False
    fields = [
        FieldSpec(
            "tenant", N_("Tenant"), placeholder="openam-example.forgeblocks.com"
        ),
        FieldSpec("realm", N_("Realm"), default="alpha"),
        FieldSpec(
            "journey",
            N_("Journey name"),
            help=N_("The WebAuthn registration journey created for YubiEnroll."),
        ),
        FieldSpec("client_id", N_("Client ID")),
        FieldSpec(
            "redirect_uri",
            N_("Redirect URI"),
            default="http://localhost:8443/yubienroll-redirect",
        ),
        FieldSpec(
            "origin",
            N_("WebAuthn origin"),
            required=False,
            placeholder="https://sso.example.com",
            help=N_("Leave empty to use the tenant address."),
        ),
    ]

    @property
    def _tenant(self) -> str:
        return clean_host(self.settings["tenant"])

    @property
    def _realm(self) -> str:
        return self.settings["realm"].strip("/")

    @property
    def _origin(self) -> str:
        return self.settings["origin"].rstrip("/") or f"https://{self._tenant}"

    def oauth_config(self) -> oauth.OAuthConfig:
        base = f"https://{self._tenant}/am/oauth2/realms/root/realms/{self._realm}"
        return oauth.OAuthConfig(
            authorize_url=f"{base}/authorize",
            token_url=f"{base}/access_token",
            client_id=self.settings["client_id"],
            redirect_uri=self.settings["redirect_uri"],
            scopes=["openid", "profile", "fr:idm:*"],
        )

    def _error_detail(self, body: dict) -> str | None:
        return body.get("message") or body.get("reason") or super()._error_detail(body)

    def search_users(self, query: str) -> list[DirectoryUser]:
        query = query.strip()
        if query:
            q = _query_quote(query)
            flt = " or ".join(
                f"{attr} co {q}" for attr in ("userName", "mail", "givenName", "sn")
            )
        else:
            flt = "true"
        return self._users(flt, 25)

    def find_user(self, identifier: str) -> DirectoryUser | None:
        q = _query_quote(identifier.strip())
        users = self._users(f"userName eq {q} or mail eq {q}", 2)
        return users[0] if len(users) == 1 else None

    def _users(self, query_filter: str, page_size: int) -> list[DirectoryUser]:
        data = self._request(
            "GET",
            f"https://{self._tenant}/openidm/managed/{quote(self._realm)}_user",
            params={
                "_queryFilter": query_filter,
                "_pageSize": str(page_size),
                "_fields": "userName,givenName,sn,mail",
            },
        ).json()
        return [
            DirectoryUser(
                id=u["_id"],
                username=u.get("userName") or "",
                display_name=" ".join(p for p in (u.get("givenName"), u.get("sn")) if p),
                email=u.get("mail") or "",
            )
            for u in data.get("result", [])
        ]

    def _journey(self, payload: dict | None) -> dict:
        resp = self._request(
            "POST",
            f"https://{self._tenant}/am/json/realms/root/realms/{self._realm}/authenticate",
            params={"authIndexType": "service", "authIndexValue": self.settings["journey"]},
            data=json.dumps(payload or {}),
            headers=JOURNEY_HEADERS,
            # A failed journey also answers 401; that is not an expired token.
            retry_auth=False,
        )
        return resp.json()

    def begin_registration(self, user: DirectoryUser) -> Registration:
        step = self._journey(None)
        callbacks = step.get("callbacks") or []
        names = [c for c in callbacks if c.get("type") == "NameCallback"]
        if len(names) != 1 or len(callbacks) != 1:
            raise ProviderError(
                f"{self.label}: the journey must start with a single username prompt"
            )
        names[0]["input"][0]["value"] = user.username
        step = self._journey(step)

        callbacks = step.get("callbacks") or []
        outcome = next(
            (
                c
                for c in callbacks
                if c.get("type") == "HiddenValueCallback"
                and _output(c, "id") == OUTCOME_ID
            ),
            None,
        )
        if outcome is None:
            raise ProviderError(
                f"{self.label}: the journey did not return a WebAuthn registration "
                "challenge after the username"
            )

        options = None
        json_response = False
        default_rp = self._origin.split("://", 1)[-1].split(":")[0]
        for cb in callbacks:
            if cb.get("type") == "MetadataCallback":
                meta = _output(cb, "data")
                if isinstance(meta, dict) and "challenge" in meta:
                    options = options_from_metadata(meta, default_rp)
                    json_response = bool(meta.get("supportsJsonResponse"))
            elif cb.get("type") == "TextOutputCallback" and options is None:
                text = _output(cb, "message")
                if isinstance(text, str) and "challenge" in text:
                    options = options_from_script(text, default_rp)
        if options is None:
            raise ProviderError(f"{self.label}: WebAuthn challenge not found in journey")

        return Registration(
            options=options,
            origin=self._origin,
            state={"step": step, "json_response": json_response},
        )

    def complete_registration(self, registration, response, display_name) -> None:
        att = response.response.attestation_object
        signed = ",".join(str(b - 256 if b > 127 else b) for b in att)
        legacy = "::".join(
            [
                bytes(response.response.client_data).decode(),
                signed,
                b64url_encode(response.raw_id),
            ]
        )
        if display_name:
            legacy += "::" + display_name
        if registration.state["json_response"]:
            value = json.dumps(
                {"authenticatorAttachment": "cross-platform", "legacyData": legacy}
            )
        else:
            value = legacy

        step = registration.state["step"]
        for cb in step["callbacks"]:
            if cb.get("type") == "HiddenValueCallback" and _output(cb, "id") == OUTCOME_ID:
                cb["input"][0]["value"] = value
        result = self._journey(step)
        if "tokenId" not in result and "successUrl" not in result:
            raise ProviderError(
                f"{self.label}: the journey did not complete after registration"
            )
