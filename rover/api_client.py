import requests


class RoverAPIClient:
    def __init__(self, base_url: str, rover_id: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.rover_id = rover_id
        self.headers = {"Authorization": f"Bearer {token}"}

    def heartbeat(self, payload: dict) -> dict:
        url = f"{self.base_url}/api/rover/{self.rover_id}/heartbeat"
        r = requests.post(url, json=payload, headers=self.headers, timeout=3)
        r.raise_for_status()
        return r.json()

    def ack(self, seq_id: str, ok: bool, message: str = "") -> None:
        url = f"{self.base_url}/api/rover/{self.rover_id}/ack"
        requests.post(url, json={"seq_id": seq_id, "ok": ok, "message": message}, headers=self.headers, timeout=3)
