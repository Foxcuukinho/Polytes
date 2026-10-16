from Utils.constants import (
    GRAVITY_ACCELERATION,
    DELTA_TIME,
    DEFAULT_WALK_SPEED,
    WINDOW_UPDATE_INTERVAL_FRAMES,
    GROUND_SNAP_TOLERANCE
)

from Utils.helpers import (
    get_work_area_geometry,
    get_windows,
    compute_ground_y_and_limit,
    compute_all_visible_intervals
)

from Body.body_physics import sync_ragpoints_to_fk


class StickmanPhysics:

    def __init__(self):
        (
            self.screen_x,
            self.screen_y,
            self.screen_width,
            self.screen_height
        ) = get_work_area_geometry()

        self.windows = []
        self.visible_intervals = {}

        # Start at the limit so the first call to refresh_windows loads
        # the window list immediately.
        self.frames_since_window_update = WINDOW_UPDATE_INTERVAL_FRAMES

    def refresh_windows(self):
        # Called once per frame by the manager (not once per stickman).
        self.frames_since_window_update += 1

        if (
            self.frames_since_window_update
            >= WINDOW_UPDATE_INTERVAL_FRAMES
        ):
            self.windows = get_windows()
            self.visible_intervals = compute_all_visible_intervals(self.windows)

            self.frames_since_window_update = 0

    def update(self, stickman):
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

        ground_y, ground_limit = compute_ground_y_and_limit(
            stickman,
            feet_y,
            self.windows,
            self.screen_x,
            self.screen_y,
            self.screen_width,
            self.screen_height,
            visible_intervals=self.visible_intervals
        )

        previous_ground_y = stickman.ground_y

        # Was the stickman standing on the ground from the previous frame?
        was_standing = (
            previous_ground_y is not None
            and feet_y >= previous_ground_y - GROUND_SNAP_TOLERANCE
        )

        # The current ground is much lower than before: the previous ground
        # disappeared (a window was minimized, closed, or moved).
        ground_vanished = (
            was_standing
            and ground_y > previous_ground_y + GROUND_SNAP_TOLERANCE
        )

        if ground_vanished:
            # The ragdoll must start from the current pose (FK).
            sync_ragpoints_to_fk(stickman)
            stickman.flying = True
            return

        stickman.ground_y = ground_y
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