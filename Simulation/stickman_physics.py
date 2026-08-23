import time
from Utils.constants import GRAVITY_ACCELERATION, DELTA_TIME, DEFAULT_WALK_SPEED, STROKE, RAGDOLL_BOUNCE_FACTOR, RAGPOINT_RADIUS, STICKMAN_WIDTH, STICKMAN_HEIGHT, WINDOW_UPDATE_INTERVAL_FRAMES
from Utils.helpers import get_screen_geometry, get_windows, detect_collision_with_ragpoint_and_window
from Body.body_physics import solve_body, calculate_joints, create_ragpoints


class StickmanPhysics:

    def __init__(self):
        self.screen_x, self.screen_y, self.screen_width, self.screen_height = get_screen_geometry()
        self.windows = []
        self.frames_since_window_update = 0

    def update(self, stickman):
        self.frames_since_window_update += 1
        if self.frames_since_window_update >= WINDOW_UPDATE_INTERVAL_FRAMES:
            self.windows = get_windows()
            self.frames_since_window_update = 0

        self.apply_ragdoll(stickman)
        self.apply_gravity(stickman)
        self.resolve_ground_collision(stickman)
        self.resolve_edge_collision(stickman)
        self.apply_walk_movement(stickman)
        self.check_ground_lost(stickman)

    def apply_gravity(self, stickman):
        if stickman.holding or stickman.flying:
            return

        stickman.velocity_y += GRAVITY_ACCELERATION * DELTA_TIME
        stickman.y += stickman.velocity_y * DELTA_TIME

    def resolve_ground_collision(self, stickman):

        if stickman.holding or stickman.flying:
            return

        feet_y = stickman.y + stickman.height

        max_y = max(point.y for point in stickman.ragpoints.values())
        ground_y, _ = self.compute_ground_y_and_limit(stickman, max_y)

        if feet_y >= ground_y:
            stickman.velocity_y = 0
            stickman.y = ground_y - stickman.height

    def resolve_edge_collision(self, stickman):

        if stickman.holding or stickman.flying:
            return

        stickman_right_edge = stickman.x + stickman.width
        screen_right_edge = self.screen_x + self.screen_width
        screen_left_edge = self.screen_x

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

            stickman.x += (
                stickman.velocity_x
                * stickman.direction
                * DELTA_TIME
            )

    # TODO: Fazer uma classe StickmanRagdoll

    def compute_ground_y_and_limit(self, stickman, max_y):
        candidates = [(self.screen_y + self.screen_height, (0, self.screen_width))]

        for window in self.windows:
            
            if window.top >= max_y:
                stickman_left = stickman.x
                stickman_right = stickman.x + stickman.width
                window_left = window.left
                window_right = window.left + window.width

                overlaps_horizontally = stickman_left < window_right and stickman_right > window_left

                if overlaps_horizontally:
                    candidates.append((window.top, (window.left, window.width)))

        best = min(candidates, key=lambda t: t[0])
        return best[0], best[1]
    
    def resolve_flying_landing(self, stickman):
        if not stickman.flying:
            return

        max_y = max(
            point.y + (stickman.head_radius if name == 'head' else RAGPOINT_RADIUS)
            for name, point in stickman.ragpoints.items()
        )

        stickman.ground_y, stickman.ground_limit = self.compute_ground_y_and_limit(stickman, max_y)

        if max_y >= stickman.ground_y:
            stickman.flying = False
    
    def resolve_flying_ground_contact(self, stickman):
        if not stickman.flying:
            return

        max_y = max(point.y for point in stickman.ragpoints.values())

        ground_y = self.screen_y + self.screen_height

        if max_y >= ground_y:
            stickman.flying = False

    def check_ground_lost(self, stickman):

        if stickman.flying or stickman.holding:
            return

        if (
            stickman.x > stickman.ground_limit[0] + stickman.ground_limit[1]
            or stickman.x + stickman.width < stickman.ground_limit[0]
        ):
            stickman.joints = calculate_joints(stickman.current_frame, stickman, stickman.head_radius)
            stickman.ragpoints = create_ragpoints(stickman.joints, stickman.x, stickman.y)

            stickman.flying = True

    def resolve_flying_edge_collision(self, stickman):

        if not stickman.flying:
            return

        screen_left = self.screen_x
        screen_right = self.screen_x + self.screen_width
        screen_top = self.screen_y

        points = list(stickman.ragpoints.values())

        min_x = min(point.x for point in points)
        max_x = max(point.x for point in points)
        min_y = min(point.y for point in points)

        hit_left = min_x < screen_left
        hit_right = max_x > screen_right
        hit_top = min_y < screen_top

        if hit_left:

            offset_x = screen_left - min_x

            for point in points:
                point.x += offset_x

            for point in points:
                vx = point.x - point.old_x
                point.old_x = point.x + vx * RAGDOLL_BOUNCE_FACTOR

        elif hit_right:

            offset_x = screen_right - max_x

            for point in points:
                point.x += offset_x

            for point in points:
                vx = point.x - point.old_x
                point.old_x = point.x + vx * RAGDOLL_BOUNCE_FACTOR

        if hit_top:

            offset_y = screen_top - min_y

            for point in points:
                point.y += offset_y

            for point in points:
                vy = point.y - point.old_y
                point.old_y = point.y + vy * RAGDOLL_BOUNCE_FACTOR

    def resolve_flying_window_collision(self, stickman):

        if not stickman.flying:
            return

        ragpoints = stickman.ragpoints

        for window in self.windows:

            window_right = window.left + window.width
            window_bottom = window.top + window.height

            for name, ragpoint in ragpoints.items():

                radius = stickman.head_radius if name == 'head' else RAGPOINT_RADIUS

                overlap, left_collision, right_collision, top_collision, bottom_collision = \
                    detect_collision_with_ragpoint_and_window(
                        ragpoint,
                        radius,
                        window
                    )

                if overlap:

                    min_x = min(
                        point.x - (stickman.head_radius if point_name == 'head' else RAGPOINT_RADIUS)
                        for point_name, point in ragpoints.items()
                    )

                    max_x = max(
                        point.x + (stickman.head_radius if point_name == 'head' else RAGPOINT_RADIUS)
                        for point_name, point in ragpoints.items()
                    )

                    min_y = min(
                        point.y - (stickman.head_radius if point_name == 'head' else RAGPOINT_RADIUS)
                        for point_name, point in ragpoints.items()
                    )

                    max_y = max(
                        point.y + (stickman.head_radius if point_name == 'head' else RAGPOINT_RADIUS)
                        for point_name, point in ragpoints.items()
                    )

                    if left_collision:

                        offset_x = window.left - max_x

                        for point in ragpoints.values():
                            point.x += offset_x

                        for point in ragpoints.values():
                            vx = point.x - point.old_x
                            point.old_x = point.x + vx * RAGDOLL_BOUNCE_FACTOR

                    elif right_collision:

                        offset_x = window_right - min_x

                        for point in ragpoints.values():
                            point.x += offset_x

                        for point in ragpoints.values():
                            vx = point.x - point.old_x
                            point.old_x = point.x + vx * RAGDOLL_BOUNCE_FACTOR

                    if top_collision:

                        offset_y = window.top - max_y

                        for point in ragpoints.values():
                            point.y += offset_y

                        for point in ragpoints.values():
                            vy = point.y - point.old_y
                            point.old_y = point.y + vy * RAGDOLL_BOUNCE_FACTOR

                        self.resolve_flying_landing(stickman)

                    elif bottom_collision:

                        offset_y = window_bottom - min_y

                        for point in ragpoints.values():
                            point.y += offset_y

                        for point in ragpoints.values():
                            vy = point.y - point.old_y
                            point.old_y = point.y + vy * RAGDOLL_BOUNCE_FACTOR

    def apply_ragdoll(self, stickman):
        if not (stickman.holding or stickman.flying):
            return

        for ragpoint in stickman.ragpoints:

            if ragpoint == stickman.grab_part:
                continue

            stickman.ragpoints[ragpoint].update()

        for _ in range(20):

            solve_body(
                stickman.ragpoints,
                stickman.head_radius,
                stickman.grab_part
            )

        self.resolve_flying_edge_collision(stickman)
        self.resolve_flying_window_collision(stickman)
        self.resolve_flying_landing(stickman)

        if stickman.flying:

            head_margin = stickman.head_radius * 2
            joint_margin = STROKE + 1 // 2

            min_x = min(
                point.x - (head_margin if name == "head" else joint_margin)
                for name, point in stickman.ragpoints.items()
            )

            min_y = min(
                point.y - (head_margin if name == "head" else joint_margin)
                for name, point in stickman.ragpoints.items()
            )

            max_x = max(
                point.x + (head_margin if name == "head" else joint_margin)
                for name, point in stickman.ragpoints.items()
            )

            max_y = max(
                point.y + (head_margin if name == "head" else joint_margin)
                for name, point in stickman.ragpoints.items()
            )

            stickman.x = int(min_x)
            stickman.y = int(min_y)
            stickman.width = int(max_x - min_x)
            stickman.height = int(max_y - min_y)

        else:

            stickman.width = STICKMAN_WIDTH
            stickman.height = STICKMAN_HEIGHT

            hip_x = stickman.ragpoints['hip'].x
            stickman.x = int(hip_x - stickman.width / 2)
            ground_y = stickman.ground_y if stickman.ground_y is not None else self.screen_y + self.screen_height
            stickman.y = int(ground_y - stickman.height)