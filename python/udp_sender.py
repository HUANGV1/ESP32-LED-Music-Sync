"""
udp_sender.py
-------------
Tiny networking helper that sends bass intensity values to the ESP32.

UDP = User Datagram Protocol.
  - Fast, lightweight network packets
  - No connection handshake
  - No guarantee of delivery
  - Perfect for real-time LED updates where a missed packet is fine
"""

# Python's built-in networking library.
# We only need this; no third-party networking package required.
import socket


class UdpSender:
    """
    Owns one UDP socket and knows the ESP32's address.

    Example packet contents:
      "0"   -> LED off
      "128" -> medium brightness
      "255" -> full brightness
    """

    def __init__(self, host: str, port: int) -> None:
        # Store destination as a (IP, port) tuple.
        # socket.sendto() expects exactly this format.
        self.address = (host, port)

        # Create a UDP socket.
        # AF_INET  = IPv4 addresses (like 192.168.1.105)
        # SOCK_DGRAM = datagram mode = UDP (not TCP)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_intensity(self, intensity: int) -> None:
        """
        Clamp intensity into 0..255, convert to text bytes, and send.
        """

        # Force the value into the legal PWM range.
        # int() protects us if a float somehow gets passed in.
        value = max(0, min(255, int(intensity)))

        # Convert number -> text -> bytes.
        # Example: 128 -> "128" -> b"128"
        # ASCII is fine because we only send digits.
        message = str(value).encode("ascii")

        # Fire-and-forget send to the ESP32.
        # No reply is expected; the ESP32 just updates the LED.
        self.socket.sendto(message, self.address)

    def close(self) -> None:
        """
        Release the OS network socket when we are done.
        Always call this on shutdown so Windows can free the handle.
        """
        self.socket.close()
