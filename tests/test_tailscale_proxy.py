"""Tailscale Serve HTTPS proxy regression tests using fake mouse only."""
from __future__ import annotations

import pytest
from aircursor import cli
from aircursor.server import create_app, normalize_tailscale_hostname

HOST = "aircursor-pc.sample-tailnet.ts.net"


class FakeMouse:
    def position(self):
        return (100, 100)
    def move_rel(self, dx, dy):
        pass
    def move_to(self, x, y):
        pass
    def click(self, **kwargs):
        pass
    def scroll(self, **kwargs):
        pass
    def press(self, key):
        pass


def proxy_headers(**extra):
    headers = {
        "Host": "127.0.0.1:5055",
        "X-Forwarded-Host": HOST,
        "X-Forwarded-Proto": "https",
        "X-AirCursor-Client": "1",
        "Origin": "https://" + HOST,
        "X-Forwarded-For": "100.64.1.2",
    }
    headers.update(extra)
    return headers


def test_exact_hostname_validation():
    assert normalize_tailscale_hostname(HOST.upper()) == HOST
    for host in ("https://" + HOST, HOST + "/",
                 "evil.example.org", "*.ts.net", "foo.ts.net",
                 "dev..tailnet.ts.net", "localhost", "x." + HOST + ":443"):
        with pytest.raises(ValueError):
            normalize_tailscale_hostname(host)


def test_https_tailscale_pair_cookie_origin_and_qr():
    app = create_app(mouse_instance=FakeMouse(), pairing_pin="123456", tailscale_host=HOST)
    app.testing = True
    client = app.test_client()
    status = client.get("/api/v1/status", headers=proxy_headers())
    assert status.status_code == 200
    assert status.json["version"] == "2.3.0"
    home = client.get("/", headers=proxy_headers())
    assert home.status_code == 200
    assert ("https://" + HOST).encode() in home.data
    assert b"motion_math.js" in home.data
    assert b"motion-transport" in home.data
    pair = client.post("/api/v1/pair", json={"pin": "123456"}, headers=proxy_headers())
    assert pair.status_code == 200
    assert "Secure" in pair.headers["Set-Cookie"]
    assert "HttpOnly" in pair.headers["Set-Cookie"]
    assert "max-age=86400" in pair.headers["Strict-Transport-Security"]
    click = client.post("/api/v1/click", json={"button": "left"}, headers=proxy_headers())
    assert click.status_code == 200


def test_reject_wrong_host_insecure_origin_and_other_proxy_client():
    app = create_app(mouse_instance=FakeMouse(), pairing_pin="123456", tailscale_host=HOST)
    app.testing = True
    c = app.test_client()
    assert c.get("/api/v1/status",
                 headers=proxy_headers(**{"X-Forwarded-Host": "evil.other.ts.net"})).status_code == 421
    assert c.get("/api/v1/status",
                 headers=proxy_headers(**{"X-Forwarded-Proto": "http"})).status_code == 421
    assert c.post("/api/v1/pair", json={"pin": "123456"},
                  headers=proxy_headers(**{"Origin": "https://other.sample-tailnet.ts.net"})).status_code == 403
    assert c.post("/api/v1/pair", json={"pin": "123456"},
                  headers=proxy_headers(**{"Origin": "http://" + HOST})).status_code == 403
    assert c.get("/api/v1/status",
                 headers=proxy_headers(**{"X-Forwarded-Host": "evil.com"})).status_code == 421


def test_proxy_headers_ignored_without_opt_in():
    app = create_app(mouse_instance=FakeMouse(), pairing_pin="123456")
    app.testing = True
    c = app.test_client()
    response = c.post("/api/v1/pair", json={"pin": "123456"}, headers=proxy_headers())
    assert response.status_code == 403


def test_cli_proxy_launch_forces_local_and_passes_host(monkeypatch):
    monkeypatch.delenv("AIRCURSOR_HOST", raising=False)
    monkeypatch.delenv("AIRCURSOR_HTTPS", raising=False)
    monkeypatch.delenv("AIRCURSOR_PORT", raising=False)
    results = []
    class App:
        config = {"PAIRING_PIN": "000000"}
        def run(self, **kwargs):
            results.append(("run", kwargs))
    def fake_app(**kwargs):
        results.append(("create", kwargs))
        return App()
    monkeypatch.setattr(cli, "create_app", fake_app)
    cli.main(["--tailscale-host", HOST])
    assert results[0] == ("create", {"tailscale_host": HOST})
    assert results[1][1]["host"] == "127.0.0.1"
    assert results[1][1]["ssl_context"] is None
    with pytest.raises(SystemExit):
        cli.main(["--lan", "--tailscale-host", HOST])
    with pytest.raises(SystemExit):
        cli.main(["--tailscale-host", "not-a-ts.net"])
    with pytest.raises(SystemExit):
        cli.main(["--https", "--tailscale-host", HOST])


def test_proxy_host_requires_local_bind(monkeypatch):
    monkeypatch.setenv("AIRCURSOR_HOST", "0.0.0.0")
    with pytest.raises(SystemExit):
        cli.main(["--tailscale-host", HOST])
