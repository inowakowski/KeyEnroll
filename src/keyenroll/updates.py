"""Checking whether a newer release has been published.

Only done when the operator asks for it; nothing is downloaded or installed.
The answer comes from the public GitHub releases API, so it only works while
the project's releases are publicly visible.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests

from . import PROJECT_URL, __version__
from .i18n import N_

TIMEOUT = 15


class UpdateError(Exception):
    """Carries an untranslated message for the operator."""


@dataclass
class UpdateInfo:
    current: str
    latest: str
    url: str  # release page to open in the browser

    @property
    def newer(self) -> bool:
        return parse_version(self.latest) > parse_version(self.current)


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.12.0' -> (1, 12, 0). Anything after the numbers (rc1, +build) is ignored."""
    match = re.match(r"\s*v?(\d+(?:\.\d+)*)", text or "")
    if not match:
        raise ValueError(f"not a version: {text!r}")
    parts = [int(p) for p in match.group(1).split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()  # 1.0 and 1.0.0 are the same release
    return tuple(parts)


def api_url(project_url: str = PROJECT_URL) -> str:
    owner_repo = project_url.rstrip("/").split("github.com/", 1)[1]
    return f"https://api.github.com/repos/{owner_repo}/releases/latest"


def check(http=None, current: str = __version__) -> UpdateInfo:
    """Asks GitHub for the latest published release."""
    http = http or requests
    try:
        resp = http.get(
            api_url(),
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"KeyEnroll/{current}",
            },
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        raise UpdateError(N_("Could not reach the update server. Check the connection.")) from e

    if resp.status_code == 404:
        # No release yet, or the repository is not public.
        raise UpdateError(N_("No published release was found."))
    if resp.status_code in (403, 429):
        raise UpdateError(N_("The update server is busy. Try again in a few minutes."))
    if resp.status_code != 200:
        raise UpdateError(N_("The update server returned an unexpected answer."))
    try:
        data = resp.json()
        latest = str(data["tag_name"])
        parse_version(latest)
        page = str(data.get("html_url") or "")
    except (ValueError, KeyError, TypeError) as e:
        raise UpdateError(N_("The update server returned an unexpected answer.")) from e

    # Only ever send the operator to the project's own release pages.
    if not page.startswith(PROJECT_URL + "/releases/"):
        page = f"{PROJECT_URL}/releases"
    return UpdateInfo(current=current, latest=latest.lstrip("v"), url=page)
