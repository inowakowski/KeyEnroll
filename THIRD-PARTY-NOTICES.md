# Third-party notices

KeyEnroll itself is released under the MIT License (see `LICENSE`).

The source code in this repository contains no third-party code. The installers
and application bundles, however, include the components below, each under its
own license. The license files shipped with these components are copied into
the `licenses/` folder of every bundle.

| Component | License | Project |
|---|---|---|
| Qt 6 and PySide6 / Shiboken6 (Qt for Python) | LGPL-3.0-only | https://www.qt.io/ · https://pypi.org/project/PySide6/ |
| python-fido2 | BSD-2-Clause; bundled public suffix list under MPL-2.0 | https://github.com/Yubico/python-fido2 |
| cryptography | Apache-2.0 OR BSD-3-Clause | https://github.com/pyca/cryptography |
| OpenSSL (inside cryptography) | Apache-2.0 | https://www.openssl.org/ |
| cffi | MIT-0 | https://github.com/python-cffi/cffi |
| pycparser | BSD-3-Clause | https://github.com/eliben/pycparser |
| requests | Apache-2.0 | https://github.com/psf/requests |
| urllib3 | MIT | https://github.com/urllib3/urllib3 |
| idna | BSD-3-Clause | https://github.com/kjd/idna |
| charset-normalizer | MIT | https://github.com/jawah/charset_normalizer |
| certifi | MPL-2.0 | https://github.com/certifi/python-certifi |
| keyring and its jaraco.* / more-itertools helpers | MIT | https://github.com/jaraco/keyring |
| pywin32-ctypes (Windows) | BSD-3-Clause | https://github.com/enthought/pywin32-ctypes |
| SecretStorage, jeepney (Linux) | BSD-3-Clause, MIT | https://github.com/mitya57/secretstorage |
| pyscard (optional NFC support) | LGPL-2.1-or-later | https://github.com/LudovicRousseau/pyscard |
| Python runtime | PSF-2.0 | https://www.python.org/ |
| PyInstaller bootloader | GPL-2.0-or-later with the bootloader exception | https://pyinstaller.org/ |

## LGPL components

Qt, PySide6, Shiboken6 and pyscard are used under the GNU Lesser General Public
License. They are included unmodified, as separate shared libraries and Python
modules inside the bundle's `_internal` folder, so they can be replaced with
other compatible builds. Their source code is available from the project pages
above. The license texts are included: `packaging/licenses/lgpl-3.0.txt` and
`packaging/licenses/gpl-3.0.txt` in this repository (copied to `licenses/` in
every bundle), and the LGPL 2.1 text in `licenses/pyscard/`.

## Trademarks

KeyEnroll is an independent project. It is not affiliated with, sponsored or
endorsed by Yubico, Microsoft, Okta or Ping Identity. YubiKey and YubiEnroll are
trademarks of Yubico AB; the other product names belong to their respective
owners and are used only to describe compatibility.
