# models/scenario.py
from typing import List, Dict
import numpy as np
from src.models.command import *

class Scenario:
    def __init__(self, name: str, motor_count: int):
        self.name = name
        self.motor_count = motor_count
        self.commands: List[Command] = []
        # Профили мощности для каждого мотора
        self.power_profiles: Dict[int, List[MotorState]] = {}
        self.time_points: np.ndarray = None

    def add_command(self, command: Command):
        self.commands.append(command)

    def get_total_duration(self) -> float:
        return sum(cmd.duration_ms for cmd in self.commands)