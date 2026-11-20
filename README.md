# AirCursor 2.0 — Remote Mouse + Webcam Gestures

AirCursor 2.0 is a local-network computer control project with an authenticated phone touchpad, presentation/media controls, an optional webcam-based hand-gesture controller, and experimental phone motion controls.

**Original project:** [NiqueWrld/AirCursor](https://github.com/NiqueWrld/AirCursor), created by NiqueWrld. This project builds on the original MIT-licensed code. The original `LICENSE` is retained; see it for attribution and license terms.

## Features

- **Phone touchpad** — Move cursor, single/double/right click and two-finger scrolling.
- **Pairing PIN** — Random 6-digit PIN printed on the computer, HTTP-only one-hour session cookie, simple per-IP rate limiting and same-origin checks for state-changing requests.
- **QR / LAN addresses** — Connect on the same trusted Wi-Fi.
- **Media/presentation shortcuts** — Slides, volume, play/pause, mute, Escape and Enter. No arbitrary command execution.
- **Customizable controls** — Touch sensitivity, tap/hold mappings and experimental motion sensitivity stored in the phone browser.
- **Computer vision** — Optional local webcam hand tracking using OpenCV and MediaPipe with mouse control, pinch clicks, two-finger scrolling, cursor smoothing and JSON-configurable gesture actions.
- **Phone motion input (experimental)** — Browser DeviceOrientation sensors; requires a supported browser and trusted HTTPS origin.

## Quick start on Windows (CMD)

Requires Python 3.11 (recommended), a computer and optionally a phone on the same private Wi-Fi.

```bat
cd C:\Users\dell\Air_Cursor
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

The server prints a **PAIRING PIN** locally in the terminal. Visit `http://127.0.0.1:5055` on your computer. On your phone, use the local IP URL or scan the QR code on the page, then enter the PIN displayed in the computer terminal. Never share the PIN in screenshots or public chats.

Stop the server with **Ctrl+C**. Set `AIRCURSOR_PORT` to change the port.

To disable phone/network access and bind to your computer only:

```bat
set AIRCURSOR_HOST=127.0.0.1
python app.py
```

To explicitly run on the local network (the default):

```bat
set AIRCURSOR_HOST=0.0.0.0
python app.py
```

Only allow the Windows Firewall prompt on **private/trusted networks**, not public networks. HTTP traffic, including the pairing PIN, is **not encrypted**. The PIN protects from accidental/unauthorized access but **does not make HTTP secure**. Never forward the port, use this over public Wi-Fi, or expose it on the internet.

## Webcam hand gesture control

```bat
python -m pip install -r requirements-vision.txt
python gesture_control.py
```

The webcam runs **locally** in a separate process, and is not started by a remote phone. The controller draws the hand landmarks and shows the recognized action in a local camera window. Press **Q** or **Esc** to stop.

| Gesture | Action |
|---|---|
| Point with index finger | Move the cursor |
| Touch thumb to index fingertip | Left click |
| Touch thumb to middle fingertip | Right click |
| Extend index + middle fingers and move vertically | Scroll |

Edit `gesture_config.json` to change the camera index, smoothing, pinch sensitivity, scroll speed, and the `index_pinch` / `middle_pinch` mappings. Allowed mapping values: `left_click`, `right_click`, `double_click`, `middle_click`, `none`. You can also pass a custom file via `python gesture_control.py --config your-settings.json`.

The optional webcam dependencies deliberately pin `mediapipe==0.10.21`, because newer MediaPipe releases removed the old `mp.solutions` API used by this controller. Python 3.11 is recommended.

## Phone motion control (experimental)

Select **Enable motion** in the phone dashboard. The feature uses the standard browser orientation API, not the webcam. For many browsers the API is restricted to **secure HTTPS contexts** and requires sensor permission. An HTTP LAN URL will still support the touchpad, but motion input may be unavailable.

`AIRCURSOR_HTTPS=1` enables Flask's development-only self-signed HTTPS mode (requires `cryptography`), **not a trusted certificate**. For reliable sensor access, use a certificate the phone trusts and a suitable HTTPS reverse proxy. Do not bypass browser security warnings on an untrusted network.

## API (paired session required)

- `GET /api/v1/status` — Connection state, accessible before pairing.
- `POST /api/v1/pair` — Pair with `{"pin":"123456"}` (example only).
- `POST /api/v1/logout` — Revoke session.
- `GET /api/v1/cursor` — Cursor position.
- `PUT /api/v1/cursor` — Absolute coordinates `{"x":500,"y":300}`.
- `PATCH /api/v1/cursor` — Relative movement `{"dx":10,"dy":-4}`.
- `POST /api/v1/click` — `{"button":"left","count":1}`.
- `POST /api/v1/scroll` — `{"dy":-2}`.
- `POST /api/v1/action` — `{"action":"next_slide"}`.

POST/PUT/PATCH requests also require `X-AirCursor-Client: 1` and an authenticated same-origin session cookie.

## Development and testing

```bat
python -m pip install pytest
python -m pytest -q
```

The repo includes a GitHub Actions workflow for headless server tests, input validation, pairing/rate-limit checks and gesture configuration tests. These do **not** substitute for manual hardware tests of the webcam, motion sensors or mobile browsers.

### Project layout

- `app.py` — Source checkout entry point.
- `src/aircursor/server.py` — Flask app and paired REST API.
- `src/aircursor/templates/index.html` — Mobile UI.
- `gesture_control.py` — Optional local webcam gesture controller.
- `gesture_config.json` — Customizable webcam gestures.
- `requirements-vision.txt` — Optional computer-vision dependencies.
- `tests/` — Automated tests.

You can also install the package in editable mode with `python -m pip install -e .` and launch using `aircursor` or `python -m aircursor`.

## Safety and attribution

AirCursor controls the host computer's mouse and keyboard shortcuts; only run it on your own devices or ones you're permitted to control. No remote arbitrary shell commands are provided. The original project and its original MIT license belong to [NiqueWrld](https://github.com/NiqueWrld). This repository extends it; it is not a claim of authorship of the original code.
