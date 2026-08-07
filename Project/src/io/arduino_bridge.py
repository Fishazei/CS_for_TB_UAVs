# io/arduino_bridge.py
import numpy as np
import serial
import time
from typing import List, Tuple, Dict
import threading


class ArduinoBridge:
    def __init__(self, config: dict):
        self.controllers = {}
        for ctrl_config in config['controllers']:
            controller = {
                'port': ctrl_config['port'],
                'baudrate': ctrl_config['baudrate'],
                'serial': None,
                'motor_mapping': {}
            }

            for motor_map in ctrl_config['motors']:
                controller['motor_mapping'][motor_map['motor_id']] = motor_map['channel']

            self.controllers[ctrl_config['id']] = controller

    def connect_all(self):
        """Подключиться ко всем контроллерам"""
        for ctrl_id, ctrl in self.controllers.items():
            ctrl['serial'] = serial.Serial(
                ctrl['port'],
                ctrl['baudrate'],
                timeout=1
            )
            time.sleep(2)  # Даем время на инициализацию

    def send_packet(self, motor_powers: Dict[int, float]):
        """Отправить пакет с мощностями на все моторы"""
        for ctrl_id, ctrl in self.controllers.items():
            for motor_id, power in motor_powers.items():
                if motor_id in ctrl['motor_mapping']:
                    channel = ctrl['motor_mapping'][motor_id]
                    angle = int(power * 180)
                    message = f"{channel} {angle}\n"
                    ctrl['serial'].write(message.encode())

    def stream_profile(self, time_points: np.ndarray,
                       motor_profiles: Dict[int, np.ndarray],
                       update_rate_hz: int = 50):
        """Потоковая передача профиля"""
        dt = 1.0 / update_rate_hz
        start_time = time.time()

        for i, t in enumerate(time_points):
            # Вычисляем когда нужно отправить следующий пакет
            target_time = start_time + t / 1000.0
            current_time = time.time()

            if current_time < target_time:
                time.sleep(target_time - current_time)

            # Формируем и отправляем пакет
            motor_powers = {
                motor_id: profile[i]
                for motor_id, profile in motor_profiles.items()
            }
            self.send_packet(motor_powers)

    def disconnect_all(self):
        """Отключиться от всех контроллеров"""
        for ctrl in self.controllers.values():
            if ctrl['serial']:
                ctrl['serial'].close()