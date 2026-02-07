import logging
from typing import Optional

import requests


class RoverAPIClient:
    def __init__(self, base_url: str, rover_id: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.rover_id = rover_id
        self.headers = {"Authorization": f"Bearer {token}"}
        self.logger = logging.getLogger("rover.api")
        self._connected = False
        self._last_error: Optional[str] = None

    def heartbeat(self, payload: dict) -> dict:
        url = f"{self.base_url}/api/rover/{self.rover_id}/heartbeat"
        try:
            r = requests.post(url, json=payload, headers=self.headers, timeout=3)
            r.raise_for_status()
            self._connected = True
            self._last_error = None
            self.logger.info("heartbeat_ok rover_id=%s status=%s", self.rover_id, r.status_code)
            return r.json()
        except requests.RequestException as exc:
            self._connected = False
            self._last_error = str(exc)
            self.logger.warning("heartbeat_fail rover_id=%s error=%s", self.rover_id, exc)
            raise

    def ack(self, seq_id: str, ok: bool, message: str = "") -> None:
        url = f"{self.base_url}/api/rover/{self.rover_id}/ack"
        try:
            r = requests.post(
                url,
                json={"seq_id": seq_id, "ok": ok, "message": message},
                headers=self.headers,
                timeout=3,
            )
            r.raise_for_status()
            self.logger.info("ack_ok rover_id=%s seq_id=%s status=%s", self.rover_id, seq_id, r.status_code)
        except requests.RequestException as exc:
            self.logger.warning("ack_fail rover_id=%s seq_id=%s error=%s", self.rover_id, seq_id, exc)
            raise

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error
