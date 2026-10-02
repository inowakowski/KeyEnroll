"""OAuth 2.0 authorization code flow with PKCE for public (native) clients.

The authorization response is received on a loopback HTTP listener, the same
way the YubiEnroll CLI does it, so the redirect URI registered at the identity
provider must start with http://localhost.
"""

from __future__ import annotations

import base64
import hashlib
import html
import logging
import queue
import secrets
import socket
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import requests

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30


class OAuthError(Exception):
    pass


class LoginCancelled(OAuthError):
    pass


@dataclass
class OAuthConfig:
    authorize_url: str
    token_url: str
    client_id: str
    redirect_uri: str
    scopes: list[str]
    revoke_url: str | None = None
    extra_authorize_params: dict[str, str] = field(default_factory=dict)


@dataclass
class TokenSet:
    access_token: str
    expires_at: float
    refresh_token: str | None = None

    @classmethod
    def from_response(cls, data: dict) -> TokenSet:
        try:
            expires_in = float(data.get("expires_in") or 3600)
        except (TypeError, ValueError):
            expires_in = 3600.0
        return cls(
            access_token=data["access_token"],
            expires_at=time.time() + expires_in,
            refresh_token=data.get("refresh_token"),
        )


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_pkce() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(48))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


_DONE_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>KeyEnroll</title></head>
<body style="font-family:sans-serif;text-align:center;margin-top:4em">
<h2>{title}</h2><p>{detail}</p></body></html>"""


class _Server(HTTPServer):
    allow_reuse_address = False

    def handle_error(self, request, client_address):  # keep stderr clean
        logger.debug("Callback request error", exc_info=True)


class _Server6(_Server):
    address_family = socket.AF_INET6


class CallbackListener:
    """Loopback HTTP listener receiving the authorization response."""

    def __init__(self, redirect_uri: str):
        parts = urlsplit(redirect_uri)
        if parts.scheme != "http" or parts.hostname not in ("localhost", "127.0.0.1"):
            raise OAuthError("Redirect URI must start with http://localhost")
        self._parts = parts
        self._path = parts.path or "/"
        self._results: queue.Queue[dict[str, str]] = queue.Queue()
        self._servers: list[HTTPServer] = []

        handler = self._make_handler()
        try:
            server = _Server(("127.0.0.1", parts.port or 0), handler)
        except OSError as e:
            raise OAuthError(
                f"Cannot listen on port {parts.port} required by the redirect URI: {e}"
            ) from e
        self._servers.append(server)
        self.port = server.server_address[1]
        try:  # browsers may resolve localhost to ::1 first
            self._servers.append(_Server6(("::1", self.port), handler))
        except OSError:
            logger.debug("IPv6 loopback not available for callback listener")

        for s in self._servers:
            threading.Thread(target=s.serve_forever, args=(0.2,), daemon=True).start()

    @property
    def redirect_uri(self) -> str:
        host = self._parts.hostname or "localhost"
        return urlunsplit(("http", f"{host}:{self.port}", self._path, "", ""))

    def _make_handler(self):
        listener = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parts = urlsplit(self.path)
                if parts.path != listener._path:
                    self.send_error(404)
                    return
                params = {k: v[0] for k, v in parse_qs(parts.query).items()}
                if "code" not in params and "error" not in params:
                    self.send_error(400)
                    return
                if "error" in params:
                    title = "Sign-in failed"
                    detail = params.get("error_description") or params["error"]
                else:
                    title = "Signed in"
                    detail = "You can close this window and return to KeyEnroll."
                body = _DONE_PAGE.format(
                    title=html.escape(title), detail=html.escape(detail)
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                listener._results.put(params)

            def log_message(self, fmt, *args):
                # The query string carries the authorization code: keep it
                # out of the log.
                logger.debug("callback: %s %s", self.command, urlsplit(self.path).path)

        return Handler

    def wait(self, cancel: threading.Event | None, timeout: float) -> dict[str, str]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cancel is not None and cancel.is_set():
                raise LoginCancelled("Sign-in cancelled")
            try:
                return self._results.get(timeout=0.2)
            except queue.Empty:
                continue
        raise OAuthError("Timed out waiting for sign-in to complete")

    def close(self) -> None:
        for s in self._servers:
            s.shutdown()
            s.server_close()
        self._servers = []


def _token_request(cfg: OAuthConfig, data: dict, http) -> TokenSet:
    try:
        resp = http.post(
            cfg.token_url,
            data=data,
            headers={"Accept": "application/json"},
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException as e:
        raise OAuthError(f"Token request failed: {e}") from e
    try:
        payload = resp.json()
    except ValueError:
        payload = {}
    if resp.status_code != 200 or "access_token" not in payload:
        detail = (
            payload.get("error_description")
            or payload.get("error")
            or f"HTTP {resp.status_code}"
        )
        raise OAuthError(f"Token request failed: {detail}")
    return TokenSet.from_response(payload)


def authorize(
    cfg: OAuthConfig,
    open_browser: Callable[[str], None],
    cancel: threading.Event | None = None,
    timeout: float = 300,
    http=None,
) -> TokenSet:
    """Runs the interactive sign-in and returns the resulting tokens."""
    http = http or requests
    verifier, challenge = make_pkce()
    state = _b64url(secrets.token_bytes(16))
    listener = CallbackListener(cfg.redirect_uri)
    try:
        redirect_uri = listener.redirect_uri
        params = {
            "response_type": "code",
            "client_id": cfg.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(cfg.scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            **cfg.extra_authorize_params,
        }
        sep = "&" if "?" in cfg.authorize_url else "?"
        open_browser(cfg.authorize_url + sep + urlencode(params))
        result = listener.wait(cancel, timeout)
    finally:
        listener.close()

    if "error" in result:
        raise OAuthError(result.get("error_description") or result["error"])
    if result.get("state") != state:
        raise OAuthError("Authorization response state mismatch")

    return _token_request(
        cfg,
        {
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": redirect_uri,
            "client_id": cfg.client_id,
            "code_verifier": verifier,
        },
        http,
    )


def refresh(cfg: OAuthConfig, refresh_token: str, http=None) -> TokenSet:
    tokens = _token_request(
        cfg,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cfg.client_id,
            "scope": " ".join(cfg.scopes),
        },
        http or requests,
    )
    if not tokens.refresh_token:  # provider did not rotate it
        tokens.refresh_token = refresh_token
    return tokens


def revoke(cfg: OAuthConfig, token: str, http=None) -> None:
    if not cfg.revoke_url:
        return
    try:
        (http or requests).post(
            cfg.revoke_url,
            data={
                "token": token,
                "token_type_hint": "refresh_token",
                "client_id": cfg.client_id,
            },
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException:
        logger.warning("Token revocation failed", exc_info=True)
