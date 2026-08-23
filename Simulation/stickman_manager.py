from stickman import Stickman
from Simulation.stickman_overlay import StickmanOverlay
from Simulation.stickman_physics import StickmanPhysics
from Brain.stickman_needs import StickmanNeeds
from Brain.stickman_brain import StickmanBrain
from Animation.stickman_animator import StickmanAnimator

class StickmanManager:
    # É quem organiza os stickmans e contém a lista deles

    def __init__(self):

        self.stickmans_overlays = []

        self.stickman_needs = StickmanNeeds()
        self.stickman_brain = StickmanBrain()
        self.stickman_animator = StickmanAnimator()
        self.stickman_physics = StickmanPhysics()

    def create_stickman(self, name, color, hollow_head):

        stickman = Stickman(name, color, hollow_head)
        # Overlay armazena stickman em self.stickman
        overlay = StickmanOverlay(stickman)

        self.stickmans_overlays.append(overlay)
        overlay.show()

    def update_stickman(self):

        for overlay in self.stickmans_overlays:
            stickman = overlay.stickman
            self.update_brain(stickman)
            self.update_physics(stickman)
            self.update_animation(stickman)
            self.update_overlay(overlay)
            print(stickman.flying, stickman.holding)

    def update_physics(self, stickman):
        self.stickman_physics.update(stickman)

    def update_brain(self, stickman):
        self.stickman_needs.update(stickman)
        self.stickman_brain.update(stickman)

    def update_animation(self, stickman):
        self.stickman_animator.update(stickman)

    def update_overlay(self, overlay):
        overlay.update_position()
