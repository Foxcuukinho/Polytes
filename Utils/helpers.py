from PyQt5.QtWidgets import QApplication
import pywinctl as pwc
import hashlib
import math
import sys
import os
import subprocess
from Utils.constants import GROUND_SNAP_TOLERANCE, FONTS_DIR, RCEDIT_PATH
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtCore import Qt
import shutil
import tempfile
import uuid
import sys
import ctypes

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
SM_SWAPBUTTON = 23

VK_LBUTTON = 0x01


def is_left_mouse_pressed():
    # On Windows, ask the operating system whether the primary button is
    # currently pressed. QApplication.mouseButtons() is not suitable here: it
    # only knows which events Qt received, and if Alt+Tab swallows the release
    # event, it keeps reporting the button as pressed indefinitely.
    if sys.platform == "win32":
        import ctypes

        user32 = ctypes.windll.user32

        # GetAsyncKeyState checks the PHYSICAL button. If buttons are swapped
        # in system settings, the "primary" button (which Qt calls left) is
        # the physical right button.
        swapped = user32.GetSystemMetrics(SM_SWAPBUTTON) != 0
        virtual_key = VK_RBUTTON if swapped else VK_LBUTTON

        return bool(user32.GetAsyncKeyState(virtual_key) & 0x8000)

    return bool(QApplication.mouseButtons() & Qt.LeftButton)

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def is_mirrored(stickman):
    # Single mirroring rule, used by both drawing and the mask.
    # Mirror only in FK mode (walking/idle). In ragdoll mode (holding/flying),
    # joints are already absolute and must not be mirrored.
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
        start_x = ragpoint.old_x
        start_y = ragpoint.old_y
        delta_x = ragpoint.x - start_x
        delta_y = ragpoint.y - start_y

        expanded_left = first_x - ragpoint_radius
        expanded_right = first_right + ragpoint_radius
        expanded_top = first_y - ragpoint_radius
        expanded_bottom = first_bottom + ragpoint_radius

        starts_inside = (
            expanded_left < start_x < expanded_right
            and expanded_top < start_y < expanded_bottom
        )

        if starts_inside:
            return False, False, False, False, False, 1.0

        if delta_x == 0:
            if not expanded_left <= start_x <= expanded_right:
                return False, False, False, False, False, 1.0
            entry_x = float("-inf")
            exit_x = float("inf")
        else:
            first_x_time = (expanded_left - start_x) / delta_x
            second_x_time = (expanded_right - start_x) / delta_x
            entry_x = min(first_x_time, second_x_time)
            exit_x = max(first_x_time, second_x_time)

        if delta_y == 0:
            if not expanded_top <= start_y <= expanded_bottom:
                return False, False, False, False, False, 1.0
            entry_y = float("-inf")
            exit_y = float("inf")
        else:
            first_y_time = (expanded_top - start_y) / delta_y
            second_y_time = (expanded_bottom - start_y) / delta_y
            entry_y = min(first_y_time, second_y_time)
            exit_y = max(first_y_time, second_y_time)

        collision_time = max(entry_x, entry_y)
        exit_time = min(exit_x, exit_y)

        if collision_time > exit_time or collision_time < 0 or collision_time > 1:
            return False, False, False, False, False, 1.0

        hit_x = abs(entry_x - collision_time) < 1e-9
        hit_y = abs(entry_y - collision_time) < 1e-9

        return (
            True,
            hit_x and delta_x > 0,
            hit_x and delta_x < 0,
            hit_y and delta_y > 0,
            hit_y and delta_y < 0,
            collision_time
        )

    left_collision = (
        second_right > first_x and
        second_right < first_right and
        ragpoint.x > ragpoint.old_x
    )

    right_collision = (
        second_x < first_right and
        second_x > first_x and
        ragpoint.x < ragpoint.old_x
    )

    top_collision = (
        second_bottom > first_y and
        second_bottom < first_bottom and
        ragpoint.y > ragpoint.old_y
    )

    bottom_collision = (
        second_y < first_bottom and
        second_y > first_y and
        ragpoint.y < ragpoint.old_y
    )

    horizontal_collision = left_collision or right_collision
    vertical_collision = top_collision or bottom_collision

    if horizontal_collision and vertical_collision:
        horizontal_penetration = min(
            depth for depth in (
                second_right - first_x if left_collision else None,
                first_right - second_x if right_collision else None
            )
            if depth is not None
        )
        vertical_penetration = min(
            depth for depth in (
                second_bottom - first_y if top_collision else None,
                first_bottom - second_y if bottom_collision else None
            )
            if depth is not None
        )

        if horizontal_penetration <= vertical_penetration:
            top_collision = False
            bottom_collision = False
        else:
            left_collision = False
            right_collision = False

    return (
        True,
        left_collision,
        right_collision,
        top_collision,
        bottom_collision,
        1.0
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
    # Return handles from bottom to top (the same order as X11's
    # _NET_CLIENT_LIST_STACKING) so the rest of the code works the same on
    # both systems. None means stacking information is unavailable.

    if sys.platform == "win32":
        try:
            import win32gui
            import win32con

            handles = []
            hwnd = win32gui.GetTopWindow(None)

            # Walk down from the top of the stack. The limit prevents an
            # infinite loop if a window is destroyed during the scan.
            while hwnd and len(handles) < 2000:
                handles.append(hwnd)
                hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)

            handles.reverse()
            return handles
        except Exception:
            return None

    if sys.platform != "linux":
        return None

    try:
        from ewmhlib import EwmhRoot
        return EwmhRoot().getClientListStacking()
    except Exception:
        return None


