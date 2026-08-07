# models/command.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CommandType(Enum):
    HOVER = "hover"
    CLIMB = "climb"
    DESCEND = "descend"
    PITCH_FORWARD = "pitch_forward"
    PITCH_BACKWARD = "pitch_backward"
    ROLL_LEFT = "roll_left"
    ROLL_RIGHT = "roll_right"
    YAW_LEFT = "yaw_left"
    YAW_RIGHT = "yaw_right"
    CUSTOM = "custom"


@dataclass
class Command:
    type: CommandType
    duration_ms: float
    intensity: float  # 0.0 to 1.0
    transition_type: str = "smooth"  # "none", "linear", "smooth"
    transition_duration_ms: float = 200


@dataclass
class MotorState:
    """Состояние мотора в конкретный момент времени"""
    timestamp_ms: float
    power: float  # 0.0 to 1.0