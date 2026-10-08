from Utils.world_helpers import get_screen_geometry

class World:
    def __init__(self):
        self.screen_x, self.screen_y, self.screen_width, self.screen_height = get_screen_geometry()