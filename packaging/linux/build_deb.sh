#!/bin/sh
# Builds the Linux packages: PyInstaller output -> .deb and .tar.gz
# Run from the repository root on Linux:  sh packaging/linux/build_deb.sh
set -eu

PYTHON="${PYTHON:-python3}"
VERSION=$("$PYTHON" -c "import sys; sys.path.insert(0, 'src'); import keyenroll; print(keyenroll.__version__)")
DEB_ARCH=$(dpkg --print-architecture)
ARCH=$(echo "$DEB_ARCH" | sed 's/amd64/x64/')

"$PYTHON" -m PyInstaller packaging/keyenroll.spec --noconfirm --log-level WARN

STAGE="$(mktemp -d)/keyenroll"
mkdir -p "$STAGE/DEBIAN" "$STAGE/opt" "$STAGE/usr/bin" \
    "$STAGE/usr/share/applications" "$STAGE/usr/share/icons/hicolor/256x256/apps"
cp -R dist/KeyEnroll "$STAGE/opt/keyenroll"
ln -s /opt/keyenroll/KeyEnroll "$STAGE/usr/bin/keyenroll"
cp packaging/linux/keyenroll.desktop "$STAGE/usr/share/applications/"
cp packaging/icons/icon_256.png "$STAGE/usr/share/icons/hicolor/256x256/apps/keyenroll.png"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: keyenroll
Version: $VERSION
Architecture: $DEB_ARCH
Maintainer: KeyEnroll maintainers
Section: admin
Priority: optional
Depends: libxcb-cursor0, libegl1, libxkbcommon-x11-0, libfontconfig1, libdbus-1-3
Recommends: libu2f-udev | libfido2-1, pcscd
Description: Enroll FIDO2 security keys on behalf of users
 Graphical tool for enrolling YubiKeys with Microsoft Entra ID, Okta,
 PingOne and PingOne Advanced Identity Cloud on behalf of end users.
EOF

mkdir -p dist/installer
dpkg-deb --build --root-owner-group "$STAGE" "dist/installer/keyenroll_${VERSION}_${DEB_ARCH}.deb"
tar -C dist -czf "dist/installer/KeyEnroll-$VERSION-linux-$ARCH.tar.gz" KeyEnroll
ls -l dist/installer
