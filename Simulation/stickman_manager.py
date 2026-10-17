import subprocess
import logging
import sys
from PyQt5.QtWidgets import QApplication
from Simulation.stickman import Stickman
from Simulation.stickman_overlay import StickmanOverlay
from Simulation.stickman_physics import StickmanPhysics
from Brain.stickman_needs import StickmanNeeds
from Brain.stickman_brain import StickmanBrain
from Animation.stickman_animator import StickmanAnimator
from Simulation.stickman_ragdoll import StickmanRagdoll
from Utils.helpers import get_ghost_process_command


class StickmanManager:
    # Manages the stickmen and stores their list.

    def __init__(self):

        self.stickmans_overlays = []

        self.stickman_needs = StickmanNeeds()
        self.stickman_brain = StickmanBrain()
        self.stickman_animator = StickmanAnimator()
        self.stickman_physics = StickmanPhysics()
        self.stickman_ragdoll = StickmanRagdoll()

    def create_stickman(self, name, color, hollow_head):

        name = "".join(character for character in str(name) if character.isprintable()).strip()
        name = name or "Untitled"

        existing_names = {overlay.stickman.name.casefold() for overlay in self.stickmans_overlays}
        base_name = name
        suffix = 2
        while name.casefold() in existing_names:
            name = f"{base_name} ({suffix})"
            suffix += 1

        stickman = Stickman(name, color, hollow_head)

        overlay = StickmanOverlay(stickman)
        if sys.platform.startswith("linux") and QApplication.platformName() == "xcb":
            overlay.apply_x11_hints()

        process = None
        try:
            command, env = get_ghost_process_command(name)
            process = subprocess.Popen(command, env=env)
            stickman.ghost_process = process
            self.stickmans_overlays.append(overlay)
            overlay.show()
        except BaseException:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise

    def delete_stickman(self, stickman):

        for overlay in self.stickmans_overlays.copy():
            if overlay.stickman == stickman:
                overlay.close()
                overlay.deleteLater()
                self.stickmans_overlays.remove(overlay)

    def update_stickman(self):
        self.update_ghost_process()
        self.stickman_physics.refresh_windows()

        for overlay in self.stickmans_overlays:
            stickman = overlay.stickman
            try:
                self.update_brain(stickman)
                self.update_physics(stickman)
                self.update_animation(stickman)
                self.update_overlay(overlay)
            except Exception:
                logging.exception("Failed to update stickman %r", stickman.name)

    def update_ghost_process(self):
        for overlay in self.stickmans_overlays.copy():
            if overlay.stickman.ghost_process.poll() is not None:
                self.delete_stickman(overlay.stickman)

    def update_physics(self, stickman):
        self.stickman_physics.update(stickman)
        self.stickman_ragdoll.update(
            stickman,
            self.stickman_physics.windows,
            self.stickman_physics.visible_intervals
        )

    def update_brain(self, stickman):
        self.stickman_needs.update(stickman)
        self.stickman_brain.update(stickman)

    def update_animation(self, stickman):
        self.stickman_animator.update(stickman)

    def update_overlay(self, overlay):
        overlay.update_position()