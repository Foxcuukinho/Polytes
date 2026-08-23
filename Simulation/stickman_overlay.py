from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor,QPen, QRegion
from PyQt5.QtCore import Qt
from Animation.draw_stickman import draw_stickman
from Utils.helpers import get_screen_geometry
from Utils.constants import STICKMAN_WIDTH, STICKMAN_HEIGHT
from Body.body_physics import calculate_joints, create_ragpoints, get_drag_part, move_grab_part

class StickmanOverlay(QWidget):

    def __init__(self, stickman):
        super().__init__()

        screen_x, screen_y, screen_width, screen_height = get_screen_geometry()

        self.stickman = stickman
        self.center_on_screen()

        self.stickman.joints = calculate_joints(self.stickman.current_frame, self.stickman, self.stickman.head_radius)
        self.stickman.ragpoints = create_ragpoints(self.stickman.joints, self.stickman.x, self.stickman.y)

        self.drag_velocity_x = 0
        self.mouse_old_x = 0
        
        self.drag_velocity_y = 0
        self.mouse_old_y = 0

        self.move(screen_x, screen_y)
        self.resize(screen_width, screen_height)

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

        if bool(self.stickman.grab_part):
            # O offset permite que o stickman não se teleporte para a ponta do mouse ao ser clicado
            self.drag_offset_x = mouse_x - self.stickman.joints[self.stickman.grab_part]['position'][0]
            self.drag_offset_y = mouse_y - self.stickman.joints[self.stickman.grab_part]['position'][1]
            self.stickman.flying = False
            

        self.stickman.holding = bool(self.stickman.grab_part)
        

    def mouseMoveEvent(self, event):
        if not self.stickman.holding:
            return

        mouse_x = event.globalPos().x()
        mouse_y = event.globalPos().y()

        self.drag_velocity_x = mouse_x - self.mouse_old_x
        self.mouse_old_x = mouse_x

        self.drag_velocity_y = mouse_y - self.mouse_old_y
        self.mouse_old_y = mouse_y
    
        #self.stickman.x = mouse_x - self.drag_offset_x
        #self.stickman.y = mouse_y - self.drag_offset_y
        
        move_grab_part(self.stickman, mouse_x, mouse_y, self.drag_offset_x, self.drag_offset_y)

        # Não é precicfsso mover a janela imediatamente aqui, pois update_position() já cuida disso
    
    def mouseReleaseEvent(self, event):
        self.stickman.holding = False
        self.stickman.flying = True

        if bool(self.stickman.grab_part):
            self.stickman.ragpoints[self.stickman.grab_part].old_x = self.stickman.ragpoints[self.stickman.grab_part].x - self.drag_velocity_x 

            self.stickman.ragpoints[self.stickman.grab_part].old_y = self.stickman.ragpoints[self.stickman.grab_part].y - self.drag_velocity_y

        self.stickman.grab_part = None

        self.stickman.velocity_y = 0
        self.stickman.velocity_x = 0


    def center_on_screen(self):
        screen_x, screen_y, screen_width, screen_height = get_screen_geometry()

        self.stickman.x = screen_x + screen_width / 2 - (self.stickman.width / 2)
        self.stickman.y = screen_y + screen_height / 2 - (self.stickman.height / 2)

    def update_position(self):

        flags = self.windowFlags()

        self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)

        self.show()
        self.update()
        self.update_mask()

    def update_mask(self):

        self.stickman.joints = calculate_joints(self.stickman.current_frame, self.stickman, self.stickman.head_radius)

        def mirror_x(px):
            if self.stickman.direction == 1 and not self.stickman.holding:
                return (2 * self.stickman.x + self.stickman.width) - px
            return px

        mask_region = None

        bones = [
            ('neck', 'hip'),
            ('neck', 'right_elbow'),
            ('right_elbow', 'right_hand'),
            ('neck', 'left_elbow'),
            ('left_elbow', 'left_hand'),
            ('hip', 'right_knee'),
            ('right_knee', 'right_foot'),
            ('hip', 'left_knee'),
            ('left_knee', 'left_foot'),
        ]

        num_points = 5
        radius = 15

        for start_joint, end_joint in bones:
            x1, y1 = self.stickman.joints[start_joint]['position']
            x2, y2 = self.stickman.joints[end_joint]['position']

            x1 = mirror_x(x1)
            x2 = mirror_x(x2)

            for i in range(num_points):
                progress = i / (num_points - 1)

                x = x1 + (x2 - x1) * progress
                y = y1 + (y2 - y1) * progress

                circle = QRegion(
                    int(x - radius - self.x()),
                    int(y - radius - self.y()),
                    radius * 2,
                    radius * 2
                )

                mask_region = circle if mask_region is None else mask_region + circle

        head_x, head_y = self.stickman.joints['head']['position']
        head_x = mirror_x(head_x)
        head_r = int(self.stickman.head_radius * 1.5)

        head_circle = QRegion(
            int(head_x - head_r - self.x()),
            int(head_y - head_r - self.y()),
            head_r * 2,
            head_r * 2
        )

        mask_region = mask_region + head_circle

        self.setMask(mask_region)