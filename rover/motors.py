import time
from dataclasses import dataclass


@dataclass
class MotionCommand:
    left: float
    right: float
    ttl_s: float


class MotorController:
    def __init__(self, max_speed: float = 1.0):
        self.max_speed = max_speed
        self._last_cmd_ts = 0.0
        self._ttl_s = 0.0
        self._left = 0.0
        self._right = 0.0

    def set_speed(self, left: float, right: float, ttl_s: float = 1.5) -> None:
        self._left = max(-self.max_speed, min(self.max_speed, left))
        self._right = max(-self.max_speed, min(self.max_speed, right))
        self._ttl_s = ttl_s
        self._last_cmd_ts = time.time()

    def soft_stop(self, decel_step: float = 0.2) -> None:
        self._left *= (1 - decel_step)
        self._right *= (1 - decel_step)
        if abs(self._left) < 0.05:
            self._left = 0.0
        if abs(self._right) < 0.05:
            self._right = 0.0

    def hard_stop(self) -> None:
        self._left = 0.0
        self._right = 0.0

    def tick(self) -> None:
        if time.time() - self._last_cmd_ts > self._ttl_s:
            self.hard_stop()

    @property
    def state(self) -> dict:
        return {"left": self._left, "right": self._right}
