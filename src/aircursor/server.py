"""AirCursor 2.1: paired local-network remote input server."""
from __future__ import annotations

import base64
import functools
import hmac
import io
import ipaddress
import os
import secrets
import socket
import time
from urllib.parse import urlsplit

import qrcode
from flask import Flask, jsonify, make_response, render_template, request

from .airmouse import AirMouse

SESSION_SECONDS = 60 * 60
MAX_SESSIONS = 16
VERSION = "2.2.0"
MAX_ATTEMPTS = 5
ATTEMPT_WINDOW = 120
ACTIONS = {
    "next_slide": "right", "previous_slide": "left",
    "play_pause": "playpause", "volume_up": "volumeup",
    "volume_down": "volumedown", "mute": "volumemute",
    "escape": "esc", "enter": "enter",
}


def _number(value, lower, upper):
    if isinstance(value, bool) or value is None:
        raise ValueError("numeric value required")
    try:
        number = float(value)
        if not number.is_integer() or not lower <= number <= upper:
            raise ValueError("out of range")
        return int(number)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("integer outside allowed range") from exc


def _local_ips():
    addresses = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            addresses.add(sock.getsockname()[0])
    except OSError:
        pass
    try:
        addresses.update(info[4][0] for info in
                         socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET))
    except OSError:
        pass
    return sorted(ip for ip in addresses if ip.startswith(("10.", "192.168.")) or (ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31))


