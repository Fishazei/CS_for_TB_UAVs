"""
import os
import sys
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
  # Сигнал, передающий текст конфигурации при нажатии "Применить"
  config_applied = Signal(str)

  def __init__(self):
    super().__init__()
    self.current_file_path = None
    self.init_ui()

  def init_ui(self):
    self.setWindowTitle(
        "HIL Testbed Control Panel — Система управления стендом"
    )
    self.resize(1000, 700)

    # Главный виджет с вкладками
    self.tabs = QTabWidget()
    self.setCentralWidget(self.tabs)

    # Создаем вкладку конфигурации
    self.tab_config = QWidget()
    self.init_config_tab()

    # Заглушка под вторую вкладку
    self.tab_scenarios = QWidget()
    self.init_scenarios_tab()

    # Добавляем вкладки
    self.tabs.addTab(self.tab_config, "Настройка конфигурации")
    self.tabs.addTab(
        self.tab_scenarios, "Формирование и запуск сценариев (В разработке)"
    )

  def init_config_tab(self):
    layout = QVBoxLayout()

    # --- Верхняя панель управления файлами ---
    file_layout = QHBoxLayout()

    self.file_path_input = QLineEdit()
    self.file_path_input.setPlaceholderText("Выберите файл конфигурации...")
    self.file_path_input.setReadOnly(True)

    btn_browse = QPushButton("Обзор...")
    btn_browse.clicked.connect(self.browse_file)

    btn_save = QPushButton("Сохранить")
    btn_save.clicked.connect(self.save_file)

    btn_apply = QPushButton("Применить конфигурацию")
    # Выделяем главную кнопку цветом
    btn_apply.setStyleSheet(
        "background-color: #2e7d32; color: white; font-weight: bold;"
    )
    btn_apply.clicked.connect(self.apply_config)

    file_layout.addWidget(QLabel("Файл:"))
    file_layout.addWidget(self.file_path_input)
    file_layout.addWidget(btn_browse)
    file_layout.addWidget(btn_save)
    file_layout.addWidget(btn_apply)

    layout.addLayout(file_layout)

    # --- Текстовый редактор конфигурации ---
    self.config_editor = QTextEdit()
    # Устанавливаем моноширинный шрифт для удобного чтения YAML/JSON
    font = QFont("Consolas" if sys.platform == "win32" else "Monospace", 11)
    self.config_editor.setFont(font)
    self.config_editor.setPlaceholderText(
        "Откройте файл конфигурации (.yaml / .json) или введите параметры"
        " вручную..."
    )

    layout.addWidget(self.config_editor)

    # --- Консоль логов ---
    layout.addWidget(QLabel("Лог событий:"))
    self.log_console = QTextEdit()
    self.log_console.setReadOnly(True)
    self.log_console.setMaximumHeight(150)
    self.log_console.setFont(font)
    self.log_console.setStyleSheet(
        "background-color: #1e1e1e; color: #00ff00;"
    )

    layout.addWidget(self.log_console)

    self.tab_config.setLayout(layout)
    self.log_info("Интерфейс инициализирован.")

  def init_scenarios_tab(self):
    layout = QVBoxLayout()
    label = QLabel("Здесь будет интерфейс выполнения сценариев и графика")
    layout.addWidget(label)
    self.tab_scenarios.setLayout(layout)

  # --- Вспомогательные методы и слоты ---

  def log_info(self, message: str):
    self.log_console.append(f"[INFO] {message}")

  def log_error(self, message: str):
    self.log_console.append(f"[ERROR] {message}")

  def browse_file(self):
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Выберите файл конфигурации",
        "",
        "Config Files (*.yaml *.yml *.json);;All Files (*)",
    )
    if file_path:
      self.current_file_path = file_path
      self.file_path_input.setText(file_path)
      self.load_file(file_path)

  def load_file(self, path: str):
    try:
      with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        self.config_editor.setText(content)
      self.log_info(f"Файл успешно загружен: {path}")
    except Exception as e:
      self.log_error(f"Ошибка при чтении файла: {e}")

  def save_file(self):
    if not self.current_file_path:
      # Если файл еще не выбирался, открываем "Сохранить как"
      file_path, _ = QFileDialog.getSaveFileName(
          self,
          "Сохранить конфигурацию",
          "config.yaml",
          "YAML Files (*.yaml *.yml);;JSON Files (*.json);;All Files (*)",
      )
      if not file_path:
        return
      self.current_file_path = file_path
      self.file_path_input.setText(file_path)

    try:
      content = self.config_editor.toPlainText()
      with open(self.current_file_path, "w", encoding="utf-8") as f:
        f.write(content)
      self.log_info(f"Конфигурация сохранена в файл: {self.current_file_path}")
    except Exception as e:
      self.log_error(f"Ошибка при сохранении файла: {e}")

  def apply_config(self):
    content = self.config_editor.toPlainText().strip()
    if not content:
      QMessageBox.warning(
          self, "Предупреждение", "Нельзя применить пустую конфигурацию!"
      )
      self.log_error("Попытка применить пустую конфигурацию.")
      return

    self.log_info("Применение конфигурации к физической модели...")
    # Генерируем сигнал (в будущем его подхватит физмодель / сервис)
    self.config_applied.emit(content)
"""
import random

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from src.ui.config_tab import ConfigTab
from src.ui.scenario_tab import ScenarioTab
from src.ui.connection_bar import ConnectionBar, StandStatus

