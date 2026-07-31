from PyQt5.QtWidgets import QApplication

def get_screen_geometry():
    screen =  QApplication.primaryScreen().geometry()
    
    screen_x = screen.x()
    screen_y = screen.y()
    
    screen_width = screen.width()
    screen_height = screen.height()

    return screen_x, screen_y, screen_width, screen_height