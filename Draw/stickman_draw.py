from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt

class StickmanDraw(QWidget):
    def __init__(self, stickman):
        super().__init__()

        self.stickman = stickman
        self.config_overlay()
    
    def config_overlay(self):
        self.resize(300, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.stickman.color)
        painter.drawRect(0,0,100,200)