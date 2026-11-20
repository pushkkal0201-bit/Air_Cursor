# AirCursor 2.2 — Secure Local Controls and Windows Packaging

AirCursor 2.2 is a local-network computer control project with an authenticated phone touchpad, presentation/media controls, optional webcam hand gestures, push-to-talk voice shortcuts, accessible control profiles, and experimental phone motion controls.

**Original project:** [NiqueWrld/AirCursor](https://github.com/NiqueWrld/AirCursor), created by NiqueWrld. This project builds on the original MIT-licensed code. The original `LICENSE` is retained; see it for attribution and license terms.

## Features

- **Phone touchpad** — Move cursor, single/double/right click and two-finger scrolling.
- **Pairing PIN** — Random 6-digit PIN printed on the computer, HTTP-only one-hour session cookie, simple per-IP rate limiting and same-origin checks for state-changing requests.
- **QR / LAN addresses** — Connect on the same trusted Wi-Fi.
- **Media/presentation shortcuts** — Slides, volume, play/pause, mute, Escape and Enter. No arbitrary command execution.
- **Customizable controls** — Touch sensitivity, tap/hold mappings and experimental motion sensitivity stored in the phone browser.
- **Computer vision** — Optional local webcam hand tracking using OpenCV and MediaPipe with mouse control, pinch clicks, two-finger scrolling, cursor smoothing and JSON-configurable gesture actions.
- **Phone motion input (experimental)** — Browser DeviceOrientation sensors; requires a supported browser and trusted HTTPS origin.
- **Push-to-talk voice commands** — Browser speech recognition with strict command allowlist. Only predefined shortcuts/clicks/scrolling can run, with no free-text command execution.
- **Accessible UI profiles** — Comfort (large buttons and high contrast), precision (lower sensitivity), presentation (larger controls), reduced effects; stored locally.
- **Webcam stability** — Configurable pointer deadzone and optional dwell-click after a steady finger hold.

## Windows installer / portable executable

The `.github/workflows/windows.yml` workflow builds **both** a portable Windows ZIP and an unsigned Inno Setup installer on a Windows GitHub Actions runner. It runs a `AirCursor.exe --version` smoke test, then uploads the two build artifacts to the Actions run for manual download.

- Open **Actions → Windows executable and installer → latest successful run → Artifacts** and download either `AirCursor-2.2.0-Windows-Installer` or `AirCursor-2.2.0-Windows-Portable`.
- For the installer: extract the artifact ZIP and run `AirCursor-2.2.0-Windows-Setup.exe`. It installs per user without administrator privileges. The Start menu offers **This PC only** and **Private Wi-Fi** shortcuts. Use Private Wi-Fi only on a trusted network.
- For the portable ZIP: extract the ZIP and run `AirCursor.exe` (local-only) or `AirCursor.exe --lan` in Command Prompt. Keep the bundled files together.
- The installer is **unsigned**. Windows SmartScreen may warn; inspect the GitHub Actions source and verify the file before choosing to run it. No auto-start or network exposure occurs at install time.
- Installers are uploaded as temporary CI artifacts, **not** automatically published as a GitHub Release or to PyPI. Real Windows hardware, microphone, phone and camera testing is still required.

## Quick start on Windows (CMD)

Requires Python 3.11 (recommended), a computer and optionally a phone on the same private Wi-Fi.

```bat
cd C:\Users\dell\Air_Cursor
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py --lan
```

The server defaults to **localhost-only** when started without `--lan`. To connect a phone, explicitly run `python app.py --lan` or `aircursor --lan` on a **private, trusted Wi-Fi network**. To keep the server on this computer only, use `python app.py --local-only` or simply `python app.py`.

The server prints a **PAIRING PIN** locally in the terminal. Visit `http://127.0.0.1:5055` on your computer. On your phone, use the local IP URL or scan the QR code on the page, then enter the PIN displayed in the computer terminal. Never share the PIN in screenshots or public chats.

Stop the server with **Ctrl+C**. Set `AIRCURSOR_PORT` to change the port.

To explicitly bind to your computer only:

```bat
set AIRCURSOR_HOST=127.0.0.1
python app.py
```

To explicitly opt in to local Wi-Fi access:

```bat
python app.py --lan
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

To turn on optional **dwell-click**, edit `gesture_config.json`: set `"dwell_click_seconds": 1.5`. When one pointing finger remains in a small region for that duration, a single left click fires; moving the finger outside `dwell_radius` re-arms the feature. Dwell-click is **off by default** to avoid accidental input. `deadzone_pixels` ignores tiny movements in the webcam controller.

The optional webcam dependencies deliberately pin `mediapipe==0.10.21`, because newer MediaPipe releases removed the old `mp.solutions` API used by this controller. Python 3.11 is recommended.

## Voice commands (phase 3)

After pairing, open **Voice commands** in the web dashboard and choose **Listen for one command**. The page requests microphone access and stops recognition after one result. The **Stop listening** button and unpairing stop the microphone session. The application never stores audio or transcripts on the AirCursor server, although the **browser's speech recognition provider may process audio in the cloud**.

Supported exact phrases (English): `next slide`, `previous slide`, `play pause`, `volume up`, `volume down`, `mute`, `left click`, `right click`, `double click`, `scroll up`, `scroll down`, `escape`, `enter`. Unrecognized text is ignored. Only fixed, explicitly allowed commands are submitted to the server.

Voice support depends on the browser. Microphone input needs an HTTPS secure origin, or `http://localhost` on the same device. **An ordinary HTTP address on your phone's LAN is not a secure context**, so the touchpad still works but voice recognition normally does not. For phone voice, configure trusted HTTPS; see the warning below.

## Accessibility and comfort profiles

Choose **Standard**, **Comfort**, **Precision** or **Presentation** in the dashboard. Large buttons, high contrast and reduced visual effects can be toggled independently. The selected visual preferences remain on that browser only, not on the desktop server.

## Phone motion control (experimental)

Select **Enable motion** in the phone dashboard. The feature uses the standard browser orientation API, not the webcam. For many browsers the API is restricted to **secure HTTPS contexts** and requires sensor permission. An HTTP LAN URL will still support the touchpad, but motion input may be unavailable.

`AIRCURSOR_HTTPS=1` enables Flask's development-only self-signed HTTPS mode (requires `cryptography`), **not a trusted certificate**. For reliable sensor access, use a certificate the phone trusts and a suitable HTTPS reverse proxy. Do not bypass browser security warnings on an untrusted network.

## Release security hardening

- **Local-only by default**; LAN control is only enabled by an explicit `--lan` launch flag or advanced host configuration.
- Strict IP/localhost Host allowlist reduces DNS-rebinding exposure; cross-origin action requests are rejected and the app has no permissive CORS configuration.
- Input JSON is size-limited to 2 KiB. Device pairing remains time-limited and rate-limited. Sessions are IP-bound and the server stores no more than 16 live sessions.
- Mouse fail-safe is enabled; moving to a screen corner can interrupt automation. The phone UI serves its scripts as local files with a restrictive script Content Security Policy.
- These are defense-in-depth improvements, **not encryption**: plain HTTP on the local network can still leak the PIN/session to someone observing the network. Avoid public Wi-Fi and port forwarding. Use a properly trusted HTTPS reverse proxy for phone sensor/voice control.

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
python scripts/benchmark_api.py --requests 500
```

The CI matrix runs headless API/security tests, browser JavaScript syntax and voice parser tests, package build and metadata checks on Linux/Windows, and an **informational in-process API benchmark**. It does not claim real phone latency or webcam accuracy. Windows CI creates the executable and installer and runs an executable version smoke test. These do **not** substitute for manual hardware tests of the webcam, motion sensors or mobile browsers.

### Project layout

- `app.py` — Source checkout entry point.
- `src/aircursor/server.py` — Flask app and paired REST API.
- `src/aircursor/templates/index.html` — Mobile UI.
- `gesture_control.py` — Optional local webcam gesture controller.
- `gesture_config.json` — Customizable webcam gestures and dwell settings.
- `src/aircursor/static/touchpad.js` — External touchpad JavaScript for stronger CSP.
- `src/aircursor/static/voice_commands.js` — Strict client-side voice phrase parser.
- `src/aircursor/static/advanced.js` — Push-to-talk and accessibility settings.
- `requirements-vision.txt` — Optional computer-vision dependencies.
- `tests/` — Automated tests.
- `installer/AirCursor.iss` — Inno Setup installer recipe.
- `scripts/benchmark_api.py` — Reproducible fake-input API microbenchmark.
- `run_aircursor.py` — PyInstaller entry point.

You can also install the package in editable mode with `python -m pip install -e .` and launch using `aircursor` or `python -m aircursor`. `aircursor --version` works without starting the server.

## Manual validation checklist

Automated CI covers parser logic, API pairing, route availability, and simulated webcam dwell timing. It **cannot verify** physical webcam detection, a real phone's gyroscope, speech recognition services or Windows input behavior. On a trusted Windows laptop, check: pairing and logout, clicks and scrolling from your phone, voice controls on localhost or properly trusted HTTPS, comfort/precision profiles, the webcam gesture window, and optional dwell clicking.

## Safety and attribution

AirCursor controls the host computer's mouse and keyboard shortcuts; only run it on your own devices or ones you're permitted to control. No remote arbitrary shell commands are provided. The original project and its original MIT license belong to [NiqueWrld](https://github.com/NiqueWrld). This repository extends it; it is not a claim of authorship of the original code.
