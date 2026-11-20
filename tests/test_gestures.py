"""Tests for gesture settings independent of the webcam and MediaPipe."""
import json
from types import SimpleNamespace
import pytest

from gesture_control import distance, load_config


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
