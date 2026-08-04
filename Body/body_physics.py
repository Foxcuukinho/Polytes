import math
from Animation.rig import RIG
from Utils.utils import HIP_HEIGHT_FROM_TOP, STROKE, polar_point, DELTA_TIME, GRAVITY_ACCELERATION


class RagPoint:

    def __init__(self, x, y):
        
        self.x = x
        self.y = y

        self.old_x = x
        self.old_y = y

    def update(self):

        new_x = self.x + ( self.x - self.old_x)
        self.old_x = self.x
        self.x = new_x

        new_y = self.y + ( self.y - self.old_y) + GRAVITY_ACCELERATION * DELTA_TIME
        self.old_y = self.y
        self.y = new_y


def calculate_joints(frame, stickman, head_radius):

    joints = {}

    if stickman.dragging:
        return ragdoll_to_joints(stickman.ragpoints, head_radius, stickman.grab_part, stickman.x, stickman.y)

    else:
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

def solve_bone(origin, end, rest, grab):

    distance_x = origin.x - end.x
    distance_y = origin.y - end.y

    distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

    if distance == 0:
        return

    distance_error = distance - rest

    direction_x = distance_x / distance
    direction_y = distance_y / distance

    if grab is None:

        adjust_x = (distance_error / 2) * direction_x
        adjust_y = (distance_error / 2) * direction_y

        origin.old_x = origin.x
        origin.old_y = origin.y
        origin.x -= adjust_x
        origin.y -= adjust_y

        end.old_x = end.x
        end.old_y = end.y
        end.x += adjust_x
        end.y += adjust_y

    elif grab == "origin":

        adjust_x = distance_error * direction_x
        adjust_y = distance_error * direction_y

        end.old_x = end.x
        end.old_y = end.y
        end.x += adjust_x
        end.y += adjust_y

    elif grab == "end":

        adjust_x = distance_error * direction_x
        adjust_y = distance_error * direction_y

        origin.old_x = origin.x
        origin.old_y = origin.y
        origin.x -= adjust_x
        origin.y -= adjust_y

def create_ragpoints(joints, stickman_x, stickman_y):

    ragpoints = {}


    for joint in joints:

        x = joints[joint]['position'][0] + stickman_x
        y = joints[joint]['position'][1] + stickman_y

        ragpoints[joint] = RagPoint(x,y)

    return ragpoints

def solve_body(ragpoints, head_radius, grab_part):

    for joint in RIG:

        if joint['name'] == 'hip':
            continue            

        origin = ragpoints[joint['parent']]
        end = ragpoints[joint['name']]
        rest = joint['length']

        if joint['name'] == 'head':
            rest = head_radius

        if grab_part == joint["parent"]:
            solve_bone(origin, end, rest, "origin")

        elif grab_part == joint["name"]:
            solve_bone(origin, end, rest, "end")

        else:
            solve_bone(origin, end, rest, None)

def ragdoll_to_joints(ragpoints, head_radius, grab_part, stickman_x, stickman_y):

    joints = {}

    for ragpoint in ragpoints:

        x = ragpoints[ragpoint].x - stickman_x
        y = ragpoints[ragpoint].y - stickman_y

        joints[ragpoint] = {}
        joints[ragpoint]['position'] = (int(x), int(y))

    return joints

def get_drag_part(stickman, mouse_x, mouse_y):

    eligible_joints = []

    for joint in stickman.joints:

        joint_x = stickman.x + stickman.joints[joint]['position'][0]
        joint_y = stickman.y + stickman.joints[joint]['position'][1]

        distance_x = joint_x- mouse_x
        distance_y = joint_y- mouse_y
        
        distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

        if distance < 15:

            eligible_joints.append((joint, distance))

    if eligible_joints == []:
        return None
    else:
        return min(eligible_joints, key=lambda t: t[1])[0]