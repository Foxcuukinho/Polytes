from PyQt5.QtWidgets import QDialog, QWidget, QLineEdit, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QRect


DARK_BG = "#242426"
CARD_BG = "#3A3A3C"
TEXT_COLOR = "#F2F2F2"
MUTED_TEXT = "#B8B8BA"
BORDER_COLOR = "#45454A"


class HueSlider(QWidget):
    hueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(22)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._hue = 0

    def setHue(self, hue):
        self._hue = hue
        self.update()

    def hue(self):
        return self._hue

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(DARK_BG))

        track_rect = QRect(7, 0, 10, self.height())

        gradient = QLinearGradient(0, 0, 0, self.height())
        for i in range(7):
            stop = i / 6
            color = QColor.fromHsv(int(stop * 359), 255, 255)
            gradient.setColorAt(stop, color)

        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(track_rect, 5, 5)

        marker_y = int((self._hue / 359) * self.height())

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(MUTED_TEXT))
        painter.drawEllipse(-6, marker_y - 8, 16, 16)

    def mousePressEvent(self, event):
        self._update_from_mouse(event.y())

    def mouseMoveEvent(self, event):
        self._update_from_mouse(event.y())

    def _update_from_mouse(self, y):
        y = max(0, min(y, self.height()))
        hue = int((y / self.height()) * 359)
        self._hue = hue
        self.update()
        self.hueChanged.emit(hue)


class SaturationValueSquare(QWidget):
    valueChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._hue = 0
        self._sat = 255
        self._val = 255

    def setHue(self, hue):
        self._hue = hue
        self.update()

    def setSatVal(self, sat, val):
        self._sat = sat
        self._val = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRect(0, 0, self.width(), self.height())

        # Camada base (vertical, independe de x): hue puro no topo, branco embaixo.
        # É o eixo de saturação: topo = saturação máxima, embaixo = zero (branco).
        saturation_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        saturation_gradient.setColorAt(0, QColor.fromHsv(self._hue, 255, 255))
        saturation_gradient.setColorAt(1, QColor(255, 255, 255))
        painter.fillRect(rect, saturation_gradient)

        # Camada multiplicativa (horizontal): preto (esquerda) até branco (direita).
        # Multiply por preto zera qualquer cor (garante coluna esquerda inteira preta,
        # não só o canto) — multiply por branco não altera nada (mantém a direita intacta).
        value_gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        value_gradient.setColorAt(0, QColor(0, 0, 0))
        value_gradient.setColorAt(1, QColor(255, 255, 255))

        painter.setCompositionMode(QPainter.CompositionMode_Multiply)
        painter.fillRect(rect, value_gradient)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        marker_x = int((self._val / 255) * self.width())
        marker_y = int((1 - self._sat / 255) * self.height())

        # Crosshair, igual ao Zorin: linha horizontal + vertical cruzando o marcador
        pen = QPen(QColor(255, 255, 255, 160), 1)
        painter.setPen(pen)
        painter.drawLine(0, marker_y, self.width(), marker_y)
        painter.drawLine(marker_x, 0, marker_x, self.height())

        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(marker_x - 5, marker_y - 5, 10, 10)

    def mousePressEvent(self, event):
        self._update_from_mouse(event.x(), event.y())

    def mouseMoveEvent(self, event):
        self._update_from_mouse(event.x(), event.y())

    def _update_from_mouse(self, x, y):
        x = max(0, min(x, self.width()))
        y = max(0, min(y, self.height()))

        val = int((x / self.width()) * 255)
        sat = int((1 - y / self.height()) * 255)

        self._sat = sat
        self._val = val
        self.update()
        self.valueChanged.emit(sat, val)


class ColorPreviewSwatch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._color = QColor("#FFFFFF")

    def setColor(self, color):
        self._color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)


