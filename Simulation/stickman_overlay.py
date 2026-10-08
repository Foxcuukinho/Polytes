from PyQt6.QtGui import QColor, QPainter, QRegion
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PyQt6.QtCore import Qt
from Utils.world_helpers import get_screen_geometry
from Utils.general_helpers import check_rect_overlap

class StickmanOverlay(QWidget):
    def __init__(self, stickman):
        super().__init__()

        self.stickman = stickman
        self.config_overlay()

    def config_overlay(self):
        stickman_layout = QVBoxLayout()
        stickman_layout.setContentsMargins(0, 0, 0, 0)
        stickman_layout.addWidget(self.stickman.draw)
        self.setLayout(stickman_layout)

        screen_x, screen_y, screen_width, screen_height = get_screen_geometry()
        self.move(screen_x, screen_y)
        self.resize(screen_width, screen_height)
        
        self.set_overlay_translucent()
 
    def update_overlay(self):
        self.stickman.draw.move(self.stickman.x, self.stickman.y)
        self.setMask(self.get_qregion())

    def get_qregion(self):
        rect = self.stickman.draw.geometry()
        return QRegion(rect)   

    def set_overlay_translucent(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def mousePressEvent(self, event):
        mouse_position = event.position().toPoint()

        rect = self.stickman.draw.geometry()

        if not rect.contains(mouse_position):
            return

        self.drag_offset_x = mouse_position.x() - self.stickman.x
        self.drag_offset_y = mouse_position.y() - self.stickman.y

        self.stickman.dragging = True
        
    def mouseMoveEvent(self, event):
        if not self.stickman.dragging:
            return

        mouse_position = event.position()

        self.stickman.x = int(mouse_position.x() - self.drag_offset_x)
        self.stickman.y = int(mouse_position.y() - self.drag_offset_y)    

    def mouseReleaseEvent(self, event):
        self.stickman.dragging = False
        self.stickman.vy = 0

    


        