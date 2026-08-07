# core/scenario_manager.py
from typing import Optional, Dict
import numpy as np
from src.models.scenario import Scenario
from src.models.command import Command, CommandType, MotorState
from src.core.command_interpreter import CommandInterpreter
from src.core.transition_engine import TransitionEngine, TransitionType
from src.core.profile_editor import ProfileEditor
from src.io.profile_serializer import ProfileSerializer


class ScenarioManager:
    def __init__(self, motors: Dict[int, 'VirtualMotor'],
                 command_interpreter: CommandInterpreter,
                 transition_engine: TransitionEngine):
        self.motors = motors
        self.interpreter = command_interpreter
        self.transition_engine = transition_engine
        self.current_scenario: Optional[Scenario] = None
        self.profile_serializer = ProfileSerializer()

    def create_scenario(self, name: str) -> Scenario:
        """Создать новый сценарий"""
        self.current_scenario = Scenario(name, len(self.motors))
        return self.current_scenario

    def add_command(self, command: Command):
        """Добавить команду в сценарий"""
        if self.current_scenario is None:
            raise ValueError("No active scenario")
        self.current_scenario.add_command(command)

    def generate_profiles(self, transition_type: TransitionType = TransitionType.SMOOTH):
        """Сгенерировать профили мощности из команд"""
        if self.current_scenario is None:
            raise ValueError("No active scenario")

        # Интерпретируем команды в мощности
        power_sequence = []
        for cmd in self.current_scenario.commands:
            powers = self.interpreter.interpret_command(cmd, self.motors)
            power_sequence.append(powers)

        # Генерируем временные профили
        time_points, motor_profiles = self.transition_engine.generate_profile(
            self.current_scenario.commands,
            power_sequence,
            transition_type
        )

        # Применяем профили к виртуальным моторам
        for motor_id, profile in motor_profiles.items():
            self.motors[motor_id].set_profile(time_points, profile)

        self.current_scenario.time_points = time_points
        self.current_scenario.power_profiles = {
            motor_id: [
                MotorState(t, p) for t, p in zip(time_points, profile)
            ]
            for motor_id, profile in motor_profiles.items()
        }

    def edit_profiles(self) -> Dict[int, np.ndarray]:
        """Открыть редактор профилей"""
        if self.current_scenario is None:
            raise ValueError("No active scenario")

        editor = ProfileEditor(
            self.current_scenario.time_points,
            {mid: np.array([s.power for s in states])
             for mid, states in self.current_scenario.power_profiles.items()}
        )

        modified_profiles = editor.edit_interactive()

        # Обновляем сценарий
        for motor_id, profile in modified_profiles.items():
            self.current_scenario.power_profiles[motor_id] = [
                MotorState(t, p)
                for t, p in zip(self.current_scenario.time_points, profile)
            ]

        return modified_profiles

    def save_scenario(self, filename: str):
        """Сохранить сценарий в файл"""
        self.profile_serializer.save_scenario(self.current_scenario, filename)

    def load_scenario(self, filename: str) -> Scenario:
        """Загрузить сценарий из файла"""
        self.current_scenario = self.profile_serializer.load_scenario(filename)
        return self.current_scenario

    def export_for_arduino(self) -> bytes:
        """Экспортировать данные для Arduino"""
        if self.current_scenario is None:
            raise ValueError("No active scenario")

        # Формируем пакеты данных
        data_packets = []
        for motor_id, states in self.current_scenario.power_profiles.items():
            for state in states:
                # Конвертируем мощность в угол сервопривода (0-180)
                angle = state.power * 180
                packet = f"{motor_id} {angle}\n".encode()
                data_packets.append((state.timestamp_ms, packet))

        return data_packets