import yaml, pathlib
from maneuver import Maneuver

class Scenario:
    def __init__(self, data: dict):
        self.meta = data.get("meta", {})
        self.settings = data.get("settings", {})
        self.steps = [Maneuver(s) for s in data.get("steps", [])]

    @classmethod
    def load(cls, path: str):
        text = pathlib.Path(path).read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return cls(data)