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
    title_label.setStyleSheet("color: #000000; margin-bottom: 2px;")
    right_layout.addWidget(title_label)

    # 2. Краткая характеристика стенда (По центру)
    self.info_card = QFrame()
    self.info_card.setStyleSheet(
        "QFrame { background-color: #1a1a1a; border: 1px solid #333333;"
        " border-radius: 6px; padding: 4px; }"
    )
    info_card_layout = QGridLayout(self.info_card)
    info_card_layout.setContentsMargins(8, 6, 8, 6)

    self.lbl_info_motors = QLabel("Моторы: -- / --")
    self.lbl_info_mass = QLabel("Масса: --")
    self.lbl_info_prop = QLabel("Винты: -- / --")
    self.lbl_info_sensors = QLabel("Датчики: --")

    lbl_font = QFont("Consolas", 9)
    for lbl in [
        self.lbl_info_motors,
        self.lbl_info_mass,
        self.lbl_info_prop,
        self.lbl_info_sensors,
    ]:
        lbl.setFont(lbl_font)
        lbl.setStyleSheet("color: #E0E0E0;")

    # Сетка 2x2
    info_card_layout.addWidget(self.lbl_info_motors, 0, 0)
    info_card_layout.addWidget(self.lbl_info_mass, 0, 1)
    info_card_layout.addWidget(self.lbl_info_prop, 1, 0)
    info_card_layout.addWidget(self.lbl_info_sensors, 1, 1)

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
    # 1. Моторы: кол-во / модель
    motors_list = data.get("motors", [])
    motors_cnt = len(motors_list)

    motor_profile = data.get("motor_profile", {})
    motor_model = motor_profile.get("motor_type", "Н/Д")

    # Запасной вариант: берем модель из первого элемента списка моторов
    if (
            motor_model == "Н/Д"
            and motors_list
            and isinstance(motors_list[0], dict)
    ):
        motor_model = motors_list[0].get("model", "Н/Д")

    # 2. Масса
    mass = data.get("physics", {}).get("total_weight_kg", "Н/Д")
    mass_str = f"{mass} кг" if mass != "Н/Д" else "Н/Д"

    # 3. Винты: диаметр / кол-во лопастей
    prop = motor_profile.get("propeller", {})
    prop_diam = prop.get("diameter_inches", "?")
    prop_blades = prop.get("blades", prop.get("blades_count", "?"))

    # 4. Датчики (поддержка списка строк или списка словарей)
    sensors_raw = data.get("sensors", [])
    if isinstance(sensors_raw, list):
        sensor_names = []
        for s in sensors_raw:
            if isinstance(s, dict):
                sensor_names.append(s.get("type", s.get("name", "Датчик")))
            else:
                sensor_names.append(str(s))
        sensors_str = ", ".join(sensor_names) if sensor_names else "Отсутствуют"
    elif isinstance(sensors_raw, dict):
        sensors_str = ", ".join(sensors_raw.keys())
    else:
        sensors_str = str(sensors_raw) if sensors_raw else "Отсутствуют"

    # Форматирование текста
    self.lbl_info_motors.setText(f"Моторы: {motors_cnt} / {motor_model}")
    self.lbl_info_mass.setText(f"Масса: {mass_str}")
    self.lbl_info_prop.setText(
        f"Винты: {prop_diam}\" / {prop_blades} лоп."
    )
    self.lbl_info_sensors.setText(f"Датчики: {sensors_str}")

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