# PyInstaller spec. Build from the repository root on the target platform:
#   pyinstaller packaging/keyenroll.spec --noconfirm
# PyInstaller does not cross-compile: each OS/architecture needs its own build.
# The platform installers are made from this output, see packaging/<os>/.

import importlib.metadata
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

ROOT = Path(SPECPATH).parent

# Distributions that end up inside the bundle (see THIRD-PARTY-NOTICES.md).
BUNDLED = {
    "pyside6-essentials", "shiboken6", "fido2", "cryptography", "cffi", "pycparser",
    "requests", "urllib3", "idna", "charset-normalizer", "certifi", "keyring",
    "jaraco.classes", "jaraco.context", "jaraco.functools", "more-itertools",
    "pywin32-ctypes", "secretstorage", "jeepney", "pyscard",
}
ICONS = ROOT / "packaging" / "icons"
sys.path.insert(0, str(ROOT / "src"))
from keyenroll import __version__

# fido2 ships the public suffix list used to validate RP IDs.
datas = collect_data_files("fido2") + copy_metadata("keyring")

# License texts: our own, and those shipped with every bundled distribution.
datas += [(str(ROOT / "LICENSE"), "."), (str(ROOT / "THIRD-PARTY-NOTICES.md"), ".")]
for extra in sorted((ROOT / "packaging" / "licenses").glob("*")):
    datas.append((str(extra), "licenses"))
for dist in importlib.metadata.distributions():
    name = dist.metadata["Name"]
    if name.lower().replace("_", "-") in BUNDLED:
        for file in dist.files or []:
            if any(k in file.name.upper() for k in ("LICENSE", "COPYING", "NOTICE")):
                datas.append((str(file.locate()), f"licenses/{name}"))

# keyring picks its backend through entry points at run time.
hiddenimports = collect_submodules("keyring.backends")
if sys.platform == "win32":
    hiddenimports += collect_submodules("win32ctypes")
elif sys.platform.startswith("linux"):
    hiddenimports += ["secretstorage", "jeepney"]
try:
    import smartcard  # noqa: F401  (optional NFC support)

    hiddenimports += ["fido2.pcsc"] + collect_submodules("smartcard")
except ImportError:
    pass

icon = {"win32": ICONS / "icon.ico", "darwin": ICONS / "icon.icns"}.get(sys.platform)
icon = str(icon) if icon and icon.exists() else None

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="KeyEnroll",
    console=False,
    icon=icon,
    # Windows only lets elevated processes talk to FIDO HID devices, so the
    # installed app asks for elevation at start. KEYENROLL_NO_UAC=1 builds a
    # variant without it, for smoke tests.
    uac_admin=sys.platform == "win32" and not os.environ.get("KEYENROLL_NO_UAC"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="KeyEnroll")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="KeyEnroll.app",
        icon=icon,
        bundle_identifier="app.keyenroll",
        version=__version__,
        info_plist={"NSHighResolutionCapable": True},
    )
