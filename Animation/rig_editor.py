"""
Rig Editor — ferramenta separada do Polytes.

Reaproveita a MESMA lógica de desenho de draw_stickman.py (mesmas constantes,
mesma técnica de QPainterPath.quadTo pras juntas), mas em vez de calcular os
ângulos por fórmula fixa, deixa você arrastar cada junta e guarda o resultado
como um "frame" de animação.

Hierarquia (FK de verdade — cada osso filho gira JUNTO com o pai):
    hip (âncora fixa)
      -> torso_angle          -> neck
           -> upper_arm_angle -> elbow
                -> forearm_angle (RELATIVO ao upper_arm) -> hand
      -> upper_leg_angle -> knee
           -> lower_leg_angle (RELATIVO ao upper_leg) -> foot

Uso:
    python3 rig_editor.py

Controles:
    - Arraste o "neck" (ponto roxo) pra girar o torso inteiro em torno do hip
    - Arraste os pontos azuis (cotovelo/mão) e verdes (joelho/pé)
    - "Novo frame"    -> duplica o frame atual e vira frame novo
    - "Excluir"       -> remove o frame atual
    - "< / >"         -> navega entre frames manualmente
    - "Play/Pause"    -> roda os frames em loop pra pré-visualizar a animação
    - "Exportar JSON" -> salva os frames num arquivo .json
    - "Importar JSON" -> carrega frames de um arquivo .json

O JSON exportado é uma lista de frames, cada um com:
    torso_angle,
    upper_arm_angle_r, forearm_angle_r (relativo), upper_arm_angle_l, forearm_angle_l (relativo),
    upper_leg_angle_r, lower_leg_angle_r (relativo), upper_leg_angle_l, lower_leg_angle_l (relativo)
"""

import sys
import json
import math

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel,
    QSlider, QFileDialog
)
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QColor, QFont
from PyQt5.QtCore import Qt, QPointF, QTimer

# ---------------------------------------------------------------------------
# Mesmas constantes de draw_stickman.py (copiadas, não importadas, pra essa
# ferramenta não depender do projeto Polytes rodando)
# ---------------------------------------------------------------------------

STROKE = 9
HEAD_DIAMETER = 38
TORSO_LENGTH = 37

UPPER_ARM_LENGHT = 24
FOREARM_LENGHT = 23

UPPER_LEG_LENGHT = 28
LOWER_LEG_LENGHT = 27

# Valor padrão; agora ajustável ao vivo pelo slider no editor
JOINT_ROUNDNESS = 0.35

CANVAS_WIDTH = 320
CANVAS_HEIGHT = 340

GROUND_Y = 300
HIP_ANCHOR = (160, 150)  # ponto fixo da tela; tudo o resto gira em torno dele

HANDLE_RADIUS = 5
NECK_HANDLE_RADIUS = 6

BODY_COLOR = QColor("#2c2c2a")
GHOST_COLOR = QColor(180, 178, 170, 140)
ARM_HANDLE_COLOR = QColor("#378ADD")
LEG_HANDLE_COLOR = QColor("#639922")
NECK_HANDLE_COLOR = QColor("#7F77DD")
BG_COLOR = QColor("#f6f5f0")
GROUND_COLOR = QColor("#c9c7bd")


def polar_point(origin, length, angle_degrees):
    angle_rad = math.radians(angle_degrees)
    x = origin[0] + length * math.cos(angle_rad)
    y = origin[1] + length * math.sin(angle_rad)
    return (x, y)


def angle_between(origin, point):
    return math.degrees(math.atan2(point[1] - origin[1], point[0] - origin[0]))


def default_frame():
    return {
        "torso_angle": -90,
        "hip_offset_y": 0,
        "upper_arm_angle_r": 45, "forearm_angle_r": -90,
        "upper_arm_angle_l": 135, "forearm_angle_l": 90,
        "upper_leg_angle_r": 30, "lower_leg_angle_r": 45,
        "upper_leg_angle_l": 150, "lower_leg_angle_l": -45,
    }


# ---------------------------------------------------------------------------
# Mesma lógica de desenho de draw_stickman.py (draw_head/draw_torso/draw_arm/
# draw_leg), só recebendo as juntas já calculadas
# ---------------------------------------------------------------------------

def draw_head(painter, head_top_left):
    painter.drawEllipse(int(head_top_left[0]), int(head_top_left[1]), HEAD_DIAMETER, HEAD_DIAMETER)


def draw_torso(painter, neck, hip):
    painter.drawLine(int(neck[0]), int(neck[1]), int(hip[0]), int(hip[1]))


