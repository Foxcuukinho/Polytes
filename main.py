
import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QIcon

from Simulation.simulation import Simulation
from CreatorWindow.creator_window import CreatorWindow
from Simulation.stickman_manager import StickmanManager
from Utils.helpers import load_fonts, cleanup_old_ghost_dirs


if __name__ == "__main__":
    app = QApplication(sys.argv)

    icon_path = os.path.join(
        getattr(
            sys,
            "_MEIPASS",
            os.path.dirname(os.path.abspath(__file__))
        ),
        "Assets",
        "polytes.png"
    )

    icon = QIcon(icon_path)
    print("Icon path:", icon_path)
    print("Icon loaded:", not icon.isNull())

    app.setWindowIcon(icon)

    load_fonts()
    app.setFont(QFont("Selawik", 11))

    cleanup_old_ghost_dirs()

    manager = StickmanManager()
    simulation = Simulation(manager)
    simulation.start()

    creator_window = CreatorWindow(manager)
    creator_window.setWindowIcon(icon)
    creator_window.show()

    sys.exit(app.exec_())
