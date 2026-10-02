from __future__ import annotations

import base64
import hashlib
import threading
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from keyenroll import oauth


def cfg(redirect="http://localhost/cb"):
    return oauth.OAuthConfig(
        authorize_url="https://idp.example/authorize",
        token_url="https://idp.example/token",
        client_id="CLIENT",
        redirect_uri=redirect,
        scopes=["openid", "offline_access"],
    )


def browser(reply, seen):
    """Simulates the browser: records the authorize URL, then hits the redirect."""

    def open_url(url):
        query = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
        seen.update(query)

        def go():
            target = query["redirect_uri"] + "?" + urlencode(reply(query))
            try:
                urllib.request.urlopen(target, timeout=5).read()
            except urllib.error.URLError:
                pass

        threading.Thread(target=go, daemon=True).start()

    return open_url


def test_authorization_code_flow_with_pkce(http):
    seen = {}
    http.add({"access_token": "AT", "refresh_token": "RT", "expires_in": 600})

    tokens = oauth.authorize(
        cfg(), browser(lambda q: {"code": "CODE", "state": q["state"]}, seen), http=http
    )

    assert (tokens.access_token, tokens.refresh_token) == ("AT", "RT")
    assert seen["response_type"] == "code" and seen["code_challenge_method"] == "S256"
    # No port registered: an ephemeral one is chosen and sent to the provider.
    assert urlsplit(seen["redirect_uri"]).port
    form = http.calls[0].data
    assert form["grant_type"] == "authorization_code" and form["code"] == "CODE"
    assert form["redirect_uri"] == seen["redirect_uri"]
    expected = base64.urlsafe_b64encode(
        hashlib.sha256(form["code_verifier"].encode()).digest()
    ).rstrip(b"=")
    assert seen["code_challenge"] == expected.decode()


def test_state_mismatch_is_rejected(http):
    with pytest.raises(oauth.OAuthError, match="state mismatch"):
        oauth.authorize(cfg(), browser(lambda q: {"code": "C", "state": "forged"}, {}), http=http)
    assert http.calls == []


def test_provider_error_is_reported(http):
    def reply(q):
        return {"error": "access_denied", "error_description": "User declined", "state": q["state"]}

    with pytest.raises(oauth.OAuthError, match="User declined"):
        oauth.authorize(cfg(), browser(reply, {}), http=http)


def test_cancel_stops_waiting_and_frees_the_port(http):
    cancel = threading.Event()
    ports = []

    def open_url(url):
        ports.append(urlsplit(parse_qs(urlsplit(url).query)["redirect_uri"][0]).port)
        cancel.set()

    with pytest.raises(oauth.LoginCancelled):
        oauth.authorize(cfg(), open_url, cancel, http=http)
    listener = oauth.CallbackListener(f"http://localhost:{ports[0]}/cb")
    listener.close()


def test_fixed_port_from_redirect_uri_is_used(http):
    probe = oauth.CallbackListener("http://localhost/cb")
    port = probe.port
    probe.close()
    seen = {}
    http.add({"access_token": "AT"})
    oauth.authorize(
        cfg(f"http://localhost:{port}/yubienroll-redirect"),
        browser(lambda q: {"code": "C", "state": q["state"]}, seen),
        http=http,
    )
    assert seen["redirect_uri"] == f"http://localhost:{port}/yubienroll-redirect"


def test_port_in_use_gives_a_clear_error():
    first = oauth.CallbackListener("http://localhost/cb")
    try:
        with pytest.raises(oauth.OAuthError, match="Cannot listen on port"):
            oauth.CallbackListener(f"http://localhost:{first.port}/cb")
    finally:
        first.close()


def test_non_loopback_redirect_is_refused():
    with pytest.raises(oauth.OAuthError):
        oauth.CallbackListener("https://example.com/cb")


def test_token_error_description(http):
    http.add({"error": "invalid_grant", "error_description": "AADSTS70000: expired"}, status=400)
    with pytest.raises(oauth.OAuthError, match="AADSTS70000"):
        oauth.refresh(cfg(), "RT", http)


def test_refresh_keeps_old_refresh_token_when_not_rotated(http):
    http.add({"access_token": "AT2", "expires_in": "3600"})
    tokens = oauth.refresh(cfg(), "RT", http)
    assert tokens.refresh_token == "RT"
