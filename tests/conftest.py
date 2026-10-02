from __future__ import annotations

import json as jsonlib
import time
from dataclasses import dataclass, field

import pytest
from fido2.webauthn import (
    AttestationObject,
    AuthenticatorAttestationResponse,
    CollectedClientData,
    RegistrationResponse,
)

from keyenroll import oauth
from keyenroll.secrets_store import TokenStore


class FakeResponse:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body

    def json(self):
        if self._body is None:
            raise ValueError("no body")
        return self._body


@dataclass
class Call:
    method: str
    url: str
    params: dict | None = None
    json: object = None
    data: object = None
    headers: dict = field(default_factory=dict)

    @property
    def body(self):
        """Request body decoded from either json= or a JSON string in data=."""
        if self.json is not None:
            return self.json
        return jsonlib.loads(self.data) if isinstance(self.data, str) else self.data


class FakeHttp:
    """Stands in for requests.Session: answers from a queue, records calls."""

    def __init__(self):
        self.calls: list[Call] = []
        self.queue: list[FakeResponse] = []

    def add(self, body=None, status=200):
        self.queue.append(FakeResponse(status, body))
        return self

    def request(self, method, url, params=None, json=None, data=None, headers=None, timeout=None):
        self.calls.append(Call(method, url, params, json, data, dict(headers or {})))
        assert self.queue, f"unexpected request {method} {url}"
        return self.queue.pop(0)

    def post(self, url, data=None, headers=None, timeout=None):
        return self.request("POST", url, data=data, headers=headers)


@pytest.fixture
def http():
    return FakeHttp()


@pytest.fixture
def store():
    return TokenStore()


@pytest.fixture
def signed_in():
    """Gives a provider a valid access token without going through OAuth."""

    def apply(provider, token="ACCESS"):
        provider._tokens = oauth.TokenSet(token, time.time() + 3600, "REFRESH")
        return provider

    return apply


@pytest.fixture
def response():
    """A RegistrationResponse with recognisable binary content."""
    client_data = CollectedClientData.create(
        type="webauthn.create", challenge=b"\xfb\xff\xfe-challenge", origin="https://rp.example"
    )
    auth_data = bytes(32) + b"\x41" + bytes(4) + bytes(16) + b"\x00\x04" + b"\xfa\xfb\xfc\xfd"
    auth_data += bytes.fromhex("a5010203262001215820") + bytes(32) + bytes.fromhex("225820") + bytes(32)
    att = AttestationObject.create("none", auth_data, {})
    return RegistrationResponse(
        raw_id=b"\xfa\xfb\xfc\xfd",
        response=AuthenticatorAttestationResponse(
            client_data=client_data, attestation_object=att
        ),
    )
