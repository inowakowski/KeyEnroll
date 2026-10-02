"""Renders the application icon to packaging/icons/ (icon.ico, PNGs).

Run after changing APP_ICON_SVG in ui/theme.py:
    python packaging/make_icon.py
The macOS .icns is assembled from icon_1024.png by packaging/macos/build_dmg.sh.
"""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from keyenroll.ui.theme import APP_ICON_SVG

ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
OUT = ROOT / "packaging" / "icons"


def render(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(APP_ICON_SVG.encode())).render(painter)
    painter.end()
    return image


def png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def write_ico(path: Path) -> None:
    """Packs PNG-compressed images of several sizes into one .ico file."""
    images = [png_bytes(render(size)) for size in ICO_SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    directory = b""
    for size, data in zip(ICO_SIZES, images):
        directory += struct.pack(
            "<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset
        )
        offset += len(data)
    path.write_bytes(header + directory + b"".join(images))


def main() -> None:
    app = QGuiApplication([])  # noqa: F841  (needed for font-free SVG rendering too)
    OUT.mkdir(parents=True, exist_ok=True)
    write_ico(OUT / "icon.ico")
    for size in (256, 1024):
        render(size).save(str(OUT / f"icon_{size}.png"), "PNG")
    print("written to", OUT)


if __name__ == "__main__":
    main()
