"""PingOne (PingID), using the PingOne MFA devices API."""

from __future__ import annotations

import json
from urllib.parse import quote

from .. import oauth
from ..i18n import N_
from .base import (
    Credential,
    DirectoryUser,
    FieldSpec,
    Provider,
    ProviderError,
    Registration,
    b64_encode,
    b64url_encode,
    clean_host,
    to_b64url,
)

REGIONS = [
    ("com", "North America (.com)"),
    ("eu", "Europe (.eu)"),
    ("ca", "Canada (.ca)"),
    ("asia", "Asia-Pacific (.asia)"),
    ("com.au", "Australia (.com.au)"),
    ("sg", "Singapore (.sg)"),
]

ACTIVATE_CONTENT_TYPE = "application/vnd.pingidentity.device.activate+json"


def _scim_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class PingOneProvider(Provider):
    kind = "pingone"
    label = "PingOne PingID"
    fields = [
        FieldSpec("environment_id", N_("Environment ID")),
        FieldSpec("client_id", N_("Client ID")),
        FieldSpec(
            "redirect_uri",
            N_("Redirect URI"),
            default="http://localhost:9443/yubienroll-callback",
        ),
        FieldSpec("region", N_("Region"), default="com", choices=REGIONS),
        FieldSpec(
            "custom_domain",
            N_("Custom domain"),
            required=False,
            placeholder="auth.example.com",
            help=N_("Only if the environment uses a custom domain."),
        ),
        FieldSpec(
            "policy_id",
            N_("MFA policy ID"),
            required=False,
            help=N_("Leave empty to use the default MFA policy."),
        ),
    ]

    @property
    def _env(self) -> str:
        return self.settings["environment_id"]

    @property
    def _auth_host(self) -> str:
        return clean_host(self.settings["custom_domain"]) or (
            f"auth.pingone.{self.settings['region']}"
        )

    @property
    def _api(self) -> str:
        return f"https://api.pingone.{self.settings['region']}/v1/environments/{self._env}"

    def oauth_config(self) -> oauth.OAuthConfig:
        if self.settings["custom_domain"]:
            base = f"https://{self._auth_host}/as"
        else:
            base = f"https://{self._auth_host}/{self._env}/as"
        return oauth.OAuthConfig(
            authorize_url=f"{base}/authorize",
            token_url=f"{base}/token",
            client_id=self.settings["client_id"],
            redirect_uri=self.settings["redirect_uri"],
            scopes=["openid"],
        )

    def _error_detail(self, body: dict) -> str | None:
        details = [d.get("message") for d in body.get("details") or [] if d.get("message")]
        message = body.get("message")
        if message and details:
            return f"{message} ({'; '.join(details)})"
        return message or super()._error_detail(body)

    def _devices_url(self, user_id: str) -> str:
        return f"{self._api}/users/{quote(user_id)}/devices"

    def search_users(self, query: str) -> list[DirectoryUser]:
        params = {"limit": "25"}
        query = query.strip()
        if query:
            q = _scim_quote(query)
            params["filter"] = " or ".join(
                f"{attr} sw {q}"
                for attr in ("username", "email", "name.given", "name.family")
            )
        return self._users(params)

    def find_user(self, identifier: str) -> DirectoryUser | None:
        q = _scim_quote(identifier.strip())
        users = self._users({"limit": "2", "filter": f"username eq {q} or email eq {q}"})
        return users[0] if len(users) == 1 else None

    def _users(self, params: dict) -> list[DirectoryUser]:
        data = self._request("GET", f"{self._api}/users", params=params).json()
        users = []
        for u in (data.get("_embedded") or {}).get("users", []):
            name = u.get("name") or {}
            display = name.get("formatted") or " ".join(
                p for p in (name.get("given"), name.get("family")) if p
            )
            users.append(
                DirectoryUser(
                    id=u["id"],
                    username=u.get("username") or "",
                    display_name=display,
                    email=u.get("email") or "",
                )
            )
        return users

    def _origin(self, rp_id: str) -> str:
        host = self._auth_host
        if host == rp_id or host.endswith("." + rp_id):
            return f"https://{host}"
        return f"https://{rp_id}"

    def begin_registration(self, user: DirectoryUser) -> Registration:
        body: dict = {"type": "FIDO2"}
        if self.settings["policy_id"]:
            body["policy"] = {"id": self.settings["policy_id"]}
        device = self._request("POST", self._devices_url(user.id), json=body).json()
        state = {"user_id": user.id, "device_id": device.get("id")}
        raw = device.get("publicKeyCredentialCreationOptions")
        if not raw or not state["device_id"]:
            raise ProviderError(f"{self.label}: no creation options returned")

        options = json.loads(raw) if isinstance(raw, str) else dict(raw)
        options["challenge"] = to_b64url(options["challenge"])
        options["user"]["id"] = to_b64url(options["user"]["id"])
        for cred in options.get("excludeCredentials") or []:
            cred["id"] = to_b64url(cred["id"])
        rp = options.setdefault("rp", {})
        rp.setdefault("id", self._auth_host)
        rp.setdefault("name", "PingOne")
        return Registration(options=options, origin=self._origin(rp["id"]), state=state)

    def complete_registration(self, registration, response, display_name) -> None:
        state = registration.state
        attestation = {
            "id": b64url_encode(response.raw_id),
            "type": "public-key",
            "rawId": b64_encode(response.raw_id),
            "response": {
                "clientDataJSON": b64_encode(response.response.client_data),
                "attestationObject": b64_encode(response.response.attestation_object),
            },
            "clientExtensionResults": {},
        }
        device_url = f"{self._devices_url(state['user_id'])}/{quote(state['device_id'])}"
        self._request(
            "POST",
            device_url,
            data=json.dumps(
                {"origin": registration.origin, "attestation": json.dumps(attestation)}
            ),
            headers={"Content-Type": ACTIVATE_CONTENT_TYPE},
        )
        if display_name:
            try:
                self._request(
                    "PUT", f"{device_url}/nickname", json={"nickname": display_name}
                )
            except ProviderError:
                # The device is enrolled; a rejected nickname is cosmetic.
                pass

    def cancel_registration(self, registration: Registration) -> None:
        state = registration.state
        self._request(
            "DELETE", f"{self._devices_url(state['user_id'])}/{quote(state['device_id'])}"
        )

    def list_credentials(self, user: DirectoryUser) -> list[Credential]:
        data = self._request("GET", self._devices_url(user.id)).json()
        out = []
        for d in (data.get("_embedded") or {}).get("devices", []):
            if d.get("type") != "FIDO2":
                continue
            out.append(
                Credential(
                    id=d["id"],
                    name=d.get("nickname") or d.get("displayName") or d.get("name") or "",
                    created=d.get("createdAt") or "",
                    detail=d.get("status") or "",
                )
            )
        return out

    def delete_credential(self, user: DirectoryUser, credential_id: str) -> None:
        self._request("DELETE", f"{self._devices_url(user.id)}/{quote(credential_id)}")
