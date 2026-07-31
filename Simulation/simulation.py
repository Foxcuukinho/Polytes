from PyQt5.QtCore import QTimer
from Utils.utils import FRAME_DURATION_MS

class Simulation:

    def __init__(self, manager):

        self.manager = manager

        self.timer = QTimer() 
        # Esse é o timer principal do projeto, toda a física e cérebro rodam nele
        self.timer.timeout.connect(self.update)


    def update(self):
        self.manager.update_stickman()

    def start(self):
        self.timer.start(FRAME_DURATION_MS)