class Maneuver:
    def __init__(self, step_dict: dict):
        self.id = step_dict.get("id")
        self.name = step_dict.get("name")
        self.type = step_dict["type"]
        self.params = step_dict.get("params", {})
        self.duration = float(step_dict["duration"])