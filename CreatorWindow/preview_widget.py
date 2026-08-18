from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt
from Utils.constants import STICKMAN_WIDTH, STICKMAN_HEIGHT
from Animation.draw_stickman import draw_stickman

class MockStickman:
    def __init__(self, color, hollow_head):
        self.color = color
        self.hollow_head = hollow_head
        self.width = STICKMAN_WIDTH
        self.height = STICKMAN_HEIGHT
        self.x = 0
        self.y = 0
        self.holding = False
        self.flying = False
        self.direction = 1
        self.current_frame = {
    "torso_angle": -90,
    "hip_offset_y": 0,

    "upper_arm_angle_r": 45,
    "forearm_angle_r": 0,

    "upper_arm_angle_l": 135,
    "forearm_angle_l": 0,

    "upper_leg_angle_r": 72,
    "lower_leg_angle_r": 11,
    "upper_leg_angle_l": 108,
    "lower_leg_angle_l": -11
}   

class StickmanPreview(QWidget):
    def __init__(self, color, hollow_head):
        super().__init__()
        self.fake_stickman = MockStickman(color, hollow_head)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.save()

        width = self.width()
        height = self.height()

        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(230, 230, 230)))
        painter.drawRoundedRect(0,0, width, height, 12, 12)

        color = QColor(200, 200, 200)
        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)

        for x in range(-5, width, 20):
            painter.drawLine(x, 0, x, height)

        for y in range(-5, height, 20):
            painter.drawLine(0, y, width, y)
        
        painter.translate(
            self.width() // 2 - STICKMAN_WIDTH // 2,
            self.height() // 2 - STICKMAN_HEIGHT // 2
        )
        
        draw_stickman(painter, self.fake_stickman)
        painter.restore()

    def set_color(self, color):
        self.fake_stickman.color = color
        self.update()

    def set_hollow_head(self, hollow_head):
        self.fake_stickman.hollow_head = hollow_head
        self.update()
