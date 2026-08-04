from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor,QPen, QRegion
from PyQt5.QtCore import Qt
from Animation.draw_stickman import draw_stickman
from Utils.screen import get_screen_geometry
from Utils.utils import STICKMAN_WIDTH, STICKMAN_HEIGHT
from Body.body_physics import calculate_joints, create_ragpoints, get_drag_part

class StickmanOverlay(QWidget):

    def __init__(self, stickman):
        super().__init__()

        self.stickman = stickman
        self.center_on_screen()

        self.stickman.joints = calculate_joints(self.stickman.current_frame, self.stickman, self.stickman.head_radius)
        self.stickman.ragpoints = create_ragpoints(self.stickman.joints, self.stickman.x, self.stickman.y)

        self.resize(self.stickman.width, self.stickman.height)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_stickman(painter, self.stickman)

    def mousePressEvent(self, event):
        # Essa função apenas acontece quando o mouse clica no >Widget<
        mouse_x = event.globalPos().x()
        mouse_y = event.globalPos().y()

        self.stickman.joints = calculate_joints(self.stickman.current_frame, self.stickman, self.stickman.head_radius)
        self.stickman.ragpoints = create_ragpoints(self.stickman.joints, self.stickman.x, self.stickman.y)

        self.stickman.grab_part = get_drag_part(self.stickman, mouse_x, mouse_y)

        # O offset permite que o stickman não se teleporte para a ponta do mouse ao ser clicado
        self.drag_offset_x = mouse_x - self.stickman.x
        self.drag_offset_y = mouse_y - self.stickman.y
        self.stickman.dragging = True
        print(self.stickman.grab_part)

    def mouseMoveEvent(self, event):
        if not self.stickman.dragging:
            return

        mouse_x = event.globalPos().x()
        mouse_y = event.globalPos().y()
        
        #self.stickman.x = mouse_x - self.drag_offset_x
        #self.stickman.y = mouse_y - self.drag_offset_y
        
        # Não é precicfsso mover a janela imediatamente aqui, pois update_position() já cuida disso
    
    def mouseReleaseEvent(self, event):
        self.stickman.dragging = False
        self.stickman.velocity_y = 0
        self.stickman.velocity_x = 0
        # Zera a velocidade para já não ter velocidade acumulada ao soltar o drag
        self.stickman.width = STICKMAN_WIDTH
        self.stickman.height = STICKMAN_HEIGHT

    def center_on_screen(self):
        screen_x, screen_y, screen_width, screen_height = get_screen_geometry()

        self.stickman.x = screen_x + screen_width / 2 - (self.stickman.width / 2)
        self.stickman.y = screen_y + screen_height / 2 - (self.stickman.height / 2)

    def update_position(self):
        self.resize(self.stickman.width, self.stickman.height)
        self.move(int(self.stickman.x), int(self.stickman.y))
        self.update()

    