class RoundedCard(QWidget):
    # Desenha o fundo arredondado no próprio paintEvent, em vez de confiar
    # só em QSS (border-radius via QSS com WA_TranslucentBackground falha
    # no Windows, deixando os cantos brancos/não compositados).
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(DARK_BG))
        painter.drawRoundedRect(self.rect(), 24, 24)


class ColorPickerDialog(QDialog):
    colorSelected = pyqtSignal(QColor)

    def __init__(self, initial_color=QColor("#8ABBD8"), parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._current_color = initial_color

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)

        card = RoundedCard()
        card.setObjectName("card")
        outer_layout.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(18)

        # Barra de topo: Cancelar / título / Selecionar
        top_bar = QHBoxLayout()

        self.cancel_button = QPushButton("Cancelar")
        self.title_label = QLabel("Select Color")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.select_button = QPushButton("Select")

        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {CARD_BG};
                color: {MUTED_TEXT};
                border-radius: 10px;
                border: none;
                padding: 8px 14px;
                font-family: 'Comic Relief', Arial, sans-serif;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #45454A;
            }}
        """)

        self.select_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {TEXT_COLOR};
                color: #1A1A1C;
                border-radius: 10px;
                border: none;
                padding: 8px 14px;
                font-family: 'Comic Relief', Arial, sans-serif;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #E0E0E0;
            }}
        """)

        self.title_label.setStyleSheet(f"color: {MUTED_TEXT}; font-family: 'Comic Relief', Arial, sans-serif; font-size: 13px; font-weight: 500;")

        top_bar.addWidget(self.cancel_button)
        top_bar.addWidget(self.title_label, 1)
        top_bar.addWidget(self.select_button)

        card_layout.addLayout(top_bar)

        # Linha: preview + hex
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        self.preview_swatch = ColorPreviewSwatch()
        self.hex_input = QLineEdit()
        self.hex_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {CARD_BG};
                color: {MUTED_TEXT};
                border-radius: 10px;
                border: none;
                padding: 10px 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }}
        """)

        info_row.addWidget(self.preview_swatch)
        info_row.addWidget(self.hex_input, 1)

        card_layout.addLayout(info_row)

        # Linha: hue slider + quadrado sat/brilho
        picker_row = QHBoxLayout()
        picker_row.setSpacing(14)

        self.hue_slider = HueSlider()
        self.sv_square = SaturationValueSquare()

        picker_row.addWidget(self.hue_slider)
        picker_row.addWidget(self.sv_square, 1)

        card_layout.addLayout(picker_row)

        self.hue_slider.hueChanged.connect(self._on_hue_changed)
        self.sv_square.valueChanged.connect(self._on_sv_changed)
        self.hex_input.editingFinished.connect(self._on_hex_edited)

        self.cancel_button.clicked.connect(self.reject)
        self.select_button.clicked.connect(self._on_select)

        self.set_color(initial_color)

        outer_layout.setSizeConstraint(QLayout.SetFixedSize)

    def set_color(self, color):
        hue, sat, val, _ = color.getHsv()
        hue = max(hue, 0)

        self.hue_slider.setHue(hue)
        self.sv_square.setHue(hue)
        self.sv_square.setSatVal(sat, val)
        self.hex_input.setText(color.name())
        self.preview_swatch.setColor(color)

        self._current_color = color

    def current_color(self):
        return self._current_color

    def _on_hue_changed(self, hue):
        self.sv_square.setHue(hue)
        self._emit_from_hsv(hue, self.sv_square._sat, self.sv_square._val)

    def _on_sv_changed(self, sat, val):
        self._emit_from_hsv(self.hue_slider.hue(), sat, val)

    def _on_hex_edited(self):
        color = QColor(self.hex_input.text())
        if color.isValid():
            self.set_color(color)

    def _emit_from_hsv(self, hue, sat, val):
        color = QColor.fromHsv(hue, sat, val)
        self._current_color = color
        self.hex_input.setText(color.name())
        self.preview_swatch.setColor(color)

    def _on_select(self):
        self.colorSelected.emit(self._current_color)
        self.accept()