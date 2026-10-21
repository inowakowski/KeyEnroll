"""Updates: finding a newer release, downloading it safely, starting its installer.

Nothing happens in the background unless the operator switched on the check
at start-up, and nothing is installed without the operator's confirmation.
The answers come from the public GitHub releases API.

A downloaded file is used only if its SHA-256 matches the checksum GitHub
reports for it. When the application carries the project's release key
(release_key.py), the release must also contain SHA256SUMS signed with that
key: the key never touches GitHub, so someone who takes over the GitHub
account cannot slip in a file of their own.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import logging
import platform
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import requests

from . import PROJECT_URL, __version__
from .i18n import N_
from .release_key import PUBLIC_KEYS

logger = logging.getLogger(__name__)

TIMEOUT = 15
CHUNK = 256 * 1024
SUMS = "SHA256SUMS"
SIGNATURE = "SHA256SUMS.sig"


class UpdateError(Exception):
    """Carries an untranslated message for the operator."""


class UpdateCancelled(UpdateError):
    def __init__(self):
        super().__init__(N_("The download was cancelled."))


@dataclass
class Asset:
    name: str
    url: str
    size: int = 0
    sha256: str = ""  # as reported by GitHub; empty if it did not say


@dataclass
class UpdateInfo:
    current: str
    latest: str
    url: str  # release page to open in the browser
    assets: list[Asset] = field(default_factory=list)
    prerelease: bool = False

    @property
    def newer(self) -> bool:
        return version_key(self.latest) > version_key(self.current)

    def asset(self, name: str) -> Asset | None:
        return next((a for a in self.assets if a.name == name), None)


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.12.0' -> (1, 12, 0). Anything after the numbers (rc1, +build) is ignored."""
    match = re.match(r"\s*v?(\d+(?:\.\d+)*)", text or "")
    if not match:
        raise ValueError(f"not a version: {text!r}")
    parts = [int(p) for p in match.group(1).split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()  # 1.0 and 1.0.0 are the same release
    return tuple(parts)


_PRERELEASE = re.compile(r"\s*v?\d+(?:\.\d+)*[-._]?(?:a|alpha|b|beta|c|rc|pre|preview|dev)", re.I)


def version_key(text: str) -> tuple[tuple[int, ...], int]:
    """Orders versions, a preview before the release it leads to:
    0.7.0-preview.1 < 0.7.0 < 0.7.1."""
    return parse_version(text), 0 if _PRERELEASE.match(text or "") else 1


def _owner_repo(project_url: str = PROJECT_URL) -> str:
    return project_url.rstrip("/").split("github.com/", 1)[1]


def api_url(project_url: str = PROJECT_URL) -> str:
    return f"https://api.github.com/repos/{_owner_repo(project_url)}/releases/latest"


def _list_url(project_url: str = PROJECT_URL) -> str:
    return f"https://api.github.com/repos/{_owner_repo(project_url)}/releases"


def _download_prefix() -> str:
    return f"{PROJECT_URL}/releases/download/"


def _get(http, url: str, current: str, params: dict | None = None):
    kwargs = {"params": params} if params else {}
    try:
        resp = http.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"KeyEnroll/{current}",
            },
            timeout=TIMEOUT,
            **kwargs,
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
        return resp.json()
    except ValueError as e:
        raise UpdateError(N_("The update server returned an unexpected answer.")) from e


def _assets(data: dict) -> list[Asset]:
    out = []
    for item in data.get("assets") or []:
        if not isinstance(item, dict):
            continue
        digest = str(item.get("digest") or "")
        out.append(
            Asset(
                name=str(item.get("name") or ""),
                url=str(item.get("browser_download_url") or ""),
                size=int(item.get("size") or 0),
                sha256=digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else "",
            )
        )
    return out


def _info(data: dict, current: str) -> UpdateInfo:
    try:
        latest = str(data["tag_name"])
        parse_version(latest)
        page = str(data.get("html_url") or "")
    except (ValueError, KeyError, TypeError) as e:
        raise UpdateError(N_("The update server returned an unexpected answer.")) from e
    # Only ever send the operator to the project's own release pages.
    if not page.startswith(PROJECT_URL + "/releases/"):
        page = f"{PROJECT_URL}/releases"
    return UpdateInfo(
        current=current,
        latest=latest.lstrip("v"),
        url=page,
        assets=_assets(data),
        prerelease=bool(data.get("prerelease")),
    )


def check(http=None, current: str = __version__, previews: bool = False) -> UpdateInfo:
    """Asks GitHub for the newest published release; with ``previews`` also
    for pre-releases, which GitHub never reports as the latest one."""
    http = http or requests
    if not previews:
        data = _get(http, api_url(), current)
        if not isinstance(data, dict):
            raise UpdateError(N_("The update server returned an unexpected answer."))
        return _info(data, current)

    data = _get(http, _list_url(), current, params={"per_page": "30"})
    if not isinstance(data, list):
        raise UpdateError(N_("The update server returned an unexpected answer."))
    candidates = []
    for item in data:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        try:
            candidates.append((version_key(str(item.get("tag_name"))), item))
        except ValueError:
            continue
    if not candidates:
        raise UpdateError(N_("No published release was found."))
    return _info(max(candidates, key=lambda c: c[0])[1], current)


# -- which file fits this computer ----------------------------------------------


def installer_kind(
    platform_name: str = sys.platform,
    frozen: bool = bool(getattr(sys, "frozen", False)),
    executable: str = sys.executable,
) -> str | None:
    """How this copy was installed: "windows", "macos", "deb" or "tar".
    None when it runs from source, which an installer must not replace."""
    if not frozen:
        return None
    if platform_name == "win32":
        return "windows"
    if platform_name == "darwin":
        return "macos"
    return "deb" if executable.startswith("/opt/keyenroll/") else "tar"


