# Commit Message Reference — AirCursor

> **Product tagline:** One desktop. Four ways to control.

This file provides **file-specific subject line examples for future changes**. It does not represent a change to existing Git commit history. Git records commit messages on *commits*, not on files; one commit may cover several related files.

## Conventions

Use `type(scope): concise explanation of the change` with a subject that reflects the **actual diff**. Avoid claiming that a feature was added if only documentation, formatting, or configuration was changed. A meaningful single-purpose change should generally have one relevant commit, even when it touches several files.

Common types: `feat` (behavior), `fix` (bug), `docs` (documentation), `design` (visual assets), `test` (tests), `build` (packaging/dependencies), `ci` (automation), `refactor` (no user-visible feature), and `chore` (maintenance).

## File-by-file commit subject examples

| File | Example commit subject | Responsibility |
|:--|:--|:--|
| `README.md` | `docs(readme): explain multi-modal controls and deployment workflow` | Feature documentation and setup |
| `docs/assets/aircursor-hero.svg` | `design(hero): illustrate phone and webcam desktop controls` | Visual identity and product tagline |
| `docs/assets/control-modes.svg` | `design(modes): visualize touch, tilt, vision, and voice inputs` | Four input modes |
| `docs/assets/connection-topology.svg` | `design(network): illustrate localhost, LAN, and tailnet access` | Connection security illustration |
| `.gitignore` | `chore(git): exclude generated artifacts and local environments` | Version-control hygiene |
| `LICENSE` | `chore(license): retain applicable MIT copyright notice` | License notices; change only when legally appropriate |
| `app.py` | `refactor(launcher): delegate source execution to the AirCursor CLI` | Python source launcher |
| `airmouse.py` | `refactor(compat): maintain legacy PyAutoGUI input adapter` | Top-level compatibility module |
| `gesture_control.py` | `feat(vision): detect hand landmarks and map gestures to desktop actions` | Webcam gesture recognition |
| `gesture_config.json` | `config(vision): tune smoothing, pinch detection, and dwell settings` | Gesture controller configuration |
| `requirements.txt` | `build(deps): install AirCursor package dependencies` | Core package requirements |
| `requirements-vision.txt` | `build(vision): declare compatible OpenCV and MediaPipe dependencies` | Optional vision requirements |
| `pyproject.toml` | `build(package): define metadata, dependencies, and CLI entry point` | Packaging metadata |
| `run_aircursor.py` | `build(windows): provide packaged executable entry point` | PyInstaller launcher |
| `scripts/benchmark_api.py` | `test(benchmark): measure in-process paired cursor API overhead` | Headless API microbenchmark |
| `installer/AirCursor.iss` | `build(installer): configure per-user Windows installation and shortcuts` | Inno Setup packaging |
| `src/aircursor/__init__.py` | `refactor(package): expose AirCursor package API and version` | Package exports |
| `src/aircursor/__main__.py` | `refactor(cli): support python -m aircursor invocation` | Module entry point |
| `src/aircursor/app.py` | `refactor(wsgi): expose Flask app factory for development` | WSGI compatibility |
| `src/aircursor/cli.py` | `feat(cli): validate host, port, and private network launch options` | Launch modes and arguments |
| `src/aircursor/server.py` | `feat(api): validate paired sessions and route permitted desktop actions` | Flask HTTP service and safeguards |
| `src/aircursor/airmouse.py` | `feat(input): wrap mouse and shortcut actions with PyAutoGUI` | Host OS input adapter |
| `src/aircursor/templates/index.html` | `feat(ui): organize paired touchpad and advanced browser controls` | Current web dashboard |
| `templates/index.html` | `refactor(legacy-ui): maintain compatible touchpad template` | Legacy standalone template |
| `src/aircursor/static/touchpad.js` | `feat(touch): process taps, scrolling, movement, and phone motion` | Touch/motion browser controller |
| `src/aircursor/static/motion_math.js` | `feat(motion): map calibrated phone orientation to bounded pointer deltas` | Tilt math |
| `src/aircursor/static/voice_commands.js` | `feat(voice): map recognized phrases to supported actions` | Voice allowlist/parser |
| `src/aircursor/static/advanced.js` | `feat(accessibility): manage voice capture and local UI profiles` | Voice UI and preference state |
| `tests/test_server.py` | `test(api): cover pairing, mouse operations, and error responses` | REST API integration tests |
| `tests/test_hardening.py` | `test(security): validate host, session, and request restrictions` | Security tests |
| `tests/test_tailscale_proxy.py` | `test(proxy): verify trusted private HTTPS proxy behavior` | Tailscale proxy tests |
| `tests/test_gestures.py` | `test(vision): check gesture configuration and dwell tracking` | Gesture logic tests |
| `tests/motion.test.cjs` | `test(motion): cover orientation dead zones and movement limits` | Browser sensor math tests |
| `tests/voice.test.cjs` | `test(voice): verify allowed speech phrases and rejected text` | Voice parser tests |
| `.github/workflows/ci.yml` | `ci(tests): run Python and browser checks across platforms` | Continuous integration |
| `.github/workflows/windows.yml` | `ci(windows): package portable executable and installer artifacts` | Windows packaging workflow |
| `.github/workflows/release.yml` | `ci(package): validate source distributions and wheel metadata` | Package validation workflow |

## Commit examples

**Scoped documentation update**

```text
docs(readme): clarify Tailscale Serve onboarding and sensor permissions
```

**API authorization change plus tests**

```text
fix(api): reject unpaired state-changing cursor requests

Ensure cursor mutation endpoints require a valid session.
Add regression coverage for requests without session cookies.
```

**Multiple related files in one commit**

```text
feat(motion): calibrate orientation and filter small device movements

Update the browser motion controller and pure mapping helper.
Add focused tests for dead zones and movement bounds.
```

## Existing history

Historical commit messages are intentionally preserved. Replacing published commit messages would require rewriting commit objects and changing hashes, which may disrupt forks, pull requests, references, or collaborators. Do not rewrite shared history merely to create a file-by-file appearance; use these descriptions for **future genuine changes** instead.

## Branding reference

**AirCursor — One desktop. Four ways to control.**

Four interaction modes: **Touch · Tilt · Gestures · Voice**.
