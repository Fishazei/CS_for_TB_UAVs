import os
import sys
import yaml
import numpy as np
from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QSplitter, QGridLayout
)
import pyqtgraph as pg

# Настройка стиля графиков pyqtgraph под темную тему
pg.setConfigOption('background', '#121212')
pg.setConfigOption('foreground', '#CCCCCC')


class ScenarioTab(QWidget):
    """
    Вкладка загрузки, редактирования и исполнения сценариев,
    а также отслеживания оборотов моторов в реальном времени.
    """
    scenario_started = Signal(dict)
    scenario_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file_path = None
        self.is_running = False
        self.motor_count = 4  # По умолчанию 4 мотора (обновляется из конфига)

        # Буферы данных для графиков (Ось X: Время, Ось Y: Обороты)
        self.buffer_size = 200
        self.time_data = np.linspace(-10, 0, self.buffer_size)
        self.target_rpm_data = {}
        self.actual_rpm_data = {}

        # Графические объекты
        self.plots = {}
        self.curves_target = {}
        self.curves_actual = {}

        self.init_ui()
        self.init_buffers()

        # Таймер эмуляции данных (для теста интерфейса до подключения HIL-модели)
        self.sim_timer = QTimer()
        self.sim_timer.setInterval(50)  # 20 Гц обновление
        self.sim_timer.timeout.connect(self._emulate_telemetry_step)

    def init_buffers(self):
        """Инициализация буферов данных под текущее число моторов."""
        self.target_rpm_data = {i: np.zeros(self.buffer_size) for i in range(1, self.motor_count + 1)}
        self.actual_rpm_data = {i: np.zeros(self.buffer_size) for i in range(1, self.motor_count + 1)}

    def update_motor_count(self, count: int):
        """Перестраивает сетку графиков при изменении конфигурации стенда."""
        if count != self.motor_count:
            self.motor_count = count
            self.init_buffers()
            self._rebuild_plots_grid()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter()

        # --- Левая панель: Редактор сценария ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Выберите файл сценария (.yaml / .json)...")
        self.file_path_input.setReadOnly(True)

        btn_browse = QPushButton("Обзор...")
        btn_browse.clicked.connect(self.browse_file)

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_file)

        self.btn_run = QPushButton("Запустить сценарий")
        self.btn_run.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_run.clicked.connect(self.toggle_scenario)

        file_layout.addWidget(QLabel("Сценарий:"))
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(btn_browse)
        file_layout.addWidget(btn_save)
        file_layout.addWidget(self.btn_run)

        left_layout.addLayout(file_layout)

        # Текстовый редактор
        self.scenario_editor = QTextEdit()
        font = QFont("Consolas" if sys.platform == "win32" else "Monospace", 10)
        self.scenario_editor.setFont(font)
        self.scenario_editor.setPlaceholderText("Загрузите yaml/json файл сценария...")
        left_layout.addWidget(self.scenario_editor)

        # Консоль логов сценариста
        left_layout.addWidget(QLabel("Лог выполнения сценария:"))
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(120)
        self.log_console.setFont(font)
        self.log_console.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        left_layout.addWidget(self.log_console)

        # --- Правая панель: Графики моторов ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("Обороты моторов (Target vs Actual RPM):"))

        # Контейнер для сетки графиков
        self.plots_container = QWidget()
        self.plots_grid = QGridLayout(self.plots_container)
        self.plots_grid.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.plots_container)

        self._rebuild_plots_grid()

        # Добавляем левую и правую панели в Splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        self.log_info("Модуль сценариев готов.")

    def _rebuild_plots_grid(self):
        """Динамически перестраивает сетку графиков для моторов."""
        # Очищаем старые графики из сетки
        for i in reversed(range(self.plots_grid.count())):
            widget = self.plots_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.plots.clear()
        self.curves_target.clear()
        self.curves_actual.clear()

        # Размещаем графики в 2 колонки
        cols = 2
        for i in range(1, self.motor_count + 1):
            plot_widget = pg.PlotWidget(title=f"Мотор M{i}")
            plot_widget.setLabel('left', 'RPM')
            plot_widget.setLabel('bottom', 'Время (с)')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)

            # Линия планируемых оборотов (Target) — Пунктирная желтая
            curve_target = plot_widget.plot(
                pen=pg.mkPen(color='#FFD54F', width=2, style=pg.QtCore.Qt.DashLine),
                name="Target"
            )
            # Линия реальных оборотов (Actual) — Зеленая
            curve_actual = plot_widget.plot(
                pen=pg.mkPen(color='#00E676', width=2),
                name="Actual"
            )

            self.plots[i] = plot_widget
            self.curves_target[i] = curve_target
            self.curves_actual[i] = curve_actual

            row = (i - 1) // cols
            col = (i - 1) % cols
            self.plots_grid.addWidget(plot_widget, row, col)

    def log_info(self, message: str):
        self.log_console.append(f"[INFO] {message}")

    def log_error(self, message: str):
        self.log_console.append(f"[ERROR] {message}")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл сценария", "", "Scenario Files (*.yaml *.yml *.json);;All Files (*)"
        )
        if file_path:
            self.current_file_path = file_path
            self.file_path_input.setText(file_path)
            self.load_file(file_path)

    def load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.scenario_editor.setText(f.read())
            self.log_info(f"Сценарий загружен: {os.path.basename(path)}")
        except Exception as e:
            self.log_error(f"Ошибка загрузки сценария: {e}")

    def save_file(self):
        if not self.current_file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить сценарий", "mission.yaml", "YAML Files (*.yaml *.yml);;JSON Files (*.json)"
            )
            if not file_path:
                return
            self.current_file_path = file_path
            self.file_path_input.setText(file_path)

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.scenario_editor.toPlainText())
            self.log_info(f"Сценарий сохранен: {os.path.basename(self.current_file_path)}")
        except Exception as e:
            self.log_error(f"Ошибка сохранения: {e}")

    def toggle_scenario(self):
        if not self.is_running:
            raw_text = self.scenario_editor.toPlainText().strip()
            if not raw_text:
                QMessageBox.warning(self, "Ошибка", "Нельзя запустить пустой сценарий!")
                return

            try:
                parsed_scenario = yaml.safe_load(raw_text)
                self.is_running = True
                self.btn_run.setText("Остановить сценарий")
                self.btn_run.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")
                self.log_info("Сценарий запущен.")

                self.sim_timer.start()
                self.scenario_started.emit(parsed_scenario)
            except Exception as e:
                self.log_error(f"Ошибка парсинга сценария: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать сценарий:\n{e}")
        else:
            self.is_running = False
            self.sim_timer.stop()
            self.btn_run.setText("Запустить сценарий")
            self.btn_run.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
            self.log_info("Сценарий остановлен пользователем.")
            self.scenario_stopped.emit()

    def update_telemetry(self, telemetry_dict: dict):
        """
        Принимает живые данные оборотов от HIL-модели / контроллера и обновляет графики.
        Ожидаемая структура telemetry_dict:
        {
           'target_rpm': {1: 12000, 2: 12000, 3: 12000, 4: 12000},
           'actual_rpm': {1: 11850, 2: 11920, 3: 11800, 4: 12050}
        }
        """
        target_rpm = telemetry_dict.get("target_rpm", {})
        actual_rpm = telemetry_dict.get("actual_rpm", {})

        for m_id in range(1, self.motor_count + 1):
            if m_id in self.target_rpm_data:
                # Сдвиг буфера влево
                self.target_rpm_data[m_id] = np.roll(self.target_rpm_data[m_id], -1)
                self.actual_rpm_data[m_id] = np.roll(self.actual_rpm_data[m_id], -1)

                # Запись нового значения в конец
                self.target_rpm_data[m_id][-1] = target_rpm.get(m_id, 0)
                self.actual_rpm_data[m_id][-1] = actual_rpm.get(m_id, 0)

                # Обновление графических кривых
                self.curves_target[m_id].setData(self.time_data, self.target_rpm_data[m_id])
                self.curves_actual[m_id].setData(self.time_data, self.actual_rpm_data[m_id])

    def _emulate_telemetry_step(self):
        """Тестовая эмуляция реакции моторов для проверки плавности графиков."""
        target = {}
        actual = {}

        base_rpm = 15000 + 3000 * np.sin(pg.ptime.time() * 2)

        for i in range(1, self.motor_count + 1):
            t_rpm = base_rpm + (i * 500)
            target[i] = t_rpm

            # Инерция мотора + небольшие шумы
            last_actual = self.actual_rpm_data[i][-1]
            actual[i] = last_actual + 0.2 * (t_rpm - last_actual) + np.random.normal(0, 50)

        self.update_telemetry({"target_rpm": target, "actual_rpm": actual})