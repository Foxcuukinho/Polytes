from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QRegion, QCursor
from PyQt5.QtCore import Qt, QRect
from Animation.draw_stickman import draw_stickman
from Utils.helpers import get_screen_geometry, is_mirrored, is_left_mouse_pressed
from Utils.constants import STICKMAN_WIDTH, STICKMAN_HEIGHT, RAGDOLL_SPIN_FACTOR
from Body.body_physics import (
    calculate_joints,
    create_ragpoints,
    get_drag_part,
    move_grab_part,
    apply_spin
)
import sys
import ctypes
from ctypes import wintypes


class StickmanOverlay(QWidget):

    def __init__(self, stickman):
        super().__init__()

        screen_x, screen_y, screen_width, screen_height = get_screen_geometry()

        self.stickman = stickman
        self.center_on_screen()

        self.stickman.joints = calculate_joints(self.stickman.current_frame, self.stickman, self.stickman.head_radius)
        self.stickman.ragpoints = create_ragpoints(self.stickman.joints)

        self.drag_velocity_x = 0
        self.mouse_old_x = 0

        self.drag_velocity_y = 0
        self.mouse_old_y = 0

        # Previous mask rectangle, used to call setMask only when it changes
        # and to repaint only the area occupied by the stickman (before and after).
        self.last_mask_rect = None

        # Tight rectangle from the previous frame (used to calculate the dirty area)
        # and extra mask padding: the mask is rebuilt only when the body leaves it.
        self.last_tight_rect = None
        self.mask_padding = 80

        self.screen_geometry = (screen_x, screen_y, screen_width, screen_height)
        self.move(screen_x, screen_y)
        self.resize(screen_width, screen_height)

        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # False when the click came from touch or a pen (the system converts it
        # to a mouse event). In that case, the physical button state does not apply.
        self.pressed_by_real_mouse = True

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_stickman(painter, self.stickman)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

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

        self.pressed_by_real_mouse = (
            event.source() == Qt.MouseEventNotSynthesized
        )

        # Start the mouse reference here; otherwise, the first movement computes
        # velocity against a stale value (or zero).
        self.mouse_old_x = mouse_x
        self.mouse_old_y = mouse_y
        self.drag_velocity_x = 0
        self.drag_velocity_y = 0

        self.drag_offset_x = (
            mouse_x
            - self.stickman.joints[self.stickman.grab_part]['position'][0]
        )

        self.drag_offset_y = (
            mouse_y
            - self.stickman.joints[self.stickman.grab_part]['position'][1]
        )

        self.stickman.ragpoints = create_ragpoints(
            self.stickman.joints
        )

        self.stickman.flying = False
        self.stickman.holding = True

    def mouseMoveEvent(self, event):
        if not self.stickman.holding:
            return

        self.follow_mouse(event.globalPos().x(), event.globalPos().y())

    def follow_mouse(self, mouse_x, mouse_y):
        self.drag_velocity_x = mouse_x - self.mouse_old_x
        self.mouse_old_x = mouse_x

        self.drag_velocity_y = mouse_y - self.mouse_old_y
        self.mouse_old_y = mouse_y

        move_grab_part(self.stickman, mouse_x, mouse_y, self.drag_offset_x, self.drag_offset_y)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self.release_stickman()

    def release_stickman(self):
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

    def sync_to_screen(self):
        # If the display changes (resolution or primary monitor), the overlay
        # window must follow. Rebuild the mask from scratch afterward.
        geometry = get_screen_geometry()

        if geometry == self.screen_geometry:
            return

        self.screen_geometry = geometry

        screen_x, screen_y, screen_width, screen_height = geometry

        self.move(screen_x, screen_y)
        self.resize(screen_width, screen_height)

        self.last_mask_rect = None
        self.last_tight_rect = None

    def update_position(self):
        self.sync_to_screen()

        # Alt+Tab (or another window switch) can swallow the mouse-release
        # event. If the button is no longer pressed but the stickman is still
        # held, release it manually.
        # The checks below read the physical mouse state, so they apply only
        # when the click came from a physical mouse (not touch or a pen).
        if self.stickman.holding and self.pressed_by_real_mouse:
            if not is_left_mouse_pressed():
                self.release_stickman()
            else:
                # While Alt+Tab is open, movement events go to the switcher
                # instead of reaching us. If the cursor moved without Qt
                # notifying us, keep following it.
                cursor = QCursor.pos()

                if (cursor.x(), cursor.y()) != (self.mouse_old_x, self.mouse_old_y):
                    self.follow_mouse(cursor.x(), cursor.y())
                else:
                    self.drag_velocity_x = 0
                    self.drag_velocity_y = 0

        tight_rect = self.compute_mask_rect()

        if self.last_tight_rect is None:
            dirty_rect = tight_rect
        else:
            dirty_rect = tight_rect.united(self.last_tight_rect)

        self.last_tight_rect = tight_rect

        mask_is_stale = (
            self.last_mask_rect is None
            or not self.last_mask_rect.contains(tight_rect)
        )

        if mask_is_stale:
            padded_rect = tight_rect.adjusted(
                -self.mask_padding,
                -self.mask_padding,
                self.mask_padding,
                self.mask_padding
            )

            self.setMask(QRegion(padded_rect))

            self.last_mask_rect = padded_rect

            # When the mask changes, the newly exposed area may contain stale
            # frame data. Repaint the full screen for this frame only (the mask
            # changes rarely, so the cost is small).
            self.update()
            return

        # Repaint only the stickman's area (where it was and where it is),
        # instead of the entire screen.
        self.update(dirty_rect)

    def compute_mask_rect(self):
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

        return QRect(left, top, width, height)

    def apply_x11_hints(self):
        from Utils.x11_hints import set_window_type_dock, set_always_on_top_x11
        set_window_type_dock(int(self.winId()))
        set_always_on_top_x11(int(self.winId()))
        
    def showEvent(self, event):
        super().showEvent(event)

        if sys.platform == "win32":
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000

            hwnd = int(self.winId())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE
            )

    def nativeEvent(self, event_type, message):
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))

            WM_MOUSEACTIVATE = 0x0021
            MA_NOACTIVATE = 3

            if msg.message == WM_MOUSEACTIVATE:
                return True, MA_NOACTIVATE

        return super().nativeEvent(event_type, message)