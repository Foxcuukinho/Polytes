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
import pprint

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel,
    QSlider, QFileDialog, QCheckBox, QGroupBox, QFrame, QShortcut,
    QScrollArea, QGridLayout, QBoxLayout, QComboBox, QInputDialog, QMessageBox,
    QSizePolicy, QTabWidget, QSpinBox
)
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QColor, QFont, QKeySequence
from PyQt5.QtCore import Qt, QPointF, QTimer, QSettings

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

CANVAS_WIDTH = 366
CANVAS_HEIGHT = 463
BODY_DISPLAY_SCALE = 2.25
BODY_DRAW_OFFSET_X = 8
BODY_DRAW_OFFSET_Y = -39

GROUND_Y = 430
HIP_ANCHOR = (183, 150)  # fixed canvas anchor; the rest of the rig rotates around it

HANDLE_RADIUS = 5
NECK_HANDLE_RADIUS = 6

GHOST_COLOR = QColor(180, 178, 170, 140)
NECK_HANDLE_COLOR = QColor("#378ADD")
JOINT_HANDLE_COLOR = QColor("#ffd84d")
END_HANDLE_COLOR = QColor("#f04444")
LIGHT_BG_COLOR = QColor("#f6f5f0")
LIGHT_GROUND_COLOR = QColor("#c9c7bd")
DARK_BG_COLOR = QColor("#202326")
DARK_GROUND_COLOR = QColor("#62686d")
BODY_COLORS = {
    "head": "#2d2d2b",
    "torso": "#2d2d2b",
    "right_arm": "#e65b5b",
    "left_arm": "#378add",
    "right_leg": "#70c990",
    "left_leg": "#f4c15d",
}


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


def standing_frame():
    frame = default_frame()
    frame.update({
        "upper_arm_angle_r": 65, "forearm_angle_r": 11,
        "upper_arm_angle_l": 115, "forearm_angle_l": -11,
        "upper_leg_angle_r": 80, "lower_leg_angle_r": 0,
        "upper_leg_angle_l": 100, "lower_leg_angle_l": 0,
    })
    return frame


