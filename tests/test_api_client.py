import pytest

requests = pytest.importorskip("requests")

from rover.api_client import RoverAPIClient


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"ok": True}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")

    def json(self):
        return self._payload


def test_heartbeat_marks_connected(monkeypatch):
    def _ok_post(*args, **kwargs):
        return _Resp(status_code=200, payload={"ok": True})

    monkeypatch.setattr(requests, "post", _ok_post)
    c = RoverAPIClient("http://localhost:8000", "rover-1", "token")
    c.heartbeat({"mode_reported": "MANUAL"})
    assert c.is_connected is True
    assert c.last_error is None


def test_heartbeat_marks_disconnected_on_error(monkeypatch):
    def _bad_post(*args, **kwargs):
        raise requests.ConnectionError("unreachable")

    monkeypatch.setattr(requests, "post", _bad_post)
    c = RoverAPIClient("http://localhost:8000", "rover-1", "token")

    with pytest.raises(requests.RequestException):
        c.heartbeat({"mode_reported": "MANUAL"})

    assert c.is_connected is False
    assert "unreachable" in (c.last_error or "")
