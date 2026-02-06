import statistics
from collections import deque


class SensorSuite:
    def __init__(self, window: int = 5):
        self._distance = deque(maxlen=window)
        self._battery_v = deque(maxlen=window)

    def push_distance(self, cm: float) -> None:
        self._distance.append(cm)

    def push_battery(self, volts: float) -> None:
        self._battery_v.append(volts)

    def distance_cm(self) -> float:
        return statistics.median(self._distance) if self._distance else 999.0

    def battery_v(self) -> float:
        return statistics.median(self._battery_v) if self._battery_v else 0.0
