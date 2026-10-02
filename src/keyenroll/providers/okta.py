"""Okta, using the User Factors API (factorType webauthn)."""

from __future__ import annotations

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
    b64url_decode,
    b64url_encode,
    clean_host,
    to_b64url,
)


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
    ]

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
            scopes=["openid", "offline_access", "okta.users.read", "okta.users.manage"],
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
        return [self._to_user(u) for u in data]

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
        return [
            Credential(
                id=f["id"],
                name=(f.get("profile") or {}).get("authenticatorName") or "",
                created=f.get("created") or "",
                detail=f.get("status") or "",
            )
            for f in data
            if f.get("factorType") == "webauthn"
        ]

    def delete_credential(self, user: DirectoryUser, credential_id: str) -> None:
        self._request("DELETE", f"{self._factors_url(user.id)}/{quote(credential_id)}")
