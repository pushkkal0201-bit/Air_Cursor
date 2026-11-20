"""Small reproducible API benchmark with fake input (never controls a desktop).

Usage: python scripts/benchmark_api.py --requests 600
Reports indicative in-process Flask timings; not a LAN or real-device benchmark.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aircursor.server import create_app  # noqa: E402


class FakeMouse:
    def __init__(self):
        self.x, self.y = 100, 100
    def position(self):
        return self.x, self.y
    def move_rel(self, dx, dy):
        self.x += dx
        self.y += dy
    def move_to(self, x, y):
        self.x, self.y = x, y
    def click(self, **kwargs):
        pass
    def scroll(self, **kwargs):
        pass
    def press(self, key):
        pass


def benchmark(count):
    if count < 1 or count > 100000:
        raise ValueError("requests must be between 1 and 100000")
    app = create_app(mouse_instance=FakeMouse(), pairing_pin="123456")
    app.testing = True
    with app.test_client() as client:
        pair = client.post("/api/v1/pair", json={"pin": "123456"},
                           headers={"X-AirCursor-Client": "1"})
        if pair.status_code != 200:
            raise RuntimeError("test pairing failed")
        samples = []
        started = time.perf_counter()
        for _ in range(count):
            t0 = time.perf_counter()
            response = client.patch("/api/v1/cursor", json={"dx": 1, "dy": 0},
                                    headers={"X-AirCursor-Client": "1"})
            if response.status_code != 200:
                raise RuntimeError("benchmark API request failed: " + str(response.status_code))
            samples.append(1000 * (time.perf_counter() - t0))
        seconds = time.perf_counter() - started
    samples.sort()
    return {
        "requests": count,
        "seconds": round(seconds, 4),
        "requests_per_second": round(count / seconds, 1),
        "p50_ms": round(statistics.median(samples), 3),
        "p95_ms": round(samples[max(0, int(count * 0.95) - 1)], 3),
        "mode": "headless in-process Flask test client; no LAN or OS input",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=500)
    args = parser.parse_args()
    print(json.dumps(benchmark(args.requests), indent=2))
