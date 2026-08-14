from Utils.utils import GRAVITY_ACCELERATION, DELTA_TIME, DEFAULT_WALK_SPEED, STROKE
from Utils.screen import get_screen_geometry
from Body.body_physics import solve_body

class StickmanPhysics:

    def __init__(self):
        self.screen_x, self.screen_y, self.screen_width, self.screen_height = get_screen_geometry()

    def update(self,stickman):
        self.apply_ragdoll(stickman)
        self.apply_gravity(stickman)
        self.resolve_ground_collision(stickman)
        self.resolve_edge_collision(stickman)
        self.apply_walk_movement(stickman)

    def apply_gravity(self, stickman):
        if stickman.holding or stickman.flying:
            return
        
        stickman.velocity_y += GRAVITY_ACCELERATION * DELTA_TIME
        stickman.y += stickman.velocity_y * DELTA_TIME

    def resolve_ground_collision(self, stickman):

        if stickman.holding or stickman.flying:
            return

        feet_y = stickman.y + stickman.height
        ground_y = self.screen_height 

        if feet_y >= ground_y:
            stickman.velocity_y = 0
            stickman.y = ground_y - stickman.height

    def resolve_edge_collision(self, stickman):

        if stickman.holding or stickman.flying:
            return
        
        stickman_right_edge = stickman.x + stickman.width
        screen_right_edge = self.screen_x + self.screen_width
        screen_left_edge  = self.screen_x
        
        if stickman.x <= screen_left_edge:
            stickman.x = screen_left_edge
        
        elif stickman_right_edge >= screen_right_edge:
            stickman.x = screen_right_edge - stickman.width

    def apply_walk_movement(self, stickman):

        if stickman.holding or stickman.flying:
            return

        if stickman.state == 'WALK':
            if stickman.target_x > stickman.x:
                stickman.direction = 1
            else:
                stickman.direction = -1

            stickman.velocity_x = DEFAULT_WALK_SPEED
 
            stickman.x += stickman.velocity_x * stickman.direction * DELTA_TIME 

    def check_ground_contact(self, stickman):
        if not stickman.flying:
            return

        max_y = max(
            point.y
            for point in stickman.ragpoints.values()
        )

        ground_y = self.screen_y + self.screen_height

        if max_y >= ground_y:
            stickman.flying = False

    def apply_ragdoll(self, stickman):
        if not (stickman.holding or stickman.flying):
            return

        for ragpoint in stickman.ragpoints:
            if ragpoint == stickman.grab_part:
                continue

            stickman.ragpoints[ragpoint].update()

        for _ in range(200):
            solve_body(
                stickman.ragpoints,
                stickman.head_radius,
                stickman.grab_part
            )

        head_margin = stickman.head_radius * 2
        joint_margin = STROKE + 1 // 2

        min_x = min(
            point.x - (
                head_margin if name == "head"
                else joint_margin
            )
            for name, point in stickman.ragpoints.items()
        )

        min_y = min(
            point.y - (
                head_margin if name == "head"
                else joint_margin
            )
            for name, point in stickman.ragpoints.items()
        )

        max_x = max(
            point.x + (
                head_margin if name == "head"
                else joint_margin
            )
            for name, point in stickman.ragpoints.items()
        )

        max_y = max(
            point.y + (
                head_margin if name == "head"
                else joint_margin
            )
            for name, point in stickman.ragpoints.items()
        )

        stickman.x = int(min_x)
        stickman.y = int(min_y)
        stickman.width = int(max_x - min_x)
        stickman.height = int(max_y - min_y)

        self.check_ground_contact(stickman)