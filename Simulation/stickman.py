from Draw.stickman_draw import StickmanDraw

class StickmanData:
    def __init__(self, color):

        # Default Configs
        self.color =  color
        self.draw = StickmanDraw(self)

        # Physics
        self.x = 0
        self.y = 0
        self.vy = 0

        # Drag
        self.dragging = None
        
    def update(self):
        self.draw.update()
