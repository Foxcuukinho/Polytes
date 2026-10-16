from Utils.constants import (
    RAGPOINT_RADIUS,
    RAGDOLL_BOUNCE_FACTOR,
    RAGDOLL_CENTER_DAMPING_X,
    RAGDOLL_CENTER_DAMPING_Y,
    RAGDOLL_SOLVER_ITERATIONS,
    LANDING_RECOVERY_TIME,
    STICKMAN_WIDTH,
    STICKMAN_HEIGHT,
    STROKE
)
from Utils.helpers import (
    detect_collision_with_ragpoint_and_window,
    get_work_area_geometry,
    compute_ground_y_and_limit,
    rectangle_overlap,
    measure
)
from Body.body_physics import sync_ragpoints_to_fk, solve_body


class StickmanRagdoll:
    def __init__(self):
        self.refresh_screen_geometry()

        self.windows = []
        self.visible_intervals = {}

        # Bounding-box cache, valid only during one call to apply_ragdoll.
        self._bounds = None

    def refresh_screen_geometry(self):
        (
            self.screen_x,
            self.screen_y,
            self.screen_width,
            self.screen_height
        ) = get_work_area_geometry()

    def update(self, stickman, windows, visible_intervals):
        # windows and visible_intervals are provided by the manager (computed
        # once every WINDOW_UPDATE_INTERVAL_FRAMES, not every frame).
        # The window list is replaced only when the manager refreshes its cache.
        # Use that opportunity to read the screen geometry again as well.
        if windows is not self.windows:
            self.refresh_screen_geometry()

        self.windows = windows
        self.visible_intervals = visible_intervals

        if not (stickman.flying or stickman.holding):
            self.check_ground_lost(stickman)
            return

        self.apply_ragdoll(stickman)

    def get_point_radius(self, name, stickman):
        return (
            stickman.head_radius
            if name == "head"
            else RAGPOINT_RADIUS
        )

    def move_points(self, points, offset_x=0, offset_y=0):
        for point in points:
            point.x += offset_x
            point.y += offset_y

        self._bounds = None

    def bounce_x(self, points):
        for point in points:
            vx = point.x - point.old_x
            point.old_x = point.x + vx * RAGDOLL_BOUNCE_FACTOR

    def bounce_y(self, points):
        for point in points:
            vy = point.y - point.old_y
            point.old_y = point.y + vy * RAGDOLL_BOUNCE_FACTOR

    def compute_ragdoll_bounds(self, stickman):
        if self._bounds is not None:
            return self._bounds

        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for name, point in stickman.ragpoints.items():
            radius = self.get_point_radius(name, stickman)

            min_x = min(min_x, point.x - radius)
            max_x = max(max_x, point.x + radius)
            min_y = min(min_y, point.y - radius)
            max_y = max(max_y, point.y + radius)

        self._bounds = (min_x, min_y, max_x, max_y)
        return self._bounds

    def update_overlapped_windows_in_holding(self, stickman):
        if not stickman.holding:
            return

        min_x, min_y, max_x, max_y = self.compute_ragdoll_bounds(stickman)

        ragdoll_width = max_x - min_x
        ragdoll_height = max_y - min_y

        for window in self.windows:
            handle = window.getHandle()

            overlap = rectangle_overlap(
                window.left, window.top, window.width, window.height,
                min_x, min_y, ragdoll_width, ragdoll_height
            )

            if overlap:
                if handle in stickman.overlap_windows:
                    continue

                stickman.overlap_windows.append(handle)

    def update_overlapped_windows_in_flying(self, stickman):
        if not stickman.flying:
            return

        min_x, min_y, max_x, max_y = self.compute_ragdoll_bounds(stickman)

        ragdoll_width = max_x - min_x
        ragdoll_height = max_y - min_y

        hip = stickman.ragpoints["hip"]

        for window in self.windows:
            handle = window.getHandle()

            overlap = rectangle_overlap(
                window.left, window.top, window.width, window.height,
                min_x, min_y, ragdoll_width, ragdoll_height
            )

            if handle in stickman.overlap_windows:
                if not overlap:
                    stickman.overlap_windows.remove(handle)
                continue

            hip_inside_window = (
                window.left <= hip.x <= window.left + window.width
                and window.top <= hip.y <= window.top + window.height
            )

            if overlap and hip_inside_window:
                stickman.overlap_windows.append(handle)

    def resolve_flying_landing(self, stickman):
        if not stickman.flying:
            return

        _, _, _, max_y = self.compute_ragdoll_bounds(stickman)

        stickman.ground_y, stickman.ground_limit = (
            compute_ground_y_and_limit(
                stickman,
                max_y,
                self.windows,
                self.screen_x,
                self.screen_y,
                self.screen_width,
                self.screen_height,
                visible_intervals=self.visible_intervals
            )
        )

        if max_y >= stickman.ground_y:
            stickman.flying = False
            self.on_landed(stickman)

    def on_landed(self, stickman):
        # After landing, remain still for a while instead of walking away.
        # Set the state to IDLE and extend the brain cooldown so decide() runs
        # again only after the recovery period.
        stickman.state = 'IDLE'
        stickman.target_x = None
        stickman.velocity_x = 0
        stickman.decide_cooldown = LANDING_RECOVERY_TIME
        stickman.animation_frame_index = 0
        stickman.animation_timer = 0

    def check_ground_lost(self, stickman):
        if stickman.flying or stickman.holding:
            return

        ground_left, ground_width = stickman.ground_limit

        if (
            stickman.x > ground_left + ground_width
            or stickman.x + stickman.width < ground_left
        ):
            sync_ragpoints_to_fk(stickman)
            stickman.flying = True

    def resolve_flying_edge_collision(self, stickman):
        if not stickman.flying:
            return

        screen_left = self.screen_x
        screen_right = self.screen_x + self.screen_width
        screen_top = self.screen_y

        points = list(stickman.ragpoints.values())

        min_x, min_y, max_x, _ = self.compute_ragdoll_bounds(stickman)

        if min_x < screen_left:
            self.move_points(
                points,
                offset_x=screen_left - min_x
            )
            self.bounce_x(points)

        elif max_x > screen_right:
            self.move_points(
                points,
                offset_x=screen_right - max_x
            )
            self.bounce_x(points)

        if min_y < screen_top:
            self.move_points(
                points,
                offset_y=screen_top - min_y
            )
            self.bounce_y(points)

    def resolve_flying_window_collision(self, stickman):
        if not stickman.flying:
            return

        ragpoints = stickman.ragpoints

        for window in self.windows:
            handle = window.getHandle()

            if window.fullscreen:
                continue

            if handle in stickman.overlap_windows:
                continue

            visible_intervals = self.visible_intervals.get(handle, [])

            if not visible_intervals:
                continue

            window_right = window.left + window.width
            window_bottom = window.top + window.height

            for name, ragpoint in ragpoints.items():
                radius = self.get_point_radius(name, stickman)

                (
                    overlap,
                    left_collision,
                    right_collision,
                    top_collision,
                    bottom_collision,
                    collision_time
                ) = detect_collision_with_ragpoint_and_window(
                    ragpoint,
                    radius,
                    window
                )

                if not overlap:
                    continue

                if top_collision:
                    collision_x = (
                        ragpoint.old_x
                        + (ragpoint.x - ragpoint.old_x) * collision_time
                    )
                    point_visible = any(
                        start <= collision_x <= end
                        for start, end in visible_intervals
                    )
                    if not point_visible:
                        top_collision = False

                if not (left_collision or right_collision or top_collision or bottom_collision):
                    continue

                min_x, min_y, max_x, max_y = (
                    self.compute_ragdoll_bounds(stickman)
                )

                points = list(ragpoints.values())

                if left_collision:
                    self.move_points(
                        points,
                        offset_x=window.left - max_x
                    )
                    self.bounce_x(points)

                elif right_collision:
                    self.move_points(
                        points,
                        offset_x=window_right - min_x
                    )
                    self.bounce_x(points)

                if top_collision:
                    self.move_points(
                        points,
                        offset_y=window.top - max_y
                    )
                    self.bounce_y(points)

                    self.resolve_flying_landing(stickman)

                elif bottom_collision:
                    self.move_points(
                        points,
                        offset_y=window_bottom - min_y
                    )
                    self.bounce_y(points)

    def damp_center_velocity(self, stickman):
        # Damp only the body's mean velocity (translation).
        # Each point's velocity relative to the mean (rotation) remains unchanged.
        if not stickman.flying:
            return

        points = list(stickman.ragpoints.values())

        mean_vx = sum(p.x - p.old_x for p in points) / len(points)
        mean_vy = sum(p.y - p.old_y for p in points) / len(points)

        for point in points:
            point.old_x += mean_vx * (1 - RAGDOLL_CENTER_DAMPING_X)
            point.old_y += mean_vy * (1 - RAGDOLL_CENTER_DAMPING_Y)

    def apply_ragdoll(self, stickman):
        if not (stickman.holding or stickman.flying):
            return

        # The cache is valid only for this frame.
        self._bounds = None

        for name, ragpoint in stickman.ragpoints.items():
            if name == stickman.grab_part:
                continue

            ragpoint.update()

        for _ in range(RAGDOLL_SOLVER_ITERATIONS):
            solve_body(
                stickman.ragpoints,
                stickman.head_radius,
                stickman.grab_part
            )

        self.damp_center_velocity(stickman)

        # Points changed (update + solver + damping), so invalidate the cache again.
        self._bounds = None

        self.update_overlapped_windows_in_holding(stickman)
        self.update_overlapped_windows_in_flying(stickman)
        self.resolve_flying_edge_collision(stickman)

        # Note: this includes part of resolve_flying_landing when landing on a window.
        self.resolve_flying_window_collision(stickman)
        self.resolve_flying_landing(stickman)

        if stickman.flying:
            min_x, min_y, max_x, max_y = (
                self.compute_ragdoll_bounds(stickman)
            )

            stickman.x = int(min_x)
            stickman.y = int(min_y)
            stickman.width = int(max_x - min_x)
            stickman.height = int(max_y - min_y)

        elif not stickman.holding:
            stickman.width = STICKMAN_WIDTH
            stickman.height = STICKMAN_HEIGHT

            hip_x = stickman.ragpoints["hip"].x

            stickman.x = int(
                hip_x - stickman.width / 2
            )

            ground_y = (
                stickman.ground_y
                if stickman.ground_y is not None
                else self.screen_y + self.screen_height
            )

            stickman.y = int(
                ground_y - stickman.height
            )