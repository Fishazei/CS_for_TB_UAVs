# core/profile_editor.py
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector


class ProfileEditor:
    """Редактор профилей мощности с графическим интерфейсом"""

    def __init__(self, time_points: np.ndarray, motor_profiles: Dict[int, np.ndarray]):
        self.time_points = time_points
        self.motor_profiles = motor_profiles
        self.modified_profiles = {k: v.copy() for k, v in motor_profiles.items()}
        self.selected_points = []

    def edit_interactive(self):
        """Запуск интерактивного редактирования"""
        fig, axes = plt.subplots(len(self.motor_profiles), 1, sharex=True)
        if len(self.motor_profiles) == 1:
            axes = [axes]

        for ax, (motor_id, profile) in zip(axes, self.motor_profiles.items()):
            ax.plot(self.time_points, profile, 'b-', label=f'Motor {motor_id}')
            ax.plot(self.time_points, profile, 'r.', markersize=2)
            ax.set_ylabel(f'M{motor_id} power')
            ax.grid(True)
            ax.legend()

        axes[-1].set_xlabel('Time (ms)')

        def onselect(eclick, erelease):
            """Обработчик выделения области"""
            x1, x2 = sorted([eclick.xdata, erelease.xdata])
            mask = (self.time_points >= x1) & (self.time_points <= x2)

            # Редактирование выделенной области
            for motor_id in self.modified_profiles:
                # Пример: масштабирование выделенного участка
                self.modified_profiles[motor_id][mask] *= 1.1

            self._update_plots(axes)

        # Добавляем инструмент выделения
        toggle_selector = RectangleSelector(
            axes[0], onselect, useblit=True,
            button=[1], minspanx=5, minspany=5,
            spancoords='pixels', interactive=True
        )

        plt.show()
        return self.modified_profiles

    def add_point(self, time_ms: float, motor_powers: Dict[int, float]):
        """Добавить точку в профили"""
        insert_idx = np.searchsorted(self.time_points, time_ms)
        self.time_points = np.insert(self.time_points, insert_idx, time_ms)

        for motor_id, power in motor_powers.items():
            self.modified_profiles[motor_id] = np.insert(
                self.modified_profiles[motor_id], insert_idx, power
            )

    def scale_region(self, start_ms: float, end_ms: float,
                     motor_id: int, scale_factor: float):
        """Масштабировать регион профиля"""
        mask = (self.time_points >= start_ms) & (self.time_points <= end_ms)
        self.modified_profiles[motor_id][mask] *= scale_factor
        self.modified_profiles[motor_id][mask] = np.clip(
            self.modified_profiles[motor_id][mask], 0, 1
        )

    def smooth_region(self, start_ms: float, end_ms: float,
                      motor_id: int, window_size: int = 5):
        """Сгладить регион скользящим средним"""
        mask = (self.time_points >= start_ms) & (self.time_points <= end_ms)
        region = self.modified_profiles[motor_id][mask]
        smoothed = np.convolve(region, np.ones(window_size) / window_size, mode='same')
        self.modified_profiles[motor_id][mask] = smoothed

    def _update_plots(self, axes):
        """Обновить графики"""
        for ax, (motor_id, profile) in zip(axes, self.modified_profiles.items()):
            ax.clear()
            ax.plot(self.time_points, profile, 'b-', label=f'Motor {motor_id}')
            ax.plot(self.time_points, profile, 'r.', markersize=2)
            ax.set_ylabel(f'M{motor_id} power')
            ax.grid(True)
            ax.legend()
        plt.draw()