def build_stacking_index(stacking_handles):
    # Convert the handle list to a handle -> stack-position mapping, allowing
    # direct position lookups without a linear search.
    if stacking_handles is None:
        return None

    return {
        handle: index
        for index, handle in enumerate(stacking_handles)
    }


def get_visible_top_intervals(window, all_windows, stacking_index):

    full_interval = (window.left, window.left + window.width)

    if stacking_index is None:
        return [full_interval]

    window_handle = window.getHandle()

    window_index = stacking_index.get(window_handle)

    if window_index is None:
        return [full_interval]

    intervals = [full_interval]

    for other in all_windows:
        other_handle = other.getHandle()

        if other_handle == window_handle:
            continue

        other_index = stacking_index.get(other_handle)

        if other_index is None or other_index <= window_index:
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


def compute_all_visible_intervals(windows):
    # Calculate visible intervals for ALL windows at once, reading the stacking
    # order only once. Called only when the window list is refreshed, not every frame.
    stacking_index = build_stacking_index(get_stacking_handles())

    return {
        window.getHandle(): get_visible_top_intervals(
            window, windows, stacking_index
        )
        for window in windows
    }


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
            else get_visible_top_intervals(
                window,
                windows,
                build_stacking_index(get_stacking_handles())
            )
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


def get_work_area_geometry():
    # Usable screen area. On Windows, excludes the taskbar (wherever it is),
    # so the "ground" is always above it. The overlay still uses
    # get_screen_geometry (the full screen) for drawing.
    screen = QApplication.primaryScreen()

    rect = (
        screen.availableGeometry()
        if sys.platform == "win32"
        else screen.geometry()
    )

    return (
        rect.x(),
        rect.y(),
        rect.width(),
        rect.height()
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


# Windows window classes that are UI elements rather than application windows.
# Identify them by class instead of title, because titles vary with the system language.
NOT_REAL_WINDOW_CLASSES = {
    "MultitaskingViewFrame",         # Alt+Tab / Task View (Windows 10)
    "XamlExplorerHostIslandWindow",  # Alt+Tab (Windows 11)
}

GA_ROOT = 2
DWMWA_CLOAKED = 14


def is_cloaked(hwnd):
    # A window "hidden" by Windows: reported as visible by the API, but not
    # seen by the user (closed Cortana/Search, suspended UWP apps, or windows
    # on another virtual desktop).
    import ctypes
    from ctypes import wintypes

    cloaked = wintypes.DWORD(0)

    result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd),
        DWMWA_CLOAKED,
        ctypes.byref(cloaked),
        ctypes.sizeof(cloaked)
    )

    return result == 0 and cloaked.value != 0


