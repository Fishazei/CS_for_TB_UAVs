# core/command_interpreter.py
from typing import Dict, List, Tuple
import numpy as np
from src.models.command import Command, CommandType
from src.models.virtual_motor import VirtualMotor


class CommandInterpreter:
    def __init__(self, model_config: dict):
        self.model_config = model_config
        self.base_power = model_config['profiles']['quad_4motors_basic']['base_power']
        self.maneuvers = model_config['profiles']['quad_4motors_basic']['maneuvers']

    def interpret_command(self, command: Command,
                          motors: Dict[int, VirtualMotor]) -> Dict[int, float]:
        """Интерпретирует команду в базовые мощности для моторов"""
        powers = {motor_id: self.base_power['hover']
                  for motor_id in motors.keys()}

        if command.type == CommandType.HOVER:
            return powers

        elif command.type == CommandType.CLIMB:
            climb_rate = command.intensity
            k = self.maneuvers['climb_rate']['k']
            for motor_id in powers:
                powers[motor_id] += k * climb_rate

        elif command.type in [CommandType.PITCH_FORWARD, CommandType.PITCH_BACKWARD]:
            pitch_value = command.intensity
            if command.type == CommandType.PITCH_BACKWARD:
                pitch_value = -pitch_value

            gains = self.maneuvers['attitude_pitch']['roles']
            for motor_id, motor in motors.items():
                if motor.role in gains:
                    powers[motor_id] += gains[motor.role]['gain'] * pitch_value

        elif command.type in [CommandType.ROLL_LEFT, CommandType.ROLL_RIGHT]:
            roll_value = command.intensity
            if command.type == CommandType.ROLL_LEFT:
                roll_value = -roll_value

            gains = self.maneuvers['attitude_roll']['roles']
            for motor_id, motor in motors.items():
                if motor.role in gains:
                    powers[motor_id] += gains[motor.role]['gain'] * roll_value

        elif command.type in [CommandType.YAW_LEFT, CommandType.YAW_RIGHT]:
            yaw_value = command.intensity
            if command.type == CommandType.YAW_RIGHT:
                yaw_value = -yaw_value

            gains = self.maneuvers['yaw']['roles']
            for motor_id, motor in motors.items():
                if motor.role in gains:
                    powers[motor_id] += gains[motor.role]['gain'] * yaw_value

        # Клиппинг значений
        for motor_id in powers:
            powers[motor_id] = np.clip(powers[motor_id], 0.0, 1.0)

        return powers