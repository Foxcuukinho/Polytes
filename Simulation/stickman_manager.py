from Simulation.stickman_overlay import StickmanOverlay
from Simulation.stickman import StickmanData
from Physics.world_physics import StickmanWorldPhysics

class StickmanManager:
    def __init__(self, world):
        self.overlays_list = []

        self.world = world
        self.stickman_world_physics = StickmanWorldPhysics(self.world)

    def create_stickman(self, color):
        stickman = StickmanData(color)
        overlay = StickmanOverlay(stickman)

        self.overlays_list.append(overlay)
        overlay.show()

    def update_stickmen(self):
        for overlay in self.overlays_list:
            stickman = overlay.stickman
            overlay.update_overlay()
            self.stickman_world_physics.update(stickman)

        
        