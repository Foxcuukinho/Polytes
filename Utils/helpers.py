from PyQt5.QtWidgets import QApplication
import pywinctl as pwc
import hashlib
import math

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))



def rectangle_overlap(first_x, first_y, first_width, first_height,second_x, second_y, second_width, second_height):

    first_right = first_x + first_width
    first_bottom = first_y + first_height
    second_right = second_x + second_width
    second_bottom = second_y + second_height

    separated_horizontally = first_right <= second_x or second_right <= first_x
    separated_vertically = first_bottom <= second_y or second_bottom <= first_y

    return not separated_horizontally and not separated_vertically

def detect_collision_with_ragpoint_and_window(ragpoint, ragpoint_radius, window):

    first_x, first_y, first_width, first_height = window.left, window.top, window.width, window.height

    first_right, first_bottom = first_x + first_width, first_y + first_height

    second_x, second_y = ragpoint.x - ragpoint_radius, ragpoint.y - ragpoint_radius
    second_width, second_height = ragpoint_radius * 2, ragpoint_radius * 2

    second_right, second_bottom = second_x + second_width, second_y + second_height

    delta_x = abs(ragpoint.x - ragpoint.old_x)
    delta_y = abs(ragpoint.y - ragpoint.old_y)

    overlap = rectangle_overlap(
        first_x, first_y, first_width, first_height,
        second_x, second_y, second_width, second_height
    )

    if overlap:

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

        return overlap, left_collision, right_collision, top_collision, bottom_collision

    else:
        return False, False, False, False, False
      
def seed_from_name(name):
    hash = hashlib.sha256(name.encode())
    number = int(hash.hexdigest(), 16)
    return number

def polar_point(origin,length, angle_degress):
    angle_rad = math.radians(angle_degress)
    x = origin[0] + length * math.cos(angle_rad)
    y = origin[1] + length * math.sin(angle_rad)
    return (int(x), int(y))

def get_screen_geometry():

    screen =  QApplication.primaryScreen().geometry()
    
    screen_x = screen.x()
    screen_y = screen.y()
    
    screen_width = screen.width()
    screen_height = screen.height()

    return screen_x, screen_y, screen_width, screen_height

def get_windows():

    windows = pwc.getAllWindows()
    valid_windows = []

    for window in windows:
        if window.isMinimized or not window.isVisible:
                continue

        screen_x, screen_y, screen_width, screen_height = get_screen_geometry()

        screen_area = screen_width* screen_height
        window_area = window.width * window.height

        if window_area >= screen_area * 0.95:
            continue
        else:
            valid_windows.append(window)

    return valid_windows
