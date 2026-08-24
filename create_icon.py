import os
import sys

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtGui import QImage, QPainter, QColor, QLinearGradient, QPen, QBrush, QFont, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF

def create_app_icon():
    os.makedirs("assets", exist_ok=True)
    size = 256
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # 1. Background Rounded Rectangle / Circle with Gradient
    bg_grad = QLinearGradient(0, 0, size, size)
    bg_grad.setColorAt(0.0, QColor(24, 24, 37))      # #181825 Catppuccin Base
    bg_grad.setColorAt(0.5, QColor(30, 30, 46))      # #1E1E2E Catppuccin Mantle
    bg_grad.setColorAt(1.0, QColor(17, 17, 27))      # #11111B Catppuccin Crust

    painter.setBrush(QBrush(bg_grad))
    
    # Border Gradient
    border_grad = QLinearGradient(0, 0, size, size)
    border_grad.setColorAt(0.0, QColor(137, 180, 250)) # Blue
    border_grad.setColorAt(0.5, QColor(203, 166, 247)) # Mauve
    border_grad.setColorAt(1.0, QColor(166, 227, 161)) # Green

    pen = QPen(QBrush(border_grad), 8)
    painter.setPen(pen)
    painter.drawRoundedRect(QRectF(12, 12, 232, 232), 48, 48)

    # 2. Magnifying Glass Lens
    lens_pen = QPen(QColor(137, 180, 250), 10)
    painter.setPen(lens_pen)
    lens_brush = QBrush(QColor(49, 50, 68, 160))
    painter.setBrush(lens_brush)
    painter.drawEllipse(QPointF(108, 108), 58, 58)

    # Magnifying Glass Handle
    handle_path = QPainterPath()
    handle_path.moveTo(150, 150)
    handle_path.lineTo(198, 198)
    handle_pen = QPen(QColor(137, 180, 250), 14, Qt.SolidLine, Qt.RoundCap)
    painter.strokePath(handle_path, handle_pen)

    # 3. Rising Rank Analytics Bars inside Lens
    painter.setPen(Qt.NoPen)
    
    # Bar 1 (Left - Blue)
    b1_grad = QLinearGradient(0, 120, 0, 140)
    b1_grad.setColorAt(0.0, QColor(137, 180, 250))
    b1_grad.setColorAt(1.0, QColor(116, 199, 236))
    painter.setBrush(QBrush(b1_grad))
    painter.drawRoundedRect(QRectF(74, 118, 16, 26), 4, 4)

    # Bar 2 (Middle - Yellow/Orange)
    b2_grad = QLinearGradient(0, 96, 0, 140)
    b2_grad.setColorAt(0.0, QColor(249, 226, 175))
    b2_grad.setColorAt(1.0, QColor(250, 179, 135))
    painter.setBrush(QBrush(b2_grad))
    painter.drawRoundedRect(QRectF(98, 96, 16, 48), 4, 4)

    # Bar 3 (Right - Green #1 Rank)
    b3_grad = QLinearGradient(0, 72, 0, 140)
    b3_grad.setColorAt(0.0, QColor(166, 227, 161))
    b3_grad.setColorAt(1.0, QColor(148, 226, 213))
    painter.setBrush(QBrush(b3_grad))
    painter.drawRoundedRect(QRectF(122, 72, 16, 72), 4, 4)

    # 4. Top Rank #1 Star / Crown
    painter.setBrush(QBrush(QColor(249, 226, 175))) # Gold star
    star_path = QPainterPath()
    cx, cy = 130, 58
    star_path.moveTo(cx, cy - 8)
    star_path.lineTo(cx + 3, cy - 2)
    star_path.lineTo(cx + 9, cy - 1)
    star_path.lineTo(cx + 4, cy + 4)
    star_path.lineTo(cx + 6, cy + 10)
    star_path.lineTo(cx, cy + 6)
    star_path.lineTo(cx - 6, cy + 10)
    star_path.lineTo(cx - 4, cy + 4)
    star_path.lineTo(cx - 9, cy - 1)
    star_path.lineTo(cx - 3, cy - 2)
    star_path.closeSubpath()
    painter.drawPath(star_path)

    painter.end()

    # Save as PNG
    png_path = "assets/icon.png"
    image.save(png_path, "PNG")
    print(f"[OK] Saved {png_path}")

    # Also save as ICO
    ico_path = "assets/icon.ico"
    image.save(ico_path, "ICO")
    print(f"[OK] Saved {ico_path}")

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    create_app_icon()
