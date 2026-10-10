from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtCore import Qt
from CreatorWindow.preview_widget import StickmanPreview
from Utils.constants import STICKMAN_WIDTH, STICKMAN_HEIGHT
from CreatorWindow.widgets import ToggleSwitch
from CreatorWindow.color_picker import ColorPickerDialog


TITLE_BAR_BG = "#2B2B2E"
TITLE_TEXT_COLOR = "#F2F2F2"
BODY_BG = "#F2F2F0"
CORNER_RADIUS = 16
TITLE_BAR_HEIGHT = 40


def build_rounded_path(rect, radius, top_left, top_right, bottom_left, bottom_right):
    # QPainterPath com cantos arredondados seletivos - permite, por exemplo,
    # uma barra de título com só o topo arredondado, e um corpo com só a
    # base arredondada, encaixando perfeitamente um sobre o outro.
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

    path = QPainterPath()
    path.moveTo(x + (radius if top_left else 0), y)
    path.lineTo(x + w - (radius if top_right else 0), y)

    if top_right:
        path.quadTo(x + w, y, x + w, y + radius)
    else:
        path.lineTo(x + w, y)

    path.lineTo(x + w, y + h - (radius if bottom_right else 0))

    if bottom_right:
        path.quadTo(x + w, y + h, x + w - radius, y + h)
    else:
        path.lineTo(x + w, y + h)

    path.lineTo(x + (radius if bottom_left else 0), y + h)

    if bottom_left:
        path.quadTo(x, y + h, x, y + h - radius)
    else:
        path.lineTo(x, y + h)

    path.lineTo(x, y + (radius if top_left else 0))

    if top_left:
        path.quadTo(x, y, x + radius, y)
    else:
        path.lineTo(x, y)

    path.closeSubpath()
    return path


class TitleBarButton(QPushButton):
    def __init__(self, icon_type, parent=None):
        super().__init__("", parent)
        self.icon_type = icon_type  # "minimize" | "maximize" | "close"
        self.setFixedSize(38, TITLE_BAR_HEIGHT)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 25);
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(TITLE_TEXT_COLOR), 1.3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        cx = self.width() / 2
        cy = self.height() / 2
        size = 5

        if self.icon_type == "minimize":
            painter.drawLine(
                int(cx - size), int(cy),
                int(cx + size), int(cy)
            )

        elif self.icon_type == "maximize":
            painter.drawRoundedRect(
                int(cx - size), int(cy - size),
                size * 2, size * 2,
                2, 2
            )

        elif self.icon_type == "close":
            painter.drawLine(
                int(cx - size), int(cy - size),
                int(cx + size), int(cy + size)
            )
            painter.drawLine(
                int(cx - size), int(cy + size),
                int(cx + size), int(cy - size)
            )


class TitleBar(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFixedHeight(TITLE_BAR_HEIGHT)

        self._drag_offset = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 6, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: {TITLE_TEXT_COLOR}; font-family: 'Comic Relief', Arial, sans-serif; "
            f"font-size: 13px; font-weight: bold; letter-spacing: 0.5px; background: transparent;"
        )

        self.minimize_button = TitleBarButton("minimize")
        self.maximize_button = TitleBarButton("maximize")
        self.close_button = TitleBarButton("close")

        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(TITLE_BAR_BG))

        path = build_rounded_path(
            self.rect(), CORNER_RADIUS,
            top_left=True, top_right=True,
            bottom_left=False, bottom_right=False
        )
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPos() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None


class BodyContainer(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(BODY_BG))

        path = build_rounded_path(
            self.rect(), CORNER_RADIUS,
            top_left=False, top_right=False,
            bottom_left=True, bottom_right=True
        )
        painter.drawPath(path)


class CreatorWindow(QWidget):
    def __init__(self, manager):
        super().__init__()

        self.manager = manager
        self.selected_color = QColor("#8ABBD8")

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(265, 440)

        self._is_maximized = False
        self._normal_geometry = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.title_bar = TitleBar("Stickman creator")
        outer_layout.addWidget(self.title_bar)

        self.body = BodyContainer()
        outer_layout.addWidget(self.body, 1)

        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.preview = StickmanPreview(self.selected_color, False)

        self.name_label = QLabel('Name:')
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Untitled")

        self.color_button = QPushButton("Color")
        self.create_stickman_button = QPushButton("Create Stickman")

        self.hollow_head_label = QLabel('Hollow Head')
        self.hollow_head_checkbox = ToggleSwitch()

        layout.addWidget(self.preview, 1)  # ocupa o espaço disponível

        name_layout = QHBoxLayout()
        name_layout.setContentsMargins(0, 12, 12, 0)
        name_layout.setSpacing(10)
        layout.addLayout(name_layout)
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)

        layout.addWidget(self.color_button)

        hollow_head_layout = QHBoxLayout()
        hollow_head_layout.setContentsMargins(0, 0, 0, 0)
        hollow_head_layout.setSpacing(10)
        layout.addLayout(hollow_head_layout)
        hollow_head_layout.addWidget(self.hollow_head_checkbox)
        hollow_head_layout.addWidget(self.hollow_head_label)

        layout.addStretch()
        layout.addWidget(self.create_stickman_button)

        self.apply_default_widget_style(self.name_input)
        self.apply_default_widget_style(self.color_button)
        self.apply_default_widget_style(self.create_stickman_button)
        self.apply_color_button_style(self.selected_color)

        self.color_button.clicked.connect(self.open_selector)
        self.create_stickman_button.clicked.connect(self.spawn_stickman)
        self.hollow_head_checkbox.toggled.connect(self.preview.set_hollow_head)

        self.title_bar.minimize_button.clicked.connect(self.showMinimized)
        self.title_bar.maximize_button.clicked.connect(self.toggle_maximize)
        self.title_bar.close_button.clicked.connect(self.close)

    def toggle_maximize(self):
        if self._is_maximized:
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            self._is_maximized = False
        else:
            self._normal_geometry = self.geometry()
            screen_geometry = self.screen().availableGeometry()
            self.setGeometry(screen_geometry)
            self._is_maximized = True

    def spawn_stickman(self):
        name = self.name_input.text()

        if name == '':
            name = 'Untitled'

        hollow_head = self.hollow_head_checkbox.isChecked()

        self.manager.create_stickman(name, self.selected_color, hollow_head)

    def open_selector(self):
        dialog = ColorPickerDialog(self.selected_color, parent=self)
        dialog.colorSelected.connect(self.on_color_selected)
        dialog.exec_()

    def on_color_selected(self, color):
        self.selected_color = color
        self.apply_color_button_style(color)
        self.preview.set_color(color)

    def apply_color_button_style(self, color):
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                color: #3A3A3A;
                border-radius: 7px;
                border: 1px solid #B0B0B0;
                padding: 6px;
                font-family: 'Segoe UI';
            }}
        """)

    def apply_default_widget_style(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #3A3A3A;
                border-radius: 7px;
                border: 1px solid #B0B0B0;
                padding: 6px;
                font-family: 'Segoe UI';
            }

            QPushButton:hover {
                background-color: #F0F0F0;
            }

            QLineEdit {
                background-color: #FFFFFF;
                color: #3A3A3A;
                border-radius: 7px;
                border: 1px solid #B0B0B0;
                padding: 6px;
                font-family: 'Segoe UI';
            }

            QLineEdit:focus {
                border: 1px solid #4A90D9;
            }
        """)