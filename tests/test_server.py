"""Headless Flask integration tests for paired AirCursor API."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aircursor.server import create_app


class FakeMouse:
    def __init__(self):
        self.x = 40
        self.y = 60
        self.events = []

    def position(self):
        return self.x, self.y

    def move_to(self, x, y):
        self.x, self.y = x, y
        self.events.append(("move_to", x, y))

    def move_rel(self, dx, dy):
        self.x += dx
        self.y += dy
        self.events.append(("move_rel", dx, dy))

    def click(self, **kwargs):
        self.events.append(("click", kwargs))

    def scroll(self, **kwargs):
        self.events.append(("scroll", kwargs))

    def press(self, key):
        self.events.append(("press", key))


@pytest.fixture
def client():
    mouse = FakeMouse()
    app = create_app(mouse_instance=mouse, pairing_pin="123456")
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client, mouse


def headers():
    return {"X-AirCursor-Client": "1"}


def pair(client):
    return client.post("/api/v1/pair", json={"pin": "123456"}, headers=headers())


def test_requires_pairing(client):
    c, _ = client
    assert c.get("/api/v1/status").json["paired"] is False
    assert c.get("/api/v1/cursor").status_code == 401
    assert c.post("/api/v1/click", json={"button": "left"}, headers=headers()).status_code == 401


def test_pair_and_mouse_operations(client):
    c, mouse = client
    assert pair(c).status_code == 200
    assert c.get("/api/v1/status").json["paired"] is True
    assert c.patch("/api/v1/cursor", json={"dx": 2, "dy": -3}, headers=headers()).json == {"x": 42, "y": 57}
    assert c.put("/api/v1/cursor", json={"x": 100, "y": 120}, headers=headers()).json == {"x": 100, "y": 120}
    assert c.post("/api/v1/click", json={"button": "left", "count": 2}, headers=headers()).status_code == 200
    assert c.post("/api/v1/scroll", json={"dy": -2}, headers=headers()).status_code == 200
    assert c.post("/api/v1/action", json={"action": "next_slide"}, headers=headers()).status_code == 200
    assert ("press", "right") in mouse.events


def test_invalid_commands_and_cross_origin(client):
    c, _ = client
    assert pair(c).status_code == 200
    assert c.patch("/api/v1/cursor", json={"dx": 99999, "dy": 0}, headers=headers()).status_code == 400
    assert c.post("/api/v1/action", json={"action": "open_terminal"}, headers=headers()).status_code == 400
    assert c.post("/api/v1/click", json={"button": "left", "count": 100}, headers=headers()).status_code == 400
    assert c.post("/api/v1/action", json={"action": "enter"}).status_code == 403
    assert c.post("/api/v1/action", json={"action": "enter"},
                  headers={**headers(), "Origin": "https://attacker.example"}).status_code == 403


def test_pairing_rate_limit(client):
    c, _ = client
    for _ in range(5):
        assert c.post("/api/v1/pair", json={"pin": "111111"}, headers=headers()).status_code == 401
    assert c.post("/api/v1/pair", json={"pin": "123456"}, headers=headers()).status_code == 429


def test_logout_revokes_session(client):
    c, _ = client
    pair(c)
    assert c.post("/api/v1/logout", json={}, headers=headers()).status_code == 200
    assert c.get("/api/v1/cursor").status_code == 401

def test_dashboard_and_voice_assets(client):
    c, _ = client
    home = c.get("/")
    assert home.status_code == 200
    assert b'id="voice-start"' in home.data
    assert b'id="access-profile"' in home.data
    assert c.get("/static/advanced.js").status_code == 200
    assert c.get("/static/voice_commands.js").status_code == 200
    assert c.get("/api/v1/status").json["version"] == "2.3.0"
