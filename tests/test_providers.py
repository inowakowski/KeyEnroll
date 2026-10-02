from __future__ import annotations

import base64
import json

import pytest
from fido2.webauthn import PublicKeyCredentialCreationOptions

from keyenroll.providers import PROVIDERS, AuthRequired, ProviderError
from keyenroll.providers.base import DirectoryUser, b64url_decode, to_b64url
from keyenroll.providers.entra import EntraProvider
from keyenroll.providers.okta import OktaProvider
from keyenroll.providers.pingone import PingOneProvider
from keyenroll.providers.pingone_aic import PingOneAicProvider, options_from_script

USER = DirectoryUser(id="user-1", username="alice@example.com", display_name="Alice")


def parse(options: dict) -> PublicKeyCredentialCreationOptions:
    """Options must be accepted by python-fido2 exactly as the engine passes them."""
    return PublicKeyCredentialCreationOptions.from_dict(options)


def test_to_b64url_accepts_all_wire_forms():
    raw = b"\xfb\xff\xfe\x00\x80"
    assert b64url_decode(to_b64url(base64.b64encode(raw).decode())) == raw
    assert b64url_decode(to_b64url(base64.urlsafe_b64encode(raw).decode())) == raw
    assert b64url_decode(to_b64url([-5, -1, -2, 0, -128])) == raw
    assert b64url_decode(to_b64url([251, 255, 254, 0, 128])) == raw


def test_registry_covers_all_yubienroll_providers():
    assert set(PROVIDERS) == {"entra", "okta", "pingone", "pingone_aic"}
    for cls in PROVIDERS.values():
        keys = [f.key for f in cls.fields]
        assert "client_id" in keys and "redirect_uri" in keys


def test_missing_settings():
    missing = PingOneProvider.missing_settings({"environment_id": "e"})
    assert [f.key for f in missing] == ["client_id"]


# -- session handling -------------------------------------------------------


def test_request_without_session_requires_sign_in(http, store):
    p = OktaProvider("i1", {"domain": "x.okta.com", "client_id": "c"}, store, http)
    assert not p.has_session()
    with pytest.raises(AuthRequired):
        p.search_users("a")
    assert http.calls == []


def test_expired_access_token_is_refreshed_and_rotated(http, store):
    store.set("i1", "OLD-REFRESH")
    p = OktaProvider("i1", {"domain": "x.okta.com", "client_id": "c"}, store, http)
    assert p.has_session()
    http.add({"access_token": "A1", "refresh_token": "NEW-REFRESH", "expires_in": 3600})
    http.add([])

    p.search_users("")

    token_call, api_call = http.calls
    assert token_call.url == "https://x.okta.com/oauth2/v1/token"
    assert token_call.data["grant_type"] == "refresh_token"
    assert token_call.data["refresh_token"] == "OLD-REFRESH"
    assert api_call.headers["Authorization"] == "Bearer A1"
    assert store.get("i1") == "NEW-REFRESH"


def test_rejected_refresh_token_ends_the_session(http, store):
    store.set("i1", "REVOKED")
    p = OktaProvider("i1", {"domain": "x.okta.com", "client_id": "c"}, store, http)
    http.add({"error": "invalid_grant"}, status=400)

    with pytest.raises(AuthRequired):
        p.search_users("")
    assert store.get("i1") is None
    assert not p.has_session()


def test_401_triggers_one_refresh_and_retry(http, store, signed_in):
    p = signed_in(OktaProvider("i1", {"domain": "x.okta.com", "client_id": "c"}, store, http))
    http.add({"errorSummary": "Invalid token"}, status=401)
    http.add({"access_token": "A2", "expires_in": 3600})
    http.add([])

    p.search_users("")

    assert [c.headers.get("Authorization") for c in http.calls] == [
        "Bearer ACCESS",
        None,
        "Bearer A2",
    ]


def test_logout_revokes_and_forgets(http, store, signed_in):
    p = signed_in(OktaProvider("i1", {"domain": "x.okta.com", "client_id": "c"}, store, http))
    store.set("i1", "REFRESH")
    http.add({})

    p.logout()

    assert http.calls[0].url == "https://x.okta.com/oauth2/v1/revoke"
    assert http.calls[0].data["token"] == "REFRESH"
    assert store.get("i1") is None and not p.has_session()


