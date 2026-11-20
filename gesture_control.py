"""Optional webcam hand-gesture mouse for AirCursor 2.0.

Run after installing requirements-vision.txt: python gesture_control.py
Close the webcam window with Q or Escape.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time

DEFAULTS = {
    "camera": 0,
    "smoothing": 0.28,
    "pinch_threshold": 0.32,
    "scroll_speed": 24,
    "deadzone_pixels": 3,
    "dwell_click_seconds": 0.0,
    "dwell_radius": 0.018,
    "gesture_actions": {"index_pinch": "left_click", "middle_pinch": "right_click"},
}
ALLOWED_ACTIONS = {"left_click", "right_click", "double_click", "middle_click", "none"}


def distance(points, a, b):
    return math.hypot(points[a].x - points[b].x, points[a].y - points[b].y)


class DwellTracker:
    """Trigger once after a finger remains within a small area for a set time."""

    def __init__(self, seconds, radius):
        self.seconds = seconds
        self.radius = radius
        self.reset()

    def reset(self):
        self.anchor = None
        self.since = None
        self.triggered = False

    def update(self, x, y, now):
        if self.seconds <= 0:
            return False
        if self.anchor is None or math.hypot(x - self.anchor[0], y - self.anchor[1]) > self.radius:
            self.anchor = (x, y)
            self.since = now
            self.triggered = False
            return False
        if not self.triggered and now - self.since >= self.seconds:
            self.triggered = True
            return True
        return False


def load_config(path):
    settings = dict(DEFAULTS)
    settings["gesture_actions"] = dict(DEFAULTS["gesture_actions"])
    if path.exists():
        incoming = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(incoming, dict):
            raise ValueError("config must contain a JSON object")
        for key in ("camera", "smoothing", "pinch_threshold", "scroll_speed", "deadzone_pixels", "dwell_click_seconds", "dwell_radius"):
            if key in incoming:
                settings[key] = incoming[key]
        settings["gesture_actions"].update(incoming.get("gesture_actions", {}))
    settings["camera"] = int(settings["camera"])
    settings["smoothing"] = float(settings["smoothing"])
    settings["pinch_threshold"] = float(settings["pinch_threshold"])
    settings["scroll_speed"] = float(settings["scroll_speed"])
    settings["deadzone_pixels"] = int(settings["deadzone_pixels"])
    settings["dwell_click_seconds"] = float(settings["dwell_click_seconds"])
    settings["dwell_radius"] = float(settings["dwell_radius"])
    if not 0 < settings["smoothing"] <= 1:
        raise ValueError("smoothing must be in (0, 1]")
    if not 0.1 <= settings["pinch_threshold"] <= 0.7:
        raise ValueError("pinch_threshold must be between 0.1 and 0.7")
    if not 1 <= settings["scroll_speed"] <= 100:
        raise ValueError("scroll_speed must be between 1 and 100")
    if not 0 <= settings["deadzone_pixels"] <= 30:
        raise ValueError("deadzone_pixels must be between 0 and 30")
    if not 0 <= settings["dwell_click_seconds"] <= 5:
        raise ValueError("dwell_click_seconds must be between 0 and 5 (0 disables dwell)")
    if not 0.005 <= settings["dwell_radius"] <= 0.08:
        raise ValueError("dwell_radius must be between 0.005 and 0.08")
    if any(action not in ALLOWED_ACTIONS for action in settings["gesture_actions"].values()):
        raise ValueError("gesture_actions supports left_click, right_click, double_click, middle_click, none")
    return settings


def perform_action(pyautogui, action):
    if action == "left_click":
        pyautogui.click(button="left")
    elif action == "right_click":
        pyautogui.click(button="right")
    elif action == "double_click":
        pyautogui.doubleClick()
    elif action == "middle_click":
        pyautogui.click(button="middle")


def main():
    parser = argparse.ArgumentParser(description="Webcam-based hand control for AirCursor")
    parser.add_argument("--config", default="gesture_config.json", help="JSON gesture settings")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    try:
        import cv2
        import mediapipe as mp
        import pyautogui
    except ImportError as exc:
        raise SystemExit("Install optional packages: python -m pip install -r requirements-vision.txt") from exc

    pyautogui.FAILSAFE = True
    width, height = pyautogui.size()
    cap = cv2.VideoCapture(config["camera"])
    if not cap.isOpened():
        raise SystemExit("Could not open the webcam. Check permissions and camera index.")

    smoothed = None
    last_pinch = None
    last_action_time = 0.0
    last_scroll_y = None
    scroll_remainder = 0.0
    dwell = DwellTracker(config["dwell_click_seconds"], config["dwell_radius"])
    drawing = mp.solutions.drawing_utils
    hands_lib = mp.solutions.hands
    print("Webcam active. Index finger = move, thumb-index pinch = left click,")
    print("thumb-middle pinch = right click, index+middle fingers = scroll. Q = quit.")
    if config["dwell_click_seconds"]:
        print("Dwell click enabled: hold the index finger still for {:.1f}s.".format(config["dwell_click_seconds"]))
    try:
        with hands_lib.Hands(max_num_hands=1, min_detection_confidence=0.65,
                             min_tracking_confidence=0.55) as hands:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("Camera read failed.")
                    break
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = hands.process(rgb)
                label = "No hand detected"
                if result.multi_hand_landmarks:
                    hand = result.multi_hand_landmarks[0]
                    points = hand.landmark
                    drawing.draw_landmarks(frame, hand, hands_lib.HAND_CONNECTIONS)
                    palm = max(distance(points, 5, 17), 0.01)
                    pinch_distance = config["pinch_threshold"] * palm
                    index_pinch = distance(points, 4, 8) < pinch_distance
                    middle_pinch = distance(points, 4, 12) < pinch_distance and not index_pinch
                    pinch = "index_pinch" if index_pinch else ("middle_pinch" if middle_pinch else None)
                    now = time.monotonic()
                    if pinch and pinch != last_pinch and now - last_action_time > 0.40:
                        action = config["gesture_actions"].get(pinch, "none")
                        perform_action(pyautogui, action)
                        label = "Gesture: " + action
                        last_action_time = now
                    last_pinch = pinch

                    index_up = points[8].y < points[6].y
                    middle_up = points[12].y < points[10].y
                    ring_up = points[16].y < points[14].y
                    if not pinch and index_up and middle_up and not ring_up:
                        dwell.reset()
                        label = "Two-finger scroll"
                        avg_y = (points[8].y + points[12].y) / 2
                        if last_scroll_y is not None:
                            scroll_remainder += (last_scroll_y - avg_y) * config["scroll_speed"]
                            step = math.trunc(scroll_remainder)
                            if step:
                                pyautogui.scroll(max(-8, min(8, step)))
                                scroll_remainder -= step
                        last_scroll_y = avg_y
                    else:
                        last_scroll_y = None
                        scroll_remainder = 0.0
                        if not pinch and index_up and not middle_up:
                            label = "Point to move"
                            # Keep away from display corners so the fail-safe stays accessible.
                            x = min(0.95, max(0.05, points[8].x))
                            y = min(0.95, max(0.05, points[8].y))
                            target = (int(x * width), int(y * height))
                            if smoothed is None:
                                smoothed = target
                            alpha = config["smoothing"]
                            smoothed = (smoothed[0] + (target[0] - smoothed[0]) * alpha,
                                        smoothed[1] + (target[1] - smoothed[1]) * alpha)
                            current_x, current_y = pyautogui.position()
                            if math.hypot(smoothed[0] - current_x, smoothed[1] - current_y) >= config["deadzone_pixels"]:
                                pyautogui.moveTo(int(smoothed[0]), int(smoothed[1]), duration=0)
                            if dwell.update(x, y, now):
                                pyautogui.click(button="left")
                                label = "Dwell click"
                            elif dwell.since is not None and dwell.seconds > 0 and not dwell.triggered:
                                elapsed = min(100, int(100 * (now - dwell.since) / dwell.seconds))
                                label = "Point to move | Dwell {}%".format(elapsed)
                        else:
                            dwell.reset()
                else:
                    last_pinch = None
                    last_scroll_y = None
                    smoothed = None
                    dwell.reset()
                cv2.putText(frame, label, (18, 33), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (80, 255, 130), 2)
                cv2.imshow("AirCursor - Hand Gesture Control (Q to quit)", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
