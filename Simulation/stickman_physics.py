
from Utils.constants import GRAVITY_ACCELERATION, DELTA_TIME, DEFAULT_WALK_SPEED, STROKE, RAGDOLL_BOUNCE_FACTOR, RAGPOINT_RADIUS
from Utils.helpers import get_screen_geometry, get_windows, rectangle_overlap
from Body.body_physics import solve_body


class StickmanPhysics:

    def __init__(self):
        self.screen_x, self.screen_y, self.screen_width, self.screen_height = get_screen_geometry()

    def update(self, stickman):
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

    def resolve_flying_ground_contact(self, stickman):
        if not stickman.flying:
            return

        max_y = max(point.y for point in stickman.ragpoints.values())

        ground_y = self.screen_y + self.screen_height

        if max_y >= ground_y:
            stickman.flying = False

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

        ragpoints = stickman.ragpoints

        for window in get_windows():

            for ragpoint in ragpoints:

                radius = stickman.head_radius if ragpoint == 'head' else RAGPOINT_RADIUS

                overlap = rectangle_overlap(
                    window.left, window.top, window.width, window.height,
                    ragpoints[ragpoint].x - RAGPOINT_RADIUS, ragpoints[ragpoint].y - RAGPOINT_RADIUS, RAGPOINT_RADIUS * 2, RAGPOINT_RADIUS * 2
                )

                if overlap:
                    print('Hit')

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

        self.resolve_flying_ground_contact(stickman)