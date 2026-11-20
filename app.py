from __future__ import annotations

import logging
import os
import socket
import base64
import io
import ipaddress
from typing import Any, Dict, Optional

from flask import Flask, Blueprint, jsonify, request, Response, render_template
from flask_cors import CORS

from airmouse import AirMouse
import qrcode


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # Disable Flask/Werkzeug logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.logger.disabled = True

    logging.basicConfig(
        level=os.getenv("AIRCURSOR_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    api = Blueprint("api", __name__, url_prefix="/api/v1")

    mouse = AirMouse()

    @app.errorhandler(400)
    def handle_400(err):
        return jsonify({"error": "bad_request", "message": str(err)}), 400

    @app.errorhandler(404)
    def handle_404(err):
        return jsonify({"error": "not_found", "message": "resource not found"}), 404

    @app.errorhandler(415)
    def handle_415(err):
        return jsonify({"error": "unsupported_media_type", "message": "use application/json"}), 415

    @app.errorhandler(Exception)
    def handle_exception(err: Exception):
        app.logger.exception("Unhandled error: %s", err)
        return jsonify({"error": "internal_error", "message": "unexpected server error"}), 500

    @api.get("/status")
    def get_status():
        return jsonify(
            {
                "app": "AirCursor",
                "status": "ok",
                "version": "1.0.0",
                "platform": os.name,
            }
        )

    @api.get("/cursor")
    def get_cursor():
        x, y = mouse.position()
        return jsonify({"x": x, "y": y})

    @api.put("/cursor")
    def put_cursor():
        if not request.is_json:
            return handle_415(None)
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        if not _has_keys(data, ["x", "y"], allow_partial=False):
            return (
                jsonify({"error": "validation_error", "message": "require numeric 'x' and 'y'"}),
                400,
            )
        try:
            x = _as_int(data.get("x"))
            y = _as_int(data.get("y"))
        except (TypeError, ValueError):
            return jsonify({"error": "validation_error", "message": "x and y must be integers"}), 400
        mouse.move_to(x, y)
        nx, ny = mouse.position()
        return jsonify({"x": nx, "y": ny})

    @api.patch("/cursor")
    def patch_cursor():
        if not request.is_json:
            return handle_415(None)
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        if _has_keys(data, ["dx", "dy"], allow_partial=False):
            try:
                dx = _as_int(data.get("dx"))
                dy = _as_int(data.get("dy"))
            except (TypeError, ValueError):
                return jsonify({"error": "validation_error", "message": "dx and dy must be integers"}), 400
            mouse.move_rel(dx, dy)
        elif _has_keys(data, ["x", "y"], allow_partial=False):
            try:
                x = _as_int(data.get("x"))
                y = _as_int(data.get("y"))
            except (TypeError, ValueError):
                return jsonify({"error": "validation_error", "message": "x and y must be integers"}), 400
            mouse.move_to(x, y)
        else:
            return (
                jsonify(
                    {
                        "error": "validation_error",
                        "message": "provide either {dx,dy} for relative or {x,y} for absolute",
                    }
                ),
                400,
            )
        x2, y2 = mouse.position()
        return jsonify({"x": x2, "y": y2})

    @api.post("/click")
    def post_click():
        if not request.is_json:
            return handle_415(None)
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        button = (data.get("button") or "left").lower()
        if button not in ("left", "right", "middle"):
            return jsonify({"error": "validation_error", "message": "button must be left|right|middle"}), 400
        count = data.get("count")
        double = data.get("double")
        try:
            clicks = 2 if isinstance(double, bool) and double else (1 if count is None else _as_int(count))
        except (TypeError, ValueError):
            return jsonify({"error": "validation_error", "message": "count must be integer"}), 400
        at: Optional[Dict[str, Any]] = data.get("at")
        if at is not None:
            if not _has_keys(at, ["x", "y"], allow_partial=False):
                return jsonify({"error": "validation_error", "message": "at requires x and y"}), 400
            try:
                x = _as_int(at.get("x"))
                y = _as_int(at.get("y"))
            except (TypeError, ValueError):
                return jsonify({"error": "validation_error", "message": "at.x and at.y must be integers"}), 400
            mouse.click(button=button, clicks=clicks, x=x, y=y)
        else:
            mouse.click(button=button, clicks=clicks)
        return jsonify({"result": "ok"}), 201

    @api.post("/scroll")
    def post_scroll():
        if not request.is_json:
            return handle_415(None)
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        if "dy" not in data and "dx" not in data:
            return jsonify({"error": "validation_error", "message": "provide dy and/or dx"}), 400
        try:
            dy = _as_int(data.get("dy")) if data.get("dy") is not None else 0
            dx = _as_int(data.get("dx")) if data.get("dx") is not None else 0
        except (TypeError, ValueError):
            return jsonify({"error": "validation_error", "message": "dx/dy must be integers"}), 400
        mouse.scroll(dx=dx, dy=dy)
        return jsonify({"result": "ok"}), 201

    app.register_blueprint(api)

    @app.get("/")
    def root():
        if request.args.get("format") == "json":
            return jsonify({"message": "AirCursor API", "docs": "/api/v1/status"})

        port = int(os.getenv("AIRCURSOR_PORT", "5055"))
        ips = _candidate_ips()
        entries = []
        for ip in ips:
            url = f"http://{ip}:{port}"
            img_data = _qr_data_url(url)
            entries.append({"ip": ip, "url": url, "img": img_data})

        return render_template("index.html", entries=entries)

    return app


def _has_keys(d: Dict[str, Any], keys: list[str], *, allow_partial: bool) -> bool:
    if allow_partial:
        return any(k in d for k in keys)
    return all(k in d for k in keys)


def _as_int(v: Any) -> int:
    if isinstance(v, bool):
        raise ValueError("bool not allowed")
    if isinstance(v, (int,)):
        return int(v)
    if isinstance(v, (float, str)):
        return int(float(v))
    raise TypeError("unsupported type")


def _candidate_ips() -> list[str]:
    ips: set[str] = set()
    # Primary outbound IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
    except Exception:
        pass
    finally:
        try:
            s.close()  # type: ignore[name-defined]
        except Exception:
            pass

    # Hostname-bound addresses
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET):
            ips.add(info[4][0])
    except Exception:
        pass

    # Env host
    host = os.getenv("AIRCURSOR_HOST")
    if host and host != "0.0.0.0":
        ips.add(host)

    # Always include localhost
    ips.add("127.0.0.1")

    def ok(ip: str) -> bool:
        try:
            ipobj = ipaddress.ip_address(ip)
            if ipobj.is_loopback:
                return True
            if ipobj.is_private and not ipobj.is_link_local:
                return True
            return False
        except Exception:
            return False

    ordered = [ip for ip in ips if ok(ip)]
    # Prefer non-loopback first
    ordered.sort(key=lambda x: (x.startswith("127."), x))
    return ordered


def _qr_data_url(text: str) -> str:
    qr = qrcode.QRCode(border=2, box_size=8)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


app = create_app()


if __name__ == "__main__":
    # ANSI color codes
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    print(f"\n{CYAN}")
    print("     _    ___ ____   ____ _   _ ____  ____   ___  ____  ")
    print("    / \\  |_ _|  _ \\ / ___| | | |  _ \\/ ___| / _ \\|  _ \\ ")
    print("   / _ \\  | || |_) | |   | | | | |_) \\___ \\| | | | |_) |")
    print("  / ___ \\ | ||  _ <| |___| |_| |  _ < ___) | |_| |  _ < ")
    print(" /_/   \\_\\___|_| \\_\\\\____\\___/|_| \\_\\____/ \\___/|_| \\_\\")
    print(f"{RESET}")
    print(f"{YELLOW}         Remote Mouse Control Server{RESET}")
    print(f"{GREEN}         Created by: NiqueWrld{RESET}")
    print(f"{BLUE}         GitHub: https://github.com/NiqueWrld")
    print()
    
    host = os.getenv("AIRCURSOR_HOST", "0.0.0.0")
    port = int(os.getenv("AIRCURSOR_PORT", "5055"))
    debug = os.getenv("AIRCURSOR_DEBUG", "false").lower() == "true"
    
    print(f"{BOLD}{GREEN}🚀 Starting AirCursor Server...{RESET}")
    print(f"{YELLOW}📡 Port: {BOLD}{port}{RESET}")
    if debug:
        print(f"{YELLOW}🔧 Debug Mode: {BOLD}ON{RESET}")
    
    # Get and display all available IP addresses
    ips = _candidate_ips()
    print(f"{YELLOW}🌐 Available on:{RESET}")
    for ip in ips:
        print(f"   {BLUE}http://{BOLD}{ip}:{port}/{RESET}")

    print(f"\n{CYAN}─────────────────────────────────────────{RESET}")
    
    print(f"\n{GREEN}📱 Quick Usage:{RESET}")
    print(f"   • Open any URL above in your browser")
    print(f"   • Scan QR code with your phone")
    print(f"   • Use trackpad gestures to control mouse")
    print(f"   • API available at /api/v1/")
    print()
    
    # Generate and display QR code for the primary IP
    if ips:
        primary_url = f"http://{ips[0]}:{port}"
        qr = qrcode.QRCode(border=1, box_size=1)
        qr.add_data(primary_url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    
    print(f"\n{CYAN}─────────────────────────────────────────{RESET}")
    print(f"{YELLOW}💡 Press Ctrl+C to stop the server{RESET}\n")
    
    app.run(host=host, port=port, debug=debug, use_reloader=False)
