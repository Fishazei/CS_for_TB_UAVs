# core/transition_engine.py
from enum import Enum
from typing import List, Dict, Tuple
import numpy as np
from scipy.interpolate import CubicSpline
from src.models.command import Command

class TransitionType(Enum):
    NONE = "none"  # Без переходов
    LINEAR = "linear"  # Прямые переходы
    SMOOTH = "smooth"  # Плавные переходы (сплайны)


class TransitionEngine:
    def __init__(self, update_rate_hz: int = 50):
        self.update_rate_hz = update_rate_hz
        self.dt = 1000.0 / update_rate_hz  # период в мс

    def generate_profile(self,
                         commands: List[Command],
                         motor_power_sequence: List[Dict[int, float]],
                         transition_type: TransitionType = TransitionType.SMOOTH) -> Tuple[
        np.ndarray, Dict[int, np.ndarray]]:
        """
        Генерирует профили мощности для всех моторов
        Возвращает: (time_points, {motor_id: power_array})
        """
        if transition_type == TransitionType.NONE:
            return self._generate_stepped(commands, motor_power_sequence)
        elif transition_type == TransitionType.LINEAR:
            return self._generate_linear(commands, motor_power_sequence)
        else:
            return self._generate_smooth(commands, motor_power_sequence)

    def _generate_stepped(self, commands, power_sequence):
        """Генерация ступенчатого профиля"""
        time_points = [0]
        motor_powers = {i: [0] for i in power_sequence[0].keys()}

        current_time = 0
        for i, (cmd, powers) in enumerate(zip(commands, power_sequence)):
            # Добавляем точку в начале команды
            if i > 0:
                time_points.append(current_time)
                for motor_id in motor_powers:
                    motor_powers[motor_id].append(motor_powers[motor_id][-1])

            # Добавляем точку с новыми значениями
            time_points.append(current_time)
            for motor_id, power in powers.items():
                motor_powers[motor_id].append(power)

            current_time += cmd.duration_ms

        # Финальная точка
        time_points.append(current_time)
        for motor_id in motor_powers:
            motor_powers[motor_id].append(motor_powers[motor_id][-1])

        return np.array(time_points), {k: np.array(v) for k, v in motor_powers.items()}

    def _generate_linear(self, commands, power_sequence):
        """Генерация с линейными переходами"""
        time_points = []
        motor_power_lists = {i: [] for i in power_sequence[0].keys()}

        current_time = 0
        prev_powers = {mid: 0 for mid in motor_power_lists}

        for cmd, powers in zip(commands, power_sequence):
            transition_time = cmd.transition_duration_ms

            # Генерируем точки перехода
            if transition_time > 0:
                num_points = int(transition_time / self.dt)
                for t in np.linspace(0, transition_time, num_points):
                    time_points.append(current_time + t)
                    for motor_id in motor_power_lists:
                        interp_power = np.interp(t, [0, transition_time],
                                                 [prev_powers[motor_id], powers[motor_id]])
                        motor_power_lists[motor_id].append(interp_power)

            # Стабильное состояние команды
            stable_duration = cmd.duration_ms - transition_time
            if stable_duration > 0:
                num_points = int(stable_duration / self.dt)
                for _ in range(num_points):
                    current_time += self.dt
                    time_points.append(current_time)
                    for motor_id in motor_power_lists:
                        motor_power_lists[motor_id].append(powers[motor_id])

            current_time += transition_time
            prev_powers = powers

        return np.array(time_points), {k: np.array(v) for k, v in motor_power_lists.items()}

    def _generate_smooth(self, commands, power_sequence):
        """Генерация с плавными переходами (кубические сплайны)"""
        # Сначала генерируем ключевые точки
        key_times = [0]
        key_powers = {i: [0] for i in power_sequence[0].keys()}

        current_time = 0
        for cmd, powers in zip(commands, power_sequence):
            key_times.append(current_time + cmd.duration_ms / 2)  # средняя точка
            key_times.append(current_time + cmd.duration_ms)

            for motor_id in key_powers:
                key_powers[motor_id].extend([powers[motor_id], powers[motor_id]])

            current_time += cmd.duration_ms

        # Создаем сплайны
        time_points = np.arange(0, current_time, self.dt)
        motor_profiles = {}

        for motor_id in key_powers:
            cs = CubicSpline(key_times, key_powers[motor_id], bc_type='natural')
            motor_profiles[motor_id] = np.clip(cs(time_points), 0, 1)

        return time_points, motor_profiles