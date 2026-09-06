from Utils.constants import (
    GRAVITY_ACCELERATION,
    DELTA_TIME,
    DEFAULT_WALK_SPEED,
    WINDOW_UPDATE_INTERVAL_FRAMES
)

from Utils.helpers import (
    get_screen_geometry,
    get_windows,
    compute_ground_y_and_limit
)


class StickmanPhysics:

    def __init__(self):
        (
            self.screen_x,
            self.screen_y,
            self.screen_width,
            self.screen_height
        ) = get_screen_geometry()

        self.windows = []
        self.frames_since_window_update = 0

    def update(self, stickman):
        self.frames_since_window_update += 1

        if (
            self.frames_since_window_update
            >= WINDOW_UPDATE_INTERVAL_FRAMES
        ):
            self.windows = get_windows()
            self.frames_since_window_update = 0

        self.apply_gravity(stickman)
        self.resolve_ground_collision(stickman)
        self.resolve_edge_collision(stickman)
        self.apply_walk_movement(stickman)

    def apply_gravity(self, stickman):
        if stickman.holding or stickman.flying:
            return

        stickman.velocity_y += (
            GRAVITY_ACCELERATION * DELTA_TIME
        )

        stickman.y += (
            stickman.velocity_y * DELTA_TIME
        )

    def resolve_ground_collision(self, stickman):
        if stickman.holding or stickman.flying:
            return


        feet_y = stickman.y + stickman.height

        max_y = max(
            point.y
            for point in stickman.ragpoints.values()
        )

        ground_y, ground_limit = compute_ground_y_and_limit(
            stickman,
            feet_y,
            self.windows,
            self.screen_x,
            self.screen_y,
            self.screen_width,
            self.screen_height
        )

        stickman.ground_limit = ground_limit

        if feet_y >= ground_y:
            stickman.velocity_y = 0
            stickman.y = ground_y - stickman.height

    def resolve_edge_collision(self, stickman):
        if stickman.holding or stickman.flying:
            return

        screen_left = self.screen_x
        screen_right = self.screen_x + self.screen_width

        stickman_right = stickman.x + stickman.width

        if stickman.x <= screen_left:
            stickman.x = screen_left

        elif stickman_right >= screen_right:
            stickman.x = screen_right - stickman.width

    def apply_walk_movement(self, stickman):
        if stickman.holding or stickman.flying:
            return

        if stickman.state != "WALK":
            return

        if stickman.target_x > stickman.x:
            stickman.direction = 1
        else:
            stickman.direction = -1

        stickman.velocity_x = DEFAULT_WALK_SPEED

        stickman.x += (
            stickman.velocity_x
            * stickman.direction
            * DELTA_TIME
        )