def interpolate_frames(start, end, progress):
    result = {}
    for key, start_value in start.items():
        end_value = end.get(key, start_value)
        if isinstance(start_value, (int, float)) and isinstance(end_value, (int, float)):
            difference = end_value - start_value
            if "angle" in key:
                difference = (difference + 180) % 360 - 180
            result[key] = start_value + difference * progress
        else:
            result[key] = start_value if progress < 0.5 else end_value
    return result


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
        self.setFixedSize(
            round(editor.canvas_width * editor.canvas_scale),
            round(editor.canvas_height * editor.canvas_scale),
        )
        self.setMouseTracking(True)
        self.dragging_key = None
        self.dragging_angle = None
        self.dragging_ground = False
        self.panning = False
        self.last_pan_pos = None
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag a joint to pose. Drag empty space to move the character.")

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
        painter.setBrush(Qt.NoBrush)

        joints = compute_joints(frame)
        neck = joints["neck"]
        head_center = polar_point(neck, HEAD_DIAMETER / 2, frame["torso_angle"])
        head_top_left = (head_center[0] - HEAD_DIAMETER / 2, head_center[1] - HEAD_DIAMETER / 2)

        def set_part_color(part):
            pen = QPen(color if color is not None else QColor(BODY_COLORS[part]))
            pen.setWidth(STROKE)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

        set_part_color("head")
        draw_head(painter, head_top_left)
        set_part_color("torso")
        draw_torso(painter, neck, joints["hip"])
        set_part_color("right_arm")
        draw_arm(painter, neck, joints["elbow_r"], joints["hand_r"])
        set_part_color("left_arm")
        draw_arm(painter, neck, joints["elbow_l"], joints["hand_l"])
        set_part_color("right_leg")
        draw_leg(painter, joints["hip"], joints["knee_r"], joints["foot_r"])
        set_part_color("left_leg")
        draw_leg(painter, joints["hip"], joints["knee_l"], joints["foot_l"])
        return joints

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.scale(self.editor.canvas_scale, self.editor.canvas_scale)
            background = DARK_BG_COLOR if self.editor.dark_mode else LIGHT_BG_COLOR
            ground = DARK_GROUND_COLOR if self.editor.dark_mode else LIGHT_GROUND_COLOR
            painter.fillRect(0, 0, self.editor.canvas_width,
                             self.editor.canvas_height, background)

            ground_pen = QPen(ground)
            ground_pen.setWidth(2)
            painter.setPen(ground_pen)
            ground_y = self.editor.ground_line_y + self.editor.canvas_origin_offset_y()
            painter.drawLine(0, round(ground_y), self.editor.canvas_width, round(ground_y))
            painter.setBrush(ground)
            painter.drawEllipse(QPointF(self.editor.canvas_width - 12, ground_y), 4, 4)
            painter.setBrush(Qt.NoBrush)

            body_scale = self.editor.body_display_scale()
            offset_x, offset_y = self.editor.body_draw_offset()
            painter.save()
            painter.translate(HIP_ANCHOR[0] + offset_x, offset_y)
            painter.scale(body_scale, body_scale)
            painter.translate(-HIP_ANCHOR[0], 0)

            # Onion skin: frame anterior em cinza translúcido, só no modo edição
            if not self.editor.playing and self.editor.current_index > 0:
                ghost_frame = self.editor.frames[self.editor.current_index - 1]
                self.draw_body(
                    painter, self.editor.grounded_frame(ghost_frame), GHOST_COLOR
                )

            frame = self.editor.playback_frame() if self.editor.playing else self.current_frame()
            frame = self.editor.grounded_frame(frame)
            joints = self.draw_body(painter, frame, None)

            if not self.editor.playing:
                for key, point in joints.items():
                    if key == "hip":
                        continue
                    if key == "neck":
                        handle_pen = QPen(NECK_HANDLE_COLOR)
                        handle_pen.setWidth(1)
                        painter.setPen(handle_pen)
                        painter.setBrush(Qt.NoBrush)
                        radius = NECK_HANDLE_RADIUS / body_scale
                        painter.drawEllipse(QPointF(*point), radius, radius)
                        continue
                    if "elbow" in key or "knee" in key:
                        color = JOINT_HANDLE_COLOR
                    else:
                        color = END_HANDLE_COLOR
                    handle_pen = QPen(color)
                    handle_pen.setWidth(1)
                    painter.setPen(handle_pen)
                    painter.setBrush(Qt.NoBrush)
                    radius = HANDLE_RADIUS / body_scale
                    painter.drawEllipse(QPointF(*point), radius, radius)

            if self.dragging_key is not None and self.dragging_angle is not None:
                label_pos = joints[self.dragging_key]
                painter.setPen(QPen(QColor(BODY_COLORS["torso"])))
                painter.setFont(QFont("Sans", max(1, round(9 / body_scale))))
                painter.drawText(int(label_pos[0]) + 10, int(label_pos[1]) - 10, f"{self.dragging_angle}°")
            painter.restore()
        finally:
            painter.end()

    def body_point(self, pos):
        canvas_x = pos.x() / self.editor.canvas_scale
        canvas_y = pos.y() / self.editor.canvas_scale
        body_scale = self.editor.body_display_scale()
        offset_x, offset_y = self.editor.body_draw_offset()
        return (
            HIP_ANCHOR[0] + (canvas_x - offset_x - HIP_ANCHOR[0]) / body_scale,
            (canvas_y - offset_y) / body_scale,
        )

    def handle_at(self, pos):
        visible_frame = self.editor.grounded_frame(self.current_frame())
        joints = compute_joints(visible_frame)
        point_x, point_y = self.body_point(pos)
        for key in self.handle_specs:
            point = joints[key]
            radius = NECK_HANDLE_RADIUS if key == "neck" else HANDLE_RADIUS
            dx = point_x - point[0]
            dy = point_y - point[1]
            if dx * dx + dy * dy <= (radius * 2.5) ** 2:
                return key
        return None

    def mousePressEvent(self, event):
        if self.editor.playing or event.button() != Qt.LeftButton:
            return
        canvas_x = event.pos().x() / self.editor.canvas_scale
        canvas_y = event.pos().y() / self.editor.canvas_scale
        ground_grip_x = self.editor.canvas_width - 12
        ground_display_y = self.editor.ground_line_y + self.editor.canvas_origin_offset_y()
        if (abs(canvas_x - ground_grip_x) <= 14
            and abs(canvas_y - ground_display_y) <= 14):
            self.dragging_ground = True
            self.setCursor(Qt.SizeVerCursor)
        elif self.editor.move_rig_button.isChecked():
            self.panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif not self.editor.physics_checkbox.isChecked():
            self.dragging_key = self.handle_at(event.pos())
            if self.dragging_key is not None:
                return
            self.panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            self.dragging_key = self.handle_at(event.pos())
            if self.dragging_key is not None:
                return
            self.setCursor(Qt.ForbiddenCursor)

    def mouseMoveEvent(self, event):
        if self.dragging_ground:
            ground_y = event.pos().y() / self.editor.canvas_scale
            ground_y -= self.editor.canvas_origin_offset_y()
            self.editor.set_ground_line_y(ground_y)
            self.setCursor(Qt.SizeVerCursor)
            return
        if self.panning and self.last_pan_pos is not None:
            scale = self.editor.canvas_scale
            self.editor.canvas_pan_x += (event.pos().x() - self.last_pan_pos.x()) / scale
            if not self.editor.physics_checkbox.isChecked():
                self.editor.canvas_pan_y += (event.pos().y() - self.last_pan_pos.y()) / scale
            self.last_pan_pos = event.pos()
            self.update()
            return
        if self.dragging_key is None:
            canvas_x = event.pos().x() / self.editor.canvas_scale
            canvas_y = event.pos().y() / self.editor.canvas_scale
            on_ground_grip = (
                abs(canvas_x - (self.editor.canvas_width - 12)) <= 14
                and abs(canvas_y - self.editor.ground_line_y
                        - self.editor.canvas_origin_offset_y()) <= 14
            )
            if on_ground_grip:
                self.setCursor(Qt.SizeVerCursor)
            elif self.editor.physics_checkbox.isChecked():
                self.setCursor(
                    Qt.PointingHandCursor if self.handle_at(event.pos()) is not None
                    else Qt.ForbiddenCursor
                )
            else:
                self.setCursor(
                    Qt.PointingHandCursor if self.handle_at(event.pos()) is not None
                    else Qt.OpenHandCursor
                )
            return
        frame = self.current_frame()
        parent_key, _, setter = self.handle_specs[self.dragging_key]
        visible_frame = self.editor.grounded_frame(frame)
        joints = compute_joints(visible_frame)
        origin = joints[parent_key]
        mouse = self.body_point(event.pos())
        absolute_angle = angle_between(origin, mouse)
        setter(frame, round(absolute_angle))
        self.dragging_angle = round(absolute_angle)
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_key = None
        self.dragging_angle = None
        self.dragging_ground = False
        self.panning = False
        self.last_pan_pos = None
        self.setCursor(Qt.OpenHandCursor)
        self.update()


class RigEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rig Editor — Polytes")
        self.setMinimumSize(320, 440)

        QApplication.instance().setOrganizationName("Polytes")
        QApplication.instance().setApplicationName("Rig Editor")
        self.settings = QSettings()
        saved_default = self.settings.value("default_pose")
        self.pose_presets = {
            "Standing": standing_frame(),
            "Squat": default_frame(),
        }
        startup_fallback = "Standing"
        legacy_startup = False
        saved_presets = self.settings.value("pose_presets")
        if saved_presets:
            try:
                loaded_presets = json.loads(saved_presets)
                if isinstance(loaded_presets, dict):
                    self.pose_presets.update({
                        name: pose for name, pose in loaded_presets.items()
                        if isinstance(name, str) and isinstance(pose, dict)
                    })
            except (TypeError, json.JSONDecodeError):
                pass
        elif saved_default:
            try:
                legacy_pose = json.loads(saved_default)
                if isinstance(legacy_pose, dict):
                    self.pose_presets["Saved Default"] = legacy_pose
                    startup_fallback = "Saved Default"
                    legacy_startup = True
            except (TypeError, json.JSONDecodeError):
                pass
        self.startup_pose_name = self.settings.value("startup_pose_name", startup_fallback)
        if legacy_startup and not self.settings.contains("startup_pose_name"):
            self.startup_pose_name = "Saved Default"
        if self.startup_pose_name not in self.pose_presets:
            self.startup_pose_name = next(iter(self.pose_presets))
        self.default_pose = dict(self.pose_presets[self.startup_pose_name])
        self.frames = [dict(self.default_pose)]
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.ui_scale = 1.0
        self.canvas_zoom = 1.0
        self.canvas_scale = 1.0
        self.character_scale = 1.0
        self.canvas_pan_x = 0.0
        self.canvas_pan_y = 0.0
        self.canvas_width = max(
            240, min(1600, self.settings.value("canvas_width", CANVAS_WIDTH, type=int))
        )
        self.canvas_height = max(
            320, min(1800, self.settings.value("canvas_height", CANVAS_HEIGHT, type=int))
        )
        self.ground_line_y = float(GROUND_Y)
        self.copied_frame = None
        self.current_index = 0
        self.playing = False
        self.playback_index = 0
        self.playback_position = 0.0

        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.advance_playback)

        self.canvas = RigCanvas(self)

        self.frame_label = QLabel()
        self.frame_label.setFont(QFont("Sans", 10))
        self.update_frame_label()

        prev_button = QPushButton("<")
        next_button = QPushButton(">")
        prev_button.setToolTip("Previous frame (Left Arrow)")
        next_button.setToolTip("Next frame (Right Arrow)")
        prev_button.setToolTip("Previous frame (Left Arrow)")
        next_button.setToolTip("Next frame (Right Arrow)")
        new_button = QPushButton("New Frame")
        new_button.setToolTip("Duplicate the current frame (Ctrl+N)")
        delete_button = QPushButton("Delete")
        delete_button.setToolTip("Delete the current frame (Delete)")
        self.play_button = QPushButton()
        self.play_button.setObjectName("primaryAction")
        self.play_button.setMinimumHeight(44)
        mirror_button = QPushButton("Mirror Right -> Left")
        mirror_button.setToolTip("Copy the right-side pose to the left (Ctrl+Shift+Left)")
        mirror_reverse_button = QPushButton("Mirror Left -> Right")
        mirror_reverse_button.setToolTip("Copy the left-side pose to the right (Ctrl+Shift+Right)")
        copy_button = QPushButton("Copy Frame")
        copy_button.setToolTip("Copy the current frame (Ctrl+C)")
        paste_button = QPushButton("Paste Frame")
        paste_button.setToolTip("Paste into the current frame (Ctrl+V)")
        self.move_rig_button = QPushButton("Move Rig")
        self.move_rig_button.setCheckable(True)
        self.move_rig_button.setToolTip(
            "Move the whole rig (M) without changing the pose or JSON"
        )
        self.pose_preset_combo = QComboBox()
        self.refresh_pose_preset_combo(self.startup_pose_name)
        save_preset_button = QPushButton("Save Pose As...")
        save_preset_button.setToolTip("Save a named pose preset (Ctrl+S)")
        load_preset_button = QPushButton("Load Preset")
        load_preset_button.setToolTip("Load the selected pose into the current frame")
        self.startup_preset_button = QPushButton("Use on Startup")
        self.startup_preset_button.setToolTip("Open the editor with the selected pose next time")
        self.delete_preset_button = QPushButton("Delete Preset")
        self.theme_button = QPushButton()
        self.update_theme_button()
        self.physics_checkbox = QCheckBox("Snap rig to ground")
        self.physics_checkbox.setChecked(True)
        self.physics_checkbox.setToolTip(
            "Align the lowest foot with the movable canvas ground without changing frame data"
        )
        self.physics_checkbox.toggled.connect(self.set_ground_mode)
        self.physics_checkbox.toggled.connect(self.update_move_rig_availability)
        self.move_rig_button.setEnabled(True)
        self.scale_label = QLabel("UI scale: 100%")
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(75, 175)
        self.scale_slider.setValue(100)
        self.scale_slider.valueChanged.connect(self.set_ui_scale)
        self.character_size_label = QLabel("Character size: 100%")
        self.character_size_slider = QSlider(Qt.Horizontal)
        self.character_size_slider.setRange(50, 250)
        self.character_size_slider.setValue(100)
        self.character_size_slider.valueChanged.connect(self.set_character_scale)
        self.canvas_zoom_label = QLabel("Canvas zoom: 100%")
        self.canvas_zoom_slider = QSlider(Qt.Horizontal)
        self.canvas_zoom_slider.setRange(50, 150)
        self.canvas_zoom_slider.setValue(100)
        self.canvas_zoom_slider.valueChanged.connect(self.set_canvas_zoom)
        self.canvas_size_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.canvas_size_layout.addWidget(QLabel("Width"))
        self.canvas_width_input = QSpinBox()
        self.canvas_width_input.setRange(240, 1600)
        self.canvas_width_input.setSingleStep(20)
        self.canvas_width_input.setValue(self.canvas_width)
        self.canvas_width_input.valueChanged.connect(self.set_canvas_width)
        self.canvas_size_layout.addWidget(self.canvas_width_input)
        self.canvas_size_layout.addWidget(QLabel("Height"))
        self.canvas_height_input = QSpinBox()
        self.canvas_height_input.setRange(320, 1800)
        self.canvas_height_input.setSingleStep(20)
        self.canvas_height_input.setValue(self.canvas_height)
        self.canvas_height_input.valueChanged.connect(self.set_canvas_height)
        self.canvas_size_layout.addWidget(self.canvas_height_input)
        reset_view_button = QPushButton("Reset View")
        reset_view_button.setToolTip("Reset zoom and position (Home)")
        reset_view_button.clicked.connect(self.reset_view)
        export_button = QPushButton("Export JSON")
        import_button = QPushButton("Import JSON")
        self.copy_python_button = QPushButton("Copy Python")
        self.copy_python_button.setToolTip(
            "Copy the current frames as an ANIMATIONS Python dictionary"
        )
        self.python_copy_status = QLabel()

        speed_label = QLabel("Frame delay")
        self.speed_value_label = QLabel()
        self.speed_value_label.setObjectName("valueBadge")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(60)
        self.speed_slider.setMaximum(500)
        self.speed_slider.setValue(150)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.update_speed_label(self.speed_slider.value())
        self.interpolation_label = QLabel("In-betweens")
        self.interpolation_slider = QSlider(Qt.Horizontal)
        self.interpolation_slider.setRange(1, 12)
        self.interpolation_slider.setValue(4)
        self.interpolation_slider.setToolTip(
            "More in-betweens create smoother transitions between frames"
        )
        self.interpolation_slider.valueChanged.connect(self.update_interpolation_label)
        self.interpolation_value_label = QLabel("4")
        self.interpolation_value_label.setObjectName("valueBadge")

        self.roundness_label = QLabel(f"Joint rounding: {JOINT_ROUNDNESS:.2f}")
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
        mirror_reverse_button.clicked.connect(self.mirror_left_to_right)
        copy_button.clicked.connect(self.copy_frame)
        paste_button.clicked.connect(self.paste_frame)
        save_preset_button.clicked.connect(self.prompt_save_pose_preset)
        load_preset_button.clicked.connect(self.load_selected_pose_preset)
        self.startup_preset_button.clicked.connect(self.set_startup_pose_preset)
        self.delete_preset_button.clicked.connect(self.delete_selected_pose_preset)
        self.pose_preset_combo.currentTextChanged.connect(self.update_preset_controls)
        self.theme_button.clicked.connect(self.toggle_theme)
        export_button.clicked.connect(self.export_json)
        import_button.clicked.connect(self.import_json)
        self.copy_python_button.clicked.connect(self.copy_python_dictionary)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("POLYTES  /  RIG EDITOR")
        self.title_label.setObjectName("windowTitle")
        self.subtitle_label = QLabel("FRAME ANIMATION")
        self.subtitle_label.setObjectName("windowSubtitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.subtitle_label)

        stage = QFrame()
        stage.setObjectName("canvasStage")
        self.canvas_stage = stage
        stage_layout = QHBoxLayout(stage)
        stage_layout.addStretch(1)
        self.canvas_view = QScrollArea()
        self.canvas_view.setObjectName("canvasViewport")
        self.canvas_view.setWidgetResizable(False)
        self.canvas_view.setAlignment(Qt.AlignCenter)
        self.canvas_view.setFrameShape(QFrame.NoFrame)
        self.canvas_view.setMinimumSize(200, 240)
        self.canvas_view.setWidget(self.canvas)
        stage_layout.addWidget(self.canvas_view, 1)
        stage_layout.addStretch(1)
        stage_layout.setContentsMargins(20, 20, 20, 20)

        frame_group = QGroupBox("ANIMATION")
        nav_layout = QHBoxLayout()
        prev_button.setFixedWidth(48)
        next_button.setFixedWidth(48)
        nav_layout.addWidget(prev_button)
        nav_layout.addWidget(self.frame_label, 1)
        nav_layout.addWidget(next_button)

        self.frame_actions_layout = QGridLayout()
        self.frame_action_buttons = [new_button, delete_button, copy_button,
                         paste_button, mirror_button, mirror_reverse_button,
                         self.move_rig_button]
        self.frame_action_labels = [button.text() for button in self.frame_action_buttons]
        self.compact_action_labels = ["New", "Delete", "Copy", "Paste",
                          "Mirror R -> L", "Mirror L -> R", "Move"]
        for column, button in enumerate(self.frame_action_buttons):
            self.frame_actions_layout.addWidget(button, 0, column)
        self.frame_actions_layout.setHorizontalSpacing(8)
        self.frame_actions_layout.setVerticalSpacing(8)

        self.speed_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.speed_layout.addWidget(speed_label)
        self.speed_layout.addWidget(self.speed_slider, 1)
        self.speed_layout.addWidget(self.speed_value_label)
        self.interpolation_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.interpolation_layout.addWidget(self.interpolation_label)
        self.interpolation_layout.addWidget(self.interpolation_slider, 1)
        self.interpolation_layout.addWidget(self.interpolation_value_label)

        frame_layout = QVBoxLayout(frame_group)
        frame_layout.addLayout(nav_layout)
        frame_layout.addLayout(self.speed_layout)
        frame_layout.addLayout(self.interpolation_layout)
        frame_layout.addWidget(self.play_button)
        frame_layout.addLayout(self.frame_actions_layout)

        appearance_group = QGroupBox("POSE & TOOLS")
        self.appearance_layout = QGridLayout(appearance_group)
        self.appearance_layout.setHorizontalSpacing(8)
        self.appearance_layout.setVerticalSpacing(8)
        self.appearance_widgets = [
            self.pose_preset_combo, save_preset_button, load_preset_button,
            self.startup_preset_button, self.delete_preset_button,
            self.physics_checkbox, self.theme_button,
        ]

        adjust_group = QGroupBox("SETTINGS")
        adjust_layout = QVBoxLayout(adjust_group)
        self.scale_layout = QBoxLayout(QBoxLayout.LeftToRight)
        scale_layout = self.scale_layout
        scale_layout.addWidget(self.scale_label)
        scale_layout.addWidget(self.scale_slider)
        self.roundness_layout = QBoxLayout(QBoxLayout.LeftToRight)
        roundness_layout = self.roundness_layout
        roundness_layout.addWidget(self.roundness_label)
        roundness_layout.addWidget(self.roundness_slider)
        adjust_layout.addLayout(scale_layout)
        self.character_scale_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.character_scale_layout.addWidget(self.character_size_label)
        self.character_scale_layout.addWidget(self.character_size_slider)
        self.canvas_zoom_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.canvas_zoom_layout.addWidget(self.canvas_zoom_label)
        self.canvas_zoom_layout.addWidget(self.canvas_zoom_slider)
        adjust_layout.addLayout(self.canvas_size_layout)
        adjust_layout.addLayout(self.character_scale_layout)
        adjust_layout.addLayout(self.canvas_zoom_layout)
        adjust_layout.addLayout(roundness_layout)
        adjust_layout.addWidget(reset_view_button)

        files_group = QGroupBox("FILES")
        self.file_layout = QGridLayout()
        self.file_buttons = [export_button, import_button, self.copy_python_button]
        files_layout = QVBoxLayout(files_group)
        files_layout.addLayout(self.file_layout)
        files_layout.addWidget(self.python_copy_status)

        palette_group = QGroupBox("PROGRAM PALETTE")
        palette_layout = QGridLayout(palette_group)
        palette_names = [
            ("head", "Head"), ("torso", "Torso"),
            ("left_arm", "Left arm"), ("right_arm", "Right arm"),
            ("left_leg", "Left leg"), ("right_leg", "Right leg"),
        ]
        for index, (part, label) in enumerate(palette_names):
            swatch = QFrame()
            swatch.setObjectName("colorSwatch")
            swatch.setFixedSize(18, 18)
            swatch.setStyleSheet(
                f"QFrame#colorSwatch {{ background: {BODY_COLORS[part]}; "
                "border: 1px solid #858585; border-radius: 9px; }"
            )
            item_layout = QHBoxLayout()
            item_layout.addWidget(swatch)
            item_layout.addWidget(QLabel(label))
            item_layout.addStretch(1)
            palette_layout.addLayout(item_layout, index // 2, index % 2)

        self.editor_tabs = QTabWidget()
        self.editor_tabs.setObjectName("editorTabs")
        self.editor_tabs.setDocumentMode(True)
        self.editor_tabs.setTabPosition(QTabWidget.West)
        self.editor_tabs.addTab(frame_group, "Animation")
        self.editor_tabs.addTab(appearance_group, "Presets")
        self.editor_tabs.addTab(palette_group, "Palette")
        self.editor_tabs.addTab(adjust_group, "Settings")
        self.editor_tabs.addTab(files_group, "Files")
        self.editor_tabs.setMinimumHeight(260)
        self.tab_labels = ["Animation", "Presets", "Palette", "Settings", "Files"]
        self.compact_tab_labels = ["Anim", "Pose", "Color", "Setup", "File"]
        for index, label in enumerate(self.tab_labels):
            self.editor_tabs.setTabToolTip(index, label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(stage, 1)
        main_layout.addWidget(self.editor_tabs)
        main_layout.setContentsMargins(22, 18, 22, 18)
        main_layout.setSpacing(14)

        content = QWidget()
        content.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        content.setLayout(main_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setWidget(content)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)
        self._install_shortcuts()
        self._update_responsive_layout(self.width())
        self.update_preset_controls()
        self.update_play_control()
        self.apply_theme()

    def _install_shortcuts(self):
        shortcuts = [
            ("Space", self.toggle_play),
            ("Left", self.prev_frame),
            ("Right", self.next_frame),
            ("Ctrl+C", self.copy_frame),
            ("Ctrl+V", self.paste_frame),
            ("Ctrl+N", self.new_frame),
            ("Ctrl+S", self.prompt_save_pose_preset),
            ("Ctrl+Shift+Left", self.mirror_right_to_left),
            ("Ctrl+Shift+Right", self.mirror_left_to_right),
            ("M", self.toggle_move_rig_mode),
            ("Home", self.reset_view),
            ("Delete", self.delete_frame),
        ]
        self.shortcuts = []
        for key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def refresh_pose_preset_combo(self, selected_name=None):
        self.pose_preset_combo.blockSignals(True)
        self.pose_preset_combo.clear()
        self.pose_preset_combo.addItems(sorted(self.pose_presets))
        if selected_name:
            index = self.pose_preset_combo.findText(selected_name)
            if index >= 0:
                self.pose_preset_combo.setCurrentIndex(index)
        self.pose_preset_combo.blockSignals(False)

    def persist_pose_presets(self):
        self.settings.setValue("pose_presets", json.dumps(self.pose_presets))

    def prompt_save_pose_preset(self):
        name, accepted = QInputDialog.getText(
            self, "Save Pose Preset", "Preset name:",
            text=self.pose_preset_combo.currentText()
        )
        if accepted and name.strip():
            self.save_pose_preset(name.strip())

    def save_pose_preset(self, name):
        name = name.strip()
        if not name:
            return
        if name in self.pose_presets:
            answer = QMessageBox.question(
                self, "Replace Pose Preset",
                f"A preset named '{name}' already exists. Replace it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if answer != QMessageBox.Yes:
                return
        self.pose_presets[name] = dict(self.frames[self.current_index])
        self.persist_pose_presets()
        self.refresh_pose_preset_combo(name)
        self.update_preset_controls()

    def load_selected_pose_preset(self):
        name = self.pose_preset_combo.currentText()
        pose = self.pose_presets.get(name)
        if pose is None:
            return
        self.frames[self.current_index] = dict(pose)
        self.refresh()

    def set_startup_pose_preset(self):
        name = self.pose_preset_combo.currentText()
        if name not in self.pose_presets:
            return
        self.startup_pose_name = name
        self.default_pose = dict(self.pose_presets[name])
        self.settings.setValue("startup_pose_name", name)
        self.settings.setValue("default_pose", json.dumps(self.default_pose))
        self.persist_pose_presets()
        self.update_preset_controls()

    def delete_selected_pose_preset(self):
        name = self.pose_preset_combo.currentText()
        if name not in self.pose_presets or len(self.pose_presets) <= 1:
            return
        answer = QMessageBox.question(
            self, "Delete Pose Preset", f"Delete the '{name}' preset?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if answer != QMessageBox.Yes:
            return
        del self.pose_presets[name]
        if name == self.startup_pose_name:
            self.startup_pose_name = next(iter(self.pose_presets))
            self.default_pose = dict(self.pose_presets[self.startup_pose_name])
            self.settings.setValue("startup_pose_name", self.startup_pose_name)
            self.settings.setValue("default_pose", json.dumps(self.default_pose))
        self.persist_pose_presets()
        self.refresh_pose_preset_combo(self.startup_pose_name)
        self.update_preset_controls()

    def update_preset_controls(self, selected_name=None):
        selected_name = selected_name or self.pose_preset_combo.currentText()
        is_startup = selected_name == self.startup_pose_name
        self.startup_preset_button.setEnabled(bool(selected_name) and not is_startup)
        self.startup_preset_button.setText(
            "Startup Pose" if is_startup else "Use on Startup"
        )
        self.delete_preset_button.setEnabled(len(self.pose_presets) > 1)

    def toggle_move_rig_mode(self):
        if self.move_rig_button.isEnabled():
            self.move_rig_button.setChecked(not self.move_rig_button.isChecked())

    def _update_responsive_layout(self, width):
        compact = width < 820
        narrow = width < 520
        self.editor_tabs.setTabPosition(
            QTabWidget.North if narrow else QTabWidget.West
        )
        for index, label in enumerate(self.compact_tab_labels):
            self.editor_tabs.setTabText(index, label)
        self.title_label.setText("POLYTES" if narrow else "POLYTES  /  RIG EDITOR")
        self.subtitle_label.setText("RIG EDITOR" if narrow else "FRAME ANIMATION")
        action_columns = 2 if compact else len(self.frame_action_buttons)
        for index, button in enumerate(self.frame_action_buttons):
            self.frame_actions_layout.removeWidget(button)
            button.setText(self.compact_action_labels[index] if narrow
                           else self.frame_action_labels[index])
            self.frame_actions_layout.addWidget(button, index // action_columns,
                                                index % action_columns)

        for widget in self.appearance_widgets:
            self.appearance_layout.removeWidget(widget)
        appearance_columns = 1 if narrow else 2 if compact else 4
        for index, widget in enumerate(self.appearance_widgets):
            self.appearance_layout.addWidget(
                widget, index // appearance_columns, index % appearance_columns
            )

        file_columns = 1 if width < 480 else 2
        for index, button in enumerate(self.file_buttons):
            self.file_layout.removeWidget(button)
            self.file_layout.addWidget(button, index // file_columns,
                                       index % file_columns)

        direction = QBoxLayout.TopToBottom if width < 520 else QBoxLayout.LeftToRight
        self.speed_layout.setDirection(direction)
        self.interpolation_layout.setDirection(direction)
        self.scale_layout.setDirection(direction)
        self.canvas_size_layout.setDirection(direction)
        self.character_scale_layout.setDirection(direction)
        self.canvas_zoom_layout.setDirection(direction)
        self.roundness_layout.setDirection(direction)
        self._update_canvas_size()

    def _update_canvas_size(self):
        if not hasattr(self, "canvas"):
            return
        self.canvas_scale = self.ui_scale * self.canvas_zoom
        self.canvas.setFixedSize(
            round(self.canvas_width * self.canvas_scale),
            round(self.canvas_height * self.canvas_scale),
        )
        self.canvas.update()

    def canvas_origin_offset_x(self):
        return (self.canvas_width - CANVAS_WIDTH) / 2

    def canvas_origin_offset_y(self):
        return (self.canvas_height - CANVAS_HEIGHT) / 2

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "frame_actions_layout"):
            width = self.scroll_area.viewport().width()
            self._update_responsive_layout(width)
            QTimer.singleShot(0, self._refresh_responsive_layout)

    def _refresh_responsive_layout(self):
        if hasattr(self, "scroll_area"):
            self._update_responsive_layout(self.scroll_area.viewport().width())

    def body_display_scale(self):
        return BODY_DISPLAY_SCALE * self.character_scale

    def body_draw_offset(self):
        offset_x = (
            self.canvas_origin_offset_x()
            + BODY_DRAW_OFFSET_X * self.character_scale
            + self.canvas_pan_x
        )
        center_y = CANVAS_HEIGHT / 2
        offset_y = (
            self.canvas_origin_offset_y()
            + center_y * (1 - self.character_scale)
            + BODY_DRAW_OFFSET_Y * self.character_scale
            + self.canvas_pan_y
        )
        return offset_x, offset_y

    def update_theme_button(self):
        self.theme_button.setText("Light Theme" if self.dark_mode else "Dark Theme")

    def update_speed_label(self, value):
        self.speed_value_label.setText(f"{value} ms")
        if self.playing:
            self.playback_timer.setInterval(self.playback_interval())

    def playback_interval(self):
        return max(8, round(
            self.speed_slider.value() / self.interpolation_slider.value()
        ))

    def update_interpolation_label(self, value):
        self.interpolation_value_label.setText(str(value))
        if self.playing:
            self.playback_timer.setInterval(self.playback_interval())

    def apply_theme(self):
        font_size = max(10, round(12 * self.ui_scale))
        padding = max(4, round(6 * self.ui_scale))
        self.setStyleSheet("")
        if self.dark_mode:
            self.setStyleSheet(f"QWidget {{ background: #24282b; color: #e7ecee; font-family: 'DejaVu Sans'; font-size: {font_size}px; }}"
                               "QGroupBox { border: 1px solid #454d52; border-radius: 10px; margin-top: 12px; padding: 12px 10px 10px; font-weight: 600; color: #a9c7c1; }"
                               "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
                               "QFrame#canvasStage { background: #303639; border: 1px solid #454d52; border-radius: 12px; }"
                               f"QPushButton, QComboBox, QSpinBox {{ background: #363d41; color: #e7ecee; border: 1px solid #50595e; border-radius: 11px; padding: {padding + 2}px {padding + 8}px; min-height: 22px; }}"
                               "QPushButton:hover { background: #465157; border-color: #71817e; } QPushButton:pressed { background: #2c3438; } QPushButton:checked { background: #1d766d; border-color: #48ad9f; color: white; } QPushButton:disabled { color: #7f898d; background: #303639; }"
                               "QPushButton#primaryAction { background: #176b65; border-color: #21877e; border-radius: 14px; color: white; font-size: 14px; font-weight: 700; } QPushButton#primaryAction:hover { background: #21877e; }"
                               "QTabWidget::pane { border: 1px solid #454d52; border-radius: 10px; top: -1px; } QTabBar::tab { background: #303639; border: 1px solid #454d52; border-radius: 10px; padding: 5px 8px; margin: 2px; } QTabBar::tab:selected { background: #176b65; color: white; border-color: #21877e; }"
                               "QCheckBox { spacing: 8px; } QLabel#valueBadge { background: #303639; color: #9fe0d2; border-radius: 7px; padding: 4px 8px; font-weight: 700; } QLabel#windowTitle { font-size: 15px; font-weight: 700; color: #e7ecee; } QLabel#windowSubtitle { color: #9ca8ac; font-size: 10px; }")
        else:
            self.setStyleSheet(f"QWidget {{ background: #f1f0eb; color: #242927; font-family: 'DejaVu Sans'; font-size: {font_size}px; }}"
                               "QGroupBox { border: 1px solid #d1d4ce; border-radius: 10px; margin-top: 12px; padding: 12px 10px 10px; font-weight: 600; color: #386b62; }"
                               "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
                               "QFrame#canvasStage { background: #e3e6e1; border: 1px solid #d1d4ce; border-radius: 12px; }"
                               f"QPushButton, QComboBox, QSpinBox {{ background: #ffffff; color: #242927; border: 1px solid #c8cdc7; border-radius: 11px; padding: {padding + 2}px {padding + 8}px; min-height: 22px; }}"
                               "QPushButton:hover { background: #e9efeb; border-color: #83a39a; } QPushButton:pressed { background: #dce7e1; } QPushButton:checked { background: #247b70; border-color: #55a99a; color: white; } QPushButton:disabled { color: #929a95; background: #e7e9e5; }"
                               "QPushButton#primaryAction { background: #247b70; border-color: #247b70; border-radius: 14px; color: white; font-size: 14px; font-weight: 700; } QPushButton#primaryAction:hover { background: #1c665d; }"
                               "QTabWidget::pane { border: 1px solid #d1d4ce; border-radius: 10px; top: -1px; } QTabBar::tab { background: #e8ebe6; border: 1px solid #d1d4ce; border-radius: 10px; padding: 5px 8px; margin: 2px; } QTabBar::tab:selected { background: #247b70; color: white; border-color: #247b70; }"
                               "QCheckBox { spacing: 8px; } QLabel#valueBadge { background: #e1ebe5; color: #246b60; border-radius: 7px; padding: 4px 8px; font-weight: 700; } QLabel#windowTitle { font-size: 15px; font-weight: 700; color: #242927; } QLabel#windowSubtitle { color: #727d78; font-size: 10px; }")
        slider_color = "#21877e" if self.dark_mode else "#247b70"
        slider_track = "#495258" if self.dark_mode else "#c9d0ca"
        self.setStyleSheet(self.styleSheet() +
                           f" QSlider::groove:horizontal {{ height: 5px; background: {slider_track}; border-radius: 2px; }}"
                           f" QSlider::sub-page:horizontal {{ background: {slider_color}; border-radius: 2px; }}"
                           f" QSlider::handle:horizontal {{ background: {slider_color}; width: 14px; margin: -5px 0; border-radius: 7px; }}")
        self.update_theme_button()
        self.canvas.update()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.settings.setValue("dark_mode", self.dark_mode)
        self.apply_theme()

    def set_ui_scale(self, value):
        self.ui_scale = value / 100
        self.scale_label.setText(f"UI scale: {value}%")
        self._update_canvas_size()
        self.apply_theme()

    def set_character_scale(self, value):
        self.character_scale = value / 100
        self.character_size_label.setText(f"Character size: {value}%")
        self.canvas.update()

    def set_canvas_zoom(self, value):
        self.canvas_zoom = value / 100
        self.canvas_zoom_label.setText(f"Canvas zoom: {value}%")
        self._update_canvas_size()

    def set_canvas_width(self, value):
        self.canvas_width = value
        self.settings.setValue("canvas_width", value)
        self._update_canvas_size()

    def set_canvas_height(self, value):
        self.canvas_height = value
        self.settings.setValue("canvas_height", value)
        self._update_canvas_size()

    def reset_view(self):
        self.canvas_pan_x = 0.0
        self.canvas_pan_y = 0.0
        self.character_size_slider.setValue(100)
        self.canvas_zoom_slider.setValue(100)
        self._update_canvas_size()
        self.canvas.update()

    def grounded_frame(self, frame):
        if not self.physics_checkbox.isChecked():
            return frame
        adjusted = dict(frame)
        joints = compute_joints(adjusted)
        head_center = polar_point(
            joints["neck"], HEAD_DIAMETER / 2, adjusted["torso_angle"]
        )
        lowest_body_y = max(
            max(point[1] for point in joints.values()),
            head_center[1] + HEAD_DIAMETER / 2,
        )
        _, offset_y = self.body_draw_offset()
        offset_y -= self.canvas_pan_y
        ground_y = self.ground_line_y + self.canvas_origin_offset_y()
        target_body_y = (
            (ground_y - offset_y) / self.body_display_scale()
            - STROKE / 2
            - 1
        )
        adjusted["hip_offset_y"] = (
            adjusted.get("hip_offset_y", 0) + target_body_y - lowest_body_y
        )
        return adjusted

    def set_ground_mode(self, enabled):
        if enabled:
            self.canvas_pan_y = 0.0
        self.canvas.update()

    def update_move_rig_availability(self, snap_enabled=None):
        snap_enabled = self.physics_checkbox.isChecked()
        if snap_enabled:
            self.move_rig_button.setChecked(False)
        self.move_rig_button.setEnabled(True)
        self.move_rig_button.setToolTip(
            "Drag horizontally; ground snap keeps the rig on the floor"
            if snap_enabled
            else "Drag anywhere on the rig to move it without changing the pose or JSON"
        )

    def set_ground_line_y(self, value):
        origin_y = self.canvas_origin_offset_y()
        minimum = 40.0 - origin_y
        maximum = self.canvas_height - 12.0 - origin_y
        self.ground_line_y = max(minimum, min(maximum, value))
        self.canvas.update()

    def copy_frame(self):
        self.copied_frame = dict(self.frames[self.current_index])

    def paste_frame(self):
        if self.copied_frame is not None:
            self.frames[self.current_index] = dict(self.copied_frame)
            self.refresh()

    def save_default_pose(self):
        self.default_pose = dict(self.frames[self.current_index])
        self.settings.setValue("default_pose", json.dumps(self.default_pose))

    def reset_pose(self):
        self.frames[self.current_index] = dict(self.default_pose)
        self.refresh()

    def update_play_control(self):
        can_play = bool(self.frames)
        self.play_button.setEnabled(can_play)
        self.play_button.setText("Pause" if self.playing else "Play")
        self.play_button.setToolTip(
            "Pause animation (Space)" if self.playing
            else "Play animation or preview this pose (Space)"
        )

    def update_frame_label(self):
        self.frame_label.setText(f"FRAME {self.current_index + 1} / {len(self.frames)}")
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
        if not self.frames:
            return
        self.playing = not self.playing
        if self.playing:
            self.playback_position = float(self.current_index)
            self.playback_index = self.current_index
            self.playback_timer.start(self.playback_interval())
        else:
            self.playback_timer.stop()
        self.update_play_control()
        self.canvas.update()

    def advance_playback(self):
        if len(self.frames) > 1:
            self.playback_position = (
                self.playback_position
                + 1 / self.interpolation_slider.value()
            ) % len(self.frames)
            self.playback_index = int(self.playback_position)
        self.playback_timer.setInterval(self.playback_interval())
        self.canvas.update()

    def playback_frame(self):
        if len(self.frames) < 2:
            return self.frames[self.playback_index]
        position = self.playback_position % len(self.frames)
        start_index = int(position)
        progress = position - start_index
        end_index = (start_index + 1) % len(self.frames)
        return interpolate_frames(
            self.frames[start_index], self.frames[end_index], progress
        )

    def set_roundness(self, slider_value):
        global JOINT_ROUNDNESS
        JOINT_ROUNDNESS = slider_value / 100
        self.roundness_label.setText(f"Joint rounding: {JOINT_ROUNDNESS:.2f}")
        self.canvas.update()

    def mirror_right_to_left(self):
        frame = self.frames[self.current_index]
        frame["upper_arm_angle_l"] = 180 - frame["upper_arm_angle_r"]
        frame["forearm_angle_l"] = -frame["forearm_angle_r"]
        frame["upper_leg_angle_l"] = 180 - frame["upper_leg_angle_r"]
        frame["lower_leg_angle_l"] = -frame["lower_leg_angle_r"]
        self.refresh()

    def mirror_left_to_right(self):
        frame = self.frames[self.current_index]
        frame["upper_arm_angle_r"] = 180 - frame["upper_arm_angle_l"]
        frame["forearm_angle_r"] = -frame["forearm_angle_l"]
        frame["upper_leg_angle_r"] = 180 - frame["upper_leg_angle_l"]
        frame["lower_leg_angle_r"] = -frame["lower_leg_angle_l"]
        self.refresh()

    def refresh(self):
        self.update_frame_label()
        self.update_play_control()
        self.canvas.update()

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Frames", "animation_frames.json", "JSON (*.json)")
        if not path:
            return
        with open(path, "w") as file:
            json.dump(self.frames, file, indent=2)
        print(f"Saved to {path}")

    def copy_python_dictionary(self):
        name, accepted = QInputDialog.getText(
            self, "Copy Python Animation", "Animation key:", text="CUSTOM"
        )
        name = name.strip().upper()
        if not accepted or not name:
            return
        animation = {
            "default_seconds_per_cycle": round(
                self.speed_slider.value() * len(self.frames) / 1000, 3
            ),
            "frames": self.frames,
        }
        python_source = pprint.pformat(
            {name: animation}, sort_dicts=False, width=88
        )
        QApplication.clipboard().setText(python_source)
        self.python_copy_status.setText("Copied Python dictionary to clipboard")

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Frames", "", "JSON (*.json)")
        if not path:
            return
        with open(path, "r") as file:
            loaded = json.load(file)
        if not loaded:
            return
        self.frames = loaded
        self.current_index = 0
        self.refresh()
        print(f"Loaded from {path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = RigEditor()
    editor.show()
    sys.exit(app.exec_())