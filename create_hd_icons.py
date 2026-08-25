import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PySide6.QtCore import Qt, QPointF, QRectF

def create_hd_icons():
    # Ensure QApplication exists for QPixmap / QPainter
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    assets_dir = "assets"
    os.makedirs(assets_dir, exist_ok=True)
    size = 64

    # 1. Country Globe Icon (Professional Blue/Teal Vector)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    
    pen = QPen(QColor("#89B4FA"), 3.5)
    painter.setPen(pen)
    painter.drawEllipse(6, 6, 52, 52)
    # Latitude & Longitude lines
    painter.drawLine(6, 32, 58, 32)
    painter.drawLine(32, 6, 32, 58)
    painter.drawEllipse(16, 6, 32, 52)
    painter.end()
    pix.save(os.path.join(assets_dir, "icon_globe.png"))

    # 2. Play Start Icon (Crisp Green Triangle)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.moveTo(18, 12)
    path.lineTo(52, 32)
    path.lineTo(18, 52)
    path.closeSubpath()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#11111B"))
    painter.drawPath(path)
    painter.end()
    pix.save(os.path.join(assets_dir, "icon_play.png"))

    # 3. Stop Icon (Solid Soft Red Square)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#11111B"))
    painter.drawRoundedRect(QRectF(14, 14, 36, 36), 6, 6)
    painter.end()
    pix.save(os.path.join(assets_dir, "icon_stop.png"))

    # 4. Pause Icon (Double Vertical Bars)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#CDD6F4"))
    painter.drawRoundedRect(QRectF(16, 12, 11, 40), 4, 4)
    painter.drawRoundedRect(QRectF(37, 12, 11, 40), 4, 4)
    painter.end()
    pix.save(os.path.join(assets_dir, "icon_pause.png"))

    # 5. Refresh / Update Icon (Circular Arrows)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#89B4FA"), 4)
    painter.setPen(pen)
    painter.drawArc(QRectF(10, 10, 44, 44), 30 * 16, 300 * 16)
    # Arrow head
    path = QPainterPath()
    path.moveTo(42, 6)
    path.lineTo(54, 16)
    path.lineTo(38, 22)
    path.closeSubpath()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#89B4FA"))
    painter.drawPath(path)
    painter.end()
    pix.save(os.path.join(assets_dir, "icon_refresh.png"))

    # 6. Clear Session Trash Icon
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#FAB387"), 3.5)
    painter.setPen(pen)
    painter.drawRoundedRect(QRectF(16, 20, 32, 38), 4, 4)
    painter.drawLine(12, 16, 52, 16)
    painter.drawLine(26, 10, 38, 10)
    painter.drawLine(26, 26, 26, 48)
    painter.drawLine(38, 26, 38, 48)
    painter.end()
    pix.save(os.path.join(assets_dir, "icon_trash.png"))

    # 7. Export CSV Icon
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#A6E3A1"), 3.5)
    painter.setPen(pen)
    painter.drawRoundedRect(QRectF(12, 10, 40, 46), 4, 4)
    # Down arrow inside
    painter.drawLine(32, 20, 32, 40)
    path = QPainterPath()
    path.moveTo(22, 32)
    path.lineTo(32, 42)
    path.lineTo(42, 32)
    painter.drawPath(path)
    painter.end()
    pix.save(os.path.join(assets_dir, "icon_export.png"))

    print("HD Icons generated successfully in assets/ directory!")

if __name__ == "__main__":
    create_hd_icons()
