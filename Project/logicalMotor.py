class LogicalMotor:
    def __init__(self, motor_config, esc_config, mapping):
        self.id = motor_config["id"]
        self.role = motor_config["role"]
        self.type = motor_config["type"]
        self.max_power = motor_config.get("max_power", 1.0)
        self.current_power = 0.0

        # данные для перевода мощности в ESC-значение:
        self.esc_config = esc_config
        self.mapping = mapping  # {controller_id, channel}

    def set_power(self, power: float):
        # clamp [0..max_power]
        self.current_power = max(0.0, min(self.max_power, power))

    def to_arduino_value(self) -> int:
        # например, map [0..max_power] -> [min_value..max_value]
        esc = self.esc_config
        p = self.current_power / self.max_power
        return int(esc["min_value"] + p * (esc["max_value"] - esc["min_value"]))