# -- Entra ID ---------------------------------------------------------------


@pytest.fixture
def entra(http, store, signed_in):
    return signed_in(
        EntraProvider("i1", {"tenant_id": "TENANT", "client_id": "CLIENT"}, store, http)
    )


def test_entra_oauth_config(entra):
    cfg = entra.oauth_config()
    assert cfg.authorize_url == "https://login.microsoftonline.com/TENANT/oauth2/v2.0/authorize"
    assert cfg.token_url == "https://login.microsoftonline.com/TENANT/oauth2/v2.0/token"
    assert cfg.redirect_uri == "http://localhost/yubienroll-redirect"
    assert "https://graph.microsoft.com/UserAuthenticationMethod.ReadWrite.All" in cfg.scopes
    assert "offline_access" in cfg.scopes


def test_entra_search_escapes_quotes(entra, http):
    http.add({"value": [{"id": "1", "displayName": "Pat O'Neil", "userPrincipalName": "pat@x.com", "mail": None}]})
    users = entra.search_users("O'Neil")
    assert users[0].username == "pat@x.com" and users[0].email == ""
    call = http.calls[0]
    assert call.url == "https://graph.microsoft.com/v1.0/users"
    assert "startswith(displayName,'O''Neil')" in call.params["$filter"]


ENTRA_OPTIONS = {
    "@odata.type": "#microsoft.graph.webauthnCredentialCreationOptions",
    "challengeTimeoutDateTime": "2026-04-20T10:05:00Z",
    "publicKey": {
        "@odata.type": "#microsoft.graph.webauthnPublicKeyCredentialCreationOptions",
        "rp": {"@odata.type": "#x", "id": "login.microsoft.com", "name": "Microsoft"},
        "user": {"@odata.type": "#x", "id": "T0lEOjEyMw", "displayName": "Alice", "name": "alice@example.com"},
        "challenge": "QTU1MzNDNzAtNkM3Ng",
        "pubKeyCredParams": [{"@odata.type": "#x", "type": "public-key", "alg": -7}],
        "timeout": 60000,
        "excludeCredentials": [{"@odata.type": "#x", "id": "AQID", "type": "public-key"}],
        "authenticatorSelection": {
            "@odata.type": "#x",
            "authenticatorAttachment": "cross-platform",
            "requireResidentKey": True,
            "userVerification": "required",
        },
        "attestation": "direct",
        "extensions": {"@odata.type": "#x", "hmacCreateSecret": True, "credentialProtectionPolicy": "userVerificationOptional"},
    },
}


def test_entra_registration_roundtrip(entra, http, response):
    http.add(ENTRA_OPTIONS)
    reg = entra.begin_registration(USER)

    assert http.calls[0].method == "GET"
    assert http.calls[0].url == (
        "https://graph.microsoft.com/v1.0/users/user-1/authentication/fido2Methods/creationOptions"
    )
    assert reg.origin == "https://login.microsoft.com"
    assert "@odata" not in json.dumps(reg.options)
    parsed = parse(reg.options)
    assert parsed.user.id == b"OID:123"
    assert parsed.exclude_credentials[0].id == b"\x01\x02\x03"
    assert parsed.extensions["hmacCreateSecret"] is True

    http.add({"id": "m1"}, status=201)
    entra.complete_registration(reg, response, "A name that is far longer than thirty characters")

    call = http.calls[1]
    assert call.method == "POST"
    assert call.url == "https://graph.microsoft.com/v1.0/users/user-1/authentication/fido2Methods"
    assert len(call.json["displayName"]) == 30
    cred = call.json["publicKeyCredential"]
    assert b64url_decode(cred["id"]) == response.raw_id
    assert "=" not in cred["id"] + cred["response"]["attestationObject"]
    assert b64url_decode(cred["response"]["clientDataJSON"]) == bytes(response.response.client_data)
    assert b64url_decode(cred["response"]["attestationObject"]) == bytes(
        response.response.attestation_object
    )


