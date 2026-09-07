from PyQt5.QtWidgets import QApplication
import pywinctl as pwc
import hashlib, math, os, sys
from Utils.constants import GROUND_SNAP_TOLERANCE


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


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

def compute_ground_y_and_limit(
    stickman,
    max_y,
    windows,
    screen_x,
    screen_y,
    screen_width,
    screen_height
):
    candidates = [
        (
            screen_y + screen_height,
            (screen_x, screen_width),
            None
        )
    ]

    hip_x = stickman.ragpoints["hip"].x

    for window in windows:
        if window.top < max_y - GROUND_SNAP_TOLERANCE:
            continue

        window_left = window.left
        window_right = window.left + window.width

        overlaps_horizontally = (
            hip_x > window_left
            and hip_x < window_right
        )

        if overlaps_horizontally:
            candidates.append(
                (
                    window.top,
                    (window.left, window.width),
                    window.getHandle()
                )
            )

    current_handle = getattr(stickman, "ground_window_handle", None)

    if current_handle is not None:
        for candidate in candidates:
            if candidate[2] == current_handle:
                stickman.ground_window_handle = candidate[2]
                return candidate[0], candidate[1]

    chosen = min(candidates, key=lambda candidate: candidate[0])
    stickman.ground_window_handle = chosen[2]
    return chosen[0], chosen[1]

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


def get_windows():
    windows = pwc.getAllWindows()
    valid_windows = []

    screen_x, screen_y, screen_width, screen_height = (
        get_screen_geometry()
    )

    screen_area = screen_width * screen_height

    for window in windows:
        if window.isMinimized or not window.isVisible:
            continue

        window_area = window.width * window.height

        if window_area >= screen_area * 0.95:
            continue

        valid_windows.append(window)

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