def create_app(mouse_instance=None, pairing_pin=None):
    app = Flask(__name__, template_folder="templates")
    app.config["MAX_CONTENT_LENGTH"] = 2048
    app.config["PAIRING_PIN"] = pairing_pin or os.environ.get("AIRCURSOR_PAIRING_PIN") or f"{secrets.randbelow(1000000):06d}"
    mouse = mouse_instance if mouse_instance is not None else AirMouse()
    if mouse_instance is None:
        # Re-enable the PyAutoGUI corner fail-safe disabled by the original project.
        from . import airmouse
        airmouse.pyautogui.FAILSAFE = True
    sessions = {}
    failures = {}

    def _trusted_host(host):
        """Disallow DNS-rebinding via public hostnames and arbitrary Host values."""
        try:
            hostname = urlsplit("http://" + host).hostname
            if not hostname:
                return False
            if hostname == "localhost":
                return True
            parsed = ipaddress.ip_address(hostname)
            return parsed.is_loopback or parsed.is_private
        except (ValueError, TypeError):
            return False

    @app.before_request
    def check_host():
        if not _trusted_host(request.host):
            return jsonify(error="untrusted_host"), 421

    def _same_origin():
        origin = request.headers.get("Origin")
        if not origin:
            return True
        try:
            value = urlsplit(origin)
            return value.scheme == request.scheme and value.netloc == request.host
        except (ValueError, TypeError):
            return False

    def _prune(now):
        """Remove expired sessions/lockouts to bound in-memory state."""
        for key, info in list(sessions.items()):
            if info["expires"] <= now:
                sessions.pop(key, None)
        for key, (_count, reset) in list(failures.items()):
            if reset <= now:
                failures.pop(key, None)


    @app.after_request
    def secure_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), accelerometer=(self), gyroscope=(self)"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'"
        )
        return response

    def valid_session():
        token = request.cookies.get("aircursor_session", "")
        info = sessions.get(token)
        if not info:
            return False
        if info["expires"] <= time.time():
            sessions.pop(token, None)
            return False
        return hmac.compare_digest(info["ip"], request.remote_addr or "")

    def protected(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not valid_session():
                return jsonify(error="pairing_required"), 401
            if request.method != "GET":
                if not _same_origin():
                    return jsonify(error="invalid_origin"), 403
                if request.headers.get("X-AirCursor-Client") != "1":
                    return jsonify(error="client_header_required"), 403
            return fn(*args, **kwargs)
        return wrapper

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("JSON object required")
        return data

    @app.get("/")
    def home():
        host = os.environ.get("AIRCURSOR_HOST", "0.0.0.0")
        scheme = "https" if os.environ.get("AIRCURSOR_HTTPS") == "1" else "http"
        port = int(os.environ.get("AIRCURSOR_PORT", "5055"))
        urls = []
        if host != "127.0.0.1":
            for ip in _local_ips():
                urls.append(f"{scheme}://{ip}:{port}")
        qr = None
        if urls:
            picture = qrcode.make(urls[0])
            buffer = io.BytesIO()
            picture.save(buffer, format="PNG")
            qr = base64.b64encode(buffer.getvalue()).decode("ascii")
        return render_template("index.html", urls=urls, qr=qr)

    @app.get("/api/v1/status")
    def status():
        return jsonify(app="AirCursor", version=VERSION, paired=valid_session())

    @app.post("/api/v1/pair")
    def pair():
        if request.headers.get("X-AirCursor-Client") != "1":
            return jsonify(error="client_header_required"), 403
        if not _same_origin():
            return jsonify(error="invalid_origin"), 403
        ip = request.remote_addr or "unknown"
        now = time.time()
        _prune(now)
        count, reset = failures.get(ip, (0, now + ATTEMPT_WINDOW))
        if now >= reset:
            count, reset = 0, now + ATTEMPT_WINDOW
        if count >= MAX_ATTEMPTS:
            return jsonify(error="too_many_attempts", message="Try again in two minutes."), 429
        try:
            pin = str(body().get("pin", ""))
        except ValueError:
            return jsonify(error="invalid_json"), 400
        if not hmac.compare_digest(pin, app.config["PAIRING_PIN"]):
            failures[ip] = (count + 1, reset)
            return jsonify(error="incorrect_pin"), 401
        failures.pop(ip, None)
        if len(sessions) >= MAX_SESSIONS:
            return jsonify(error="too_many_sessions", message="Disconnect a paired device or restart the server."), 503
        token = secrets.token_urlsafe(32)
        sessions[token] = {"expires": now + SESSION_SECONDS, "ip": ip}
        response = make_response(jsonify(paired=True))
        response.set_cookie("aircursor_session", token, max_age=SESSION_SECONDS,
                            httponly=True, samesite="Strict",
                            secure=request.is_secure, path="/")
        return response

    @app.post("/api/v1/logout")
    @protected
    def logout():
        sessions.pop(request.cookies.get("aircursor_session", ""), None)
        response = make_response(jsonify(paired=False))
        response.delete_cookie("aircursor_session", path="/")
        return response

    @app.route("/api/v1/cursor", methods=["GET", "PUT", "PATCH"])
    @protected
    def cursor():
        if request.method == "GET":
            x, y = mouse.position()
            return jsonify(x=x, y=y)
        try:
            data = body()
            if request.method == "PATCH" and "dx" in data and "dy" in data:
                mouse.move_rel(_number(data["dx"], -1000, 1000),
                               _number(data["dy"], -1000, 1000))
            else:
                mouse.move_to(_number(data["x"], 0, 100000),
                              _number(data["y"], 0, 100000))
        except (ValueError, KeyError) as exc:
            return jsonify(error="validation_error", message=str(exc)), 400
        x, y = mouse.position()
        return jsonify(x=x, y=y)

    @app.post("/api/v1/click")
    @protected
    def click():
        try:
            data = body()
            button = data.get("button", "left")
            if button not in ("left", "right", "middle"):
                raise ValueError("unsupported button")
            clicks = _number(2 if data.get("double") is True else data.get("count", 1), 1, 2)
            at = data.get("at")
            kwargs = {}
            if at is not None:
                if not isinstance(at, dict):
                    raise ValueError("at must be an object")
                kwargs = {"x": _number(at["x"], 0, 100000),
                          "y": _number(at["y"], 0, 100000)}
            mouse.click(button=button, clicks=clicks, **kwargs)
        except (ValueError, KeyError) as exc:
            return jsonify(error="validation_error", message=str(exc)), 400
        return jsonify(result="ok")

    @app.post("/api/v1/scroll")
    @protected
    def scroll():
        try:
            data = body()
            dx = _number(data.get("dx", 0), -20, 20)
            dy = _number(data.get("dy", 0), -20, 20)
            mouse.scroll(dx=dx, dy=dy)
        except ValueError as exc:
            return jsonify(error="validation_error", message=str(exc)), 400
        return jsonify(result="ok")

    @app.post("/api/v1/action")
    @protected
    def action():
        try:
            name = body()["action"]
            if name not in ACTIONS:
                raise ValueError("unsupported action")
            if hasattr(mouse, "press"):
                mouse.press(ACTIONS[name])
            else:
                from .airmouse import pyautogui
                pyautogui.press(ACTIONS[name])
        except (ValueError, KeyError, TypeError) as exc:
            return jsonify(error="validation_error", message=str(exc)), 400
        return jsonify(result="ok")

    return app


def main():
    """Backwards-compatible entry point, delegated to the safe CLI."""
    from .cli import main as cli_main
    cli_main()




if __name__ == "__main__":
    main()