def test_entra_error_message_is_surfaced(entra, http):
    http.add({"error": {"code": "Authorization_RequestDenied", "message": "Insufficient privileges"}}, status=403)
    with pytest.raises(ProviderError, match="Insufficient privileges") as e:
        entra.preflight(USER)
    assert e.value.status == 403


def test_entra_list_and_delete(entra, http):
    http.add({"value": [{"id": "m1", "displayName": "Key", "createdDateTime": "2026-01-01T00:00:00Z", "model": "YubiKey 5"}]})
    creds = entra.list_credentials(USER)
    assert (creds[0].id, creds[0].name, creds[0].detail) == ("m1", "Key", "YubiKey 5")
    http.add(status=204)
    entra.delete_credential(USER, "m1")
    assert http.calls[1].method == "DELETE"
    assert http.calls[1].url.endswith("/users/user-1/authentication/fido2Methods/m1")


# -- Okta -------------------------------------------------------------------


@pytest.fixture
def okta(http, store, signed_in):
    return signed_in(
        OktaProvider("i1", {"domain": "https://Acme.okta.com/", "client_id": "CLIENT"}, store, http)
    )


OKTA_FACTOR = {
    "id": "fwf1",
    "factorType": "webauthn",
    "status": "PENDING_ACTIVATION",
    "_embedded": {
        "activation": {
            "attestation": "direct",
            "authenticatorSelection": {"userVerification": "preferred", "requireResidentKey": False},
            "challenge": "cdsZ1V10E0BGE4GcG3IK",
            "excludeCredentials": [],
            "pubKeyCredParams": [{"type": "public-key", "alg": -7}, {"type": "public-key", "alg": -257}],
            "rp": {"name": "Acme"},
            "u2fParams": {"appid": "https://acme.okta.com"},
            "user": {"displayName": "Alice A", "name": "alice@example.com", "id": "00u15s1KDETTQMQYABRL"},
        }
    },
}


def test_okta_oauth_config(okta):
    cfg = okta.oauth_config()
    assert cfg.authorize_url == "https://acme.okta.com/oauth2/v1/authorize"
    assert cfg.redirect_uri == "http://localhost:8080/yubienroll-redirect"
    assert {"okta.users.manage", "okta.users.read", "offline_access"} <= set(cfg.scopes)


def test_okta_registration_roundtrip(okta, http, response):
    http.add(OKTA_FACTOR)
    reg = okta.begin_registration(USER)

    assert http.calls[0].url == "https://acme.okta.com/api/v1/users/user-1/factors"
    assert http.calls[0].json == {"factorType": "webauthn", "provider": "FIDO"}
    assert reg.origin == "https://acme.okta.com"
    parsed = parse(reg.options)
    assert parsed.rp.id == "acme.okta.com"
    # The user handle is what a browser derives from the same activation data.
    assert parsed.user.id == b64url_decode("00u15s1KDETTQMQYABRL")
    assert parsed.challenge == b64url_decode("cdsZ1V10E0BGE4GcG3IK")

    http.add({"status": "ACTIVE"})
    okta.complete_registration(reg, response, "ignored")
    call = http.calls[1]
    assert call.url == "https://acme.okta.com/api/v1/users/user-1/factors/fwf1/lifecycle/activate"
    assert base64.b64decode(call.json["attestation"]) == bytes(response.response.attestation_object)
    assert base64.b64decode(call.json["clientData"]) == bytes(response.response.client_data)


def test_okta_cancel_removes_pending_factor(okta, http):
    http.add(OKTA_FACTOR)
    reg = okta.begin_registration(USER)
    http.add(status=204)
    okta.cancel_registration(reg)
    assert (http.calls[1].method, http.calls[1].url) == (
        "DELETE",
        "https://acme.okta.com/api/v1/users/user-1/factors/fwf1",
    )


