import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontInfo
from Simulation.simulation import Simulation
from CreatorWindow.creator_window import CreatorWindow
from Simulation.stickman_manager import StickmanManager
from Utils.helpers import load_fonts
from Utils.helpers import cleanup_old_ghost_dirs



if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_fonts()
    app.setFont(QFont("Selawik", 11))
    cleanup_old_ghost_dirs()
    manager = StickmanManager()
    simulation = Simulation(manager)
    simulation.start()
    creator_window = CreatorWindow(manager)
    creator_window.show()
    sys.exit(app.exec_())