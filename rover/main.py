import enum
import time

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

    def tick(self):
        self.motors.tick()
        if self.sensors.distance_cm() < 80:
            self.motors.hard_stop()
            self.pdd_state = PDDState.OBSTACLE_STOP
        else:
            self.pdd_state = PDDState.IDLE


if __name__ == "__main__":
    rover = RoverRuntime()
    while True:
        rover.tick()
        time.sleep(0.05)
