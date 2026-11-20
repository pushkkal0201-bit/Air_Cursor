"""Security and launcher regression tests using a fake desktop controller."""
from __future__ import annotations

import pytest

from aircursor import cli
from aircursor.server import create_app


class FakeMouse:
    def __init__(self):
        self.x, self.y = 20, 30
        self.events = []

    def position(self):
        return self.x, self.y

    def move_to(self, x, y):
        self.x, self.y = x, y
        self.events.append(("absolute", x, y))

    def move_rel(self, dx, dy):
        self.x += dx
        self.y += dy
        self.events.append(("relative", dx, dy))

    def click(self, **kwargs):
        self.events.append(("click", kwargs))

    def scroll(self, **kwargs):
        self.events.append(("scroll", kwargs))

    def press(self, key):
        self.events.append(("press", key))


@pytest.fixture
def app_client():
    mouse = FakeMouse()
    app = create_app(mouse_instance=mouse, pairing_pin="123456")
    app.testing = True
    with app.test_client() as client:
        yield client, mouse


def pair(client, headers=None, **kw):
    return client.post(
        "/api/v1/pair", json={"pin": "123456"},
        headers=headers or {"X-AirCursor-Client": "1"}, **kw
    )


def headers():
    return {"X-AirCursor-Client": "1"}


def test_origin_and_trusted_host_guard(app_client):
    client, _ = app_client
    assert client.get("/api/v1/status", headers={"Host": "example.com"}).status_code == 421
    assert client.get("/api/v1/status", headers={"Host": "192.168.1.2:5055"}).status_code == 200
    assert client.get("/api/v1/status", headers={"Host": "127.0.0.1:5055"}).status_code == 200
    assert pair(client, headers={"X-AirCursor-Client": "1", "Origin": "https://localhost"}).status_code == 403
    assert pair(client, headers={"X-AirCursor-Client": "1", "Origin": "http://example.com"}).status_code == 403
    assert pair(client, headers={"X-AirCursor-Client": "1", "Origin": "http://localhost"}).status_code == 200


def test_session_tied_to_remote_ip(app_client):
    client, _ = app_client
    assert pair(client).status_code == 200
    assert client.get("/api/v1/cursor", environ_overrides={"REMOTE_ADDR": "10.0.0.8"}).status_code == 401
    assert client.get("/api/v1/cursor").status_code == 200


def test_session_capacity(app_client):
    client, _ = app_client
    for _ in range(16):
        assert pair(client).status_code == 200
    overflow = pair(client)
    assert overflow.status_code == 503
    assert overflow.json["error"] == "too_many_sessions"


def test_request_size_cap_and_security_headers(app_client):
    client, _ = app_client
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in response.headers
    assert b"touchpad.js" in response.data
    assert b'<script>' not in response.data
    assert client.get("/static/touchpad.js").status_code == 200
    assert client.post("/api/v1/pair", data='{"pin": "' + ("0" * 5000) + '"}',
                       content_type="application/json", headers=headers()).status_code == 413


def test_authenticated_origins_and_input_ranges(app_client):
    client, mouse = app_client
    assert pair(client).status_code == 200
    assert client.post("/api/v1/action", json={"action": "next_slide"},
                       headers={**headers(), "Origin": "http://localhost"}).status_code == 200
    assert client.post("/api/v1/action", json={"action": "next_slide"},
                       headers={**headers(), "Origin": "https://localhost"}).status_code == 403
    assert client.patch("/api/v1/cursor", json={"dx": float("nan"), "dy": 0},
                        headers=headers()).status_code == 400
    assert client.patch("/api/v1/cursor", json={"dx": 1001, "dy": 0},
                        headers=headers()).status_code == 400
    assert ("press", "right") in mouse.events


def test_cli_port_validation():
    assert cli.port_number("5055") == 5055
    for port in ["0", "80", "65536", "x"]:
        with pytest.raises(Exception):
            cli.port_number(port)


def test_cli_version_does_not_start_server(capsys):
    with pytest.raises(SystemExit) as stop:
        cli.main(["--version"])
    assert stop.value.code == 0
    assert "2.2.0" in capsys.readouterr().out


def test_cli_local_only_default(monkeypatch):
    monkeypatch.delenv("AIRCURSOR_HOST", raising=False)
    monkeypatch.delenv("AIRCURSOR_PORT", raising=False)
    monkeypatch.delenv("AIRCURSOR_HTTPS", raising=False)
    calls = []
    class FakeApp:
        config = {"PAIRING_PIN": "123456"}
        def run(self, **kwargs):
            calls.append(kwargs)
    monkeypatch.setattr(cli, "create_app", lambda: FakeApp())
    cli.main([])
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["debug"] is False
    cli.main(["--lan"])
    assert calls[1]["host"] == "0.0.0.0"
