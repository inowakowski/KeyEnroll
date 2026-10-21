"""Updates from inside the application: choosing the release and the file,
downloading it and proving it genuine before anything is run."""

from __future__ import annotations

import base64
import hashlib
import threading
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from keyenroll import PROJECT_URL, updates
from keyenroll.updates import Asset, UpdateError, UpdateInfo

PAYLOAD = b"installer bytes " * 5000
DOWNLOAD = f"{PROJECT_URL}/releases/download/v0.8.0/"


class Response:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code = status
        self._body = body
        self.content = content
        self.headers = {"Content-Length": str(len(content))}

    def json(self):
        return self._body

    def iter_content(self, size):
        for i in range(0, len(self.content), size):
            yield self.content[i : i + size]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Http:
    """Answers by URL; records what was asked."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        return self.routes[url]


def release(tag, prerelease=False, draft=False, assets=()):
    return {
        "tag_name": tag,
        "html_url": f"{PROJECT_URL}/releases/tag/{tag}",
        "prerelease": prerelease,
        "draft": draft,
        "assets": list(assets),
    }


def asset_json(name, content=PAYLOAD, digest=True):
    return {
        "name": name,
        "browser_download_url": DOWNLOAD + name,
        "size": len(content),
        "digest": "sha256:" + hashlib.sha256(content).hexdigest() if digest else None,
    }


# -- which release -------------------------------------------------------------


def test_previews_are_offered_only_when_asked_for():
    listing = [
        release("v0.8.0-preview.2", prerelease=True),
        release("v0.9.0", draft=True),  # never offered
        release("v0.7.0"),
        release("not-a-version"),
    ]
    http = Http({
        updates.api_url(): Response(body=release("v0.7.0")),
        "https://api.github.com/repos/inowakowski/KeyEnroll/releases": Response(body=listing),
    })  # fmt: skip

    assert updates.check(http, current="0.7.0").latest == "0.7.0"
    newest = updates.check(http, current="0.7.0", previews=True)
    assert (newest.latest, newest.prerelease, newest.newer) == ("0.8.0-preview.2", True, True)


def test_release_files_and_their_checksums_are_read():
    data = release("v0.8.0", assets=[asset_json("KeyEnroll-0.8.0-windows-x64-setup.exe")])
    info = updates.check(Http({updates.api_url(): Response(body=data)}), current="0.7.0")
    (asset,) = info.assets
    assert asset.sha256 == hashlib.sha256(PAYLOAD).hexdigest() and asset.size == len(PAYLOAD)


# -- which file ------------------------------------------------------------------


NAMES = [
    "KeyEnroll-0.8.0-windows-x64-setup.exe",
    "KeyEnroll-0.8.0-windows-arm64-setup.exe",
    "KeyEnroll-0.8.0-macos-arm64.dmg",
    "KeyEnroll-0.8.0-macos-x64.dmg",
    "keyenroll_0.8.0_amd64.deb",
    "keyenroll_0.8.0_arm64.deb",
    "KeyEnroll-0.8.0-linux-x64.tar.gz",
    "KeyEnroll-0.8.0-linux-arm64.tar.gz",
    "SHA256SUMS",
]


@pytest.mark.parametrize(
    "platform_name, executable, machine, expected",
    [
        ("win32", r"C:\Program Files\KeyEnroll\KeyEnroll.exe", "AMD64", "KeyEnroll-0.8.0-windows-x64-setup.exe"),
        ("win32", r"C:\Program Files\KeyEnroll\KeyEnroll.exe", "ARM64", "KeyEnroll-0.8.0-windows-arm64-setup.exe"),
        ("darwin", "/Applications/KeyEnroll.app/Contents/MacOS/KeyEnroll", "arm64", "KeyEnroll-0.8.0-macos-arm64.dmg"),
        ("darwin", "/Applications/KeyEnroll.app/Contents/MacOS/KeyEnroll", "x86_64", "KeyEnroll-0.8.0-macos-x64.dmg"),
        ("linux", "/opt/keyenroll/KeyEnroll", "x86_64", "keyenroll_0.8.0_amd64.deb"),
        ("linux", "/opt/keyenroll/KeyEnroll", "aarch64", "keyenroll_0.8.0_arm64.deb"),
        ("linux", "/home/a/KeyEnroll/KeyEnroll", "x86_64", "KeyEnroll-0.8.0-linux-x64.tar.gz"),
    ],
)
def test_the_file_matches_the_installation(platform_name, executable, machine, expected):
    info = UpdateInfo("0.7.0", "0.8.0", "x", [Asset(n, DOWNLOAD + n) for n in NAMES])
    kind = updates.installer_kind(platform_name, frozen=True, executable=executable)
    assert updates.pick_asset(info, kind, updates.machine_arch(machine)).name == expected


def test_running_from_source_is_never_replaced():
    assert updates.installer_kind("win32", frozen=False, executable="python.exe") is None
    assert updates.pick_asset(UpdateInfo("1", "2", "x", []), None, "x64") is None


# -- verified download -------------------------------------------------------------


def make_info(content=PAYLOAD, extra=(), digest=True):
    name = "KeyEnroll-0.8.0-windows-x64-setup.exe"
    data = release("v0.8.0", assets=[asset_json(name, content, digest), *extra])
    info = updates._info(data, "0.7.0")
    return info, info.asset(name)


def test_a_verified_download_is_kept(tmp_path):
    info, asset = make_info()
    seen = []
    http = Http({asset.url: Response(content=PAYLOAD)})

    path = updates.download(info, asset, tmp_path, http, progress=lambda d, t: seen.append(d), keys=())

    assert path.read_bytes() == PAYLOAD and path.name == asset.name
    assert seen[-1] == len(PAYLOAD) and not list(tmp_path.glob("*.part"))


def test_a_file_that_differs_from_the_published_one_is_deleted(tmp_path):
    info, asset = make_info()
    http = Http({asset.url: Response(content=PAYLOAD + b"!")})
    with pytest.raises(UpdateError, match="not the one that was published"):
        updates.download(info, asset, tmp_path, http, keys=())
    assert list(tmp_path.iterdir()) == []


def test_without_a_checksum_nothing_is_downloaded(tmp_path):
    info, asset = make_info(digest=False)
    http = Http({})
    with pytest.raises(UpdateError, match="did not provide a checksum"):
        updates.download(info, asset, tmp_path, http, keys=())
    assert http.calls == []


def test_only_the_projects_own_release_files_are_fetched(tmp_path):
    info, asset = make_info()
    asset.url = "https://evil.example.com/KeyEnroll-setup.exe"
    with pytest.raises(UpdateError):
        updates.download(info, asset, tmp_path, Http({}), keys=())


def test_a_cancelled_download_leaves_nothing_behind(tmp_path):
    info, asset = make_info()
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(updates.UpdateCancelled):
        updates.download(
            info, asset, tmp_path, Http({asset.url: Response(content=PAYLOAD)}), cancel=cancel, keys=()
        )
    assert list(tmp_path.iterdir()) == []


# -- the project's own signature ---------------------------------------------------


@pytest.fixture
def release_key():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private, base64.b64encode(public).decode()


def signed_release(private, sums_text):
    sums = sums_text.encode()
    signature = base64.b64encode(private.sign(sums))
    extra = [asset_json("SHA256SUMS", sums), asset_json("SHA256SUMS.sig", signature)]
    info, asset = make_info(extra=extra)
    routes = {
        asset.url: Response(content=PAYLOAD),
        DOWNLOAD + "SHA256SUMS": Response(content=sums),
        DOWNLOAD + "SHA256SUMS.sig": Response(content=signature),
    }
    return info, asset, Http(routes)


def test_a_signed_release_is_accepted(tmp_path, release_key):
    private, public = release_key
    sums = f"{hashlib.sha256(PAYLOAD).hexdigest()}  KeyEnroll-0.8.0-windows-x64-setup.exe\n"
    info, asset, http = signed_release(private, sums)
    assert updates.download(info, asset, tmp_path, http, keys=(public,)).read_bytes() == PAYLOAD


def test_a_release_signed_with_another_key_is_refused(tmp_path, release_key):
    _, public = release_key
    sums = f"{hashlib.sha256(PAYLOAD).hexdigest()}  KeyEnroll-0.8.0-windows-x64-setup.exe\n"
    info, asset, http = signed_release(Ed25519PrivateKey.generate(), sums)
    with pytest.raises(UpdateError, match="signature of this release is not valid"):
        updates.download(info, asset, tmp_path, http, keys=(public,))
    assert asset.url not in http.calls  # the installer itself was never fetched


def test_signed_checksums_must_agree_with_github(tmp_path, release_key):
    private, public = release_key
    info, asset, http = signed_release(private, "0" * 64 + "  KeyEnroll-0.8.0-windows-x64-setup.exe\n")
    with pytest.raises(UpdateError, match="signature of this release is not valid"):
        updates.download(info, asset, tmp_path, http, keys=(public,))


def test_an_unsigned_release_is_refused_once_the_app_has_a_key(tmp_path, release_key):
    _, public = release_key
    info, asset = make_info()
    with pytest.raises(UpdateError, match="not signed with the project's key"):
        updates.download(info, asset, tmp_path, Http({}), keys=(public,))


def test_checksum_lines_are_read_like_sha256sum_writes_them():
    digest = "ab" * 32
    assert updates.parse_sums(f"{digest}  a.exe\n{digest} *b.dmg\nnoise\n") == {
        "a.exe": digest,
        "b.dmg": digest,
    }


def test_the_signing_tool_and_the_application_agree(tmp_path, release_key):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "release_signing", Path(__file__).parent.parent / "tools" / "release_signing.py"
    )
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    private, public = release_key
    assert tool.public_key_text(private) == public
    files = [tmp_path / "b.dmg", tmp_path / "a.exe"]
    for path in files:
        path.write_bytes(path.name.encode())
    sums = tool.make_sums(files)
    assert list(updates.parse_sums(sums.decode())) == ["a.exe", "b.dmg"]
    assert updates.verify_signature(sums, tool.sign(private, sums), (public,))
    assert not updates.verify_signature(sums + b"x", tool.sign(private, sums), (public,))
