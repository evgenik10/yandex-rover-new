import math
from dataclasses import dataclass


@dataclass
class Waypoint:
    lat: float
    lon: float


class Navigator:
    def __init__(self, corridor_m: float = 2.0):
        self.corridor_m = corridor_m

    @staticmethod
    def haversine_m(a_lat, a_lon, b_lat, b_lon):
        r = 6371000
        p1, p2 = math.radians(a_lat), math.radians(b_lat)
        dp = math.radians(b_lat - a_lat)
        dl = math.radians(b_lon - a_lon)
        q = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.atan2(math.sqrt(q), math.sqrt(1 - q))

    def off_track(self, current, target) -> bool:
        return self.haversine_m(current.lat, current.lon, target.lat, target.lon) > self.corridor_m
