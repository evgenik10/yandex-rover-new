import enum
import logging
import os
import time

from api_client import RoverAPIClient
from gps import GPSReader
from motors import MotorController
from sensors import SensorSuite


class PDDState(str, enum.Enum):
    BOOT = "BOOT"
    IDLE = "IDLE"
    ON_TRACK = "ON_TRACK"
    OBSTACLE_STOP = "OBSTACLE_STOP"
    HUMAN_STOP = "HUMAN_STOP"
    STOP_SIGN_STOP = "STOP_SIGN_STOP"
    GPS_DEGRADED = "GPS_DEGRADED"
    LINK_LOSS = "LINK_LOSS"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    ERROR = "ERROR"


class RoverRuntime:
    def __init__(self):
        self.mode_reported = "MANUAL"
        self.mode_desired = "MANUAL"
        self.pdd_state = PDDState.BOOT
        self.motors = MotorController()
        self.gps = GPSReader()
        self.sensors = SensorSuite()
        self.logger = logging.getLogger("rover.runtime")

    def tick(self):
        self.motors.tick()
        if self.sensors.distance_cm() < 80:
            self.motors.hard_stop()
            self.pdd_state = PDDState.OBSTACLE_STOP
        else:
            self.pdd_state = PDDState.IDLE


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def maybe_build_client() -> RoverAPIClient | None:
    server_url = os.getenv("ROVER_SERVER_URL", "").strip()
    rover_id = os.getenv("ROVER_ID", "").strip()
    token = os.getenv("ROVER_TOKEN", "").strip()
    if not server_url or not rover_id or not token:
        return None
    return RoverAPIClient(server_url, rover_id, token)


if __name__ == "__main__":
    setup_logging()
    rover = RoverRuntime()
    client = maybe_build_client()

    heartbeat_each_s = 2.0
    last_hb_ts = 0.0

    rover.logger.info("rover_start mode=%s state=%s", rover.mode_reported, rover.pdd_state)

    while True:
        rover.tick()

        now = time.time()
        if client and (now - last_hb_ts) >= heartbeat_each_s:
            payload = {
                "mode_reported": rover.mode_reported,
                "pdd_state": rover.pdd_state.value,
                "gps": {
                    "lat": rover.gps.read().lat,
                    "lon": rover.gps.read().lon,
                },
            }
            try:
                client.heartbeat(payload)
                rover.logger.info("link_state=ONLINE")
            except Exception:
                rover.logger.warning("link_state=OFFLINE reason=%s", client.last_error)
            last_hb_ts = now

        time.sleep(0.05)
