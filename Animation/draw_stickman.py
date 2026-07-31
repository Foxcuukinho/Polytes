from PyQt5.QtGui import QPainter, QPen, QPainterPath, QBrush
from PyQt5.QtCore import Qt
from Animation.rig import RIG
from Utils.utils import polar_point, HIP_HEIGHT_FROM_TOP, STROKE,  HOLLOW_HEAD_DIAMETER, FILLED_HEAD_DIAMETER

def calculate_joints(frame, stickman, head_radius):

    joints = {}

    for joint in RIG:

        if joint['name'] == 'hip':
            hip_x = stickman.width // 2
            position = (hip_x, HIP_HEIGHT_FROM_TOP)
            joints[joint["name"]] = {
                "position": position,
                "angle": 0
            }
            continue

        if joint['name'] == 'head':
            angle = joints['neck']['angle']
            origin = joints['neck']['position']
            position = polar_point(origin, head_radius, angle)

            position = (position[0] - head_radius, position[1] - head_radius)

            joints['head'] = {
                "position": position,
                "angle": angle
            }
            continue

        parent = joint['parent']
        origin = joints[parent]['position']

        angle = frame[joint['angle']]

        if joint['relative']:
            parent_angle = joints[parent]['angle']  
            angle += parent_angle

        length = joint['length']

        position = polar_point(origin, length, angle)

        joints[joint['name']] = {
            "position": position,
            "angle": angle
        }


    joints = adjust_feet_ground(joints, stickman.height)
    
    return joints

def adjust_feet_ground(joints, stickman_height):

    lowest_foot = 'right_foot' if joints['right_foot']['position'][1] >= joints['left_foot']['position'][1] else 'left_foot'

    offset_y = stickman_height - joints[lowest_foot]['position'][1] - STROKE // 2 
    for joint in joints:
                joints[joint]['position'] = (
                    joints[joint]['position'][0],
                    joints[joint]['position'][1] + offset_y
                )

    return joints


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
    mid_x = origin[0] + (end[0] - origin[0]) / 2
    mid_y = origin[1] + (end[1] - origin[1]) / 2
        
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

    if stickman.direction == 1:
            painter.translate(stickman.width, 0)
            painter.scale(-1, 1)
    
    joints = calculate_joints(frame, stickman, head_radius)

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
        