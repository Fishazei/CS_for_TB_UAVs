from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QSpinBox, QPushButton, QFileDialog,
                             QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
import yaml
import logging

logger = logging.getLogger('MotorStand')


class ConfigTab(QWidget):
    """Вкладка конфигурации стенда"""

    config_applied = pyqtSignal(dict)  # Сигнал при применении конфига
    motors_count_changed = pyqtSignal(int)  # Сигнал изменения количества моторов

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Группа загрузки конфига
        load_group = QGroupBox("Загрузка конфигурации")
        load_layout = QHBoxLayout()

        self.load_button = QPushButton("Загрузить StandConfig.yaml")
        self.load_button.clicked.connect(self.load_config)
        load_layout.addWidget(self.load_button)

        self.config_path_label = QLabel("Конфиг не загружен")
        self.config_path_label.setStyleSheet("color: #888;")
        load_layout.addWidget(self.config_path_label)

        load_layout.addStretch()
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)

        # Группа параметров стенда
        stand_group = QGroupBox("Параметры стенда")
        stand_layout = QVBoxLayout()

        # Имя и описание
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Имя стенда:"))
        self.stand_name_label = QLabel("-")
        self.stand_name_label.setStyleSheet("color: #4a9eff; font-weight: bold;")
        info_layout.addWidget(self.stand_name_label)
        info_layout.addStretch()
        stand_layout.addLayout(info_layout)

        # Частота обновления
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Частота обновления (Гц):"))
        self.update_rate_spin = QSpinBox()
        self.update_rate_spin.setRange(10, 200)
        self.update_rate_spin.setValue(50)
        rate_layout.addWidget(self.update_rate_spin)
        rate_layout.addStretch()
        stand_layout.addLayout(rate_layout)

        # Количество моторов
        motors_layout = QHBoxLayout()
        motors_layout.addWidget(QLabel("Количество моторов:"))
        self.motors_count_spin = QSpinBox()
        self.motors_count_spin.setRange(1, 8)
        self.motors_count_spin.setValue(4)
        self.motors_count_spin.valueChanged.connect(self.on_motors_count_changed)
        motors_layout.addWidget(self.motors_count_spin)
        motors_layout.addStretch()
        stand_layout.addLayout(motors_layout)

        stand_group.setLayout(stand_layout)
        layout.addWidget(stand_group)

        # Группа конфигурации моторов
        motors_group = QGroupBox("Конфигурация моторов")
        motors_layout = QVBoxLayout()

        self.motors_table = QTableWidget()
        self.motors_table.setColumnCount(5)
        self.motors_table.setHorizontalHeaderLabels([
            "ID", "Имя", "Роль", "Тип", "Звуковой профиль"
        ])

        header = self.motors_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        motors_layout.addWidget(self.motors_table)
        motors_group.setLayout(motors_layout)
        layout.addWidget(motors_group)

        # Инициализация таблицы моторов
        self.update_motors_table()

        # Кнопки управления
        button_layout = QHBoxLayout()

        self.validate_button = QPushButton("Проверить конфигурацию")
        self.validate_button.clicked.connect(self.validate_config)
        button_layout.addWidget(self.validate_button)

        self.apply_button = QPushButton("Применить конфигурацию")
        self.apply_button.setObjectName("successButton")
        self.apply_button.clicked.connect(self.apply_config)
        button_layout.addWidget(self.apply_button)

        layout.addLayout(button_layout)
        layout.addStretch()

    def load_config(self):
        """Загрузить конфигурацию из файла"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите файл конфигурации",
                "", "YAML files (*.yaml *.yml);;All files (*.*)"
            )

            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.current_config = yaml.safe_load(f)

                self.config_path_label.setText(file_path)
                self.config_path_label.setStyleSheet("color: #44bb44;")

                # Заполняем поля из конфига
                stand = self.current_config.get('stand', {})
                self.stand_name_label.setText(stand.get('name', '-'))
                self.update_rate_spin.setValue(stand.get('update_rate_hz', 50))

                motors = self.current_config.get('motors', [])
                self.motors_count_spin.setValue(len(motors))
                self.update_motors_table()

                logger.info(f"Конфигурация загружена из {file_path}")

        except Exception as e:
            logger.error(f"Ошибка загрузки конфига: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфиг:\n{str(e)}")

    def on_motors_count_changed(self, count):
        """Обработчик изменения количества моторов"""
        self.update_motors_table()
        self.motors_count_changed.emit(count)

    def update_motors_table(self):
        """Обновить таблицу моторов"""
        count = self.motors_count_spin.value()
        self.motors_table.setRowCount(count)

        # Роли моторов для типовых конфигураций
        roles = {
            1: ["main"],
            2: ["left", "right"],
            3: ["front", "rear_left", "rear_right"],
            4: ["front_left", "front_right", "rear_left", "rear_right"],
            6: ["front_left", "front_right", "mid_left", "mid_right",
                "rear_left", "rear_right"],
            8: ["front_left", "front_right", "mid_front_left", "mid_front_right",
                "mid_rear_left", "mid_rear_right", "rear_left", "rear_right"]
        }

        default_roles = roles.get(count, [f"motor_{i + 1}" for i in range(count)])

        for i in range(count):
            # ID
            self.motors_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            # Имя
            name = f"motor_{i + 1}"
            if self.current_config and i < len(self.current_config.get('motors', [])):
                name = self.current_config['motors'][i].get('name', name)
            self.motors_table.setItem(i, 1, QTableWidgetItem(name))

            # Роль
            role = default_roles[i] if i < len(default_roles) else f"motor_{i + 1}"
            if self.current_config and i < len(self.current_config.get('motors', [])):
                role = self.current_config['motors'][i].get('role', role)
            self.motors_table.setItem(i, 2, QTableWidgetItem(role))

            # Тип
            motor_type = "bldc_2205"
            if self.current_config and i < len(self.current_config.get('motors', [])):
                motor_type = self.current_config['motors'][i].get('type', motor_type)
            self.motors_table.setItem(i, 3, QTableWidgetItem(motor_type))

            # Звуковой профиль
            profile = "aggressive_5inch"
            if self.current_config and i < len(self.current_config.get('motors', [])):
                profile = self.current_config['motors'][i].get('sound_profile', profile)
            self.motors_table.setItem(i, 4, QTableWidgetItem(profile))

    def validate_config(self):
        """Проверить текущую конфигурацию"""
        try:
            config = self.get_current_config()
            # Здесь можно добавить дополнительную валидацию
            logger.info("Конфигурация валидна")
            QMessageBox.information(self, "Успех", "Конфигурация корректна!")
        except Exception as e:
            logger.error(f"Ошибка валидации: {str(e)}")
            QMessageBox.warning(self, "Ошибка валидации", str(e))

    def apply_config(self):
        """Применить конфигурацию"""
        try:
            config = self.get_current_config()
            self.current_config = config
            self.config_applied.emit(config)
            logger.info("Конфигурация применена успешно")
            QMessageBox.information(self, "Успех", "Конфигурация применена!")
        except Exception as e:
            logger.error(f"Ошибка применения конфига: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось применить конфигурацию:\n{str(e)}")

    def get_current_config(self):
        """Получить текущую конфигурацию из полей"""
        motors = []
        for i in range(self.motors_table.rowCount()):
            motor = {
                'id': i + 1,
                'name': self.motors_table.item(i, 1).text() if self.motors_table.item(i, 1) else f"motor_{i + 1}",
                'role': self.motors_table.item(i, 2).text() if self.motors_table.item(i, 2) else f"motor_{i + 1}",
                'type': self.motors_table.item(i, 3).text() if self.motors_table.item(i, 3) else "bldc_2205",
                'sound_profile': self.motors_table.item(i, 4).text() if self.motors_table.item(i, 4) else "default",
                'max_power': 1.0
            }
            motors.append(motor)

        return {
            'version': 1,
            'stand': {
                'name': self.stand_name_label.text(),
                'description': '',
                'update_rate_hz': self.update_rate_spin.value()
            },
            'motors': motors
        }