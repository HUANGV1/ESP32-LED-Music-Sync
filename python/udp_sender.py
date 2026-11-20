"""
Fire-and-forget UDP transport for LED frames.

Protocol (ASCII):
  Preferred: "R,G,B" with each channel in [0, 255]
  Legacy:    a single integer (firmware still accepts this for smoke tests)

UDP is intentional: dropped frames are preferable to blocking the audio loop.
"""

import socket


class UdpSender:
    def __init__(self, host: str, port: int) -> None:
        self.address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_rgb(self, red: int, green: int, blue: int) -> None:
        red = max(0, min(255, int(red)))
        green = max(0, min(255, int(green)))
        blue = max(0, min(255, int(blue)))
        self.socket.sendto(f"{red},{green},{blue}".encode("ascii"), self.address)

    def send_intensity(self, intensity: int) -> None:
        """Compat helper: broadcast one intensity across all channels."""
        value = max(0, min(255, int(intensity)))
        self.send_rgb(value, value, value)

    def close(self) -> None:
        self.socket.close()
