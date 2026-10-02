"""Microsoft Entra ID, using the Microsoft Graph FIDO2 provisioning API."""

from __future__ import annotations

from typing import Any
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
    b64url_encode,
    to_b64url,
)

# Entra ID rejects longer names for FIDO2 methods.
MAX_DISPLAY_NAME = 30


def _strip_odata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: _strip_odata(v) for k, v in value.items() if not k.startswith("@odata")
        }
    if isinstance(value, list):
        return [_strip_odata(v) for v in value]
    return value


class EntraProvider(Provider):
    kind = "entra"
    label = "Microsoft Entra ID"
    max_display_name = MAX_DISPLAY_NAME
    fields = [
        FieldSpec("tenant_id", N_("Directory (tenant) ID")),
        FieldSpec("client_id", N_("Application (client) ID")),
        FieldSpec(
            "redirect_uri",
            N_("Redirect URI"),
            default="http://localhost/yubienroll-redirect",
        ),
        FieldSpec(
            "authority",
            N_("Entra ID endpoint"),
            default="https://login.microsoftonline.com",
            help=N_("Change only for national cloud deployments."),
        ),
        FieldSpec(
            "graph",
            N_("Microsoft Graph endpoint"),
            default="https://graph.microsoft.com",
            help=N_("Change only for national cloud deployments."),
        ),
    ]

    @property
    def _graph(self) -> str:
        return self.settings["graph"].rstrip("/")

    @property
    def _api(self) -> str:
        return f"{self._graph}/v1.0"

    def oauth_config(self) -> oauth.OAuthConfig:
        base = f"{self.settings['authority'].rstrip('/')}/{self.settings['tenant_id']}/oauth2/v2.0"
        return oauth.OAuthConfig(
            authorize_url=f"{base}/authorize",
            token_url=f"{base}/token",
            client_id=self.settings["client_id"],
            redirect_uri=self.settings["redirect_uri"],
            scopes=[
                f"{self._graph}/User.ReadBasic.All",
                f"{self._graph}/UserAuthenticationMethod.ReadWrite.All",
                "offline_access",
                "openid",
                "profile",
            ],
            extra_authorize_params={"prompt": "select_account"},
        )

    def _error_detail(self, body: dict) -> str | None:
        err = body.get("error")
        if isinstance(err, dict):
            return err.get("message") or err.get("code")
        return super()._error_detail(body)

    def _methods_url(self, user: DirectoryUser) -> str:
        return f"{self._api}/users/{quote(user.id)}/authentication/fido2Methods"

    def search_users(self, query: str) -> list[DirectoryUser]:
        params = {
            "$select": "id,displayName,userPrincipalName,mail",
            "$top": "25",
        }
        query = query.strip()
        if query:
            q = query.replace("'", "''")
            params["$filter"] = " or ".join(
                f"startswith({attr},'{q}')"
                for attr in ("displayName", "userPrincipalName", "mail", "surname")
            )
        data = self._request("GET", f"{self._api}/users", params=params).json()
        return [self._to_user(u) for u in data.get("value", [])]

    @staticmethod
    def _to_user(u: dict) -> DirectoryUser:
        return DirectoryUser(
            id=u["id"],
            username=u.get("userPrincipalName") or "",
            display_name=u.get("displayName") or "",
            email=u.get("mail") or "",
        )

    def find_user(self, identifier: str) -> DirectoryUser | None:
        identifier = identifier.strip()
        select = {"$select": "id,displayName,userPrincipalName,mail"}
        try:
            # Accepts an object ID or a user principal name.
            data = self._request(
                "GET", f"{self._api}/users/{quote(identifier, safe='')}", params=select
            ).json()
            return self._to_user(data)
        except ProviderError as e:
            if e.status not in (400, 404):
                raise
        q = identifier.replace("'", "''")
        data = self._request(
            "GET", f"{self._api}/users", params={**select, "$filter": f"mail eq '{q}'"}
        ).json()
        matches = data.get("value", [])
        return self._to_user(matches[0]) if len(matches) == 1 else None

    def _creation_options(self, user: DirectoryUser) -> dict:
        data = self._request("GET", f"{self._methods_url(user)}/creationOptions").json()
        options = _strip_odata(data.get("publicKey") or {})
        if not options.get("challenge"):
            raise ProviderError(f"{self.label}: no creation options returned")
        return options

    def preflight(self, user: DirectoryUser) -> None:
        # Fetching options has no side effects and surfaces missing roles or
        # a disabled FIDO2 policy before the key is touched.
        self._creation_options(user)

    def begin_registration(self, user: DirectoryUser) -> Registration:
        options = self._creation_options(user)
        options["challenge"] = to_b64url(options["challenge"])
        options["user"]["id"] = to_b64url(options["user"]["id"])
        for cred in options.get("excludeCredentials") or []:
            cred["id"] = to_b64url(cred["id"])
        if not options.get("extensions"):
            options.pop("extensions", None)
        return Registration(
            options=options,
            origin=f"https://{options['rp']['id']}",
            state={"user_id": user.id},
        )

    def complete_registration(self, registration, response, display_name) -> None:
        name = (display_name or "YubiKey")[:MAX_DISPLAY_NAME]
        body = {
            "displayName": name,
            "publicKeyCredential": {
                "id": b64url_encode(response.raw_id),
                "response": {
                    "clientDataJSON": b64url_encode(response.response.client_data),
                    "attestationObject": b64url_encode(
                        response.response.attestation_object
                    ),
                },
            },
        }
        user = DirectoryUser(id=registration.state["user_id"], username="")
        self._request("POST", self._methods_url(user), json=body)

    def list_credentials(self, user: DirectoryUser) -> list[Credential]:
        data = self._request("GET", self._methods_url(user)).json()
        return [
            Credential(
                id=m["id"],
                name=m.get("displayName") or "",
                created=m.get("createdDateTime") or "",
                detail=m.get("model") or m.get("aaGuid") or "",
            )
            for m in data.get("value", [])
        ]

    def delete_credential(self, user: DirectoryUser, credential_id: str) -> None:
        self._request("DELETE", f"{self._methods_url(user)}/{quote(credential_id)}")
