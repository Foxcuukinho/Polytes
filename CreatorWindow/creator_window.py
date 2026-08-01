from PyQt5.QtWidgets import QWidget, QPushButton, QColorDialog, QLineEdit, QCheckBox, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QColor
from CreatorWindow.preview_widget import StickmanPreview
from Utils.utils import STICKMAN_WIDTH, STICKMAN_HEIGHT
from CreatorWindow.widgets import ToggleSwitch

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor


class CreatorWindow(QWidget):
    def __init__(self, manager):
        super().__init__()

        self.manager = manager
        self.selected_color = QColor("#8ABBD8")

        self.setWindowTitle("Criador de stickman")
        self.setFixedSize(250, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.preview = StickmanPreview(self.selected_color, False)

        self.name_label = QLabel('Name:')
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Untitled")

        self.color_button = QPushButton("Cor")
        self.create_stickman_button = QPushButton("Criar Stickman")

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

        self.color_button.clicked.connect(self.open_selector)
        self.create_stickman_button.clicked.connect(self.spawn_stickman)
        self.hollow_head_checkbox.toggled.connect(self.preview.set_hollow_head)




    def spawn_stickman(self):
        name = self.name_input.text()

        if name == '':
            name = 'Untitled'

        hollow_head = self.hollow_head_checkbox.isChecked()

        self.manager.create_stickman(name, self.selected_color, hollow_head)

    def open_selector(self):
        self.selected_color = QColorDialog.getColor()
            
        if self.selected_color.isValid():
            self.color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.selected_color.name()};
                    color: #3A3A3A;
                    border-radius: 7px;
                    border: 1px solid #B0B0B0;
                    padding: 6px;
                    font-family: 'Segoe UI';
                }}
            """)

            self.preview.set_color(self.selected_color)

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