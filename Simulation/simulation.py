from PyQt5.QtCore import QTimer, Qt
from Utils.constants import FRAME_DURATION_MS

class Simulation:

    def __init__(self, manager):

        self.manager = manager

        self.timer = QTimer()
        # PreciseTimer: avoids the default timer's rounding (~15 ms on Windows)
        self.timer.setTimerType(Qt.PreciseTimer)
        # This is the project's main timer; all physics and AI updates run on it
        self.timer.timeout.connect(self.update)

    def update(self):
        self.manager.update_stickman()

    def start(self):
        self.timer.start(FRAME_DURATION_MS)