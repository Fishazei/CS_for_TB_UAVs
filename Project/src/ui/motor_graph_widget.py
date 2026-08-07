import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea,
                             QSizePolicy, QLabel, QHBoxLayout, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
from typing import Dict, List, Optional, Tuple


class MotorGraphWidget(QWidget):
    """Виджет для отображения графиков мощности моторов"""

    point_selected = pyqtSignal(int, float)  # motor_id, time_ms

    def __init__(self, parent=None):
        super().__init__(parent)
        self.motor_plots = {}
        self.maneuver_lines = []
        self.time_points = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Панель управления графиками
        control_panel = QHBoxLayout()

        self.show_all_cb = QCheckBox("Показать все")
        self.show_all_cb.setChecked(True)
        self.show_all_cb.stateChanged.connect(self.toggle_all_plots)
        control_panel.addWidget(self.show_all_cb)

        control_panel.addStretch()

        self.time_label = QLabel("Время: 0 мс")
        self.time_label.setStyleSheet("color: #4a9eff; font-weight: bold;")
        control_panel.addWidget(self.time_label)

        layout.addLayout(control_panel)

        # Область с графиками
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.graph_widget = pg.GraphicsLayoutWidget()
        self.graph_widget.setBackground('#2b2b2b')
        self.scroll_area.setWidget(self.graph_widget)

        layout.addWidget(self.scroll_area)

    def create_motor_plots(self, motor_count: int, motor_names: Dict[int, str]):
        """Создать графики для указанного количества моторов"""
        self.graph_widget.clear()
        self.motor_plots.clear()

        for i in range(motor_count):
            motor_id = i + 1
            plot = self.graph_widget.addPlot(row=i, col=0)
            plot.setLabel('left', f'M{motor_id}',
                          color='#ccc', size='10pt')

            if i < motor_count - 1:
                plot.setLabel('bottom', '')
                plot.hideAxis('bottom')
            else:
                plot.setLabel('bottom', 'Время', units='мс',
                              color='#ccc', size='10pt')

            plot.showGrid(x=True, y=True, alpha=0.3)
            plot.setYRange(0, 100)
            plot.setMouseEnabled(x=True, y=False)

            # Легенда
            if motor_id in motor_names:
                plot.addLegend(offset=(10, 10))
                curve = plot.plot(pen=pg.mkPen(color=self.get_motor_color(motor_id),
                                               width=2),
                                  name=motor_names[motor_id])
            else:
                curve = plot.plot(pen=pg.mkPen(color=self.get_motor_color(motor_id),
                                               width=2))

            # Добавляем точки для редактирования
            scatter = pg.ScatterPlotItem(size=6,
                                         pen=pg.mkPen(color='white', width=1),
                                         brush=pg.mkBrush(color=self.get_motor_color(motor_id)))
            plot.addItem(scatter)

            # Обработчик клика для выбора точек
            def create_click_handler(pid=motor_id):
                def handler(event):
                    if event.button() == Qt.RightButton:
                        pos = plot.vb.mapSceneToView(event.pos())
                        self.point_selected.emit(pid, pos.x())

                return handler

            plot.scene().sigMouseClicked.connect(create_click_handler())

            # Вертикальная линия-индикатор времени
            vline = pg.InfiniteLine(angle=90, movable=False,
                                    pen=pg.mkPen(color='#4a9eff', width=1, style=Qt.DashLine))
            plot.addItem(vline)

            self.motor_plots[motor_id] = {
                'plot': plot,
                'curve': curve,
                'scatter': scatter,
                'vline': vline
            }

    def update_profiles(self, time_points: np.ndarray,
                        motor_profiles: Dict[int, np.ndarray],
                        maneuver_times: Optional[List[Tuple[float, str]]] = None):
        """Обновить графики с новыми профилями"""
        self.time_points = time_points

        for motor_id, plot_data in self.motor_plots.items():
            if motor_id in motor_profiles:
                # Нормализуем в проценты
                profile_percent = motor_profiles[motor_id] * 100
                plot_data['curve'].setData(time_points, profile_percent)

                # Обновляем точки для редактирования
                spots = [{'pos': (t, p), 'size': 6}
                         for t, p in zip(time_points[::10], profile_percent[::10])]
                plot_data['scatter'].setData(spots=spots)

                # Автомасштабирование
                plot_data['plot'].autoRange()

        # Добавляем отметки маневров
        self._clear_maneuver_lines()
        if maneuver_times:
            self._add_maneuver_lines(maneuver_times)

    def _add_maneuver_lines(self, maneuver_times: List[Tuple[float, str]]):
        """Добавить вертикальные линии маневров"""
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7']

        for i, (time_ms, name) in enumerate(maneuver_times):
            color = colors[i % len(colors)]
            for motor_id, plot_data in self.motor_plots.items():
                line = pg.InfiniteLine(
                    pos=time_ms,
                    angle=90,
                    pen=pg.mkPen(color=color, width=1, style=Qt.DotLine)
                )
                plot_data['plot'].addItem(line)

                # Добавляем текстовую метку
                label = pg.TextItem(
                    text=name,
                    color=color,
                    anchor=(0, 1) if motor_id == min(self.motor_plots.keys()) else (0, 0)
                )
                label.setPos(time_ms, 95 if motor_id == min(self.motor_plots.keys()) else 5)
                plot_data['plot'].addItem(label)

                self.maneuver_lines.append((line, label))

    def _clear_maneuver_lines(self):
        """Очистить линии маневров"""
        for line, label in self.maneuver_lines:
            for plot_data in self.motor_plots.values():
                plot_data['plot'].removeItem(line)
                plot_data['plot'].removeItem(label)
        self.maneuver_lines.clear()

    def update_time_indicator(self, current_time_ms: float):
        """Обновить индикатор текущего времени"""
        self.time_label.setText(f"Время: {current_time_ms:.0f} мс")
        for plot_data in self.motor_plots.values():
            plot_data['vline'].setPos(current_time_ms)

    def toggle_all_plots(self, state):
        """Показать/скрыть все графики"""
        visible = state == Qt.Checked
        for plot_data in self.motor_plots.values():
            plot_data['curve'].setVisible(visible)
            plot_data['scatter'].setVisible(visible)

    @staticmethod
    def get_motor_color(motor_id: int) -> str:
        """Получить цвет для мотора"""
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24',
                  '#6c5ce7', '#ff8a5c', '#25CCF7', '#FD7272']
        return colors[(motor_id - 1) % len(colors)]