from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, pyqtSignal


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)

        self.setFixedSize(46, 24)
        self._checked = checked

        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self):
        return self._checked

    def setChecked(self, value):
        self._checked = bool(value)
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(Qt.NoPen)

        if self._checked:
            p.setBrush(QColor(80, 170, 110))
        else:
            p.setBrush(QColor(200, 200, 205))

        p.drawRoundedRect(
            0,
            0,
            self.width(),
            self.height(),
            12,
            12
        )

        cx = self.width() - 20 if self._checked else 4

        p.setBrush(QColor(255, 255, 255))

        p.drawEllipse(
            cx,
            2,
            20,
            20
        )