def is_real_window(window):
    # Filter out pywinctl results that are not actual windows: internal
    # controls (buttons, "Ribbon", "Chrome Legacy Window"), cloaked windows,
    # and the Alt+Tab interface. Windows only; no filtering is needed on Linux.
    if sys.platform != "win32":
        return True

    try:
        import win32gui

        hwnd = window.getHandle()

        # A real top-level window is its own root window.
        # Child controls have a different root window.
        if win32gui.GetAncestor(hwnd, GA_ROOT) != hwnd:
            return False

        if is_cloaked(hwnd):
            return False

        if win32gui.GetClassName(hwnd) in NOT_REAL_WINDOW_CLASSES:
            return False

        return True
    except Exception:
        # When in doubt, keep the window (previous behavior).
        return True


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

        if window.width <= 0 or window.height <= 0:
            continue

        if not is_real_window(window):
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


def apply_ghost_description(exe_path):
    # Set the file description ("A StickFigure") on the ghost process .exe;
    # it appears in the Task Manager Details tab.
    # This must run BEFORE Popen because Windows locks a running .exe.
    if sys.platform != "win32":
        return

    result = subprocess.run(
        [
            str(RCEDIT_PATH),
            exe_path,
            "--set-version-string", "FileDescription", "A StickFigure",
        ],
        capture_output=True,
        text=True,
    )

# Names reserved by Windows for devices: creating a file with one of these
# names (even with an extension, such as "con.exe") writes to the device, not disk.
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def cleanup_old_ghost_dirs():
    # Remove leftovers from previous runs. Windows will not delete files for
    # active ghost processes (.exe files still running), so they remain harmlessly
    # in place (ignore_errors).
    ghosts_root = os.path.join(tempfile.gettempdir(), "polytes_ghosts")
    shutil.rmtree(ghosts_root, ignore_errors=True)



def get_ghost_process_command(name):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ghost_script = os.path.join(project_root, 'Simulation', 'stickman_ghost_process.py')
    frozen = getattr(sys, 'frozen', False)

    # Linux: setproctitle names the process, so no copy/rename/rcedit needed.
    if sys.platform.startswith('linux'):
        if frozen:
            ghost = os.path.join(sys._MEIPASS, 'stickman_ghost_process')
            return [ghost, name, str(os.getpid())], None

        env = os.environ.copy()
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')
        return [sys.executable, ghost_script, name, str(os.getpid())], env

    # Windows: each stickman gets its own exe copy named after it.
    safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip() or "Untitled"

    if safe_name.upper() in WINDOWS_RESERVED_NAMES:
        safe_name += "StickFigure"

    ghost_dir = os.path.join(tempfile.gettempdir(), "polytes_ghosts", uuid.uuid4().hex)
    os.makedirs(ghost_dir, exist_ok=True)
    ghost_exe = os.path.join(ghost_dir, f"{safe_name}.exe")

    if frozen:
        source = os.path.join(sys._MEIPASS, 'stickman_ghost_process.exe')
        shutil.copy2(source, ghost_exe)
        apply_ghost_description(ghost_exe)
        return [ghost_exe, name, str(os.getpid())], None

    base_prefix = sys.base_prefix
    shutil.copy2(os.path.join(base_prefix, 'python.exe'), ghost_exe)

    for dll in os.listdir(base_prefix):
        if dll.lower().endswith('.dll') and (
            dll.lower().startswith('python3')
            or dll.lower().startswith('vcruntime')
        ):
            shutil.copy2(os.path.join(base_prefix, dll), ghost_dir)

    env = os.environ.copy()
    env['PYTHONHOME'] = base_prefix
    apply_ghost_description(ghost_exe)

    return [ghost_exe, ghost_script, name, str(os.getpid())], env


def load_fonts():
    for font_file in FONTS_DIR.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font_file))