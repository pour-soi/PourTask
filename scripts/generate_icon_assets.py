from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "icons" / "PourTask.svg"
ICO = ROOT / "assets" / "icons" / "PourTask.ico"
PREVIEW = ROOT / "assets" / "icons" / "PourTask-256.png"
SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def render_png(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(Qt.GlobalColor.transparent))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError(f"Could not encode {size} px icon")
    return bytes(data)


def write_ico(images: list[tuple[int, bytes]]) -> None:
    header_size = 6 + 16 * len(images)
    offset = header_size
    directory = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    payload = bytearray()
    for size, png in images:
        dimension = 0 if size == 256 else size
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(png),
                offset,
            )
        )
        payload.extend(png)
        offset += len(png)
    ICO.write_bytes(directory + payload)


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(SOURCE))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid SVG source: {SOURCE}")
    images = [(size, render_png(renderer, size)) for size in SIZES]
    write_ico(images)
    PREVIEW.write_bytes(dict(images)[256])
    app.quit()


if __name__ == "__main__":
    main()