def machine_arch(machine: str | None = None) -> str:
    machine = (machine if machine is not None else platform.machine()).lower()
    return "arm64" if machine in ("arm64", "aarch64") else "x64"


def pick_asset(info: UpdateInfo, kind: str | None, arch: str) -> Asset | None:
    """The release file for this kind of installation and processor."""
    suffix = {
        "windows": f"-windows-{arch}-setup.exe",
        "macos": f"-macos-{arch}.dmg",
        "deb": "_arm64.deb" if arch == "arm64" else "_amd64.deb",
        "tar": f"-linux-{arch}.tar.gz",
    }.get(kind or "")
    if suffix is None:
        return None
    return next(
        (
            a
            for a in info.assets
            if a.name.lower().startswith("keyenroll") and a.name.lower().endswith(suffix)
        ),
        None,
    )


# -- verified download -------------------------------------------------------------


def parse_sums(text: str) -> dict[str, str]:
    """'<sha256>  <file name>' lines, as written by sha256sum."""
    sums = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *](.+)", line.strip())
        if match:
            sums[match.group(2).strip()] = match.group(1).lower()
    return sums


def verify_signature(sums: bytes, signature: bytes, keys=PUBLIC_KEYS) -> bool:
    """True if ``signature`` (base64, Ed25519) was made over ``sums`` with
    one of the project's release keys."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        raw = base64.b64decode(signature.strip(), validate=True)
    except (binascii.Error, ValueError):
        return False
    for key in keys:
        try:
            Ed25519PublicKey.from_public_bytes(base64.b64decode(key)).verify(raw, sums)
            return True
        except (InvalidSignature, ValueError):
            continue
    return False


def _small(http, asset: Asset) -> bytes:
    try:
        resp = http.get(asset.url, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise UpdateError(N_("Could not reach the update server. Check the connection.")) from e
    if resp.status_code != 200 or len(resp.content) > 1_000_000:
        raise UpdateError(N_("The update server returned an unexpected answer."))
    return resp.content


def expected_sha256(info: UpdateInfo, asset: Asset, http=None, keys=PUBLIC_KEYS) -> str:
    """The checksum the downloaded file must have.

    GitHub reports one for every file. With a release key in this build, the
    signed SHA256SUMS of the release has to agree with it as well."""
    if not re.fullmatch(r"[0-9a-f]{64}", asset.sha256):
        raise UpdateError(
            N_("The update server did not provide a checksum for this file. Install it from the download page.")
        )
    if not keys:
        return asset.sha256
    sums_asset, signature_asset = info.asset(SUMS), info.asset(SIGNATURE)
    if sums_asset is None or signature_asset is None:
        raise UpdateError(
            N_("This release is not signed with the project's key. Install it from the download page.")
        )
    http = http or requests
    for a in (sums_asset, signature_asset):
        if not a.url.startswith(_download_prefix()):
            raise UpdateError(N_("The update server returned an unexpected answer."))
    sums = _small(http, sums_asset)
    if not verify_signature(sums, _small(http, signature_asset), keys):
        raise UpdateError(
            N_("The signature of this release is not valid. Do not install it; report it to the project.")
        )
    if parse_sums(sums.decode("utf-8", "replace")).get(asset.name) != asset.sha256:
        raise UpdateError(
            N_("The signature of this release is not valid. Do not install it; report it to the project.")
        )
    return asset.sha256


def download(
    info: UpdateInfo,
    asset: Asset,
    folder: Path,
    http=None,
    progress: Callable[[int, int], None] | None = None,
    cancel: threading.Event | None = None,
    keys=PUBLIC_KEYS,
) -> Path:
    """Downloads ``asset`` into ``folder`` and returns the file, after its
    checksum (and the release signature, see above) proved it genuine.
    A file that does not match is deleted."""
    if not asset.url.startswith(_download_prefix()) or "/" in asset.name or "\\" in asset.name:
        raise UpdateError(N_("The update server returned an unexpected answer."))
    http = http or requests
    expected = expected_sha256(info, asset, http, keys)

    folder.mkdir(parents=True, exist_ok=True)
    target = folder / asset.name
    partial = folder / (asset.name + ".part")
    digest = hashlib.sha256()
    done = 0
    try:
        with http.get(asset.url, stream=True, timeout=TIMEOUT) as resp:
            if resp.status_code != 200:
                raise UpdateError(N_("The update server returned an unexpected answer."))
            total = asset.size or int(resp.headers.get("Content-Length") or 0)
            with open(partial, "wb") as f:
                for chunk in resp.iter_content(CHUNK):
                    if cancel is not None and cancel.is_set():
                        raise UpdateCancelled()
                    f.write(chunk)
                    digest.update(chunk)
                    done += len(chunk)
                    if progress is not None:
                        progress(done, total)
    except requests.RequestException as e:
        partial.unlink(missing_ok=True)
        raise UpdateError(N_("The download failed. Check the connection and try again.")) from e
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    if digest.hexdigest() != expected:
        partial.unlink(missing_ok=True)
        logger.warning("Update %s: checksum mismatch", asset.name)
        raise UpdateError(
            N_("The downloaded file is not the one that was published. It was deleted.")
        )
    partial.replace(target)
    logger.info("Update %s downloaded and verified", asset.name)
    return target


def launch_windows_installer(path: Path) -> None:
    """Runs the Inno Setup installer without its wizard. It waits for this
    application to close, replaces it and starts the new version
    (installer.iss: /relaunch=1)."""
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    subprocess.Popen(
        [str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS", "/relaunch=1"],
        creationflags=flags,
        close_fds=True,
    )
