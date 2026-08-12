import os
import sys
import yaml
import numpy as np
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QSplitter,
    QGridLayout, QTabWidget, QStackedWidget
)
import pyqtgraph as pg

# Настройка стиля графиков pyqtgraph
pg.setConfigOption('background', '#121212')
pg.setConfigOption('foreground', '#CCCCCC')


class ScenarioTab(QWidget):
    """
    Вкладка управления сценарием, динамического мониторинга моторов,
    координат/датчиков и экспорта телеметрии.
    """
    scenario_started = Signal(dict)
    scenario_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file_path = None
        self.is_running = False
        self.config_is_applied = False

        self.motor_count = 0
        self.sensor_list = []

        # Буферы данных для графиков реального времени
        self.buffer_size = 200
        self.time_data = np.linspace(-10, 0, self.buffer_size)

        # Полная история заезда для экспорта в Таблицу (.xlsx / .csv)
        self.telemetry_history = []
        self.elapsed_time = 0.0

        # Графические объекты
        self.motor_plots = {}
        self.curves_motor_target = {}
        self.curves_motor_actual = {}

        self.sensor_plots = {}
        self.sensor_curves = {}

        self.init_ui()

        # Эмуляция HIL-телеметрии (для проверки отклика UI)
        self.sim_timer = QTimer()
        self.sim_timer.setInterval(50)  # 20 Гц
        self.sim_timer.timeout.connect(self._emulate_telemetry_step)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter()

        # ==========================================
        # Левая панель: Редактор и управление
        # ==========================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Панель загрузки и запуска
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Выберите сценарий (.yaml / .json)...")
        self.file_path_input.setReadOnly(True)

        btn_browse = QPushButton("Обзор...")
        btn_browse.clicked.connect(self.browse_file)

        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_file)

        self.btn_run = QPushButton("Запустить")
        self.btn_run.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_run.clicked.connect(self.toggle_scenario)

        file_layout.addWidget(QLabel("Сценарий:"))
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(btn_browse)
        file_layout.addWidget(btn_save)
        file_layout.addWidget(self.btn_run)

        left_layout.addLayout(file_layout)

        # Текстовый редактор сценария
        self.scenario_editor = QTextEdit()
        font = QFont("Consolas" if sys.platform == "win32" else "Monospace", 10)
        self.scenario_editor.setFont(font)
        self.scenario_editor.setPlaceholderText("Загрузите файл сценария...")
        left_layout.addWidget(self.scenario_editor)

        # Нижний блок левой панели: Экспорт и Лог
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Лог сценария:"))
        export_layout.addStretch()

        self.btn_export = QPushButton("Сохранить данные (.xlsx/.csv)")
        self.btn_export.setStyleSheet("background-color: #0277bd; color: white; font-weight: bold;")
        self.btn_export.clicked.connect(self.export_telemetry_data)
        export_layout.addWidget(self.btn_export)

        left_layout.addLayout(export_layout)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(110)
        self.log_console.setFont(font)
        self.log_console.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        left_layout.addWidget(self.log_console)

        # ==========================================
        # Правая панель: Заглушка -> Графики в Табах
        # ==========================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.right_stack = QStackedWidget()

        # 1. Заглушка (показывается до применения конфигурации)
        self.placeholder = QLabel(
            "Примените конфигурацию на вкладке «Настройка конфигурации»,\n"
            "чтобы сгенерировать графики моторов и датчиков."
        )
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(
            "QLabel { color: #888888; font-size: 13pt; border: 2px dashed #444444; border-radius: 8px; }"
        )
        self.right_stack.addWidget(self.placeholder)

        # 2. Вкладки с графиками
        self.charts_tab_widget = QTabWidget()

        # Контейнеры под графики
        self.motors_container = QWidget()
        self.motors_grid = QGridLayout(self.motors_container)

        self.sensors_container = QWidget()
        self.sensors_grid = QGridLayout(self.sensors_container)

        self.charts_tab_widget.addTab(self.motors_container, "Обороты моторов")
        self.charts_tab_widget.addTab(self.sensors_container, "Координаты и Датчики")

        self.right_stack.addWidget(self.charts_tab_widget)
        self.right_stack.setCurrentWidget(self.placeholder)

        right_layout.addWidget(self.right_stack)

        # Сплиттер
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        self.log_info("Модуль сценариев готов. Ожидание конфигурации...")

    # ==========================================
    # Динамическое построение графиков
    # ==========================================
    def apply_config_data(self, config_dict: dict):
        """Вызывается при применении конфигурации стенда."""
        motors = config_dict.get("motors", [])
        self.motor_count = len(motors)
        self.sensor_list = config_dict.get("sensors", [])

        if self.motor_count == 0:
            self.log_error("Конфигурация не содержит моторов!")
            return

        # Буферы под моторы
        self.target_rpm_buffers = {i: np.zeros(self.buffer_size) for i in range(1, self.motor_count + 1)}
        self.actual_rpm_buffers = {i: np.zeros(self.buffer_size) for i in range(1, self.motor_count + 1)}

        # Буферы под координаты и датчики
        self.coords_buffers = {axis: np.zeros(self.buffer_size) for axis in ['X', 'Y', 'Z', 'Roll', 'Pitch', 'Yaw']}

        self._build_motor_plots()
        self._build_sensor_plots()

        self.config_is_applied = True
        self.right_stack.setCurrentWidget(self.charts_tab_widget)
        self.log_info(f"Сгенерированы графики для {self.motor_count} моторов и датчиков.")

    def _build_motor_plots(self):
        """Создает графики моторов по числу моторов из конфига."""
        # Очистка старой сетки
        for i in reversed(range(self.motors_grid.count())):
            w = self.motors_grid.itemAt(i).widget()
            if w: w.setParent(None)

        self.motor_plots.clear()
        self.curves_motor_target.clear()
        self.curves_motor_actual.clear()

        cols = 2
        for i in range(1, self.motor_count + 1):
            plot = pg.PlotWidget(title=f"Мотор M{i}")
            plot.setLabel('left', 'RPM')
            plot.setLabel('bottom', 'Время (с)')
            plot.showGrid(x=True, y=True, alpha=0.3)

            curve_target = plot.plot(pen=pg.mkPen('#FFD54F', width=2, style=Qt.DashLine), name="Target")
            curve_actual = plot.plot(pen=pg.mkPen('#00E676', width=2), name="Actual")

            self.motor_plots[i] = plot
            self.curves_motor_target[i] = curve_target
            self.curves_motor_actual[i] = curve_actual

            row, col = (i - 1) // cols, (i - 1) % cols
            self.motors_grid.addWidget(plot, row, col)

    def _build_sensor_plots(self):
        """Создает сетку 2x2: Акселерометр, Гироскоп, Барометр и Позиция."""
        for i in reversed(range(self.sensors_grid.count())):
            w = self.sensors_grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.sensor_plots.clear()
        self.sensor_curves.clear()

        # Буферы данных под датчики
        self.sensor_buffers = {
            'accel_x': np.zeros(self.buffer_size),
            'accel_y': np.zeros(self.buffer_size),
            'accel_z': np.zeros(self.buffer_size),
            'gyro_x': np.zeros(self.buffer_size),
            'gyro_y': np.zeros(self.buffer_size),
            'gyro_z': np.zeros(self.buffer_size),
            'baro_alt': np.zeros(self.buffer_size),
            'pos_x': np.zeros(self.buffer_size),
            'pos_y': np.zeros(self.buffer_size),
            'pos_z': np.zeros(self.buffer_size),
        }

        # 1. Акселерометр (м/с²)
        p_acc = pg.PlotWidget(title="Акселерометр (Accel X, Y, Z)")
        p_acc.setLabel('left', 'Ускорение (м/с²)')
        p_acc.showGrid(x=True, y=True, alpha=0.3)
        p_acc.addLegend()
        self.sensor_curves['accel_x'] = p_acc.plot(pen=pg.mkPen('#EF5350', width=2), name="Acc X")
        self.sensor_curves['accel_y'] = p_acc.plot(pen=pg.mkPen('#66BB6A', width=2), name="Acc Y")
        self.sensor_curves['accel_z'] = p_acc.plot(pen=pg.mkPen('#42A5F5', width=2), name="Acc Z")
        self.sensors_grid.addWidget(p_acc, 0, 0)

        # 2. Гироскоп (град/с)
        p_gyro = pg.PlotWidget(title="Гироскоп (Gyro X, Y, Z)")
        p_gyro.setLabel('left', 'Угл. скорость (град/с)')
        p_gyro.showGrid(x=True, y=True, alpha=0.3)
        p_gyro.addLegend()
        self.sensor_curves['gyro_x'] = p_gyro.plot(pen=pg.mkPen('#AB47BC', width=2), name="Gyro X (Roll)")
        self.sensor_curves['gyro_y'] = p_gyro.plot(pen=pg.mkPen('#FFA726', width=2), name="Gyro Y (Pitch)")
        self.sensor_curves['gyro_z'] = p_gyro.plot(pen=pg.mkPen('#26C6DA', width=2), name="Gyro Z (Yaw)")
        self.sensors_grid.addWidget(p_gyro, 0, 1)

        # 3. Барометр (Высота / Давление)
        p_baro = pg.PlotWidget(title="Барометр (Высота)")
        p_baro.setLabel('left', 'Высота (м)')
        p_baro.showGrid(x=True, y=True, alpha=0.3)
        p_baro.addLegend()
        self.sensor_curves['baro_alt'] = p_baro.plot(pen=pg.mkPen('#FFD54F', width=2), name="Baro Alt")
        self.sensors_grid.addWidget(p_baro, 1, 0)

        # 4. Расчетные координаты модели (X, Y, Z)
        p_pos = pg.PlotWidget(title="Модельная позиция (X, Y, Z)")
        p_pos.setLabel('left', 'Позиция (м)')
        p_pos.showGrid(x=True, y=True, alpha=0.3)
        p_pos.addLegend()
        self.sensor_curves['pos_x'] = p_pos.plot(pen=pg.mkPen('#E91E63', width=1.5, style=Qt.DashLine), name="X")
        self.sensor_curves['pos_y'] = p_pos.plot(pen=pg.mkPen('#00BCD4', width=1.5, style=Qt.DashLine), name="Y")
        self.sensor_curves['pos_z'] = p_pos.plot(pen=pg.mkPen('#8BC34A', width=1.5, style=Qt.DashLine), name="Z")
        self.sensors_grid.addWidget(p_pos, 1, 1)

    # ==========================================
    # Телеметрия и Экспорт
    # ==========================================
    def toggle_scenario(self):
        if not self.config_is_applied:
            QMessageBox.warning(self, "Внимание", "Сначала примените конфигурацию стенда!")
            return

        if not self.is_running:
            raw_text = self.scenario_editor.toPlainText().strip()
            if not raw_text:
                QMessageBox.warning(self, "Ошибка", "Пустой сценарий!")
                return

            try:
                parsed = yaml.safe_load(raw_text)
                self.is_running = True
                self.telemetry_history.clear()  # Сброс старой истории
                self.elapsed_time = 0.0

                self.btn_run.setText("Остановить")
                self.btn_run.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")
                self.log_info("Сценарий запущен.")

                self.sim_timer.start()
                self.scenario_started.emit(parsed)
            except Exception as e:
                self.log_error(f"Ошибка чтения сценария: {e}")
        else:
            self.is_running = False
            self.sim_timer.stop()
            self.btn_run.setText("Запустить")
            self.btn_run.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
            self.log_info(f"Сценарий остановлен. Записано точек: {len(self.telemetry_history)}")
            self.scenario_stopped.emit()

    def update_telemetry(self, telemetry: dict):
        """Запись телеметрии моторов, 3-х датчиков и координат модели."""
        if not self.config_is_applied:
            return

        dt = 0.05
        self.elapsed_time += dt

        target_rpm = telemetry.get("target_rpm", {})
        actual_rpm = telemetry.get("actual_rpm", {})

        # Считываем данные трех датчиков и модели
        accel = telemetry.get("accel", {'x': 0.0, 'y': 0.0, 'z': 9.81})
        gyro = telemetry.get("gyro", {'x': 0.0, 'y': 0.0, 'z': 0.0})
        baro_alt = telemetry.get("baro_alt", 0.0)
        coords = telemetry.get("coords", {'x': 0.0, 'y': 0.0, 'z': 0.0})

        # ==========================================
        # 1. Формирование строки для XLSX / CSV
        # ==========================================
        row = {
            "Time_s": round(self.elapsed_time, 3),
            # Датчик 1: Акселерометр
            "Accel_X_ms2": round(accel['x'], 3),
            "Accel_Y_ms2": round(accel['y'], 3),
            "Accel_Z_ms2": round(accel['z'], 3),
            # Датчик 2: Гироскоп
            "Gyro_X_degs": round(gyro['x'], 3),
            "Gyro_Y_degs": round(gyro['y'], 3),
            "Gyro_Z_degs": round(gyro['z'], 3),
            # Датчик 3: Барометр
            "Baro_Alt_m": round(baro_alt, 3),
            # Истинная позиция модели
            "Model_X_m": round(coords['x'], 3),
            "Model_Y_m": round(coords['y'], 3),
            "Model_Z_m": round(coords['z'], 3),
        }

        # Обороты моторов
        for m in range(1, self.motor_count + 1):
            row[f"M{m}_Target_RPM"] = round(target_rpm.get(m, 0), 1)
            row[f"M{m}_Actual_RPM"] = round(actual_rpm.get(m, 0), 1)

        self.telemetry_history.append(row)

        # ==========================================
        # 2. Обновление графиков моторов
        # ==========================================
        for m in range(1, self.motor_count + 1):
            self.target_rpm_buffers[m] = np.roll(self.target_rpm_buffers[m], -1)
            self.actual_rpm_buffers[m] = np.roll(self.actual_rpm_buffers[m], -1)
            self.target_rpm_buffers[m][-1] = target_rpm.get(m, 0)
            self.actual_rpm_buffers[m][-1] = actual_rpm.get(m, 0)

            self.curves_motor_target[m].setData(self.time_data, self.target_rpm_buffers[m])
            self.curves_motor_actual[m].setData(self.time_data, self.actual_rpm_buffers[m])

        # ==========================================
        # 3. Обновление графиков датчиков
        # ==========================================
        s_data = {
            'accel_x': accel['x'], 'accel_y': accel['y'], 'accel_z': accel['z'],
            'gyro_x': gyro['x'], 'gyro_y': gyro['y'], 'gyro_z': gyro['z'],
            'baro_alt': baro_alt,
            'pos_x': coords['x'], 'pos_y': coords['y'], 'pos_z': coords['z']
        }

        for key, value in s_data.items():
            if key in self.sensor_buffers:
                self.sensor_buffers[key] = np.roll(self.sensor_buffers[key], -1)
                self.sensor_buffers[key][-1] = value
                self.sensor_curves[key].setData(self.time_data, self.sensor_buffers[key])

    def export_telemetry_data(self):
        """Сохранение записанных данных в файл .xlsx или .csv."""
        if not self.telemetry_history:
            QMessageBox.warning(self, "Экспорт", "Нет записанных данных для экспорта! Запустите сценарий.")
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Сохранить телеметрию", "scenario_telemetry.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            import pandas as pd
            df = pd.DataFrame(self.telemetry_history)

            if file_path.endswith(".xlsx"):
                try:
                    df.to_excel(file_path, index=False)
                except ModuleNotFoundError:
                    # Если пакет openpyxl не установлен, автоматически сохраняем в CSV
                    csv_path = file_path.replace(".xlsx", ".csv")
                    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                    QMessageBox.information(
                        self, "Экспорт",
                        f"Пакет 'openpyxl' не найден. Файл автоматически сохранен в формате CSV:\n{csv_path}"
                    )
                    return
            else:
                df.to_csv(file_path, index=False, encoding="utf-8-sig")

            self.log_info(f"Данные заезда сохранены: {os.path.basename(file_path)}")
            QMessageBox.information(self, "Успех", f"Данные успешно экспортированы:\n{file_path}")

        except Exception as e:
            self.log_error(f"Ошибка экспорта данных: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные:\n{e}")

    # ==========================================
    # Вспомогательные функции
    # ==========================================
    def _emulate_telemetry_step(self):
        """Эмуляция физики HIL-модели и датчиков с шумом."""
        t = pg.ptime.time()

        # Моторы
        target, actual = {}, {}
        base_rpm = 14000 + 2000 * np.sin(t * 2)
        for i in range(1, self.motor_count + 1):
            target[i] = base_rpm + (i * 300)
            last_act = self.actual_rpm_buffers[i][-1]
            actual[i] = last_act + 0.25 * (target[i] - last_act) + np.random.normal(0, 30)

        # 1. Акселерометр (гравитация 9.81 + вибрация от винтов)
        accel = {
            'x': 0.5 * np.sin(t * 3) + np.random.normal(0, 0.15),
            'y': 0.5 * np.cos(t * 3) + np.random.normal(0, 0.15),
            'z': 9.81 + 0.3 * np.sin(t) + np.random.normal(0, 0.2)
        }

        # 2. Гироскоп (угловые скорости)
        gyro = {
            'x': 12.0 * np.sin(t * 1.5) + np.random.normal(0, 0.8),
            'y': 8.0 * np.cos(t * 1.5) + np.random.normal(0, 0.8),
            'z': 2.0 * np.sin(t * 0.5) + np.random.normal(0, 0.3)
        }

        # 3. Барометр (высота с температурным дрейфом и шумом)
        baro_alt = 2.5 + 0.8 * np.sin(t * 0.4) + np.random.normal(0, 0.05)

        # Истинные координаты
        coords = {
            'x': 1.5 * np.cos(t * 0.4),
            'y': 1.5 * np.sin(t * 0.4),
            'z': baro_alt - 0.02
        }

        self.update_telemetry({
            "target_rpm": target,
            "actual_rpm": actual,
            "accel": accel,
            "gyro": gyro,
            "baro_alt": baro_alt,
            "coords": coords
        })

    def log_info(self, msg: str):
        self.log_console.append(f"[INFO] {msg}")

    def log_error(self, msg: str):
        self.log_console.append(f"[ERROR] {msg}")

    def browse_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Открыть сценарий", "", "Scenario Files (*.yaml *.yml *.json)")
        if p:
            self.current_file_path = p
            self.file_path_input.setText(p)
            self.load_file(p)

    def load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.scenario_editor.setText(f.read())
            self.log_info(f"Загружен файл: {os.path.basename(path)}")
        except Exception as e:
            self.log_error(f"Ошибка загрузки: {e}")

    def save_file(self):
        if not self.current_file_path:
            p, _ = QFileDialog.getSaveFileName(self, "Сохранить сценарий", "scenario.yaml", "YAML Files (*.yaml)")
            if not p: return
            self.current_file_path = p
            self.file_path_input.setText(p)

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(self.scenario_editor.toPlainText())
            self.log_info(f"Сохранено: {os.path.basename(self.current_file_path)}")
        except Exception as e:
            self.log_error(f"Ошибка сохранения: {e}")