def test_okta_lists_only_webauthn_factors(okta, http):
    http.add(
        [
            {"id": "a", "factorType": "push", "status": "ACTIVE"},
            {"id": "b", "factorType": "webauthn", "status": "ACTIVE", "created": "2026-01-01", "profile": {"authenticatorName": "YubiKey 5 NFC"}},
        ]
    )
    creds = okta.list_credentials(USER)
    assert [(c.id, c.name) for c in creds] == [("b", "YubiKey 5 NFC")]


def test_okta_error_causes(okta, http):
    http.add({"errorSummary": "Api validation failed", "errorCauses": [{"errorSummary": "Factor already exists."}]}, status=400)
    with pytest.raises(ProviderError, match="Factor already exists"):
        okta.begin_registration(USER)


# -- PingOne ----------------------------------------------------------------


@pytest.fixture
def pingone(http, store, signed_in):
    return signed_in(
        PingOneProvider(
            "i1", {"environment_id": "ENV", "client_id": "CLIENT", "region": "eu"}, store, http
        )
    )


def pingone_device(rp_id="pingone.eu"):
    options = {
        "rp": {"id": rp_id, "name": "PingOne"},
        "user": {"id": [-93, 12, 127, -128], "displayName": "Alice", "name": "alice"},
        "challenge": [1, -2, 3, -4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        "pubKeyCredParams": [{"type": "public-key", "alg": -7}],
        "timeout": 120000,
        "excludeCredentials": [{"type": "public-key", "id": [-1, 0, 1]}],
        "authenticatorSelection": {"residentKey": "required", "userVerification": "required"},
        "attestation": "direct",
    }
    return {
        "id": "dev1",
        "type": "FIDO2",
        "status": "ACTIVATION_REQUIRED",
        "publicKeyCredentialCreationOptions": json.dumps(options),
    }


def test_pingone_endpoints_follow_region_and_custom_domain(pingone, http, store):
    cfg = pingone.oauth_config()
    assert cfg.authorize_url == "https://auth.pingone.eu/ENV/as/authorize"
    assert cfg.token_url == "https://auth.pingone.eu/ENV/as/token"
    custom = PingOneProvider(
        "i2",
        {"environment_id": "ENV", "client_id": "C", "custom_domain": "https://sso.acme.com"},
        store,
        http,
    )
    assert custom.oauth_config().authorize_url == "https://sso.acme.com/as/authorize"
    assert custom._origin("acme.com") == "https://sso.acme.com"
    assert custom._origin("other.example") == "https://other.example"


def test_pingone_search_uses_scim_filter(pingone, http):
    http.add({"_embedded": {"users": [{"id": "1", "username": "alice", "email": "a@x.com", "name": {"given": "Alice", "family": "A"}}]}})
    users = pingone.search_users('al"ice')
    assert users[0].display_name == "Alice A"
    call = http.calls[0]
    assert call.url == "https://api.pingone.eu/v1/environments/ENV/users"
    assert 'username sw "al\\"ice"' in call.params["filter"]


def test_pingone_registration_roundtrip(pingone, http, response):
    http.add(pingone_device(), status=201)
    reg = pingone.begin_registration(USER)

    assert http.calls[0].url == "https://api.pingone.eu/v1/environments/ENV/users/user-1/devices"
    assert http.calls[0].json == {"type": "FIDO2"}
    assert reg.origin == "https://auth.pingone.eu"
    parsed = parse(reg.options)
    assert parsed.user.id == bytes([163, 12, 127, 128])
    assert parsed.challenge[:4] == bytes([1, 254, 3, 252])
    assert parsed.exclude_credentials[0].id == bytes([255, 0, 1])

    http.add({"status": "ACTIVE"})
    http.add({})
    pingone.complete_registration(reg, response, "Alice's key")

    activate, nickname = http.calls[1], http.calls[2]
    assert activate.url.endswith("/users/user-1/devices/dev1")
    assert activate.headers["Content-Type"] == "application/vnd.pingidentity.device.activate+json"
    assert activate.body["origin"] == "https://auth.pingone.eu"
    attestation = json.loads(activate.body["attestation"])
    assert base64.b64decode(attestation["rawId"]) == response.raw_id
    assert base64.b64decode(attestation["response"]["attestationObject"]) == bytes(
        response.response.attestation_object
    )
    assert nickname.method == "PUT" and nickname.json == {"nickname": "Alice's key"}


def test_pingone_policy_id_is_sent(http, store, signed_in, response):
    p = signed_in(
        PingOneProvider(
            "i1", {"environment_id": "ENV", "client_id": "C", "policy_id": "POL"}, store, http
        )
    )
    http.add(pingone_device("pingone.com"), status=201)
    reg = p.begin_registration(USER)
    assert http.calls[0].json == {"type": "FIDO2", "policy": {"id": "POL"}}
    assert http.calls[0].url.startswith("https://api.pingone.com/")
    assert reg.origin == "https://auth.pingone.com"


def test_pingone_nickname_failure_does_not_fail_enrollment(pingone, http, response):
    http.add(pingone_device(), status=201)
    reg = pingone.begin_registration(USER)
    http.add({"status": "ACTIVE"})
    http.add({"message": "nope"}, status=400)
    pingone.complete_registration(reg, response, "name")


def test_pingone_lists_only_fido2_devices(pingone, http):
    http.add({"_embedded": {"devices": [{"id": "s", "type": "SMS"}, {"id": "f", "type": "FIDO2", "nickname": "Key", "status": "ACTIVE"}]}})
    assert [(c.id, c.name) for c in pingone.list_credentials(USER)] == [("f", "Key")]


# -- PingOne AIC ------------------------------------------------------------


@pytest.fixture
def aic(http, store, signed_in):
    return signed_in(
        PingOneAicProvider(
            "i1",
            {"tenant": "openam-acme.forgeblocks.com", "journey": "YubiEnroll", "client_id": "C"},
            store,
            http,
        )
    )


NAME_STEP = {
    "authId": "AUTH1",
    "callbacks": [
        {
            "type": "NameCallback",
            "output": [{"name": "prompt", "value": "User Name"}],
            "input": [{"name": "IDToken1", "value": ""}],
        }
    ],
}


def webauthn_step(metadata: bool = True, json_response: bool = True):
    challenge = base64.b64encode(bytes(range(32))).decode()
    hidden = {
        "type": "HiddenValueCallback",
        "output": [{"name": "value", "value": "false"}, {"name": "id", "value": "webAuthnOutcome"}],
        "input": [{"name": "IDToken2", "value": "webAuthnOutcome"}],
    }
    if metadata:
        first = {
            "type": "MetadataCallback",
            "output": [
                {
                    "name": "data",
                    "value": {
                        "_action": "webauthn_registration",
                        "_type": "WebAuthn",
                        "challenge": challenge,
                        "attestationPreference": "direct",
                        "userName": "alice",
                        "userId": "YWxpY2U",
                        "relyingPartyName": "Acme",
                        "_relyingPartyId": "forgeblocks.com",
                        "relyingPartyId": 'id: "forgeblocks.com",',
                        "_authenticatorSelection": {"userVerification": "required", "residentKey": "required"},
                        "_pubKeyCredParams": [{"type": "public-key", "alg": -7}],
                        "_excludeCredentials": [{"type": "public-key", "id": [1, -1, 2]}],
                        "timeout": "60000",
                        "displayName": "alice",
                        "supportsJsonResponse": json_response,
                    },
                }
            ],
        }
    else:
        script = """
        var publicKey = {
            challenge: new Int8Array([0, 1, 2, -3]).buffer,
            rp: { id: "forgeblocks.com", name: "Acme" },
            user: { id: Uint8Array.from("YWxpY2U", function (c) { return c.charCodeAt(0) }), name: "alice", displayName: "alice" },
            pubKeyCredParams: [ { "type": "public-key", "alg": -7 } ],
            attestation: "none",
            timeout: 60000,
            excludeCredentials: [{ "type": "public-key", "id": new Int8Array([1, -1, 2]).buffer }],
            authenticatorSelection: {"userVerification":"required"}
        };"""
        first = {"type": "TextOutputCallback", "output": [{"name": "message", "value": script}, {"name": "messageType", "value": "4"}]}
    return {"authId": "AUTH2", "callbacks": [first, hidden]}


def test_aic_endpoints(aic):
    cfg = aic.oauth_config()
    assert cfg.authorize_url == (
        "https://openam-acme.forgeblocks.com/am/oauth2/realms/root/realms/alpha/authorize"
    )
    assert cfg.token_url.endswith("/realms/alpha/access_token")
    assert cfg.scopes == ["openid", "profile", "fr:idm:*"]
    assert not aic.supports_credential_list


def test_aic_search(aic, http):
    http.add({"result": [{"_id": "uuid", "userName": "alice", "givenName": "Alice", "sn": "A", "mail": "a@x.com"}]})
    users = aic.search_users("ali")
    assert users[0].id == "uuid" and users[0].display_name == "Alice A"
    call = http.calls[0]
    assert call.url == "https://openam-acme.forgeblocks.com/openidm/managed/alpha_user"
    assert 'userName co "ali"' in call.params["_queryFilter"]


def test_aic_registration_roundtrip(aic, http, response):
    http.add(NAME_STEP)
    http.add(webauthn_step())
    reg = aic.begin_registration(USER)

    start, submit = http.calls
    assert start.url == "https://openam-acme.forgeblocks.com/am/json/realms/root/realms/alpha/authenticate"
    assert start.params == {"authIndexType": "service", "authIndexValue": "YubiEnroll"}
    # The operator's token accompanies every journey call.
    assert start.headers["Authorization"] == submit.headers["Authorization"] == "Bearer ACCESS"
    assert submit.body["authId"] == "AUTH1"
    assert submit.body["callbacks"][0]["input"][0]["value"] == "alice@example.com"

    assert reg.origin == "https://openam-acme.forgeblocks.com"
    parsed = parse(reg.options)
    assert parsed.rp.id == "forgeblocks.com"
    assert parsed.challenge == bytes(range(32))
    assert parsed.user.id == b"YWxpY2U"
    assert parsed.exclude_credentials[0].id == bytes([1, 255, 2])

    http.add({"tokenId": "SESSION", "successUrl": "/enduser"})
    aic.complete_registration(reg, response, "Alice's key")

    final = http.calls[2].body
    assert final["authId"] == "AUTH2"
    outcome = json.loads(final["callbacks"][1]["input"][0]["value"])
    assert outcome["authenticatorAttachment"] == "cross-platform"
    client_data, att, cred_id, name = outcome["legacyData"].split("::")
    assert client_data == bytes(response.response.client_data).decode()
    assert bytes(int(n) & 0xFF for n in att.split(",")) == bytes(response.response.attestation_object)
    assert b64url_decode(cred_id) == response.raw_id
    assert name == "Alice's key"


def test_aic_legacy_outcome_without_json_support(aic, http, response):
    http.add(NAME_STEP)
    http.add(webauthn_step(json_response=False))
    reg = aic.begin_registration(USER)
    http.add({"tokenId": "SESSION"})
    aic.complete_registration(reg, response, "")
    value = http.calls[2].body["callbacks"][1]["input"][0]["value"]
    assert value.count("::") == 2 and "legacyData" not in value
    assert value.startswith(bytes(response.response.client_data).decode() + "::")


def test_aic_javascript_challenge_is_parsed(aic, http):
    http.add(NAME_STEP)
    http.add(webauthn_step(metadata=False))
    reg = aic.begin_registration(USER)
    parsed = parse(reg.options)
    assert parsed.challenge == bytes([0, 1, 2, 253])
    assert parsed.rp.id == "forgeblocks.com" and parsed.rp.name == "Acme"
    assert parsed.user.id == b"YWxpY2U" and parsed.user.name == "alice"
    assert parsed.exclude_credentials[0].id == bytes([1, 255, 2])
    assert parsed.authenticator_selection.user_verification == "required"


def test_aic_unparseable_script_explains_the_fix():
    with pytest.raises(ProviderError, match="Return challenge as JavaScript"):
        options_from_script("var x = 1;", "host")


def test_aic_journey_with_extra_prompt_is_rejected(aic, http):
    step = json.loads(json.dumps(NAME_STEP))
    step["callbacks"].append({"type": "PasswordCallback", "output": [], "input": [{"name": "IDToken2", "value": ""}]})
    http.add(step)
    with pytest.raises(ProviderError, match="single username prompt"):
        aic.begin_registration(USER)


def test_aic_failed_journey_is_not_mistaken_for_expired_session(aic, http, store):
    http.add(NAME_STEP)
    http.add({"code": 401, "reason": "Unauthorized", "message": "Login failure"}, status=401)
    with pytest.raises(ProviderError, match="Login failure") as e:
        aic.begin_registration(USER)
    assert not isinstance(e.value, AuthRequired)
    assert len(http.calls) == 2  # no token refresh, no retry
    assert aic.has_session()


def test_aic_incomplete_journey_after_registration(aic, http, response):
    http.add(NAME_STEP)
    http.add(webauthn_step())
    reg = aic.begin_registration(USER)
    http.add(webauthn_step())
    with pytest.raises(ProviderError, match="did not complete"):
        aic.complete_registration(reg, response, "")


# -- exact user lookup (bulk import) ---------------------------------------


def test_entra_find_user_by_upn_then_by_mail(entra, http):
    http.add({"id": "1", "displayName": "Alice", "userPrincipalName": "alice@x.com", "mail": "a@x.com"})
    user = entra.find_user(" alice@x.com ")
    assert user.id == "1"
    assert http.calls[0].url == "https://graph.microsoft.com/v1.0/users/alice%40x.com"

    http.add({"error": {"code": "Request_ResourceNotFound", "message": "not found"}}, status=404)
    http.add({"value": [{"id": "2", "displayName": "Pat", "userPrincipalName": "pat@x.com", "mail": "o'neil@x.com"}]})
    assert entra.find_user("o'neil@x.com").id == "2"
    assert http.calls[2].params["$filter"] == "mail eq 'o''neil@x.com'"

    http.add({"error": {"message": "not found"}}, status=404)
    http.add({"value": []})
    assert entra.find_user("ghost@x.com") is None


def test_entra_find_user_encodes_guest_upn(entra, http):
    http.add({"id": "3", "userPrincipalName": "ext_user#EXT#@x.onmicrosoft.com"})
    entra.find_user("ext_user#EXT#@x.onmicrosoft.com")
    assert "#" not in http.calls[0].url and "%23EXT%23" in http.calls[0].url


def test_entra_find_user_does_not_hide_permission_errors(entra, http):
    http.add({"error": {"message": "Insufficient privileges"}}, status=403)
    with pytest.raises(ProviderError, match="Insufficient privileges"):
        entra.find_user("alice@x.com")


def test_okta_find_user(okta, http):
    http.add({"id": "00u1", "profile": {"login": "alice@x.com", "firstName": "Alice", "lastName": "A", "email": "alice@x.com"}})
    user = okta.find_user("alice@x.com")
    assert (user.id, user.display_name) == ("00u1", "Alice A")
    assert http.calls[0].url == "https://acme.okta.com/api/v1/users/alice%40x.com"
    http.add({"errorSummary": "Not found: Resource not found"}, status=404)
    assert okta.find_user("ghost@x.com") is None


def test_pingone_find_user_requires_a_single_exact_match(pingone, http):
    http.add({"_embedded": {"users": [{"id": "1", "username": "alice", "email": "a@x.com"}]}})
    assert pingone.find_user("alice").id == "1"
    assert http.calls[0].params["filter"] == 'username eq "alice" or email eq "alice"'
    http.add({"_embedded": {"users": [{"id": "1", "username": "a"}, {"id": "2", "username": "b"}]}})
    assert pingone.find_user("shared@x.com") is None
    http.add({})
    assert pingone.find_user("ghost") is None


def test_aic_find_user(aic, http):
    http.add({"result": [{"_id": "uuid", "userName": "alice", "mail": "a@x.com"}]})
    assert aic.find_user("alice").id == "uuid"
    assert http.calls[0].params["_queryFilter"] == 'userName eq "alice" or mail eq "alice"'
    http.add({"result": []})
    assert aic.find_user("ghost") is None
