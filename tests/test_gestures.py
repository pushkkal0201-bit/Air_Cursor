"""Tests for gesture settings independent of the webcam and MediaPipe."""
import json
from types import SimpleNamespace
import pytest

from gesture_control import DwellTracker, distance, load_config


def test_default_config(tmp_path):
    config = load_config(tmp_path / "missing.json")
    assert config["gesture_actions"]["index_pinch"] == "left_click"
    assert config["smoothing"] > 0


def test_custom_gesture_mapping(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"gesture_actions": {
        "index_pinch": "right_click",
        "middle_pinch": "double_click"
    }}), encoding="utf-8")
    config = load_config(path)
    assert config["gesture_actions"]["index_pinch"] == "right_click"
    assert config["gesture_actions"]["middle_pinch"] == "double_click"


def test_reject_unsupported_action(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"gesture_actions": {"index_pinch": "run_shell"}}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)


def test_distance():
    points = [SimpleNamespace(x=0, y=0), SimpleNamespace(x=3, y=4)]
    assert distance(points, 0, 1) == 5.0

def test_dwell_click_once_until_movement():
    tracker = DwellTracker(seconds=1.0, radius=0.02)
    assert not tracker.update(0.50, 0.50, 0.0)
    assert not tracker.update(0.51, 0.50, 0.9)
    assert tracker.update(0.51, 0.50, 1.01)
    assert not tracker.update(0.51, 0.50, 2.1)
    assert not tracker.update(0.54, 0.50, 2.2)
    assert not tracker.update(0.54, 0.50, 2.5)
    assert tracker.update(0.54, 0.50, 3.3)


def test_dwell_disabled():
    tracker = DwellTracker(seconds=0, radius=0.018)
    assert not tracker.update(0.5, 0.5, 0)
    assert not tracker.update(0.5, 0.5, 60)


@pytest.mark.parametrize("bad", [
    {"dwell_radius": -1},
    {"dwell_click_seconds": 9},
    {"deadzone_pixels": 100},
])
def test_reject_invalid_accessibility_settings(tmp_path, bad):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)
