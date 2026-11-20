"""
config.py
---------
Central place for all tunables used by the Python audio engine.

Why a separate config file?
  - You can change settings without digging through algorithm code.
  - main.py, audio_capture.py, and bass_detection.py all import from here.
  - Keeps "magic numbers" out of the logic files.
"""

# ============================================================
# NETWORK SETTINGS
# ============================================================

# IP address of your ESP32 on your local Wi-Fi network.
# Find this in Arduino Serial Monitor after the ESP32 connects.
# Example Serial output: "ESP32 IP address: 192.168.1.105"
ESP32_IP = "192.168.2.181"

# UDP port the ESP32 is listening on.
# Must match UDP_PORT in the Arduino firmware exactly.
UDP_PORT = 4210


# ============================================================
# AUDIO CAPTURE SETTINGS
# ============================================================

# How many audio samples per second to capture from Windows.
# 44100 Hz is CD-quality and works well for music.
# Higher = more detail but more CPU work.
SAMPLE_RATE = 44100

# How many samples we process in one batch ("chunk").
# 2048 samples at 44100 Hz is about 46 milliseconds of audio:
#   2048 / 44100 ≈ 0.046 seconds
# Smaller chunks = faster reaction, but noisier measurements.
# Larger chunks = smoother, but more lag.
CHUNK_SIZE = 2048


# ============================================================
# BASS FILTER SETTINGS
# ============================================================

# Lowest bass frequency we want to keep (in Hertz).
# Kick drums and deep bass usually start around here.
BASS_LOW_HZ = 40

# Highest bass frequency we want to keep (in Hertz).
# Above this, vocals / snares / cymbals start to dominate.
# Together, 40-150 Hz is a classic "bass energy" window.
BASS_HIGH_HZ = 150


# ============================================================
# OUTPUT TUNING
# ============================================================

# Multiplies the measured bass energy before converting to 0-255.
# Think of this as LED sensitivity:
#   - Increase GAIN if the LED barely lights up during loud songs.
#   - Decrease GAIN if the LED is maxed out even on quiet songs.
GAIN = 12.0

# Exponential smoothing amount applied to bass energy over time.
# Formula used later:
#   smoothed = SMOOTHING * old + (1 - SMOOTHING) * new
#
#   0.0  -> no smoothing (very twitchy / reactive)
#   0.25 -> mild smoothing (good starting point)
#   0.8  -> heavy smoothing (slow, floaty feel)
SMOOTHING = 0.25
