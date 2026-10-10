from PyQt5.QtGui import QPainter, QPen, QPainterPath, QBrush
from PyQt5.QtCore import Qt
from Body.body_physics import calculate_joints
from Utils.constants import HOLLOW_HEAD_DIAMETER, FILLED_HEAD_DIAMETER, STROKE
from Utils.helpers import is_mirrored

def draw_head(painter, head, width, height):
    painter.drawEllipse(head[0], head[1], width, height)

def draw_torso(painter, neck, hip):
    painter.drawLine(neck[0], neck[1], hip[0], hip[1])

def draw_arm(painter, neck, control, hand):
    path = QPainterPath()
    path.moveTo(neck[0], neck[1])
    path.quadTo(control[0], control[1], hand[0], hand[1])
    painter.drawPath(path)

def draw_leg(painter, hip, control, foot):
    path = QPainterPath()
    path.moveTo(hip[0], hip[1])
    path.quadTo(control[0], control[1], foot[0], foot[1])
    painter.drawPath(path)

def calculate_control_point(origin, mid, end):
    mid_x = origin[0] + (end[0] - origin[0]) // 2
    mid_y = origin[1] + (end[1] - origin[1]) // 2
        
    mid_x = mid[0] + (mid_x - mid[0]) * 0.5
    mid_y = mid[1] + (mid_y - mid[1]) * 0.5

    return mid_x, mid_y

def draw_stickman(painter, stickman):

    head_diameter = HOLLOW_HEAD_DIAMETER if stickman.hollow_head else FILLED_HEAD_DIAMETER
    head_radius = head_diameter // 2

    frame = stickman.current_frame

    painter.setRenderHint(QPainter.Antialiasing)
    
    pen = QPen(stickman.color)
    pen.setWidth(STROKE)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)

    if is_mirrored(stickman):
        painter.translate(2 * stickman.x + stickman.width, 0)
        painter.scale(-1, 1)
    
    joints = calculate_joints(frame, stickman, head_radius)

    joints['head']['position'] = (joints['head']['position'][0] - head_radius, joints['head']['position'][1] - head_radius)

    if stickman.hollow_head:
        painter.setBrush(Qt.NoBrush)
        draw_head(painter, joints['head']['position'], head_diameter, head_diameter)
    else:
        painter.setBrush(QBrush(stickman.color))
        draw_head(painter, joints['head']['position'], head_diameter, head_diameter)

    limbs = [
        ("neck", "right_elbow", "right_hand", draw_arm),
        ("neck", "left_elbow", "left_hand", draw_arm),
        ("hip", "right_knee", "right_foot", draw_leg),
        ("hip", "left_knee", "left_foot", draw_leg),
    ]

    draw_torso(
        painter,
        joints["neck"]["position"], 
        joints["hip"]["position"]
    )

    for limb in limbs:
        mid_x, mid_y = calculate_control_point(
            joints[limb[0]]['position'],
            joints[limb[1]]['position'],
            joints[limb[2]]['position']
        )

        limb[3](
            painter,
            joints[limb[0]]['position'],
            (mid_x, mid_y),
            joints[limb[2]]['position']
        )