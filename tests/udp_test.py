"""Smoke-test RGB UDP path without involving the audio pipeline.

Cycles primary colors so wiring / firmware parsing can be verified in isolation.
Requires ESP32_IP in python/config.py to match the board.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from config import ESP32_IP, UDP_PORT
from udp_sender import UdpSender

SAMPLES = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 255),
    (0, 0, 0),
]


def main() -> None:
    sender = UdpSender(ESP32_IP, UDP_PORT)
    print(f"RGB UDP test -> {ESP32_IP}:{UDP_PORT}")

    try:
        for red, green, blue in SAMPLES:
            sender.send_rgb(red, green, blue)
            print(f"Sent {red},{green},{blue}")
            time.sleep(1.5)
    finally:
        sender.send_rgb(0, 0, 0)
        sender.close()


if __name__ == "__main__":
    main()
