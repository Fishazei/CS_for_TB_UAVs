from enum import Enum
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
)


class StandStatus(Enum):
  OFF = ("ВЫКЛЮЧЕН", "#616161")
  CONNECTING = ("ПОДКЛЮЧАЕТСЯ...", "#FFB300")
  READY = ("ОЖИДАЕТ ЗАПУСКА", "#29B6F6")
  WORKING = ("РАБОТАЕТ", "#66BB6A")
  ERROR = ("ОШИБКА СВЯЗИ", "#EF5350")
  FAULT = ("ПОЛОМКА / АВАРИЯ", "#B71C1C")


class ConnectionBar(QWidget):
  """Сквозная панель подключения к полётному контроллеру."""

  connect_requested = Signal()
  disconnect_requested = Signal()

  def __init__(self, parent=None):
    super().__init__(parent)
    self.current_status = StandStatus.OFF
    self.init_ui()

  def init_ui(self):
    layout = QHBoxLayout(self)
    layout.setContentsMargins(12, 6, 12, 6)

    # Контейнер-рамка для визуального выделения
    frame = QFrame()
    frame.setStyleSheet(
        "QFrame { background-color: #ffffff; border: 0.5px solid #ffffff;"
        " border-radius: 4px; }"
    )
    frame_layout = QHBoxLayout(frame)
    frame_layout.setContentsMargins(12, 6, 12, 6)

    # 1. Светодиодный индикатор
    self.led_indicator = QLabel()
    self.led_indicator.setFixedSize(14, 14)

    # 2. Текст статуса
    self.status_label = QLabel()
    self.status_label.setFont(QFont("Consolas", 10, QFont.Bold))

    # 3. Скорость передачи данных
    self.speed_label = QLabel("Скорость: 0.0 КБ/с")
    self.speed_label.setFont(QFont("Consolas", 9))
    self.speed_label.setStyleSheet("color: #888888; margin-left: 15px;")

    # 4. Кнопки управления
    self.btn_connect = QPushButton("Подключить ПК")
    self.btn_connect.setStyleSheet(
        "QPushButton { background-color: #1976D2; color: white; font-weight:"
        " bold; padding: 5px 12px; }"
        "QPushButton:hover { background-color: #1565C0; }"
    )
    self.btn_connect.clicked.connect(self.connect_requested.emit)

    self.btn_disconnect = QPushButton("Принудительно отключить")
    self.btn_disconnect.setStyleSheet(
        "QPushButton { background-color: #d32f2f; color: white; font-weight:"
        " bold; padding: 5px 12px; }"
        "QPushButton:hover { background-color: #c62828; }"
    )
    self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)

    # Размещение элементов
    frame_layout.addWidget(QLabel("Статус FC:"))
    frame_layout.addWidget(self.led_indicator)
    frame_layout.addWidget(self.status_label)
    frame_layout.addWidget(self.speed_label)
    frame_layout.addStretch()
    frame_layout.addWidget(self.btn_connect)
    frame_layout.addWidget(self.btn_disconnect)

    layout.addWidget(frame)
    self.set_status(StandStatus.OFF)

  def set_status(self, status: StandStatus):
    """Обновляет состояние индикатора и активность кнопок."""
    self.current_status = status
    text, color = status.value

    # Стилизация круглого индикатора
    self.led_indicator.setStyleSheet(
        f"background-color: {color}; border-radius: 7px; border: 1px solid"
        " #ffffff;"
    )
    self.status_label.setText(text)
    self.status_label.setStyleSheet(f"color: {color};")

    # Отображение скорости актуально только в режиме работы
    if status != StandStatus.WORKING:
      self.speed_label.setText("Скорость: -- КБ/с")

  def set_transfer_speed(self, speed_kbps: float):
    """Обновляет отображаемую скорость передачи данных."""
    if self.current_status == StandStatus.WORKING:
      self.speed_label.setText(f"Скорость: {speed_kbps:.1f} КБ/с")