from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QRegion
from PyQt5.QtCore import Qt, QRect
from Animation.draw_stickman import draw_stickman
from Utils.helpers import get_screen_geometry, is_mirrored
from Utils.constants import STICKMAN_WIDTH, STICKMAN_HEIGHT, RAGDOLL_SPIN_FACTOR
from Body.body_physics import (
    calculate_joints,
    create_ragpoints,
    get_drag_part,
    move_grab_part,
    apply_spin
)


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
        mouse_x = event.globalPos().x()
        mouse_y = event.globalPos().y()

        self.stickman.grab_part = get_drag_part(
            self.stickman,
            mouse_x,
            mouse_y
        )

        if not self.stickman.grab_part:
            return

        self.stickman.overlap_windows.clear()

        self.drag_offset_x = (
            mouse_x
            - self.stickman.joints[self.stickman.grab_part]['position'][0]
        )

        self.drag_offset_y = (
            mouse_y
            - self.stickman.joints[self.stickman.grab_part]['position'][1]
        )

        self.stickman.ragpoints = create_ragpoints(
            self.stickman.joints,
            self.stickman.x,
            self.stickman.y
        )

        self.stickman.flying = False
        self.stickman.holding = True

    def mouseMoveEvent(self, event):
        if not self.stickman.holding:
            return

        mouse_x = event.globalPos().x()
        mouse_y = event.globalPos().y()

        self.drag_velocity_x = mouse_x - self.mouse_old_x
        self.mouse_old_x = mouse_x

        self.drag_velocity_y = mouse_y - self.mouse_old_y
        self.mouse_old_y = mouse_y

        move_grab_part(self.stickman, mouse_x, mouse_y, self.drag_offset_x, self.drag_offset_y)

    def mouseReleaseEvent(self, event):
        if not self.stickman.holding:
            return

        self.stickman.holding = False
        self.stickman.flying = True

        if self.stickman.grab_part:
            self.stickman.ragpoints[self.stickman.grab_part].old_x = (
                self.stickman.ragpoints[self.stickman.grab_part].x
                - self.drag_velocity_x
            )

            self.stickman.ragpoints[self.stickman.grab_part].old_y = (
                self.stickman.ragpoints[self.stickman.grab_part].y
                - self.drag_velocity_y
            )

        apply_spin(
            self.stickman.ragpoints,
            self.drag_velocity_x * RAGDOLL_SPIN_FACTOR
        )

        self.stickman.grab_part = None

        self.stickman.velocity_y = 0
        self.stickman.velocity_x = 0

    def center_on_screen(self):
        screen_x, screen_y, screen_width, screen_height = get_screen_geometry()

        self.stickman.x = screen_x + screen_width / 2 - (self.stickman.width / 2)
        self.stickman.y = screen_y + screen_height / 2 - (self.stickman.height / 2)

    def update_position(self):
        self.update()
        self.update_mask()

    def update_mask(self):
        self.stickman.joints = calculate_joints(
            self.stickman.current_frame, self.stickman, self.stickman.head_radius
        )

        def mirror_x(px):
            if is_mirrored(self.stickman):
                return (2 * self.stickman.x + self.stickman.width) - px
            return px

        xs = []
        ys = []

        for joint in self.stickman.joints.values():
            x, y = joint['position']
            xs.append(mirror_x(x))
            ys.append(y)

        margin = self.stickman.head_radius * 2 + 10

        left = int(min(xs) - margin - self.x())
        top = int(min(ys) - margin - self.y())
        width = int(max(xs) - min(xs) + margin * 2)
        height = int(max(ys) - min(ys) + margin * 2)

        self.setMask(QRegion(QRect(left, top, width, height)))

    def apply_x11_hints(self):
        from Utils.x11_hints import set_window_type_dock, set_always_on_top_x11
        set_window_type_dock(int(self.winId()))
        set_always_on_top_x11(int(self.winId()))