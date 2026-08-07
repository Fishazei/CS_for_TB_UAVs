from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QMessageBox, QSplitter, QLabel,
                             QComboBox, QGroupBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import logging
import numpy as np

from src.ui.command_list_widget import CommandListWidget
from src.ui.motor_graph_widget import MotorGraphWidget
from src.core.transition_engine import TransitionType

logger = logging.getLogger('MotorStand')


class ScenarioTab(QWidget):
    """Вкладка управления сценариями"""

    scenario_loaded = pyqtSignal(dict)  # Данные сценария
    play_requested = pyqtSignal()  # Запрос на воспроизведение
    stop_requested = pyqtSignal()  # Запрос на остановку

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_scenario = None
        self.is_playing = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback)
        self.playback_time = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель управления
        control_panel = QHBoxLayout()

        # Группа загрузки/сохранения
        file_group = QGroupBox("Файл сценария")
        file_layout = QHBoxLayout()

        self.load_button = QPushButton("Загрузить")
        self.load_button.clicked.connect(self.load_scenario)
        file_layout.addWidget(self.load_button)

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_scenario)
        file_layout.addWidget(self.save_button)

        self.scenario_name_label = QLabel("Сценарий не загружен")
        self.scenario_name_label.setStyleSheet("color: #888;")
        file_layout.addWidget(self.scenario_name_label)

        file_group.setLayout(file_layout)
        control_panel.addWidget(file_group)

        # Группа генерации профилей
        generate_group = QGroupBox("Генерация")
        generate_layout = QHBoxLayout()

        generate_layout.addWidget(QLabel("Тип перехода:"))
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(["smooth", "linear", "none"])
        generate_layout.addWidget(self.transition_combo)

        self.generate_button = QPushButton("Сгенерировать профили")
        self.generate_button.clicked.connect(self.generate_profiles)
        generate_layout.addWidget(self.generate_button)

        generate_group.setLayout(generate_layout)
        control_panel.addWidget(generate_group)

        # Группа управления воспроизведением
        play_group = QGroupBox("Воспроизведение")
        play_layout = QHBoxLayout()

        self.play_button = QPushButton("▶ Воспроизвести")
        self.play_button.setObjectName("successButton")
        self.play_button.clicked.connect(self.toggle_playback)
        play_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("■ Стоп")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        play_layout.addWidget(self.stop_button)

        play_group.setLayout(play_layout)
        control_panel.addWidget(play_group)

        layout.addLayout(control_panel)

        # Прогресс-бар воспроизведения
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                text-align: center;
                color: #ccc;
                background-color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Основной сплиттер
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель - список команд
        self.command_list = CommandListWidget()
        self.command_list.commands_changed.connect(self.on_commands_changed)
        splitter.addWidget(self.command_list)

        # Правая панель - графики
        self.motor_graph = MotorGraphWidget()
        splitter.addWidget(self.motor_graph)

        # Устанавливаем соотношение сторон
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

    def update_motor_graphs(self, motor_count: int):
        """Обновить графики при изменении количества моторов"""
        motor_names = {i + 1: f"Мотор {i + 1}" for i in range(motor_count)}
        self.motor_graph.create_motor_plots(motor_count, motor_names)

    def load_scenario(self):
        """Загрузить сценарий из файла"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите файл сценария",
                "", "YAML files (*.yaml *.yml);;All files (*.*)"
            )

            if file_path:
                # Здесь должна быть загрузка через ScenarioManager
                # Пока просто эмулируем
                logger.info(f"Сценарий загружен из {file_path}")
                self.scenario_name_label.setText(file_path.split('/')[-1])
                self.scenario_name_label.setStyleSheet("color: #44bb44;")
                QMessageBox.information(self, "Успех", "Сценарий загружен!")

        except Exception as e:
            logger.error(f"Ошибка загрузки сценария: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сценарий:\n{str(e)}")

    def save_scenario(self):
        """Сохранить сценарий в файл"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить сценарий",
                "scenario.yaml", "YAML files (*.yaml *.yml);;All files (*.*)"
            )

            if file_path:
                # Здесь должно быть сохранение через ScenarioManager
                logger.info(f"Сценарий сохранен в {file_path}")
                QMessageBox.information(self, "Успех", "Сценарий сохранен!")

        except Exception as e:
            logger.error(f"Ошибка сохранения сценария: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить сценарий:\n{str(e)}")

    def on_commands_changed(self, commands):
        """Обработчик изменения списка команд"""
        logger.debug(f"Список команд обновлен: {len(commands)} команд")
        # Здесь можно автоматически перегенерировать профили

    def generate_profiles(self):
        """Сгенерировать профили мощности"""
        try:
            transition_type = TransitionType[self.transition_combo.currentText().upper()]
            logger.info(f"Генерация профилей с типом перехода: {transition_type.value}")

            # Здесь должен быть вызов генерации через ScenarioManager
            # Пока создадим тестовые данные
            motor_count = 4  # Должно браться из текущего конфига
            time_points = np.linspace(0, 5000, 500)

            # Генерируем тестовые профили
            motor_profiles = {}
            for i in range(motor_count):
                motor_id = i + 1
                # Разные профили для разных моторов
                base = np.sin(time_points / 1000 * np.pi * (i + 1)) * 0.3 + 0.6
                motor_profiles[motor_id] = np.clip(base, 0, 1)

            # Обновляем графики
            maneuver_times = [
                (1000, "Висение"),
                (2000, "Подъем"),
                (3500, "Крен")
            ]

            self.motor_graph.update_profiles(time_points, motor_profiles, maneuver_times)
            logger.info("Профили сгенерированы успешно")

        except Exception as e:
            logger.error(f"Ошибка генерации профилей: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать профили:\n{str(e)}")

    def toggle_playback(self):
        """Запуск/пауза воспроизведения"""
        if not self.is_playing:
            self.start_playback()
        else:
            self.pause_playback()

    def start_playback(self):
        """Начать воспроизведение"""
        self.is_playing = True
        self.play_button.setText("⏸ Пауза")
        self.stop_button.setEnabled(True)
        self.playback_time = 0
        self.playback_timer.start(20)  # 50 Hz
        logger.info("Воспроизведение начато")

    def pause_playback(self):
        """Приостановить воспроизведение"""
        self.is_playing = False
        self.play_button.setText("▶ Продолжить")
        self.playback_timer.stop()
        logger.info("Воспроизведение приостановлено")

    def stop_playback(self):
        """Остановить воспроизведение"""
        self.is_playing = False
        self.play_button.setText("▶ Воспроизвести")
        self.stop_button.setEnabled(False)
        self.playback_timer.stop()
        self.playback_time = 0
        self.motor_graph.update_time_indicator(0)
        self.progress_bar.setValue(0)
        logger.info("Воспроизведение остановлено")

    def update_playback(self):
        """Обновить индикатор воспроизведения"""
        self.playback_time += 20
        self.motor_graph.update_time_indicator(self.playback_time)

        # Обновляем прогресс-бар
        if hasattr(self, 'total_duration') and self.total_duration > 0:
            progress = int((self.playback_time / self.total_duration) * 100)
            self.progress_bar.setValue(min(progress, 100))

        # Проверяем окончание
        if hasattr(self, 'total_duration') and self.playback_time >= self.total_duration:
            self.stop_playback()