class MainWindow(QMainWindow):

  def __init__(self):
    super().__init__()
    self.init_ui()

  def init_ui(self):
    self.setWindowTitle(
        "HIL Stand Control Panel — Система управления стендом"
    )
    self.resize(1150, 800)

    # Главный контейнер
    central_widget = QWidget()
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(8, 8, 8, 8)
    self.setCentralWidget(central_widget)

    # 1. Сквозная панель подключения (видна в любом окне)
    self.connection_bar = ConnectionBar()
    self.connection_bar.connect_requested.connect(self.on_connect)
    self.connection_bar.disconnect_requested.connect(self.on_disconnect)
    main_layout.addWidget(self.connection_bar)

    # 2. Вкладки приложения
    self.tabs = QTabWidget()
    self.config_tab = ConfigTab()
    self.scenario_tab = ScenarioTab()

    self.config_tab.config_applied.connect(self.on_config_applied)

    self.tabs.addTab(self.config_tab, "Настройка конфигурации")
    self.tabs.addTab(self.scenario_tab, "Сценарии и Мониторинг")
    main_layout.addWidget(self.tabs)

    # Таймер для демонстрации эмуляции скорости передачи
    self.speed_timer = QTimer()
    self.speed_timer.setInterval(200)
    self.speed_timer.timeout.connect(self._update_speed_mock)

  def on_connect(self):
    """Имитация процесса подключения к ПК."""
    self.connection_bar.set_status(StandStatus.CONNECTING)
    # Через 1.5 сек переводим в статус READY
    QTimer.singleShot(
        1500, lambda: self.connection_bar.set_status(StandStatus.READY)
    )

  def on_disconnect(self):
    """Принудительное отключение."""
    self.speed_timer.stop()
    self.connection_bar.set_status(StandStatus.OFF)

  def on_config_applied(self, config_dict: dict):
    motors = config_dict.get("motors", [])
    self.scenario_tab.update_motor_count(len(motors))

    # Если контроллер был подключен, при запуске работы меняем статус
    if self.connection_bar.current_status == StandStatus.READY:
      self.connection_bar.set_status(StandStatus.WORKING)
      self.speed_timer.start()

  def _update_speed_mock(self):
    """Генерация псевдо-данных скорости потока MAVLink."""
    fake_speed = random.uniform(112.0, 128.5)
    self.connection_bar.set_transfer_speed(fake_speed)