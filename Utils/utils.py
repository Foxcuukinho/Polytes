import hashlib
import math

FRAME_DURATION_MS = 32
DELTA_TIME = FRAME_DURATION_MS / 1000
GRAVITY_ACCELERATION = 100
RAGDOLL_DAMPING = 0.85
RAGDOLL_STIFFNES = 0.85

STICKMAN_WIDTH = 100
STICKMAN_HEIGHT = 145

STICKMAN_DEFAULT_DECIDE_COOLDOWN = 3

STROKE = 9
HOLLOW_HEAD_DIAMETER = 38
FILLED_HEAD_DIAMETER = 30

TORSO_LENGTH = 37

HIP_HEIGHT_FROM_TOP = STROKE + HOLLOW_HEAD_DIAMETER + TORSO_LENGTH

UPPER_ARM_LENGTH = 24
FOREARM_LENGTH = 23

UPPER_LEG_LENGTH = 28
LOWER_LEG_LENGTH = 27

DEFAULT_ANIMATION_CYCLE_DURATION = 0.5
DISTANCE_PER_WALK_CYCLE = 67

DEFAULT_WALK_SPEED = 170

SCORE_MARGIN = 1

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def seed_from_name(name):
    hash = hashlib.sha256(name.encode())
    number = int(hash.hexdigest(), 16)
    return number

def polar_point(origin,length, angle_degress):
    angle_rad = math.radians(angle_degress)
    x = origin[0] + length * math.cos(angle_rad)
    y = origin[1] + length * math.sin(angle_rad)
    return (int(x), int(y))
    