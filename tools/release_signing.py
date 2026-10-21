"""Signing KeyEnroll releases with the project's own key (see RELEASING.md).

    python tools/release_signing.py generate --key D:/keyenroll-release.key
    python tools/release_signing.py sign v0.8.0 --key D:/keyenroll-release.key
    python tools/release_signing.py verify v0.8.0

"generate" makes an Ed25519 key, protected by a password, and prints the
public half for src/keyenroll/release_key.py. "sign" downloads the files of
a (draft) release with the GitHub CLI, checks them against the checksums
GitHub reports, writes SHA256SUMS and its signature, uploads both and, with
--publish, publishes the draft. "verify" checks a published release the way
the application does. The private key never leaves this computer.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from keyenroll import updates  # noqa: E402
from keyenroll.release_key import PUBLIC_KEYS  # noqa: E402

REPO = "inowakowski/KeyEnroll"
SIGNED_FILES = (updates.SUMS, updates.SIGNATURE)


def public_key_text(private: Ed25519PrivateKey) -> str:
    raw = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return base64.b64encode(raw).decode()


def make_sums(files: list[Path]) -> bytes:
    """SHA256SUMS in the format of sha256sum, sorted by file name."""
    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in sorted(files, key=lambda p: p.name)
    ]
    return "".join(lines).encode()


def sign(private: Ed25519PrivateKey, data: bytes) -> bytes:
    return base64.b64encode(private.sign(data)) + b"\n"


def load_key(path: Path) -> Ed25519PrivateKey:
    password = getpass.getpass("Password of the release key: ").encode()
    key = serialization.load_pem_private_key(path.read_bytes(), password=password)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("This is not an Ed25519 key.")
    return key


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def cmd_generate(args) -> int:
    path = Path(args.key)
    if path.exists():
        raise SystemExit(f"{path} exists already; a new key would make it useless.")
    password = getpass.getpass("New password for the release key: ")
    if len(password) < 12 or password != getpass.getpass("Repeat the password: "):
        raise SystemExit("The passwords differ or are shorter than 12 characters.")
    private = Ed25519PrivateKey.generate()
    pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password.encode()),
    )
    path.write_bytes(pem)
    print(f"Private key written to {path}. Keep it and its password safe and off GitHub.")
    print("Public key for src/keyenroll/release_key.py:")
    print(f'    PUBLIC_KEYS: tuple[str, ...] = ("{public_key_text(private)}",)')
    return 0


def cmd_sign(args) -> int:
    private = load_key(Path(args.key))
    release = json.loads(gh("release", "view", args.tag, "-R", REPO, "--json", "assets,isDraft"))
    published = {
        a["name"]: (a.get("digest") or "").removeprefix("sha256:")
        for a in release["assets"]
        if a["name"] not in SIGNED_FILES
    }
    if not published:
        raise SystemExit("The release has no files to sign.")
    with tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        for name in published:
            gh("release", "download", args.tag, "-R", REPO, "-p", name, "-D", str(work))
        files = [work / name for name in published]
        for path in files:
            local = hashlib.sha256(path.read_bytes()).hexdigest()
            if published[path.name] and local != published[path.name]:
                raise SystemExit(f"{path.name}: GitHub reports another checksum. Do not sign.")
        sums = make_sums(files)
        (work / updates.SUMS).write_bytes(sums)
        (work / updates.SIGNATURE).write_bytes(sign(private, sums))
        print(sums.decode(), end="")
        gh(
            "release", "upload", args.tag, "-R", REPO, "--clobber",
            str(work / updates.SUMS), str(work / updates.SIGNATURE),
        )  # fmt: skip
    print(f"Signed {len(published)} file(s) of {args.tag}.")
    if args.publish and release.get("isDraft"):
        gh("release", "edit", args.tag, "-R", REPO, "--draft=false")
        print("The release is published.")
    elif release.get("isDraft"):
        print("The release is still a draft: publish it on GitHub, or run again with --publish.")
    return 0


def cmd_verify(args) -> int:
    if not PUBLIC_KEYS:
        raise SystemExit("src/keyenroll/release_key.py holds no key yet.")
    with tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        for name in SIGNED_FILES:
            gh("release", "download", args.tag, "-R", REPO, "-p", name, "-D", str(work))
        sums = (work / updates.SUMS).read_bytes()
        ok = updates.verify_signature(sums, (work / updates.SIGNATURE).read_bytes(), PUBLIC_KEYS)
    print(f"{args.tag}: signature {'valid' if ok else 'NOT VALID'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="make a new release key")
    generate.add_argument("--key", required=True, help="where to write the private key")
    signing = sub.add_parser("sign", help="sign the files of a release")
    signing.add_argument("tag")
    signing.add_argument("--key", required=True, help="the private key file")
    signing.add_argument("--publish", action="store_true", help="publish the draft afterwards")
    verify = sub.add_parser("verify", help="check the signature of a release")
    verify.add_argument("tag")
    args = parser.parse_args(argv)
    return {"generate": cmd_generate, "sign": cmd_sign, "verify": cmd_verify}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
