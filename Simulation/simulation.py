from PyQt6.QtCore import QTimer
from Utils.configs import FRAME_TIME_MS

class Simulation:
    def __init__(self, manager):
        self.manager = manager

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

    def start(self):
        self.timer.start(FRAME_TIME_MS)

    def update(self):
        self.manager.update_stickmen()