"""
main.py
-------
Entry point for the Windows-side audio engine.

Big picture loop:
  Windows audio out
       |
       v
  AudioCapture  -> grabs live speaker audio chunks
       |
       v
  BassDetector  -> turns each chunk into intensity 0..255
       |
       v
  UdpSender     -> sends that number to the ESP32 over Wi-Fi
       |
       v
  ESP32 firmware -> drives the RGB LED with PWM
"""

# Import our project modules.
# These live in the same python/ folder.
from audio_capture import AudioCapture
from bass_detection import BassDetector

# Import tunables from config.py so we don't hardcode numbers here.
from config import (
    ATTACK,
    BASS_HIGH_HZ,
    BASS_LOW_HZ,
    CHUNK_SIZE,
    ESP32_IP,
    GAIN,
    INTENSITY_DEADZONE,
    RELEASE,
    SAMPLE_RATE,
    UDP_PORT,
)
from udp_sender import UdpSender


def main() -> None:
    """
    Create the three workers, then run the forever processing loop.
    """

    # Worker 1: capture live system audio from the default speaker.
    capture = AudioCapture(SAMPLE_RATE, CHUNK_SIZE)

    # Worker 2: extract bass energy and convert it to 0..255.
    detector = BassDetector(
        sample_rate=SAMPLE_RATE,
        low_hz=BASS_LOW_HZ,
        high_hz=BASS_HIGH_HZ,
        gain=GAIN,
        attack=ATTACK,
        release=RELEASE,
        intensity_deadzone=INTENSITY_DEADZONE,
    )

    # Worker 3: send intensity packets to the ESP32.
    sender = UdpSender(ESP32_IP, UDP_PORT)

    print(f"Sending bass intensity to {ESP32_IP}:{UDP_PORT}")
    print("Press Ctrl+C to stop.")

    try:
        # capture.chunks() is an infinite generator.
        # Each loop iteration gets the next ~46 ms of audio.
        for audio_chunk in capture.chunks():
            # Analyze this chunk and get a brightness value.
            intensity = detector.get_intensity(audio_chunk)

            # Send that brightness to the ESP32 immediately.
            sender.send_intensity(intensity)

            # Print on one updating line:
            # \r returns the cursor to the start of the line
            # :3d prints the number in a 3-character-wide field
            # end="" avoids adding a newline each time
            print(f"\rBass intensity: {intensity:3d}", end="")

    except KeyboardInterrupt:
        # User pressed Ctrl+C. Exit the loop cleanly.
        print("\nStopping.")

    finally:
        # Always runs, whether we quit normally or via Ctrl+C.
        # Turn the LED off and free the network socket.
        sender.send_intensity(0)
        sender.close()


# Python sets __name__ to "__main__" only when you run this file directly:
#   python main.py
# That prevents main() from auto-running if another file imports this module.
if __name__ == "__main__":
    main()
