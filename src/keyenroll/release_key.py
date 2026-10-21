"""The project's release signing keys (Ed25519 public keys, base64).

When this tuple holds a key, an update is installed only if the release's
SHA256SUMS file is signed with the matching private key. That key is kept
by the maintainer, away from GitHub; RELEASING.md describes how it is made
and used. Several keys may be listed while one replaces another.

Empty: no key has been made yet, and an update is checked against the
SHA-256 checksums GitHub reports, which proves the download is intact but
not who published it.
"""

PUBLIC_KEYS: tuple[str, ...] = ()
