from Utils.utils import (
    TORSO_LENGTH,
    UPPER_ARM_LENGTH,
    FOREARM_LENGTH,
    UPPER_LEG_LENGTH,
    LOWER_LEG_LENGTH,
)


RIG = [
    {
        "name": "hip",
        "parent": None,
    },
    {
        "name": "neck",
        "parent": "hip",
        "length": TORSO_LENGTH,
        "angle": "torso_angle",
        "relative": False,
    },
    {
        "name": 'head',
        "parent": "neck",
        "length": None,
        "angle": "torso_angle",
        "relative": False,
    },
    {
        "name": "right_elbow",
        "parent": "neck",
        "length": UPPER_ARM_LENGTH,
        "angle": "upper_arm_angle_r",
        "relative": False,
    },
    {
        "name": "right_hand",
        "parent": "right_elbow",
        "length": FOREARM_LENGTH,
        "angle": "forearm_angle_r",
        "relative": True,
    },
    {
        "name": "left_elbow",
        "parent": "neck",
        "length": UPPER_ARM_LENGTH,
        "angle": "upper_arm_angle_l",
        "relative": False,
    },
    {
        "name": "left_hand",
        "parent": "left_elbow",
        "length": FOREARM_LENGTH,
        "angle": "forearm_angle_l",
        "relative": True,
    },
    {
        "name": "right_knee",
        "parent": "hip",
        "length": UPPER_LEG_LENGTH,
        "angle": "upper_leg_angle_r",
        "relative": False,
    },
    {
        "name": "right_foot",
        "parent": "right_knee",
        "length": LOWER_LEG_LENGTH,
        "angle": "lower_leg_angle_r",
        "relative": True,
    },
    {
        "name": "left_knee",
        "parent": "hip",
        "length": UPPER_LEG_LENGTH,
        "angle": "upper_leg_angle_l",
        "relative": False,
    },
    {
        "name": "left_foot",
        "parent": "left_knee",
        "length": LOWER_LEG_LENGTH,
        "angle": "lower_leg_angle_l",
        "relative": True,
    },
]