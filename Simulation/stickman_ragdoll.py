from Utils.constants import (
    WINDOW_UPDATE_INTERVAL_FRAMES,
    RAGPOINT_RADIUS,
    RAGDOLL_BOUNCE_FACTOR,
    STICKMAN_WIDTH,
    STICKMAN_HEIGHT,
    STROKE
)
from Utils.helpers import get_windows, detect_collision_with_ragpoint_and_window, get_screen_geometry, compute_ground_y_and_limit, rectangle_overlap
from Body.body_physics import calculate_joints, create_ragpoints, solve_body


class StickmanRagdoll:
    def __init__(self):
        self.screen_x, self.screen_y, self.screen_width, self.screen_height = get_screen_geometry()

        self.windows = []
        self.frames_since_window_update = 0

    def update(self, stickman):
        if not (stickman.flying or stickman.holding):
            return

        self.frames_since_window_update += 1

        if self.frames_since_window_update >= WINDOW_UPDATE_INTERVAL_FRAMES:
            self.windows = get_windows()
            self.frames_since_window_update = 0

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

    def bounce_x(self, points):
        for point in points:
            vx = point.x - point.old_x
            point.old_x = point.x + vx * RAGDOLL_BOUNCE_FACTOR

    def bounce_y(self, points):
        for point in points:
            vy = point.y - point.old_y
            point.old_y = point.y + vy * RAGDOLL_BOUNCE_FACTOR

    def compute_ragdoll_bounds(self, stickman):
        ragpoints = stickman.ragpoints

        min_x = min(
            point.x - self.get_point_radius(name, stickman)
            for name, point in ragpoints.items()
        )

        max_x = max(
            point.x + self.get_point_radius(name, stickman)
            for name, point in ragpoints.items()
        )

        min_y = min(
            point.y - self.get_point_radius(name, stickman)
            for name, point in ragpoints.items()
        )

        max_y = max(
            point.y + self.get_point_radius(name, stickman)
            for name, point in ragpoints.items()
        )

        return min_x, min_y, max_x, max_y

    def update_overlapped_windows_in_holding(self, stickman):
        if not stickman.holding:
            return

        min_x, min_y, max_x, max_y = self.compute_ragdoll_bounds(stickman)

        ragdoll_width = max_x - min_x
        ragdoll_height = max_y - min_y

        for window in self.windows:
            overlap = rectangle_overlap(
                window.left, window.top, window.width, window.height,
                min_x, min_y, ragdoll_width, ragdoll_height
            )

            if overlap:
                if window.getHandle() in stickman.overlap_windows:
                    continue

                stickman.overlap_windows.append(window.getHandle())
                


    def update_overlapped_windows_in_flying(self, stickman):
        if not stickman.flying:
            return

        min_x, min_y, max_x, max_y = self.compute_ragdoll_bounds(stickman)

        ragdoll_width = max_x - min_x
        ragdoll_height = max_y - min_y

        for window in self.windows:
            overlap = rectangle_overlap(
                window.left, window.top, window.width, window.height,
                min_x, min_y, ragdoll_width, ragdoll_height
            )

            if window.getHandle() in stickman.overlap_windows and not overlap:
                stickman.overlap_windows.remove(window.getHandle())
        

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
                self.screen_height
            )
        )

        if max_y >= stickman.ground_y:
            stickman.flying = False

    def check_ground_lost(self, stickman):
        ground_left, ground_width = stickman.ground_limit

        if (
            stickman.x > ground_left + ground_width
            or stickman.x + stickman.width < ground_left
        ):
            stickman.joints = calculate_joints(
                stickman.current_frame,
                stickman,
                stickman.head_radius
            )

            stickman.ragpoints = create_ragpoints(
                stickman.joints,
                stickman.x,
                stickman.y
            )

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
            

            if window.getHandle() in stickman.overlap_windows:
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
                    bottom_collision
                ) = detect_collision_with_ragpoint_and_window(
                    ragpoint,
                    radius,
                    window
                )

                if not overlap:
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
                    
    def apply_ragdoll(self, stickman):
        if not (stickman.holding or stickman.flying):
            return

        for name, ragpoint in stickman.ragpoints.items():
            if name == stickman.grab_part:
                continue

            ragpoint.update()

        for _ in range(20):
            solve_body(
                stickman.ragpoints,
                stickman.head_radius,
                stickman.grab_part
            )


        self.update_overlapped_windows_in_holding(stickman)
        self.update_overlapped_windows_in_flying(stickman)
        self.resolve_flying_edge_collision(stickman)
        self.resolve_flying_window_collision(stickman)
        self.resolve_flying_landing(stickman)

        if stickman.flying:
            self.check_ground_lost(stickman)

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