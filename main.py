import sys
from Simulation.stickman_manager import StickmanManager
from Simulation.simulation import Simulation
from Simulation.world import World
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor


app = QApplication([])
world = World()
manager = StickmanManager(world)
simulation = Simulation(manager)
simulation.start()
manager.create_stickman(QColor('#8ABBD8'))
sys.exit(app.exec())
