from Utils.constants import (
    STICKMAN_WIDTH, STICKMAN_HEIGHT,FILLED_HEAD_DIAMETER, HOLLOW_HEAD_DIAMETER,
    STICKMAN_DEFAULT_DECIDE_COOLDOWN, DEFAULT_ANIMATION_CYCLE_DURATION
)

from Utils.helpers import get_screen_geometry
from Brain.stickman_personality import generate_personality
from Animation.animations import ANIMATIONS
from Body.body_physics import calculate_joints, create_ragpoints



class Stickman:

    def __init__(self, name, color, hollow_head):

        # Main settings
        self.name = name
        self.color = color
        self.hollow_head = hollow_head

        # Window settings
        self.width = STICKMAN_WIDTH
        self.height = STICKMAN_HEIGHT
        self.ghost_process = None

        # Physics
        self.x = 0
        self.y = 0
        self.velocity_y = 0
        self.velocity_x = 0
        self.ground_y = None
        screen_x, _, screen_width, _ = get_screen_geometry()
        self.ground_limit = (screen_x, screen_width)
        self.overlap_windows = []
        self.ground_window_handle = None

        # Miscellaneous
        self.head_radius = HOLLOW_HEAD_DIAMETER //2 if self.hollow_head else FILLED_HEAD_DIAMETER // 2

        # Ragdoll
        self.holding = False
        self.flying = False
        self.grab_part = None

        # Brain
        self.state = 'IDLE'

        # TODO: In V2, move this inline value.
        self.energy, self.curiosity = generate_personality(name, hollow_head, color)

        # TODO: Consider moving this to utils.py as DEFAULT_NEEDS.
        self.stamina = 100
        self.boredom = 45

        self.target_x = None
        self.direction = 1

        self.decide_cooldown = STICKMAN_DEFAULT_DECIDE_COOLDOWN

        # Animation
        self.animation_frame_index = 0
        self.animation_timer = 0
        self.current_frame = ANIMATIONS['IDLE']['frames'][0]
        self.base_frame = ANIMATIONS['IDLE']['frames'][0]
        self.animation_cycle_duration = DEFAULT_ANIMATION_CYCLE_DURATION


        self.joints = calculate_joints(self.current_frame, self, self.head_radius)
        self.ragpoints = create_ragpoints(self.joints, self.x, self.y)

