import math

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

        new_y = self.y + ( self.y - self.old_y) + 0.5
        self.old_y = self.y
        self.y = new_y

        print(self.x)
        print(self.y)


def solve_bone(origin, end, rest, grab):

    distance_x = origin.x - end.x
    distance_y = origin.y - end.y

    distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

    distance_error = distance - rest

    direction_x = distance_x / distance
    direction_y = distance_y / distance

    if not grab:

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

    else:

        adjust_x = distance_error * direction_x
        adjust_y = distance_error * direction_y

        end.old_x = end.x
        end.old_y = end.y
        end.x += adjust_x
        end.y += adjust_y

ragpoint = RagPoint(0, 0)
ragpoint2 = RagPoint(0, 50)


for i in range(5):
    ragpoint.update()
    ragpoint2.update()
    print('Antes:')
    print(ragpoint.x)
    print(ragpoint.y)
    print(ragpoint2.x)
    print(ragpoint2.y)
    solve_bone(ragpoint, ragpoint2, 30, True)
    print('Solve bone:')
    print(ragpoint.x)
    print(ragpoint.y)
    print(ragpoint2.x)
    print(ragpoint2.y)