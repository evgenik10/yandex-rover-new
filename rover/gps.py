from dataclasses import dataclass


@dataclass
class GPSFix:
    lat: float = 0.0
    lon: float = 0.0
    speed_mps: float = 0.0
    course_deg: float = 0.0
    hdop: float = 99.9
    fix_quality: int = 0


class GPSReader:
    def __init__(self):
        self._fix = GPSFix()

    def read(self) -> GPSFix:
        return self._fix

    def set_simulated(self, lat: float, lon: float, hdop: float = 1.2) -> None:
        self._fix = GPSFix(lat=lat, lon=lon, hdop=hdop, fix_quality=1)
