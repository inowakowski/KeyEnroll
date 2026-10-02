#!/bin/sh
# Builds the macOS disk image: icon -> PyInstaller .app -> .dmg
# Run from the repository root on macOS:  sh packaging/macos/build_dmg.sh
set -eu

PYTHON="${PYTHON:-python3}"
VERSION=$("$PYTHON" -c "import sys; sys.path.insert(0, 'src'); import keyenroll; print(keyenroll.__version__)")
ARCH=$(uname -m | sed 's/x86_64/x64/')
ICONS=packaging/icons

# .icns from the 1024px PNG
SET="$(mktemp -d)/icon.iconset"
mkdir -p "$SET"
for size in 16 32 128 256 512; do
    sips -z "$size" "$size" "$ICONS/icon_1024.png" --out "$SET/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z "$double" "$double" "$ICONS/icon_1024.png" --out "$SET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$SET" -o "$ICONS/icon.icns"

"$PYTHON" -m PyInstaller packaging/keyenroll.spec --noconfirm --log-level WARN

STAGE="$(mktemp -d)"
cp -R "dist/KeyEnroll.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
mkdir -p dist/installer
DMG="dist/installer/KeyEnroll-$VERSION-macos-$ARCH.dmg"
hdiutil create -volname "KeyEnroll" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
echo "$DMG"
