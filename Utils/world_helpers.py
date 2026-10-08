from PyQt6.QtWidgets import QApplication

def get_screen_geometry():
    screen = QApplication.primaryScreen().geometry()
    return screen.x(), screen.y(), screen.width(), screen.height()

