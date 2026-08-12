import os
import sys
import yaml
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.ui.stand_view import StandViewWidget


class ConfigTab(QWidget):

  config_applied = Signal(dict)

  def __init__(self, parent=None):
    super().__init__(parent)
    self.current_file_path = None
    self.init_ui()

  def init_ui(self):
    main_layout = QVBoxLayout(self)
    splitter = QSplitter()

    # --- Левая панель: Редактор и консоль ---
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)

    file_layout = QHBoxLayout()
    self.file_path_input = QLineEdit()
    self.file_path_input.setPlaceholderText(
        "Выберите файл конфигурации (.yaml / .json)..."
    )
    self.file_path_input.setReadOnly(True)

    btn_browse = QPushButton("Обзор...")
    btn_browse.clicked.connect(self.browse_file)

    btn_save = QPushButton("Сохранить")
    btn_save.clicked.connect(self.save_file)

    btn_apply = QPushButton("Применить конфиг")
    btn_apply.setStyleSheet(
        "background-color: #2e7d32; color: white; font-weight: bold;"
    )
    btn_apply.clicked.connect(self.apply_config)

    file_layout.addWidget(QLabel("Файл:"))
    file_layout.addWidget(self.file_path_input)
    file_layout.addWidget(btn_browse)
    file_layout.addWidget(btn_save)
    file_layout.addWidget(btn_apply)

    left_layout.addLayout(file_layout)

    self.config_editor = QTextEdit()
    font = QFont("Consolas" if sys.platform == "win32" else "Monospace", 10)
    self.config_editor.setFont(font)
    left_layout.addWidget(self.config_editor)

    left_layout.addWidget(QLabel("Лог событий редактора:"))
    self.log_console = QTextEdit()
    self.log_console.setReadOnly(True)
    self.log_console.setMaximumHeight(120)
    self.log_console.setFont(font)
    self.log_console.setStyleSheet(
        "background-color: #1e1e1e; color: #00ff00;"
    )
    left_layout.addWidget(self.log_console)

    # --- Правая панель: Заголовок -> Характеристики -> Схема ---
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)

    # 1. Заголовок (Компактный сверху)
    title_label = QLabel("КОНФИГУРАЦИЯ И СХЕМА СТЕНДА")
    title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
    title_label.setStyleSheet("color: #4A90E2; margin-bottom: 2px;")
    right_layout.addWidget(title_label)

    # 2. Краткая характеристика стенда (По центру)
    self.info_card = QFrame()
    self.info_card.setStyleSheet(
        "QFrame { background-color: #1a1a1a; border: 1px solid #333333;"
        " border-radius: 6px; padding: 4px; }"
    )
    info_card_layout = QGridLayout(self.info_card)

    self.lbl_info_name = QLabel("Модель: --")
    self.lbl_info_mass = QLabel("Масса: -- кг")
    self.lbl_info_motors = QLabel("Моторов: --")
    self.lbl_info_prop = QLabel("Винты: --")

    lbl_font = QFont("Consolas", 9)
    for lbl in [
        self.lbl_info_name,
        self.lbl_info_mass,
        self.lbl_info_motors,
        self.lbl_info_prop,
    ]:
      lbl.setFont(lbl_font)
      lbl.setStyleSheet("color: #E0E0E0;")

    info_card_layout.addWidget(self.lbl_info_name, 0, 0)
    info_card_layout.addWidget(self.lbl_info_mass, 0, 1)
    info_card_layout.addWidget(self.lbl_info_motors, 1, 0)
    info_card_layout.addWidget(self.lbl_info_prop, 1, 1)

    right_layout.addWidget(self.info_card)

    # 3. Схема стенда (Снизу, занимает все оставшееся место)
    self.stand_view = StandViewWidget()
    right_layout.addWidget(self.stand_view, stretch=1)

    splitter.addWidget(left_widget)
    splitter.addWidget(right_widget)
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 1)

    main_layout.addWidget(splitter)

  def update_info_card(self, data: dict):
    """Обновляет блок кратких характеристик."""
    name = data.get("drone_name", "Н/Д")
    mass = data.get("physics", {}).get("total_weight_kg", "Н/Д")
    motors_cnt = len(data.get("motors", []))

    prop = data.get("motor_profile", {}).get("propeller", {})
    prop_str = f"{prop.get('diameter_inches', '?')}\"x{prop.get('pitch_inches', '?')}"

    self.lbl_info_name.setText(f"Модель: {name}")
    self.lbl_info_mass.setText(f"Масса: {mass} кг")
    self.lbl_info_motors.setText(f"Моторов: {motors_cnt}")
    self.lbl_info_prop.setText(f"Винты: {prop_str}")

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
        self.config_editor.setText(f.read())
      self.log_console.append(
          f"[INFO] Файл загружен: {os.path.basename(path)}"
      )
    except Exception as e:
      self.log_console.append(f"[ERROR] Ошибка загрузки: {e}")

  def save_file(self):
    if not self.current_file_path:
      file_path, _ = QFileDialog.getSaveFileName(
          self,
          "Сохранить конфигурацию",
          "config.yaml",
          "YAML Files (*.yaml *.yml);;JSON Files (*.json)",
      )
      if not file_path:
        return
      self.current_file_path = file_path
      self.file_path_input.setText(file_path)

    try:
      with open(self.current_file_path, "w", encoding="utf-8") as f:
        f.write(self.config_editor.toPlainText())
      self.log_console.append(
          f"[INFO] Сохранено: {os.path.basename(self.current_file_path)}"
      )
    except Exception as e:
      self.log_console.append(f"[ERROR] Ошибка сохранения: {e}")

  def apply_config(self):
    raw_text = self.config_editor.toPlainText().strip()
    if not raw_text:
      QMessageBox.warning(
          self, "Ошибка", "Нельзя применить пустую конфигурацию!"
      )
      return

    try:
      parsed_data = yaml.safe_load(raw_text)
      if not isinstance(parsed_data, dict):
        raise ValueError("Структура должна быть словарем!")

      # Обновляем схему и карточку характеристик
      self.stand_view.set_config(parsed_data)
      self.update_info_card(parsed_data)

      self.config_applied.emit(parsed_data)
      self.log_console.append(
          f"[INFO] Конфигурация '{parsed_data.get('drone_name', 'Drone')}'"
          " применена!"
      )
    except Exception as e:
      self.log_console.append(f"[ERROR] Ошибка валидации: {e}")
      QMessageBox.critical(
          self, "Ошибка", f"Не удалось применить конфигурацию:\n{e}"
      )