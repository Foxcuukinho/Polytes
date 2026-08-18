import sys
from PyQt5.QtWidgets import QApplication
from Simulation.simulation import Simulation
from CreatorWindow.creator_window import CreatorWindow
from Simulation.stickman_manager import StickmanManager


if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = StickmanManager()
    simulation = Simulation(manager)
    simulation.start()
    creator_window = CreatorWindow(manager)

    creator_window.show()
    sys.exit(app.exec_())
