from PyQt5.QtWidgets import QApplication
import pywinctl as pwc
import hashlib
import math
import sys
import os
from Utils.constants import GROUND_SNAP_TOLERANCE


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def is_mirrored(stickman):
    # Regra única de espelhamento, usada pelo desenho e pela máscara.
    # Espelha só no modo FK (andando/parado). No ragdoll (holding/flying)
    # os joints já vêm absolutos e não devem ser espelhados.
    ragdoll_active = stickman.holding or stickman.flying
    return stickman.direction == 1 and not ragdoll_active


def rectangle_overlap(
    first_x, first_y, first_width, first_height,
    second_x, second_y, second_width, second_height
):
    first_right = first_x + first_width
    first_bottom = first_y + first_height

    second_right = second_x + second_width
    second_bottom = second_y + second_height

    separated_horizontally = (
        first_right <= second_x or
        second_right <= first_x
    )

    separated_vertically = (
        first_bottom <= second_y or
        second_bottom <= first_y
    )

    return not separated_horizontally and not separated_vertically


def detect_collision_with_ragpoint_and_window(
    ragpoint,
    ragpoint_radius,
    window
):
    first_x = window.left
    first_y = window.top
    first_width = window.width
    first_height = window.height

    first_right = first_x + first_width
    first_bottom = first_y + first_height

    second_x = ragpoint.x - ragpoint_radius
    second_y = ragpoint.y - ragpoint_radius
    second_width = ragpoint_radius * 2
    second_height = ragpoint_radius * 2

    second_right = second_x + second_width
    second_bottom = second_y + second_height

    delta_x = abs(ragpoint.x - ragpoint.old_x)
    delta_y = abs(ragpoint.y - ragpoint.old_y)

    overlap = rectangle_overlap(
        first_x,
        first_y,
        first_width,
        first_height,
        second_x,
        second_y,
        second_width,
        second_height
    )

    if not overlap:
        return False, False, False, False, False

    left_collision = (
        second_right > first_x and
        second_right < first_right and
        ragpoint.x > ragpoint.old_x and
        delta_x > delta_y
    )

    right_collision = (
        second_x < first_right and
        second_x > first_x and
        ragpoint.x < ragpoint.old_x and
        delta_x > delta_y
    )

    top_collision = (
        second_bottom > first_y and
        second_bottom < first_bottom and
        ragpoint.y > ragpoint.old_y and
        delta_y > delta_x
    )

    bottom_collision = (
        second_y < first_bottom and
        second_y > first_y and
        ragpoint.y < ragpoint.old_y and
        delta_y > delta_x
    )

    return (
        True,
        left_collision,
        right_collision,
        top_collision,
        bottom_collision
    )


def subtract_interval(original, covering):

    original_left, original_right = original
    covering_left, covering_right = covering

    no_overlap = (
        covering_right <= original_left
        or covering_left >= original_right
    )

    if no_overlap:
        return [original]

    remaining = []

    if covering_left > original_left:
        remaining.append((original_left, covering_left))

    if covering_right < original_right:
        remaining.append((covering_right, original_right))

    return remaining


def get_stacking_handles():

    if sys.platform != "linux":
        return None

    try:
        from ewmhlib import EwmhRoot
        return EwmhRoot().getClientListStacking()
    except Exception:
        return None


def get_visible_top_intervals(window, all_windows, stacking_handles):

    full_interval = (window.left, window.left + window.width)

    if stacking_handles is None:
        return [full_interval]

    window_handle = window.getHandle()

    if window_handle not in stacking_handles:
        return [full_interval]

    window_index = stacking_handles.index(window_handle)

    intervals = [full_interval]

    for other in all_windows:
        if other.getHandle() == window_handle:
            continue

        other_handle = other.getHandle()

        if other_handle not in stacking_handles:
            continue

        other_index = stacking_handles.index(other_handle)

        if other_index <= window_index:
            continue

        covers_top_line = (
            other.top <= window.top
            and other.top + other.height > window.top
        )

        if not covers_top_line:
            continue

        covering_interval = (other.left, other.left + other.width)

        new_intervals = []

        for interval in intervals:
            new_intervals.extend(
                subtract_interval(interval, covering_interval)
            )

        intervals = new_intervals

    return intervals


def compute_ground_y_and_limit(
    stickman,
    max_y,
    windows,
    screen_x,
    screen_y,
    screen_width,
    screen_height,
    visible_intervals=None
):
    candidates = [
        (
            screen_y + screen_height,
            (screen_x, screen_width)
        )
    ]

    for window in windows:
        if window.fullscreen:
            continue

        if window.top < max_y - GROUND_SNAP_TOLERANCE:
            continue

        intervals = (
            visible_intervals.get(window.getHandle(), [])
            if visible_intervals is not None
            else get_visible_top_intervals(window, windows, get_stacking_handles())
        )

        for start, end in intervals:
            stickman_left = stickman.x
            stickman_right = stickman.x + stickman.width

            overlaps_horizontally = (
                stickman_left < end
                and stickman_right > start
            )

            if overlaps_horizontally:
                candidates.append(
                    (
                        window.top,
                        (window.left, window.width)
                    )
                )

    return min(candidates, key=lambda candidate: candidate[0])


def seed_from_name(name):
    hash_value = hashlib.sha256(name.encode())
    number = int(hash_value.hexdigest(), 16)
    return number


def polar_point(origin, length, angle_degrees):
    angle_rad = math.radians(angle_degrees)

    x = origin[0] + length * math.cos(angle_rad)
    y = origin[1] + length * math.sin(angle_rad)

    return int(x), int(y)


def get_screen_geometry():
    screen = QApplication.primaryScreen().geometry()

    screen_x = screen.x()
    screen_y = screen.y()
    screen_width = screen.width()
    screen_height = screen.height()

    return (
        screen_x,
        screen_y,
        screen_width,
        screen_height
    )


class WindowSnapshot:
    __slots__ = ("left", "top", "width", "height", "handle", "fullscreen")

    def __init__(self, window, fullscreen=False):
        self.left = window.left
        self.top = window.top
        self.width = window.width
        self.height = window.height
        self.handle = window.getHandle()
        self.fullscreen = fullscreen

    def getHandle(self):
        return self.handle

def get_windows():
    windows = pwc.getAllWindows()
    valid_windows = []

    screen_x, screen_y, screen_width, screen_height = (
        get_screen_geometry()
    )

    screen_area = screen_width * screen_height
    own_pid = os.getpid()

    for window in windows:
        if window.isMinimized or not window.isVisible:
            continue

        is_fullscreen = window.width * window.height >= screen_area * 0.95

        if is_fullscreen:
            try:
                if window.getPID() == own_pid:
                    continue
            except Exception:
                pass

        valid_windows.append(WindowSnapshot(window, is_fullscreen))

    return valid_windows

def get_ghost_process_command(name):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        ghost_path = os.path.join(base_path, 'stickman_ghost_process.exe')
        return [ghost_path, name]
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        ghost_path = os.path.join(
            os.path.dirname(base_path),
            'Simulation',
            'stickman_ghost_process.py'
        )
        return ['python3', ghost_path, name]