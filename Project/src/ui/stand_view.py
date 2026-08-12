import math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import QWidget

class StandViewWidget(QWidget):
    """
    Виджет для 2D-визуализации схемы стенда дрона.
    Отображает раму, центры двигателей, винты (с направлением вращения CW/CCW),
    а также блок псевдодатчиков и текущую телеметрию.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_data = None
        self.telemetry_data = {}  # Для будущего вывода телеметрии в прямом эфире
        self.setMinimumSize(350, 350)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")

    def set_config(self, config_dict: dict):
        """Обновляет конфигурацию и перерисовывает схему стенда."""
        self.config_data = config_dict
        self.update()

    def update_telemetry(self, telemetry: dict):
        """Обновляет живые данные с ПК / физической модели."""
        self.telemetry_data = telemetry
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Отрисовка фона и сетки
        painter.fillRect(self.rect(), QColor("#121212"))
        self._draw_grid(painter, w, h)

        if not self.config_data or "motors" not in self.config_data:
            painter.setPen(QColor("#777777"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(self.rect(), Qt.AlignCenter, "Конфигурация не применена\nЗагрузите и примените config.yaml")
            return

        # Центр виджета
        center_x = w / 2.0
        center_y = h / 2.0

        motors = self.config_data.get("motors", [])
        physics = self.config_data.get("physics", {})
        motor_prof = self.config_data.get("motor_profile", {})
        propeller = motor_prof.get("propeller", {})

        # Вычисляем масштаб исходя из радиусов расположения моторов
        max_dist = 0.1
        for m in motors:
            pos = m.get("position_m", [0, 0, 0])
            dist = math.hypot(pos[0], pos[1])
            if dist > max_dist:
                max_dist = dist

        scale = (min(w, h) / 2.0 * 0.60) / max_dist

        # 1. Отрисовка лучей от центра масс к моторам
        pen_arm = QPen(QColor("#4A90E2"), 4, Qt.SolidLine)
        painter.setPen(pen_arm)
        for m in motors:
            pos = m.get("position_m", [0, 0, 0])
            mx = center_x + pos[1] * scale
            my = center_y - pos[0] * scale
            painter.drawLine(QPointF(center_x, center_y), QPointF(mx, my))

        # 2. Отрисовка центрального блока (ЦМ / Псевдодатчики)
        cb_radius = 22
        painter.setPen(QPen(QColor("#00E676"), 2))
        painter.setBrush(QBrush(QColor(0, 230, 118, 40)))
        painter.drawEllipse(QPointF(center_x, center_y), cb_radius, cb_radius)

        # Ориентация носа дрона (Стрелка Вперед / +X)
        painter.setPen(QPen(QColor("#FF5252"), 3))
        painter.drawLine(QPointF(center_x, center_y), QPointF(center_x, center_y - cb_radius - 12))
        painter.drawText(int(center_x - 12), int(center_y - cb_radius - 16), "FORWARD (+X)")

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(QRectF(center_x - cb_radius, center_y - 10, cb_radius*2, 20), Qt.AlignCenter, "IMU / FC")

        # 3. Отрисовка моторов и пропеллеров
        prop_diam_in = propeller.get("diameter_inches", 5.0)
        prop_radius_px = (prop_diam_in * 0.0254 / 2.0) * scale

        for m in motors:
            pos = m.get("position_m", [0, 0, 0])
            m_id = m.get("id", 0)
            spin = m.get("spin_direction", "CW")

            mx = center_x + pos[1] * scale
            my = center_y - pos[0] * scale

            # Окружность пропеллера
            is_cw = (spin.upper() == "CW")
            prop_color = QColor(255, 152, 0, 70) if is_cw else QColor(33, 150, 243, 70)
            border_color = QColor("#FF9800") if is_cw else QColor("#2196F3")

            painter.setPen(QPen(border_color, 1.5, Qt.DashLine))
            painter.setBrush(QBrush(prop_color))
            painter.drawEllipse(QPointF(mx, my), prop_radius_px, prop_radius_px)

            # Окружность самого мотора
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawEllipse(QPointF(mx, my), 12, 12)

            # Текст ID и направления
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(QRectF(mx - 15, my - 8, 30, 16), Qt.AlignCenter, f"M{m_id}")

            painter.setFont(QFont("Consolas", 8))
            painter.setPen(border_color)
            painter.drawText(int(mx + prop_radius_px * 0.7), int(my), spin)

        # 4. Вывод информационного блока характеристик стенда
        self._draw_info_overlay(painter, physics, motor_prof, len(motors))

    def _draw_grid(self, painter, w, h):
        pen = QPen(QColor("#222222"), 1, Qt.DotLine)
        painter.setPen(pen)
        step = 40
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

    def _draw_info_overlay(self, painter, physics, motor_prof, motor_count):
        painter.setFont(QFont("Consolas", 9))
        info_text = (
            f"=== Свойства стенда ===\n"
            f"Моторов: {motor_count}\n"
            f"Масса: {physics.get('total_weight_kg', 'N/A')} кг\n"
            f"Моторы: {motor_prof.get('motor_type', 'N/A')}\n"
            f"Винты: {motor_prof.get('propeller', {}).get('diameter_inches', '?')}\" "
            f"({motor_prof.get('propeller', {}).get('blades_count', '?')}-blade)\n"
            f"IMU/Датчики: Активны [HIL]"
        )

        rect = QRectF(10, 10, 240, 105)
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.drawRoundedRect(rect, 5, 5)

        painter.setPen(QColor("#CCCCCC"))
        painter.drawText(rect.adjusted(8, 6, -8, -6), Qt.AlignLeft | Qt.AlignTop, info_text)