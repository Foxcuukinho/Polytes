from Utils.physics_constants import GRAVITY_ACCELERATION
from Utils.configs import DELTA_TIME

class StickmanWorldPhysics:
    def __init__(self, world):
        self.world = world

    def update(self, stickman):
        if stickman.dragging:
            return
        
        self.apply_gravity(stickman)
        self.solve_ground_collision(stickman)

    def apply_gravity(self, stickman):
        stickman.vy += GRAVITY_ACCELERATION * DELTA_TIME
        stickman.y += int(stickman.vy * DELTA_TIME)

    def solve_ground_collision(self, stickman):
        if stickman.y + 200 > self.world.screen_height:
            stickman.y = self.world.screen_height - 200
            stickman.vy = 0