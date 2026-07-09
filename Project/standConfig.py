import yaml
from pathlib import Path

class StandConfig:
    def __init__(self, data: dict):
        self.data = data
        self.motors = {m["id"]: m for m in data["motors"]}
        self.controllers = {c["id"]: c for c in data["controllers"]}

        # построить быстрый маппинг motor_id -> (controller_id, channel)
        self.motor_map = {}
        for cid, ctrl in self.controllers.items():
            for m in ctrl["motors"]:
                self.motor_map[m["motor_id"]] = {
                    "controller_id": cid,
                    "channel": m["channel"],
                }

    @classmethod
    def load(cls, path: str):
        text = Path(path).read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return cls(data)

    def get_motor(self, motor_id: int):
        return self.motors[motor_id]

    def get_controller_for_motor(self, motor_id: int):
        info = self.motor_map[motor_id]
        ctrl = self.controllers[info["controller_id"]]
        return ctrl, info["channel"]