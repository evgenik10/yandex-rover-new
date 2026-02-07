import enum
import logging
import os
import time
from pathlib import Path

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


def read_client_settings_from_yaml() -> tuple[str, str, str]:
    cfg_path = Path(__file__).with_name("config.yaml")
    if not cfg_path.exists():
        return "", "", ""

    try:
        import yaml  # type: ignore

        data = yaml.safe_load(cfg_path.read_text()) or {}
        return (
            str((data.get("server") or {}).get("base_url") or "").strip(),
            str((data.get("rover") or {}).get("id") or "").strip(),
            str((data.get("rover") or {}).get("token") or "").strip(),
        )
    except Exception:
        # YAML parser may be unavailable; env vars can still be used.
        return "", "", ""


def maybe_build_client() -> RoverAPIClient | None:
    cfg_server_url, cfg_rover_id, cfg_token = read_client_settings_from_yaml()
    server_url = os.getenv("ROVER_SERVER_URL", cfg_server_url).strip()
    rover_id = os.getenv("ROVER_ID", cfg_rover_id).strip()
    token = os.getenv("ROVER_TOKEN", cfg_token).strip()
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
    if client:
        rover.logger.info("client_configured rover_id=%s server=%s", client.rover_id, client.base_url)
    else:
        rover.logger.warning(
            "client_not_configured set ROVER_SERVER_URL/ROVER_ID/ROVER_TOKEN or fill rover/config.yaml"
        )

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