def lerp_point(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw_bent_limb(painter, start, joint, end, roundness):
    # roundness=1 -> curva do início ao fim (igual antes)
    # roundness=0 -> duas retas com canto quase reto na junta
    approach_from_start = lerp_point(joint, start, roundness)
    approach_to_end = lerp_point(joint, end, roundness)

    path = QPainterPath()
    path.moveTo(start[0], start[1])
    path.lineTo(approach_from_start[0], approach_from_start[1])
    path.quadTo(joint[0], joint[1], approach_to_end[0], approach_to_end[1])
    path.lineTo(end[0], end[1])
    painter.drawPath(path)


def draw_arm(painter, neck, elbow, hand):
    draw_bent_limb(painter, neck, elbow, hand, JOINT_ROUNDNESS)


def draw_leg(painter, hip, knee, foot):
    draw_bent_limb(painter, hip, knee, foot, JOINT_ROUNDNESS)


def hip_of_frame(frame):
    return (HIP_ANCHOR[0], HIP_ANCHOR[1] + frame.get("hip_offset_y", 0))


def compute_joints(frame):
    """Calcula todas as juntas a partir do frame, respeitando a hierarquia:
    cada osso filho herda a rotação do pai (ângulos relativos somados)."""

    hip = hip_of_frame(frame)
    neck = polar_point(hip, TORSO_LENGTH, frame["torso_angle"])

    elbow_r = polar_point(neck, UPPER_ARM_LENGHT, frame["upper_arm_angle_r"])
    hand_r = polar_point(elbow_r, FOREARM_LENGHT, frame["upper_arm_angle_r"] + frame["forearm_angle_r"])

    elbow_l = polar_point(neck, UPPER_ARM_LENGHT, frame["upper_arm_angle_l"])
    hand_l = polar_point(elbow_l, FOREARM_LENGHT, frame["upper_arm_angle_l"] + frame["forearm_angle_l"])

    knee_r = polar_point(hip, UPPER_LEG_LENGHT, frame["upper_leg_angle_r"])
    foot_r = polar_point(knee_r, LOWER_LEG_LENGHT, frame["upper_leg_angle_r"] + frame["lower_leg_angle_r"])

    knee_l = polar_point(hip, UPPER_LEG_LENGHT, frame["upper_leg_angle_l"])
    foot_l = polar_point(knee_l, LOWER_LEG_LENGHT, frame["upper_leg_angle_l"] + frame["lower_leg_angle_l"])

    return {
        "hip": hip, "neck": neck,
        "elbow_r": elbow_r, "hand_r": hand_r,
        "elbow_l": elbow_l, "hand_l": hand_l,
        "knee_r": knee_r, "foot_r": foot_r,
        "knee_l": knee_l, "foot_l": foot_l,
    }


class RigCanvas(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setFixedSize(CANVAS_WIDTH, CANVAS_HEIGHT)
        self.setMouseTracking(True)
        self.dragging_key = None
        self.dragging_angle = None

        # cada handle sabe: junta_pai, junta_propria (pra origem do drag)
        # e como escrever de volta no frame
        self.handle_specs = {
            "neck": ("hip", "neck", self.set_torso_angle),
            "elbow_r": ("neck", "elbow_r", lambda f, ang: f.__setitem__("upper_arm_angle_r", ang)),
            "hand_r": ("elbow_r", "hand_r", self.set_forearm_r),
            "elbow_l": ("neck", "elbow_l", lambda f, ang: f.__setitem__("upper_arm_angle_l", ang)),
            "hand_l": ("elbow_l", "hand_l", self.set_forearm_l),
            "knee_r": ("hip", "knee_r", lambda f, ang: f.__setitem__("upper_leg_angle_r", ang)),
            "foot_r": ("knee_r", "foot_r", self.set_lower_leg_r),
            "knee_l": ("hip", "knee_l", lambda f, ang: f.__setitem__("upper_leg_angle_l", ang)),
            "foot_l": ("knee_l", "foot_l", self.set_lower_leg_l),
        }

    def set_torso_angle(self, f, ang):
        f["torso_angle"] = ang

    def set_forearm_r(self, f, ang):
        f["forearm_angle_r"] = ang - f["upper_arm_angle_r"]

    def set_forearm_l(self, f, ang):
        f["forearm_angle_l"] = ang - f["upper_arm_angle_l"]

    def set_lower_leg_r(self, f, ang):
        f["lower_leg_angle_r"] = ang - f["upper_leg_angle_r"]

    def set_lower_leg_l(self, f, ang):
        f["lower_leg_angle_l"] = ang - f["upper_leg_angle_l"]

    def current_frame(self):
        return self.editor.frames[self.editor.current_index]

    def draw_body(self, painter, frame, color):
        pen = QPen(color)
        pen.setWidth(STROKE)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        joints = compute_joints(frame)
        neck = joints["neck"]
        head_center = polar_point(neck, HEAD_DIAMETER / 2, frame["torso_angle"])
        head_top_left = (head_center[0] - HEAD_DIAMETER / 2, head_center[1] - HEAD_DIAMETER / 2)

        draw_head(painter, head_top_left)
        draw_torso(painter, neck, joints["hip"])
        draw_arm(painter, neck, joints["elbow_r"], joints["hand_r"])
        draw_arm(painter, neck, joints["elbow_l"], joints["hand_l"])
        draw_leg(painter, joints["hip"], joints["knee_r"], joints["foot_r"])
        draw_leg(painter, joints["hip"], joints["knee_l"], joints["foot_l"])
        return joints

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), BG_COLOR)

            ground_pen = QPen(GROUND_COLOR)
            ground_pen.setWidth(2)
            painter.setPen(ground_pen)
            painter.drawLine(0, GROUND_Y, CANVAS_WIDTH, GROUND_Y)

            # Onion skin: frame anterior em cinza translúcido, só no modo edição
            if not self.editor.playing and self.editor.current_index > 0:
                ghost_frame = self.editor.frames[self.editor.current_index - 1]
                self.draw_body(painter, ghost_frame, GHOST_COLOR)

            frame = self.editor.playback_frame() if self.editor.playing else self.current_frame()
            joints = self.draw_body(painter, frame, BODY_COLOR)

            if not self.editor.playing:
                for key, point in joints.items():
                    if key == "hip":
                        continue
                    if key == "neck":
                        handle_pen = QPen(NECK_HANDLE_COLOR)
                        handle_pen.setWidth(2)
                        painter.setPen(handle_pen)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawEllipse(QPointF(*point), NECK_HANDLE_RADIUS, NECK_HANDLE_RADIUS)
                        continue
                    color = ARM_HANDLE_COLOR if "elbow" in key or "hand" in key else LEG_HANDLE_COLOR
                    handle_pen = QPen(color)
                    handle_pen.setWidth(2)
                    painter.setPen(handle_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(QPointF(*point), HANDLE_RADIUS, HANDLE_RADIUS)

            if self.dragging_key is not None and self.dragging_angle is not None:
                label_pos = joints[self.dragging_key]
                painter.setPen(QPen(BODY_COLOR))
                painter.setFont(QFont("Sans", 9))
                painter.drawText(int(label_pos[0]) + 10, int(label_pos[1]) - 10, f"{self.dragging_angle}°")
        finally:
            painter.end()

    def handle_at(self, pos):
        joints = compute_joints(self.current_frame())
        for key in self.handle_specs:
            point = joints[key]
            radius = NECK_HANDLE_RADIUS if key == "neck" else HANDLE_RADIUS
            dx = pos.x() - point[0]
            dy = pos.y() - point[1]
            if dx * dx + dy * dy <= (radius * 2.5) ** 2:
                return key
        return None

    def mousePressEvent(self, event):
        if self.editor.playing:
            return
        self.dragging_key = self.handle_at(event.pos())

    def mouseMoveEvent(self, event):
        if self.dragging_key is None:
            return
        frame = self.current_frame()
        parent_key, _, setter = self.handle_specs[self.dragging_key]
        joints = compute_joints(frame)
        origin = joints[parent_key]
        mouse = (event.pos().x(), event.pos().y())
        absolute_angle = angle_between(origin, mouse)
        setter(frame, round(absolute_angle))
        self.dragging_angle = round(absolute_angle)
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_key = None
        self.dragging_angle = None
        self.update()


class RigEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rig Editor — Polytes")
        self.setStyleSheet("background-color: #eceae3;")

        self.frames = [default_frame()]
        self.current_index = 0
        self.playing = False
        self.playback_index = 0

        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.advance_playback)

        self.canvas = RigCanvas(self)

        self.frame_label = QLabel()
        self.frame_label.setFont(QFont("Sans", 10))
        self.update_frame_label()

        prev_button = QPushButton("<")
        next_button = QPushButton(">")
        new_button = QPushButton("Novo frame")
        delete_button = QPushButton("Excluir")
        self.play_button = QPushButton("Play")
        mirror_button = QPushButton("Espelhar D -> E")
        export_button = QPushButton("Exportar JSON")
        import_button = QPushButton("Importar JSON")

        speed_label = QLabel("Velocidade")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(60)
        self.speed_slider.setMaximum(500)
        self.speed_slider.setValue(150)

        self.roundness_label = QLabel(f"Arredondamento da junta: {JOINT_ROUNDNESS:.2f}")
        self.roundness_slider = QSlider(Qt.Horizontal)
        self.roundness_slider.setMinimum(0)
        self.roundness_slider.setMaximum(100)
        self.roundness_slider.setValue(int(JOINT_ROUNDNESS * 100))
        self.roundness_slider.valueChanged.connect(self.set_roundness)

        prev_button.clicked.connect(self.prev_frame)
        next_button.clicked.connect(self.next_frame)
        new_button.clicked.connect(self.new_frame)
        delete_button.clicked.connect(self.delete_frame)
        self.play_button.clicked.connect(self.toggle_play)
        mirror_button.clicked.connect(self.mirror_right_to_left)
        export_button.clicked.connect(self.export_json)
        import_button.clicked.connect(self.import_json)

        for button in (prev_button, next_button, new_button, delete_button,
                       self.play_button, mirror_button, export_button, import_button):
            button.setStyleSheet(
                "QPushButton { background: white; border: 1px solid #b4b2a9; border-radius: 6px; padding: 6px 10px; }"
                "QPushButton:hover { background: #f1efe8; }"
            )

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(prev_button)
        nav_layout.addWidget(self.frame_label)
        nav_layout.addWidget(next_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(new_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(mirror_button)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)

        roundness_layout = QVBoxLayout()
        roundness_layout.addWidget(self.roundness_label)
        roundness_layout.addWidget(self.roundness_slider)

        file_layout = QHBoxLayout()
        file_layout.addWidget(export_button)
        file_layout.addWidget(import_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.canvas)
        main_layout.addLayout(nav_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.play_button)
        main_layout.addLayout(speed_layout)
        main_layout.addLayout(roundness_layout)
        main_layout.addLayout(file_layout)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        self.setLayout(main_layout)

    def update_frame_label(self):
        self.frame_label.setText(f"Frame {self.current_index + 1} / {len(self.frames)}")
        self.frame_label.setAlignment(Qt.AlignCenter)

    def prev_frame(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.refresh()

    def next_frame(self):
        if self.current_index < len(self.frames) - 1:
            self.current_index += 1
            self.refresh()

    def new_frame(self):
        copy = dict(self.frames[self.current_index])
        self.frames.insert(self.current_index + 1, copy)
        self.current_index += 1
        self.refresh()

    def delete_frame(self):
        if len(self.frames) == 1:
            return
        del self.frames[self.current_index]
        self.current_index = max(0, self.current_index - 1)
        self.refresh()

    def toggle_play(self):
        if len(self.frames) < 2:
            return
        self.playing = not self.playing
        if self.playing:
            self.playback_index = self.current_index
            self.play_button.setText("Pause")
            self.playback_timer.start(self.speed_slider.value())
        else:
            self.play_button.setText("Play")
            self.playback_timer.stop()
        self.canvas.update()

    def advance_playback(self):
        self.playback_index = (self.playback_index + 1) % len(self.frames)
        self.playback_timer.setInterval(self.speed_slider.value())
        self.canvas.update()

    def playback_frame(self):
        return self.frames[self.playback_index]

    def set_roundness(self, slider_value):
        global JOINT_ROUNDNESS
        JOINT_ROUNDNESS = slider_value / 100
        self.roundness_label.setText(f"Arredondamento da junta: {JOINT_ROUNDNESS:.2f}")
        self.canvas.update()

    def mirror_right_to_left(self):
        frame = self.frames[self.current_index]
        frame["upper_arm_angle_l"] = 180 - frame["upper_arm_angle_r"]
        frame["forearm_angle_l"] = -frame["forearm_angle_r"]
        frame["upper_leg_angle_l"] = 180 - frame["upper_leg_angle_r"]
        frame["lower_leg_angle_l"] = -frame["lower_leg_angle_r"]
        self.refresh()

    def refresh(self):
        self.update_frame_label()
        self.canvas.update()

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar frames", "animation_frames.json", "JSON (*.json)")
        if not path:
            return
        with open(path, "w") as file:
            json.dump(self.frames, file, indent=2)
        print(f"Salvo em {path}")

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar frames", "", "JSON (*.json)")
        if not path:
            return
        with open(path, "r") as file:
            loaded = json.load(file)
        if not loaded:
            return
        self.frames = loaded
        self.current_index = 0
        self.refresh()
        print(f"Carregado de {path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = RigEditor()
    editor.show()
    sys.exit(app.exec_())