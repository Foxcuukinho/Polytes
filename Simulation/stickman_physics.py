from Utils.utils import GRAVITY_ACCELERATION, DELTA_TIME, DEFAULT_WALK_SPEED
from Utils.screen import get_screen_geometry

class StickmanPhysics:

    def __init__(self):
        self.screen_x, self.screen_y, self.screen_width, self.screen_height = get_screen_geometry()

    def update(self,stickman):
        self.apply_gravity(stickman)
        self.resolve_ground_collision(stickman)
        self.resolve_edge_collision(stickman)
        self.apply_walk_movement(stickman)

    def apply_gravity(self, stickman):
        if stickman.dragging:
            return
        
        stickman.velocity_y += GRAVITY_ACCELERATION * DELTA_TIME
        stickman.y += stickman.velocity_y * DELTA_TIME

    def resolve_ground_collision(self, stickman):

        feet_y = stickman.y + stickman.height
        ground_y = self.screen_height 

        if feet_y >= ground_y:
            stickman.velocity_y = 0
            stickman.y = ground_y - stickman.height

    def resolve_edge_collision(self, stickman):
        
        stickman_right_edge = stickman.x + stickman.width
        screen_right_edge = self.screen_x + self.screen_width
        screen_left_edge  = self.screen_x
        
        if stickman.x <= screen_left_edge:
            stickman.x = screen_left_edge
        
        elif stickman_right_edge >= screen_right_edge:
            stickman.x = screen_right_edge - stickman.width

    def apply_walk_movement(self, stickman):

        if stickman.dragging:
            return

        if stickman.state == 'WALK':
            if stickman.target_x > stickman.x:
                stickman.direction = 1
            else:
                stickman.direction = -1

            stickman.velocity_x = DEFAULT_WALK_SPEED
 
            stickman.x += stickman.velocity_x * stickman.direction * DELTA_TIME 
        